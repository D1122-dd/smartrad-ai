from flask import Flask, app, render_template, request, jsonify, redirect, url_for, make_response
from flask_cors import CORS
from flask_mail import Mail
import logging
import os
from app.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
mail = Mail()

def create_app():
    """
    Application factory pattern for Flask app
    
    Returns:
        Flask application instance
    """
    
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    
    # Initialize extensions
    mail.init_app(app)
    
    # Enable CORS for web frontend
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Initialize Database pool
    from app.database import db
    db.initialize()

    # Pre-load AI Model (Eager Loading)
    # This prevents the 'first take' delay by loading the 63MB model into RAM now.
    from app.services.prediction_service import load_model
    load_model()

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.close()

    
    # Register blueprints (routes)
    from app.routes.auth import auth_bp
    from app.routes.user import user_bp
    from app.routes.ris import ris_bp
    from app.routes.rooms import rooms_bp
    from app.routes.analytics import analytics_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(ris_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(analytics_bp)

    # Start background tasks ONLY in the main process (prevents duplicates in debug mode)
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        # Start the RIS file-watcher background thread
        from app.services.ris_watcher import start_watcher
        start_watcher()

        # Start the Orchestrator dispatch loop
        from app.services.orchestrator import start_orchestrator
        start_orchestrator()

    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return {
            'status': 'healthy',
            'message': 'SmartRAD AI API is running'
        }, 200
    
    # Global template context processor for translation
    @app.context_processor
    def inject_translation_engine():
        from app.utils.translations import translate
        current_lang = request.cookies.get('lang', 'ar')
        return dict(
            lang=current_lang,
            t=translate
        )
    
    @app.route('/set-lang/<lang>')
    def set_language(lang):
        if lang not in ['ar', 'en']:
            lang = 'ar'  # fallback to Arabic

    # Redirect back to the page user came from (or to register if no referrer)
        response = make_response(redirect(request.referrer or url_for('register_page')))

    # Set cookie for 1 year
        response.set_cookie('lang', lang, max_age=31536000, httponly=True, samesite='Lax')

        return response

    # Root endpoint — Redirect to Login Page
    @app.route('/')
    def index():
        return redirect(url_for('login_page'))

    # ---- Auth Pages ----
    @app.route('/register')
    def register_page():
        return render_template('register.html')

    @app.route('/login')
    def login_page():
        return render_template('login.html')

    @app.route('/forgot-password')
    def forgot_password_page():
        return render_template('forgot_password.html')

    @app.route('/reset-password')
    def reset_password_page():
        return render_template('reset_password.html')

    # ---- Protected Pages ----
    @app.route('/profile')
    def profile_page():
        return render_template('profile.html')

    @app.route('/settings')
    def settings_page():
        return render_template('settings.html')

    @app.route('/dashboard')
    def dashboard_page():
        return render_template('dashboard.html')

    @app.route('/performance')
    def performance_page():
        return render_template('performance.html')

    @app.route('/history')
    def history_page():
        return render_template('history.html')

    @app.route('/queue')
    def queue_page():
        return render_template('queue.html')

    logger.info("Flask app created successfully")

    return app