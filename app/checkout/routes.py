import stripe  # Import the Stripe SDK for webhook verification
from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for  # Import Flask helpers for checkout routes

from app.constants import DROP_STATUS_ACTIVE  # Import the active status constant
from app.models import Drop  # Import Drop so checkout can find the current active drop
from app.services.stripe_checkout import StripeCheckoutError, StripeConfigError, create_checkout_session_for_drop, mark_order_paid_from_checkout_session  # Import checkout services


checkout = Blueprint("checkout", __name__, url_prefix="/checkout")  # Create the checkout blueprint with /checkout URL prefix


@checkout.route("/current-drop", methods=["POST"])  # Register a POST route for buying the current active drop
def current_drop_checkout():  # Define the route that starts Stripe Checkout for the current drop
    active_drop = Drop.query.filter_by(status=DROP_STATUS_ACTIVE).first()  # Find the current active drop

    if not active_drop:  # Check if there is no active drop
        flash("There is no active drop available right now.", "warning")  # Show a safe message
        return redirect(url_for("main.home"))  # Redirect back to the homepage

    selected_size = request.form.get("selected_size", "").strip().upper()  # Read and normalize the selected size from the checkout form
    available_sizes = active_drop.get_available_sizes()  # Read available sizes from the active drop

    if selected_size not in available_sizes:  # Check if the submitted size is missing or unavailable
        flash("Please select an available size before checkout.", "warning")  # Show a clear validation message
        return redirect(url_for("main.home"))  # Redirect back to the homepage

    printify_variant_id = active_drop.get_printify_variant_id_for_size(selected_size)  # Find the Printify variant ID for the selected size

    if not printify_variant_id:  # Check if no Printify variant exists for this size
        flash("This size is not connected to a Printify variant yet.", "danger")  # Show a safe configuration error
        return redirect(url_for("main.home"))  # Redirect back to the homepage

    try:  # Start a protected block for Checkout Session creation
        session = create_checkout_session_for_drop(active_drop, selected_size, printify_variant_id)  # Create a Stripe Checkout Session for the selected size
    except (StripeConfigError, StripeCheckoutError) as error:  # Catch Stripe configuration and checkout errors
        flash(str(error), "danger")  # Show the error message to the user
        return redirect(url_for("main.home"))  # Redirect back to the homepage

    return redirect(session.url, code=303)  # Redirect the customer to Stripe-hosted Checkout


@checkout.route("/success")  # Register the checkout success route
def success():  # Define the route that renders successful checkout return page
    session_id = request.args.get("session_id")  # Read the Stripe Checkout Session ID from the query string
    return render_template("checkout/success.html", session_id=session_id)  # Render the success page


@checkout.route("/cancel")  # Register the checkout cancel route
def cancel():  # Define the route that renders cancelled checkout return page
    return render_template("checkout/cancel.html")  # Render the cancel page


@checkout.route("/webhook", methods=["POST"])  # Register the Stripe webhook endpoint
def webhook():  # Define the route that receives Stripe webhook events
    payload = request.get_data()  # Read the raw request body required for Stripe signature verification
    sig_header = request.headers.get("Stripe-Signature")  # Read the Stripe signature header
    endpoint_secret = current_app.config.get("STRIPE_WEBHOOK_SECRET")  # Read the configured webhook signing secret

    if not endpoint_secret:  # Check if the webhook verification is not configured
        abort(400)  # Reject the webhook because verification cannot be performed safely

    try:  # Start a protected block for webhook verification
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)  # Verify and construct the Stripe event
    except ValueError:  # Catch invalid JSON payload errors
        abort(400)  # Reject invalid payloads
    except stripe.SignatureVerificationError:  # Catch invalid Stripe signature errors
        abort(400)  # Reject unverifiable webhook events

    if event["type"] == "checkout.session.completed":  # Check if Checkout completed successfully
        session = event["data"]["object"]  # Extract the Checkout Session object from the event
        mark_order_paid_from_checkout_session(session)  # Mark the matching local order as paid

    return {"status": "success"}  # Return a success response to Stripe
