import logging  # Import logging so checkout and webhook failures can be recorded

import stripe  # Import the Stripe SDK for webhook verification
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for  # Import Flask helpers for checkout routes

from app.constants import DROP_STATUS_ACTIVE  # Import the active status constant
from app.extensions import db  # Import the database object so webhook failures can roll back failed transactions
from app.models import Drop  # Import Drop so checkout can find the current active drop
from app.services.stripe_checkout import StripeCheckoutError, StripeConfigError, create_checkout_session_for_drop, mark_order_paid_from_checkout_session  # Import checkout services


logger = logging.getLogger(__name__)  # Create a module logger for checkout routes and Stripe webhook events

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
        logger.error("Checkout blocked because Drop #%s size %s has no Printify variant ID.", active_drop.drop_number, selected_size)  # Log the missing Printify variant configuration
        flash("This size is not connected to a Printify variant yet.", "danger")  # Show a safe configuration error
        return redirect(url_for("main.home"))  # Redirect back to the homepage

    try:  # Start a protected block for Checkout Session creation
        session = create_checkout_session_for_drop(active_drop, selected_size, printify_variant_id)  # Create a Stripe Checkout Session for the selected size
    except (StripeConfigError, StripeCheckoutError) as error:  # Catch Stripe configuration and checkout errors
        logger.exception("Checkout start failed for Drop #%s and size %s.", active_drop.drop_number, selected_size)  # Log the technical checkout failure
        flash(str(error), "danger")  # Show the safe error message to the user
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
        logger.error("Stripe webhook rejected because STRIPE_WEBHOOK_SECRET is missing.")  # Log missing webhook configuration
        return "Webhook not configured", 400  # Reject the webhook without exposing technical details

    try:  # Try to verify and construct the Stripe webhook event
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)  # Verify the Stripe webhook signature and parse the event
    except ValueError as error:  # Catch invalid JSON payload errors
        logger.warning("Stripe webhook rejected because payload was invalid JSON.")  # Log invalid webhook payloads
        return "Invalid payload", 400  # Return a bad request response to Stripe
    except stripe.SignatureVerificationError as error:  # Catch invalid Stripe signature errors
        logger.warning("Stripe webhook rejected because signature verification failed.")  # Log webhook signature failures
        return "Invalid signature", 400  # Return a bad request response to Stripe
    except stripe.StripeError as error:  # Catch unexpected Stripe webhook parsing failures
        logger.exception("Stripe webhook construction failed.")  # Log the technical webhook failure
        return "Webhook error", 400  # Return a bad request response to Stripe

    if event["type"] == "checkout.session.completed":  # Check if Checkout completed successfully
        try:  # Try to process the verified Stripe checkout event
            session = event["data"]["object"]  # Extract the Checkout Session object from the event
            mark_order_paid_from_checkout_session(session)  # Mark the matching local order as paid
            db.session.commit()  # Save webhook-driven database changes
            logger.info("Processed Stripe checkout.session.completed event %s.", event["id"])  # Log successful checkout webhook processing
        except Exception as error:  # Catch unexpected local webhook processing failures
            db.session.rollback()  # Roll back failed local database changes
            logger.exception("Stripe webhook processing failed for event %s.", event.get("id"))  # Log the full webhook processing failure
            return "Webhook processing failed", 500  # Tell Stripe the webhook failed so it can retry
    else:  # Run this block for Stripe events this app does not process
        logger.info("Ignored Stripe webhook event type: %s", event["type"])  # Log ignored Stripe webhook event types

    return {"status": "success"}  # Return a success response to Stripe