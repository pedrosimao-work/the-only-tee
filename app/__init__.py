from flask import Flask  # Import Flask class used to create the web application


def create_app():  # Define the application factory function used to build and configure the Flask app
    app =  Flask(__name__)  # Create a new Flask application instance using the current package name

    app.config["SECRET_KEY"] = "temporary-development-key"  # Set a temporary secret key for local development sessions

    from app.routes import main  # Import the main routes blueprint after creating the app to avoid circular imports

    app.register_blueprint(main)  # Register the main blueprint so its routes become available in the app

    return app  # Return the fully configured Flask application instance