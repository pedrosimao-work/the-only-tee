from flask import Blueprint, render_template  # Import Blueprint for route grouping and render_template for HTML responses


legal = Blueprint("legal", __name__, url_prefix="/legal")  # Create the legal blueprint with the /legal URL prefix


@legal.get("/privacy-policy")  # Register the public Privacy Policy route
def privacy_policy():  # Define the view function that renders the Privacy Policy page
    return render_template("legal/privacy_policy.html")  # Render the Privacy Policy template


@legal.get("/terms-of-service")  # Register the public Terms of Service route
def terms_of_service():  # Define the view function that renders the Terms of Service page
    return render_template("legal/terms_of_service.html")  # Render the Terms of Service template


@legal.get("/shipping-returns")  # Register the public Shipping & Returns route
def shipping_returns():  # Define the view function that renders the Shipping & Returns page
    return render_template("legal/shipping_returns.html")  # Render the Shipping & Returns template