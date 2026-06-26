from flask import Blueprint, render_template  # Import Blueprint for route organization

from app.constants import DROP_STATUS_ACTIVE, DROP_STATUS_ARCHIVED  # Import reusable status constants for database queries
from app.models import Drop  # Import the Drop model so routes can query drop records from the database


main = Blueprint("main", __name__)  # Create a blueprint named main to group public website routes


@main.route("/")  # Register the homepage URL route
def home():  # Define the function that runs when a user visits the homepage
    active_drop = Drop.query.filter_by(status=DROP_STATUS_ACTIVE).first()  # Query the database for the first drop with active status

    return render_template("home.html", active_drop=active_drop)  # Render the homepage and send active_drop data to the template


@main.route("/archive")  # Register the archive page URL route
def archive():  # Define the function that runs when a user visits the archive page
    archived_drops = Drop.query.filter_by(status=DROP_STATUS_ARCHIVED).order_by(Drop.drop_number.asc()).all()  # Query archived drops ordered by drop number

    return render_template("archive.html", archived_drops=archived_drops)  # Render the archive page and send archived drops to the template


@main.route("/about")  # Register the about page URL route
def about():  # Define the function that runs when a user visits the about page
    return render_template("about.html")  # Render and return the about template