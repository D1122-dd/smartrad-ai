import mysql.connector
from mysql.connector import Error, pooling
from app.config import Config
import logging
import threading
import contextlib

logger = logging.getLogger(__name__)

class Database:
    """Database connection handler with pooling"""
    
    _pool = None
    _local = threading.local()
    
    @classmethod
    def initialize(cls):
        """Initialize the connection pool"""
        if cls._pool is None:
            try:
                cls._pool = mysql.connector.pooling.MySQLConnectionPool(
                    pool_name="smartrad_pool",
                    pool_size=10,
                    pool_reset_session=True,
                    host=Config.DB_HOST,
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD,
                    database=Config.DB_NAME,
                    port=Config.DB_PORT,
                    autocommit=False,
                    charset="utf8mb4",
                    use_unicode=True
                )
                logger.info("Database connection pool initialized")
            except Error as e:
                logger.error(f"Error while initializing MySQL pool: {e}")
                raise

    @classmethod
    def get_connection(cls):
        """Get a connection from the pool"""
        if cls._pool is None:
            cls.initialize()
        try:
            return cls._pool.get_connection()
        except Error as e:
            logger.error(f"Failed to get connection from pool: {e}")
            # Fallback to direct connection if pool fails
            return mysql.connector.connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                port=Config.DB_PORT,
                autocommit=False
            )
    
    @classmethod
    def get_cursor(cls):
        """
        Get a cursor. Reuses connection per thread.
        Note: You should prefer the context manager `with db.cursor() as cursor:`
        """
        if not hasattr(cls._local, 'connection') or cls._local.connection is None:
            cls._local.connection = cls.get_connection()
        
        if not cls._local.connection.is_connected():
            cls._local.connection = cls.get_connection()

        return cls._local.connection.cursor(dictionary=True)

    @contextlib.contextmanager
    def cursor(self):
        """Context manager for database cursors"""
        c = self.get_cursor()
        try:
            yield c
        finally:
            # Consume any remaining results to avoid "Unread result found"
            try:
                while c.nextset():
                    pass
            except:
                pass
            c.close()
    
    @classmethod
    def commit(cls):
        """Commit transaction on the thread-local connection"""
        if hasattr(cls._local, 'connection') and cls._local.connection:
            cls._local.connection.commit()
    
    @classmethod
    def rollback(cls):
        """Rollback transaction on the thread-local connection"""
        if hasattr(cls._local, 'connection') and cls._local.connection:
            cls._local.connection.rollback()
    
    @classmethod
    def close(cls):
        """
        In this pooled version, close() should return the connection to the pool.
        We'll clear the thread-local state.
        """
        if hasattr(cls._local, 'connection') and cls._local.connection:
            try:
                cls._local.connection.close()
            except:
                pass
            cls._local.connection = None

# Create a singleton instance
db = Database()