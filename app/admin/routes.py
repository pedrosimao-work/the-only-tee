from functools import wraps  # Import wraps so custom decorators preserve function metadata

from flask import Blueprint, abort, current_app, flash, redirect, render_template, url_for  # Import Flask helpers for admin routes, app config, feedback, redirects, and templates
from flask_login import current_user, login_required  # Import login helpers for protected admin routes
from sqlalchemy.exc import IntegrityError  # Import IntegrityError so duplicate drop numbers can be handled safely

from app.admin.forms import DropForm, EmptyForm  # Import admin forms for drop creation, editing, and button-only POST actions
from app.constants import DROP_STATUS_ACTIVE, DROP_STATUS_ARCHIVED, DROP_STATUS_DRAFT  # Import reusable status constants
from app.extensions import db  # Import the database object so admin routes can save and delete records
from app.models import Drop, Order  # Import Drop and Order models so admin routes can manage drops and inspect orders
from app.services.printify import PrintifyAPIError, PrintifyConfigError, PrintifyFulfillmentError, submit_order_to_printify, sync_drop_with_printify  # Import Printify sync and fulfillment helpers
from app.validators import validate_drop_status, validate_product_type  # Import reusable drop validation functions


admin = Blueprint("admin", __name__, url_prefix="/admin")  # Create the admin blueprint with an /admin URL prefix


def clean_optional_text(value):  # Define a helper function for cleaning optional text form fields
    if not value:  # Check if the submitted value is missing or empty
        return None  # Store empty optional values as None in the database

    return value.strip() or None  # Strip whitespace and return None if the result is empty


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
    active_drops = Drop.query.filter_by(status=DROP_STATUS_ACTIVE).count()  # Count active drops in the database
    archived_drops = Drop.query.filter_by(status=DROP_STATUS_ARCHIVED).count()  # Count archived drops in the database
    draft_drops = Drop.query.filter_by(status=DROP_STATUS_DRAFT).count()  # Count draft drops in the database

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
def drops():  # Define the function that renders the admin drop list
    all_drops = Drop.query.order_by(Drop.drop_number.asc()).all()  # Query all drops ordered by drop number
    sync_form = EmptyForm()  # Create a CSRF-protected form for Printify sync buttons
    delete_form = EmptyForm()  # Create a CSRF-protected form for drop delete buttons

    return render_template("admin/drops.html", drops=all_drops, sync_form=sync_form, delete_form=delete_form)  # Render the drop list template with drops, sync form, and delete form


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

        if form.starts_at.data and form.ends_at.data and form.ends_at.data <= form.starts_at.data:  # Check if the end time is not after the start time
            flash("The drop end date must be after the start date.", "danger")  # Show a date validation error message
            return render_template("admin/create_drop.html", form=form)  # Re-render the create-drop form

        validated_status = validate_drop_status(form.status.data)  # Validate the submitted status using shared validation logic
        validated_product_type = validate_product_type(form.product_type.data)  # Validate the submitted product type using shared validation logic

        drop = Drop(  # Create a new Drop object from the form data
            drop_number=form.drop_number.data.strip(),  # Store the cleaned drop number
            season=form.season.data,  # Store the submitted season number
            name=form.name.data.strip(),  # Store the cleaned drop name
            description=form.description.data.strip(),  # Store the cleaned drop description
            price=float(form.price.data),  # Store the submitted price as a normal float for SQLite compatibility
            status=validated_status,  # Store the validated lifecycle status
            product_type=validated_product_type,  # Store the validated product type
            shirt_color=form.shirt_color.data.strip(),  # Store the selected shirt color
            image_url=clean_optional_text(form.image_url.data),  # Store the optional image URL or None
            printify_product_id=clean_optional_text(form.printify_product_id.data),  # Store the optional Printify product ID or None
            printify_variant_ids=clean_optional_text(form.printify_variant_ids.data),  # Store the optional Printify variant IDs or None
            stripe_product_id=clean_optional_text(form.stripe_product_id.data),  # Store the optional Stripe product ID or None
            stripe_price_id=clean_optional_text(form.stripe_price_id.data),  # Store the optional Stripe price ID or None
            starts_at=form.starts_at.data,  # Store the optional scheduled start date
            ends_at=form.ends_at.data,  # Store the optional scheduled end date
        )  # Close the Drop object creation

        db.session.add(drop)  # Add the new drop to the database session
        db.session.commit()  # Save the new drop permanently to the database

        flash("Drop created successfully.", "success")  # Show a success message after creating the drop
        return redirect(url_for("admin.drops"))  # Redirect the admin user to the drop list

    return render_template("admin/create_drop.html", form=form)  # Render the create-drop form for GET requests or invalid submissions


@admin.route("/drops/<int:drop_id>/edit", methods=["GET", "POST"])  # Register the edit-drop route for GET and POST requests
@login_required  # Require the user to be logged in
@admin_required  # Require the logged-in user to be an admin
def edit_drop(drop_id):  # Define the function that handles editing existing drops
    drop = Drop.query.get_or_404(drop_id)  # Find the requested drop or return a 404 page
    form = DropForm(obj=drop)  # Create a drop form pre-filled with the existing drop data

    if form.validate_on_submit():  # Check if the edit form was submitted and passed validation
        existing_drop = Drop.query.filter(Drop.drop_number == form.drop_number.data.strip(), Drop.id != drop.id).first()  # Look for another drop using the submitted drop number

        if existing_drop:  # Check if another drop already uses this drop number
            flash("Another drop already uses that number.", "danger")  # Show a duplicate drop error message
            return render_template("admin/edit_drop.html", form=form, drop=drop)  # Re-render the edit-drop form

        if form.starts_at.data and form.ends_at.data and form.ends_at.data <= form.starts_at.data:  # Check if the end time is not after the start time
            flash("The drop end date must be after the start date.", "danger")  # Show a date validation error message
            return render_template("admin/edit_drop.html", form=form, drop=drop)  # Re-render the edit-drop form

        validated_status = validate_drop_status(form.status.data)  # Validate the submitted status using shared validation logic
        validated_product_type = validate_product_type(form.product_type.data)  # Validate the submitted product type using shared validation logic

        drop.drop_number = form.drop_number.data.strip()  # Update the drop number
        drop.season = form.season.data  # Update the season number
        drop.name = form.name.data.strip()  # Update the drop name
        drop.description = form.description.data.strip()  # Update the drop description
        drop.price = float(form.price.data)  # Update the price as a normal float for SQLite compatibility
        drop.status = validated_status  # Update the lifecycle status
        drop.product_type = validated_product_type  # Update the product type
        drop.shirt_color = form.shirt_color.data.strip()  # Update the selected shirt color
        drop.image_url = clean_optional_text(form.image_url.data)  # Update the optional image URL or None
        drop.printify_product_id = clean_optional_text(form.printify_product_id.data)  # Update the optional Printify product ID or None
        drop.printify_variant_ids = clean_optional_text(form.printify_variant_ids.data)  # Update the optional Printify variant IDs or None
        drop.stripe_product_id = clean_optional_text(form.stripe_product_id.data)  # Update the optional Stripe product ID or None
        drop.stripe_price_id = clean_optional_text(form.stripe_price_id.data)  # Update the optional Stripe price ID or None
        drop.starts_at = form.starts_at.data  # Update the optional scheduled start date
        drop.ends_at = form.ends_at.data  # Update the optional scheduled end date

        try:  # Try to save the edited drop safely
            db.session.commit()  # Save the updated drop permanently
        except IntegrityError:  # Catch database-level duplicate or constraint errors
            db.session.rollback()  # Roll back the failed database transaction
            flash("The drop could not be updated because of a database constraint.", "danger")  # Show a safe database error message
            return render_template("admin/edit_drop.html", form=form, drop=drop)  # Re-render the edit-drop form

        flash(f"Drop #{drop.drop_number} was updated successfully.", "success")  # Show a success message after updating the drop
        return redirect(url_for("admin.drops"))  # Redirect the admin user back to the drop list

    return render_template("admin/edit_drop.html", form=form, drop=drop)  # Render the edit-drop form for GET requests or invalid submissions


@admin.post("/drops/<int:drop_id>/delete")  # Register the admin delete-drop route
@login_required  # Require the user to be logged in
@admin_required  # Require the logged-in user to be an admin
def delete_drop(drop_id):  # Define the function that deletes safe local drops
    drop = Drop.query.get_or_404(drop_id)  # Find the requested drop or return a 404 page
    delete_form = EmptyForm()  # Create a CSRF-protected form for this delete action

    if not delete_form.validate_on_submit():  # Check if the delete form submission is invalid
        flash("Invalid drop delete request.", "danger")  # Show a safe error message
        return redirect(url_for("admin.drops"))  # Redirect back to the admin drops page

    if drop.status == DROP_STATUS_ACTIVE:  # Check if this is the active public drop
        flash("Active drops cannot be deleted. Archive or replace the active drop first.", "warning")  # Explain why active drop deletion is blocked
        return redirect(url_for("admin.drops"))  # Redirect back to the admin drops page

    connected_order_count = Order.query.filter_by(drop_id=drop.id).count()  # Count orders connected to this drop

    if connected_order_count > 0:  # Check if this drop already has order history
        flash("Drops with orders cannot be deleted because order history depends on them.", "warning")  # Explain why ordered drops cannot be deleted
        return redirect(url_for("admin.drops"))  # Redirect back to the admin drops page

    drop_number_for_message = drop.drop_number  # Store the drop number before deleting the row
    db.session.delete(drop)  # Delete the safe local drop from the database
    db.session.commit()  # Save the deletion permanently

    flash(f"Drop #{drop_number_for_message} was deleted.", "success")  # Show a success message after deleting the drop
    return redirect(url_for("admin.drops"))  # Redirect the admin user back to the drop list


@admin.route("/drops/<int:drop_id>/sync-printify", methods=["POST"])  # Register a POST route for syncing one drop with Printify
@login_required  # Require the user to be logged in
@admin_required  # Require the logged-in user to be an admin
def sync_printify_drop(drop_id):  # Define the function that syncs one drop with Printify
    form = EmptyForm()  # Create a CSRF-protected empty form instance

    if not form.validate_on_submit():  # Check if the CSRF-protected POST is invalid
        flash("Invalid sync request.", "danger")  # Show a safe error message
        return redirect(url_for("admin.drops"))  # Redirect back to the admin drops page

    drop = Drop.query.get_or_404(drop_id)  # Find the requested drop or return a 404 page

    try:  # Start a protected block for Printify sync
        result = sync_drop_with_printify(drop)  # Sync the drop with its connected Printify product
    except (PrintifyConfigError, PrintifyAPIError) as error:  # Catch Printify configuration and API errors
        flash(str(error), "danger")  # Show the error message to the admin user
        return redirect(url_for("admin.drops"))  # Redirect back to the admin drops page

    selected_count = len(result["variant_summary"]["selected_variants"])  # Count selected variants found on the Printify product
    selected_available_count = len(result["variant_summary"]["selected_available_variants"])  # Count selected variants currently available

    flash(f"Printify sync complete. Selected variants available: {selected_available_count}/{selected_count}.", "success")  # Show the sync result
    return redirect(url_for("admin.drops"))  # Redirect back to the admin drops page


@admin.get("/orders")  # Register the admin orders list route
@login_required  # Require the user to be logged in before viewing orders
@admin_required  # Require the logged-in user to be an admin before viewing orders
def orders():  # Define the admin view that lists local Stripe orders
    order_list = Order.query.order_by(Order.created_at.desc()).all()  # Retrieve all orders newest first
    return render_template("admin/orders.html", orders=order_list)  # Render the admin orders page


@admin.get("/orders/<int:order_id>")  # Register the admin order detail route
@login_required  # Require the user to be logged in before viewing one order
@admin_required  # Require the logged-in user to be an admin before viewing one order
def order_detail(order_id):  # Define the admin view that shows one order
    order = Order.query.get_or_404(order_id)  # Retrieve the requested order or return a 404 page
    fulfill_form = EmptyForm()  # Create an empty form for the Printify fulfillment submit button
    delete_form = EmptyForm()  # Create an empty form for the local test order delete button
    printify_fulfillment_enabled = current_app.config.get("PRINTIFY_FULFILLMENT_ENABLED")  # Read whether real Printify fulfillment is enabled
    return render_template("admin/order_detail.html", order=order, fulfill_form=fulfill_form, delete_form=delete_form, printify_fulfillment_enabled=printify_fulfillment_enabled)  # Render the admin order detail page


@admin.post("/orders/<int:order_id>/fulfill-printify")  # Register the admin Printify fulfillment route
@login_required  # Require the user to be logged in before submitting fulfillment
@admin_required  # Require the logged-in user to be an admin before submitting fulfillment
def fulfill_printify_order(order_id):  # Define the admin action that submits a paid order to Printify
    order = Order.query.get_or_404(order_id)  # Retrieve the requested order or return a 404 page
    fulfill_form = EmptyForm()  # Create the empty form used to validate the POST request

    if not fulfill_form.validate_on_submit():  # Check if the CSRF-protected form submission is invalid
        flash("Invalid fulfillment request.", "danger")  # Show a safe error message
        return redirect(url_for("admin.order_detail", order_id=order.id))  # Redirect back to the order detail page

    try:  # Start a protected block for Printify fulfillment
        submit_order_to_printify(order)  # Submit the paid local order to Printify
    except (PrintifyConfigError, PrintifyAPIError, PrintifyFulfillmentError) as error:  # Catch expected Printify fulfillment errors
        flash(str(error), "danger")  # Show the error message in the admin UI
        return redirect(url_for("admin.order_detail", order_id=order.id))  # Redirect back to the order detail page

    flash(f"Order #{order.id} was submitted to Printify.", "success")  # Show a success message after successful Printify submission
    return redirect(url_for("admin.order_detail", order_id=order.id))  # Redirect back to the order detail page


@admin.post("/orders/<int:order_id>/delete")  # Register the admin test order deletion route
@login_required  # Require the user to be logged in before deleting an order
@admin_required  # Require the logged-in user to be an admin before deleting an order
def delete_order(order_id):  # Define the admin action that deletes one local test order
    order = Order.query.get_or_404(order_id)  # Retrieve the requested order or return a 404 page
    delete_form = EmptyForm()  # Create the empty form used to validate the POST request

    if not delete_form.validate_on_submit():  # Check if the form submission is invalid
        flash("Invalid delete request.", "danger")  # Show a safe error message
        return redirect(url_for("admin.order_detail", order_id=order.id))  # Redirect back to the order detail page

    order_id_for_message = order.id  # Store the order ID before deleting the database row
    db.session.delete(order)  # Delete the local test order from the database
    db.session.commit()  # Save the deletion permanently

    flash(f"Test order #{order_id_for_message} was deleted locally.", "success")  # Show a success message
    return redirect(url_for("admin.orders"))  # Redirect back to the admin orders page