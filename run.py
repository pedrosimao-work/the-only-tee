from app import create_app  # Import that application factory from the app package


app = create_app()  # Create the Flask application instance


if __name__ == "__main__":  # Check if this file is being run directly
    app.run(debug=True)  # Start the Flask development server with debug mode enabled
