import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# --- Initialize Extensions globally ---
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    # 1. Path setup (TemplateNotFound fix)
    basedir = os.path.abspath(os.path.dirname(__file__))
    template_path = os.path.join(basedir, '..', 'templates')
    
    # 2. Initialize Flask
    app = Flask(__name__, template_folder=template_path)
    
    # Standard Flask setup (assuming config is correct)
    app.config.from_object("config.Config")

    # 3. Initialize Extensions with the app instance
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "main.login" # IMPORTANT: Use 'main.login' for Blueprint

    # FIX: Register the Blueprint
    from .routes import bp # Import the Blueprint object
    app.register_blueprint(bp) # Register it with the app instance
    
    with app.app_context():
        # Create database tables inside the application context
        db.create_all()

    return app