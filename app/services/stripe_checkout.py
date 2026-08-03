from datetime import datetime  # Import datetime so paid orders can store completion time
import logging  # Import logging so Stripe checkout failures can be recorded

import stripe  # Import the Stripe SDK
from flask import current_app, url_for  # Import current_app for config and url_for for checkout redirect URLs
from flask_login import current_user  # Import current_user so checkout can connect orders to logged-in users

from app.extensions import db  # Import the database object so checkout orders can be saved
from app.models import Order  # Import the Order model so checkout sessions can create local order records


logger = logging.getLogger(__name__)  # Create a module logger for Stripe checkout service failures


class StripeConfigError(Exception):  # Create a custom error for missing Stripe configuration
    pass  # Keep the custom exception body empty because the class name explains the error type


class StripeCheckoutError(Exception):  # Create a custom error for failed Stripe Checkout operations
    pass  # Keep the custom exception body empty because the class name explains the error


def get_stripe_secret_key():  # Define a helper function that reads the Stripe secret key
    stripe_secret_key = current_app.config.get("STRIPE_SECRET_KEY")  # Read the Stripe secret key from Flask config

    if not stripe_secret_key:  # Check if the Stripe secret key is missing
        raise StripeConfigError("STRIPE_SECRET_KEY is not configured.")  # Raise a clear configuration error

    return stripe_secret_key  # Return the configured Stripe secret key


def configure_stripe():  # Define a helper function that configures the Stripe SDK
    stripe.api_key = get_stripe_secret_key()  # Set the Stripe SDK API key from Flask config


def retrieve_checkout_session(session_id):  # Define a helper function that retrieves a Stripe Checkout Session
    configure_stripe()  # Configure the Stripe SDK with the secret key

    try:  # Start a protected block for Stripe API retrieval
        return stripe.checkout.Session.retrieve(session_id)  # Retrieve and return the Checkout Session from Stripe
    except stripe.StripeError as error:  # Catch Stripe SDK errors
        logger.exception("Stripe Checkout Session retrieval failed for session %s.",
                         session_id)  # Log the technical Stripe retrieval failure
        raise StripeCheckoutError(
            "Stripe session could not be retrieved. Please try again in a moment.") from error  # Raise a user-safe checkout error


def create_checkout_session_for_drop(drop, selected_size, printify_variant_id):  # Define a service function that creates a Stripe Checkout Session for one selected size
    if not drop.stripe_price_id:  # Check if this drop is missing a saved Stripe Price ID
        logger.warning("Checkout attempted for Drop #%s without a Stripe Price ID.", drop.drop_number)  # Log the missing Stripe Price before trying recovery
        from app.services.stripe_products import ensure_stripe_product_and_price_for_drop, StripeProductSyncError  # Import here to avoid a circular import with stripe_products.py

        try:  # Try to create the missing Stripe Product and Price automatically
            ensure_stripe_product_and_price_for_drop(drop)  # Create missing Stripe catalog records for this drop
            db.session.commit()  # Save the newly created Stripe IDs before creating Checkout
            logger.info("Recovered missing Stripe Price ID for Drop #%s before checkout.", drop.drop_number)  # Log successful checkout recovery
        except StripeProductSyncError as error:  # Catch Stripe product sync failures
            db.session.rollback()  # Undo any partial local Stripe ID changes
            logger.exception("Checkout recovery failed while syncing Stripe catalog for Drop #%s.", drop.drop_number)  # Log the technical Stripe catalog recovery failure
            raise StripeCheckoutError("Checkout is not available for this drop yet.") from error  # Raise a user-safe checkout error

    if not drop.stripe_price_id:  # Check again in case automatic Stripe sync did not create a price
        logger.error("Checkout blocked because Drop #%s still has no Stripe Price ID after recovery attempt.", drop.drop_number)  # Log the unrecovered missing Stripe Price
        raise StripeCheckoutError("Checkout is not available for this drop yet.")  # Raise a user-safe checkout error

    configure_stripe()  # Configure the Stripe SDK with the secret key

    success_url = url_for("checkout.success", _external=True) + "?session_id={CHECKOUT_SESSION_ID}"  # Build the Stripe success URL
    cancel_url = url_for("checkout.cancel", _external=True)  # Build the Stripe cancel URL

    checkout_metadata = {  # Create metadata that connects Stripe checkout to local app data
        "drop_id": str(drop.id),  # Store the local drop ID
        "drop_number": drop.drop_number,  # Store the public drop number
        "selected_size": selected_size,  # Store the customer-selected size
        "printify_variant_id": str(printify_variant_id),  # Store the Printify variant ID needed for fulfillment
    }  # Close the metadata dictionary

    try:  # Start a protected block for Stripe Checkout Session creation
        session = stripe.checkout.Session.create(  # Create a Stripe-hosted Checkout Session
            mode="payment",  # Use one-time payment mode
            line_items=[  # Define the products being purchased through Checkout
                {  # Create one line item for the current monthly drop
                    "price": drop.stripe_price_id,  # Use the saved Stripe Price ID connected to this drop
                    "quantity": 1,  # Sell one item per Checkout Session for this MVP
                },  # Close the one line item
            ],  # Close line items
            success_url=success_url,  # Send successful customers back to the success page
            cancel_url=cancel_url,  # Send cancelled customers back to the cancel page
            shipping_address_collection={  # Ask Stripe Checkout to collect the shipping address
                "allowed_countries": ["US"],  # Limit MVP shipping to the United States only
            },  # Close shipping address collection configuration
            custom_text={  # Add portfolio demo messaging inside Stripe-hosted Checkout
                "submit": {  # Add a message near the final payment submission area
                    "message": "Portfolio demo checkout. Use Stripe test card 4242 4242 4242 4242 only. No real order will be submitted to production."  # Explain that this is a safe test checkout
                },  # Close the submit custom text object
                "shipping_address": {  # Add a message near the shipping address collection area
                    "message": "Demo checkout for a Python portfolio project. Shipping information is used only to test the checkout and fulfillment flow."  # Explain why shipping details are requested
                },  # Close the shipping address custom text object
            },  # Close the custom text configuration
            metadata=checkout_metadata,  # Store local app metadata on the Checkout Session
            payment_intent_data={  # Attach metadata to the underlying payment
                "metadata": checkout_metadata  # Store the same fulfillment metadata on the PaymentIntent
            },  # Close payment intent data
        )  # Close the Checkout Session creation call
    except stripe.StripeError as error:  # Catch Stripe SDK errors
        logger.exception("Stripe Checkout Session creation failed for Drop #%s and size %s.", drop.drop_number, selected_size)  # Log the technical checkout failure
        raise StripeCheckoutError("Checkout could not be started. Please try again in a moment.") from error  # Raise a user-safe checkout error

    user_id = current_user.id if current_user.is_authenticated else None  # Store the logged-in user ID when available

    order = Order(  # Create a local order record for this Checkout Session
        user_id=user_id,  # Store the optional user ID
        drop_id=drop.id,  # Store the purchased drop ID
        stripe_checkout_session_id=session.id,  # Store the Stripe Checkout Session ID
        payment_status=session.payment_status or "created",  # Store the initial Stripe payment status
        customer_email=None,  # Leave customer email empty until Stripe returns it
        selected_size=selected_size,  # Store the customer-selected size
        printify_variant_id=str(printify_variant_id),  # Store the Printify variant ID needed for fulfillment
        quantity=1,  # Store one item for this MVP checkout flow
        currency=session.currency,  # Store the Stripe currency if available
        amount_total=session.amount_total,  # Store the total amount if available
    )  # Close the Order object creation

    try:  # Try to save the local order record
        db.session.add(order)  # Add the order to the database session
        db.session.commit()  # Save the order permanently
    except Exception as error:  # Catch unexpected local order save failures
        db.session.rollback()  # Roll back the failed order creation
        logger.exception("Local order creation failed for Stripe Checkout Session %s.", session.id)  # Log the technical local order failure
        raise StripeCheckoutError("Checkout started, but the local order could not be saved.") from error  # Raise a user-safe checkout error

    logger.info("Created Stripe Checkout Session %s for Drop #%s and size %s.", session.id, drop.drop_number, selected_size)  # Log successful checkout session creation
    return session  # Return the Stripe Checkout Session so the route can redirect to its URL


def mark_order_paid_from_checkout_session(session):  # Define a service function that marks an order paid from a Stripe session object
    order = Order.query.filter_by(stripe_checkout_session_id=session.get("id")).first()  # Find the local order by Checkout Session ID

    if not order:  # Check if no matching local order exists
        logger.warning("No local order found for completed Stripe Checkout Session %s.",
                       session.get("id"))  # Log the missing local order
        return None  # Return None because there is no order to update

    session_metadata = session.get("metadata") or {}  # Read metadata from the completed Stripe Checkout Session

    order.stripe_payment_intent_id = session.get("payment_intent")  # Store the Stripe PaymentIntent ID
    order.payment_status = session.get("payment_status") or "paid"  # Store the final payment status
    order.customer_email = (session.get("customer_details") or {}).get("email")  # Store the customer email returned by Checkout
    order.selected_size = order.selected_size or session_metadata.get("selected_size")  # Preserve or restore the selected size from Stripe metadata
    order.printify_variant_id = order.printify_variant_id or session_metadata.get("printify_variant_id")  # Preserve or restore the Printify variant ID from Stripe metadata
    order.amount_total = session.get("amount_total")  # Store the final total amount
    order.currency = session.get("currency")  # Store the final currency code
    order.paid_at = datetime.utcnow()  # Store when the payment was confirmed locally

    try:  # Try to save the paid order update
        db.session.commit()  # Save the paid order update
    except Exception as error:  # Catch unexpected local paid-order update failures
        db.session.rollback()  # Roll back the failed paid-order update
        logger.exception("Failed to mark local order paid for Stripe Checkout Session %s.",
                         session.get("id"))  # Log the technical paid-order update failure
        raise StripeCheckoutError(
            "Paid order could not be saved locally.") from error  # Raise a user-safe checkout error

    logger.info("Marked local Order #%s paid from Stripe Checkout Session %s.", order.id,
                session.get("id"))  # Log successful paid-order update
    return order  # Return the updated order