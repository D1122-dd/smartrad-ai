# Note this is the main entery file for the whole app to run
from app import create_app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='localhost', port=5000)