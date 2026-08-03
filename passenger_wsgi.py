import os  # Import os so the project path can be resolved safely
import sys  # Import sys so the project folder can be added to Python's import path


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))  # Resolve the absolute path to this project folder


if PROJECT_ROOT not in sys.path:  # Check if the project folder is missing from Python's import path
    sys.path.insert(0, PROJECT_ROOT)  # Add the project folder so DirectAdmin Passenger can import the app package


from app import create_app  # Import the Flask application factory after the project path is configured


application = create_app()  # Expose the Flask app as the WSGI callable expected by Passenger