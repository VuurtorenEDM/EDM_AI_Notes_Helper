from flask import Flask
from flask_sqlalchemy import SQLAchemy
from flask_login import LoginManager

db = SQLAchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "login"

    with app.app_context():
        from . import routes
        db.create_all()


    return app