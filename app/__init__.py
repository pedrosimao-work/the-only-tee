from flask import Flask  # Import the Flask class used to create the web application


def create_app():  # Define the application factory function
    app = Flask(__name__)  # Create a new Flask application instance

    app.config["SECRET_KEY"] = "temporary_development_key"  # Set a temporary secret key for local development

    @app.route("/")  # Register the homepage route
    def home():  # Define the function that runs when the homepage is visited
        return "The Only Tee is running."  # Return a simple test message in the browser

    return app  # Return the configured Flask application

