from flask import Blueprint, render_template  # Import Blueprint for route organization

main = Blueprint("main", __name__)  # Create a blueprint named main to group public website routes

@main.route("/")  # Register the homepage URL route
def home():  # Define the function that runs when a user visits the homepage
    active_drop = {  # Create a temporary Python dictionary representing the current active drop
        "drop_number": "0001",  # Store the unique drop number as a string to preserve leading zeros
        "season": 1,  # Store the season number as an integer
        "name": "Silent Horizon",  # Store the public name of the current drop
        "description": "A one-time T-shirt drop available for a limited window before entering the Archive Collection.",  # Store the current drop description
        "price": 59,  # Store the fixed price of the current drop as an integer
        "status": "active",  # Store the current lifecycle status of the drop
        "days_left": 7,  # Store the number of daus remaining before the drop expires
    }  # Close the active_drop dictionary

    return render_template("home.html", active_drop=active_drop)  # Render the homepage and send active_drop data to the template


@main.route("/archive")  # Register the archive page URL route
def archive():  # Define the function that runs when a user visits the archive page
    return render_template("archive.html")  # Render and return the archive template

@main.route("/about")  # Register the about page URL route
def about():  # Define the function that runs when a user visits the about page
    return render_template("about.html")  # Render and return the about template