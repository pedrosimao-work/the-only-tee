from flask import Blueprint, render_template  # Import Blueprint for route organization

main = Blueprint("main", __name__)  # Create a blueprint named main to group public website routes

@main.route("/")  # Register the homepage URL route
def home():  # Define the function that runs when a user visits the homepage
    return render_template("home.html")  # Render and return the homepage template

@main.route("/archive")  # Register the archive page URL route
def archive():  # Define the function that runs when a user visits the archive page
    return render_template("archive.html")  # Render and return the archive template

@main.route("/about")  # Register the about page URL route
def about():  # Define the function that runs when a user visits the about page
    return render_template("about.html")  # Render and return the about template