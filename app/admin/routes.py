from functools import wraps  # Import wraps so custom decorators preserve function metadata

from flask import Blueprint, abort, flash, redirect, render_template, url_for  # Import Flask helpers for admin routes
from flask_login import current_user, login_required  # Import login helpers for protected admin routes

from app.admin.forms import DropForm  # Import the drop creation form
from app.extensions import db  # Import the database object so admin routes can save records
from app.models import Drop  # Import the Drop model so admin routes can query and create drops
from app.validators import validate_drop_status  # Import the reusable drop status validation function


admin = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(route_function):  # Define a reusable decorator for admin-only routes
    @wraps(route_function)  # Preserve the wrapped route function name and metadata
    def wrapper(*args, **kwargs):  # Define the wrapper that runs before the protected route
        if not current_user.is_admin:  # Check if the current logged-in user is not an admin
            abort(403)  # Stop the request with a 403 Forbidden error

        return route_function(*args, **kwargs)  # Run the original route if the user is an admin

    return wrapper  # Return the protected wrapper function


@admin.route("/")  # Register the admin dashboard route
@login_required  # Require the user to be logged in
@admin_required  # Require the logged-in user to be an admin
def dashboard():  # Define the function that renders the admin dashboard
    total_drops = Drop.query.count()  # Count all drops in the database
    active_drops = Drop.query.filter_by(status="active").count()  # Count active drops in the database
    archived_drops = Drop.query.filter_by(status="archived").count()  # Count archived drops in the database
    draft_drops = Drop.query.filter_by(status="draft").count()  # Count draft drops in the database

    return render_template(  # Render the admin dashboard template
        "admin/dashboard.html",  # Use the admin dashboard template file
        total_drops=total_drops,  # Send the total drop count to the template
        active_drops=active_drops,  # Send the active drop count to the template
        archived_drops=archived_drops,  # Send the archived drop count to the template
        draft_drops=draft_drops,  # Send the draft drop count to the template
    )  # Close the render_template call


@admin.route("/drops")  # Register the admin drops list route
@login_required  # Require the user to be logged in
@admin_required  # Require the logged-in user to be an admin
def drops():  # Define a function that renders the admin drop list
    all_drops = Drop.query.order_by(Drop.drop_number.asc()).all()  # Query all drops by drop number

    return render_template("admin/drops.html", drops=all_drops)  # Render the drop list template with all drops


@admin.route("/drops/create", methods=["GET", "POST"])  # Register the create-drop route for GET and POST requests
@login_required  # Require the user to be logged in
@admin_required  # Require the logged-in user to be an admin
def create_drop():  # Define the function that handles creating new drops
    form = DropForm()  # Create a new drop form instance

    if form.validate_on_submit():  # Check if the form was submitted and passed validation
        existing_drop = Drop.query.filter_by(drop_number=form.drop_number.data.strip()).first()  # Look for an existing drop with the same drop number

        if existing_drop:  # Check if another drop already uses this drop number
            flash("A drop with that number already exists.", "danger")  # Show a duplicate drop error message
            return render_template("admin/create_drop.html", form=form)  # Re-render the create-drop form

        validated_status = validate_drop_status(form.status.data)  # Validate the submitted status using shared validation logic

        drop = Drop(  # Create a new Drop object from the form data
            drop_number=form.drop_number.data.strip(),  # Store the cleaned drop number
            season=form.season.data,  # Store the submitted season number
            name=form.name.data.strip(),  # Store the cleaned drop name
            description=form.description.data.strip(),  # Store the cleaned drop description
            price=form.price.data,  # Store the submitted price
            status=validated_status,  # Store the validated lifecycle status
            image_url=form.image_url.data.strip() or None,  # Store the cleaned image URL or None
        )  # Close the Drop object creation

        db.session.add(drop)  # Add the new drop to the database session
        db.session.commit()  # Save the new drop permanently to the database

        flash("Drop created successfully.", "success")  # Show a success message after creating the drop
        return redirect(url_for("admin.drops"))  # Redirect the admin user to the drop list

    return render_template("admin/create_drop.html", form=form)  # Render the create-drop form for GET requests or invalid submissions