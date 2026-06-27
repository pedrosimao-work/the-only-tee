from flask_login import LoginManager  # Import LoginManager to manage user sessions and authentication
from flask_sqlalchemy import SQLAlchemy  # Import SQLAlchemy integration for Flask

db = SQLAlchemy()  # Create the database extension object without binding it to the app yet
login_manager = LoginManager()  # Create the login manager extension object without binding it to the app yet
