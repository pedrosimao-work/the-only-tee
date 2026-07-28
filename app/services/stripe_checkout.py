from datetime import datetime  # Import datetime so paid orders can store completion time

import stripe  # Import the Stripe SDK
from flask import current_app, url_for  # Import current_app for config and url_for for checkout redirect URLs
from flask_login import current_user  # Import current_user so checkout can connect orders to logged-in users

from app.extensions import db  # Import the database object so checkout orders can be saved
from app.models import Order  # Import the Order model so checkout sessions can create local order records


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


def create_checkout_session_for_drop(drop):  # Define a service function that creates a Stripe Checkout Session for one drop
    if not drop.stripe_price_id:  # Check if the drop does not have a Stripe Price ID
        raise StripeCheckoutError("This drop does not have a Stripe Price ID.")  # Raise a clear checkout error

    configure_stripe()  # Configure the Stripe SDK with the secret key

    success_url = url_for("checkout.success", _external=True) + "?session_id={CHECKOUT_SESSION_ID}"  # Build the Stripe success URL
    cancel_url = url_for("checkout.cancel", _external=True)  # Build the Stripe cancel URL

    try:  # Start a protected block for Stripe Checkout Session creation
        session = stripe.checkout.Session.create(  # Create a Stripe-hosted Checkout Session
            mode="payment",  # Use one-time payment mode
            line_items=[  # Define the products being purchased
                {  # Start the single line item
                    "price": drop.stripe_price_id,  # Use the Stripe Price ID connected to the drop
                    "quantity": 1,  # Sell one item per Checkout Session for now
                    "adjustable_quantity": {  # Allow the customer to adjust quantity in Checkout
                        "enabled": True,  # Enable quantity adjustment on Stripe Checkout
                        "minimum": 1,  # Require at least one item
                        "maximum": 10,  # Limit checkout quantity to avoid accidental excessive orders
                    },  # Close adjustable quantity configuration
                }  # Close the single line item
            ],  # Close the line items list
            success_url=success_url,  # Send successful customers back to the success page
            cancel_url=cancel_url,  # Send cancelled customers back to the cancel page
            shipping_address_collection={  # Ask Stripe Checkout to collect the shipping address
                "allowed_countries": ["US"],  # Limit MVP shipping to the United States only
            },  # Close the shipping address collection configuration
            metadata={  # Store useful identifiers on the Checkout Session
                "drop_id": str(drop.id),  # Store the local drop ID
                "drop_number": drop.drop_number,  # Store the public drop number
            },  # Close session metadata
            payment_intent_data={  # Attach metadata to the underlying payment
                "metadata": {  # Store useful identifiers on the PaymentIntent
                    "drop_id": str(drop.id),  # Store the local drop ID
                    "drop_number": drop.drop_number,  # Store the public drop number
                }  # Close payment intent metadata
            },  # Close payment intent data
        )  # Close the Checkout Session creation call
    except stripe.StripeError as error:  # Catch Stripe SDK errors
        raise StripeCheckoutError(f"Stripe checkout error: {error}") from error  # Raise a clear app-level-checkout error

    user_id = current_user.id if current_user.is_authenticated else None  # Store the logged-in user ID when available

    order = Order(  # Create a local order record for this Checkout Session
        user_id=user_id,  # Store the optional user ID
        drop_id=drop.id,  # Store the purchased drop ID
        stripe_checkout_session_id=session.id,  # Store the Stripe Checkout Session ID
        payment_status=session.payment_status or "created",  # Store the initial Stripe payment status
        quantity=1,  # Store the initial quantity for now
        currency=session.currency,  # Store the Stripe currency if available
        amount_total=session.amount_total,  # Store the total amount if available
    )  # Close the Order object creation

    db.session.add(order)  # Add the order to the database session
    db.session.commit()  # Save the order permanently

    return session  # Return the Stripe Checkout Session so the route can redirect to its URL


def mark_order_paid_from_checkout_session(session):  # Define a service function that marks an order paid from a Stripe session object
    order = Order.query.filter_by(stripe_checkout_session_id=session.get("id")).first()  # Find the local order by Checkout Session ID

    if not order:  # Check if no matching local order exists
        return None  # Return None because there is no order to update

    order.stripe_payment_intent_id = session.get("payment intent")  # Store the Stripe PaymentIntent ID
    order.payment_status = session.get("payment_status") or "paid"  # Store the final payment status
    order.customer_email = (session.get("customer_details") or {}).get("email")  # Store the customer email returned by Checkout
    order.amount_total = session.get("amount_total")  # Store the final total amount
    order.currency = session.get("currency")  # Store the final currency code
    order.paid_at = datetime.utcnow()  # Store when the payment was confirmed locally

    db.session.commit()  # Save the paid order update

    return order  # Return the updated order
