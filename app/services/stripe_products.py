from decimal import Decimal, InvalidOperation, ROUND_HALF_UP # Import Decimal tools so prices can be converted safely to cents
import logging # Import logging so Stripe sync failures can be recorded

from flask import current_app # Import current_app so Stripe config can be read without creating circular imports
import stripe # Import Stripe's Python SDK so products and prices can be managed through the API


STRIPE_CURRENCY = "usd" # Store the Stripe currency used by the platform
logger = logging.getLogger(__name__) # Create a logger for this Stripe product service


class StripeProductSyncError(RuntimeError): # Define a custom error for Stripe product sync failures
    pass # Keep the custom exception body empty because the message comes from raise statements


def configure_stripe(): # Define a local Stripe configuration helper to avoid circular imports
    stripe_secret_key = current_app.config.get("STRIPE_SECRET_KEY") # Read the Stripe secret key from Flask config

    if not stripe_secret_key: # Check if the Stripe secret key is missing
        raise StripeProductSyncError("Stripe secret key is not configured.") # Stop with a clear admin-safe error

    stripe.api_key = stripe_secret_key # Configure Stripe SDK with the secret key


def convert_price_to_cents(price): # Define a helper that converts a drop price into Stripe minor units
    try: # Try to parse the price safely
        price_decimal = Decimal(str(price)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) # Convert the price to a two-decimal Decimal
    except (InvalidOperation, TypeError, ValueError) as error: # Catch invalid price values
        raise StripeProductSyncError("Drop price must be a valid number before syncing to Stripe.") from error # Raise a clear sync error

    if price_decimal <= Decimal("0.00"): # Check if the price is zero or negative
        raise StripeProductSyncError("Drop price must be greater than zero before syncing to Stripe.") # Stop syncing invalid prices

    return int(price_decimal * 100) # Convert dollars to cents for Stripe unit_amount


def build_product_name(drop): # Define a helper that builds the Stripe Product name
    return f"{drop.name} — Drop #{drop.drop_number}" # Return a readable Stripe product name


def build_product_description(drop): # Define a helper that builds the Stripe Product description
    description = drop.description or "" # Use the drop description or an empty fallback
    return description[:500] # Keep the Stripe description safely short


def build_product_images(drop): # Define a helper that builds Stripe Product image data
    if not drop.image_url: # Check if the drop has no synced primary image
        return None # Return nothing so Stripe keeps images unchanged or empty

    return [drop.image_url] # Return the primary mockup image as the Stripe Product image list


def build_product_metadata(drop): # Define a helper that builds metadata shared by Stripe Product and Price records
    return { # Return Stripe metadata for local traceability
        "drop_id": str(drop.id), # Store the local Drop ID
        "drop_number": drop.drop_number, # Store the public drop number
        "source": "the_only_drop_admin", # Store the source of this Stripe catalog record
    } # Close metadata dictionary


def retrieve_stripe_product(product_id): # Define a helper that safely retrieves a Stripe Product
    configure_stripe() # Configure Stripe with the secret key from the app environment

    if not product_id: # Check if there is no product ID to retrieve
        return None # Return no Stripe Product

    try: # Try to retrieve the Stripe Product
        product = stripe.Product.retrieve(product_id) # Retrieve the Stripe Product from Stripe
    except stripe.StripeError: # Catch missing, deleted, or inaccessible Stripe Products
        logger.exception("Stripe Product retrieval failed for product %s.", product_id) # Log the retrieval failure
        return None # Treat the saved product ID as stale

    if getattr(product, "deleted", False): # Check if Stripe returned a deleted Product object
        return None # Treat deleted Products as missing

    return product # Return the usable Stripe Product


def create_stripe_product_for_drop(drop): # Define a helper that creates one Stripe Product for one drop
    configure_stripe() # Configure Stripe with the secret key from the app environment

    product_data = { # Create the Stripe Product payload
        "name": build_product_name(drop), # Use the drop name and drop number as the Stripe Product name
        "description": build_product_description(drop), # Use the drop description as the Stripe Product description
        "metadata": build_product_metadata(drop), # Store local app references in Stripe metadata
    } # Close the Stripe Product payload

    product_images = build_product_images(drop) # Build the optional Stripe Product image list

    if product_images: # Check if the drop has a primary image URL
        product_data["images"] = product_images # Add the primary mockup image to the Stripe Product

    try: # Try to create the Stripe Product
        product = stripe.Product.create(**product_data) # Create the Stripe Product through the Stripe API
    except stripe.StripeError as error: # Catch Stripe SDK/API failures
        logger.exception("Stripe Product creation failed for Drop #%s.", drop.drop_number) # Log the failure for debugging
        raise StripeProductSyncError("Stripe Product creation failed. Check Stripe configuration and try again.") from error # Raise a safe app-level error

    drop.stripe_product_id = product.id # Save the created Stripe Product ID on the local Drop
    return product # Return the created Stripe Product object


def update_stripe_product_for_drop(drop): # Define a helper that updates an existing Stripe Product
    configure_stripe() # Configure Stripe with the secret key from the app environment

    product = retrieve_stripe_product(drop.stripe_product_id) # Retrieve the saved Stripe Product safely

    if product is None: # Check if the saved Stripe Product ID is missing, deleted, or inaccessible
        drop.stripe_product_id = None # Clear the stale local Stripe Product ID
        drop.stripe_price_id = None # Clear the stale local Stripe Price ID because Prices belong to Products
        return create_stripe_product_for_drop(drop) # Create a fresh Stripe Product instead

    product_data = { # Create the Stripe Product update payload
        "name": build_product_name(drop), # Keep the Stripe Product name aligned with the drop
        "description": build_product_description(drop), # Keep the Stripe Product description aligned with the drop
        "metadata": build_product_metadata(drop), # Keep local app references in Stripe metadata
        "active": True, # Keep the current local drop product active in Stripe
    } # Close the Stripe Product update payload

    product_images = build_product_images(drop) # Build the optional Stripe Product image list

    if product_images: # Check if the drop has a primary image URL
        product_data["images"] = product_images # Update the Stripe Product image with the primary mockup

    try: # Try to update the existing Stripe Product
        product = stripe.Product.modify(drop.stripe_product_id, **product_data) # Update the Stripe Product through the Stripe API
    except stripe.StripeError as error: # Catch Stripe SDK/API failures
        logger.exception("Stripe Product update failed for Drop #%s.", drop.drop_number) # Log the failure for debugging
        raise StripeProductSyncError("Stripe Product update failed. Check Stripe configuration and try again.") from error # Raise a safe app-level error

    return product # Return the updated Stripe Product object


def retrieve_stripe_price(price_id): # Define a helper that safely retrieves a Stripe Price
    configure_stripe() # Configure Stripe with the secret key from the app environment

    if not price_id: # Check if there is no price ID to retrieve
        return None # Return no Stripe Price

    try: # Try to retrieve the Stripe Price
        return stripe.Price.retrieve(price_id) # Retrieve the Stripe Price from Stripe
    except stripe.StripeError: # Catch missing or inaccessible Stripe Prices
        logger.exception("Stripe Price retrieval failed for price %s.", price_id) # Log the retrieval failure
        return None # Treat the saved price as unusable


def stripe_price_matches_drop(drop): # Define a helper that checks whether the saved Stripe Price still matches the drop
    price = retrieve_stripe_price(drop.stripe_price_id) # Retrieve the saved Stripe Price

    if price is None: # Check if no valid Stripe Price exists
        return False # Signal that a new Stripe Price is needed

    expected_amount = convert_price_to_cents(drop.price) # Convert the local drop price into cents

    if price.product != drop.stripe_product_id: # Check if the saved Price belongs to a different Product
        return False # Signal that a new Stripe Price is needed for this Product

    if price.currency != STRIPE_CURRENCY: # Check if the saved Price uses the wrong currency
        return False # Signal that a new USD Stripe Price is needed

    if price.unit_amount != expected_amount: # Check if the saved Price amount is outdated
        return False # Signal that a new Stripe Price is needed

    if not price.active: # Check if the saved Price is inactive
        return False # Signal that a new Stripe Price is needed

    return True # Signal that the saved Stripe Price is valid for this drop


def create_stripe_price_for_drop(drop): # Define a helper that creates one Stripe Price for one drop
    configure_stripe() # Configure Stripe with the secret key from the app environment

    if not drop.stripe_product_id: # Check if the drop does not have a Stripe Product yet
        raise StripeProductSyncError("Stripe Product must exist before creating a Stripe Price.") # Stop because prices belong to products

    unit_amount = convert_price_to_cents(drop.price) # Convert the local drop price into cents

    try: # Try to create the Stripe Price
        price = stripe.Price.create( # Create the Stripe Price through the Stripe API
            product=drop.stripe_product_id, # Attach the price to the existing Stripe Product
            unit_amount=unit_amount, # Store the price amount in cents
            currency=STRIPE_CURRENCY, # Use USD for this platform
            metadata=build_product_metadata(drop), # Store local app references in Stripe metadata
        ) # Close Stripe Price creation
    except stripe.StripeError as error: # Catch Stripe SDK/API failures
        logger.exception("Stripe Price creation failed for Drop #%s.", drop.drop_number) # Log the failure for debugging
        raise StripeProductSyncError("Stripe Price creation failed. Check Stripe configuration and try again.") from error # Raise a safe app-level error

    drop.stripe_price_id = price.id # Save the created Stripe Price ID on the local Drop
    return price # Return the created Stripe Price object


def deactivate_stripe_price(price_id): # Define a helper that deactivates an old Stripe Price
    configure_stripe() # Configure Stripe with the secret key from the app environment

    if not price_id: # Check if there is no old price to deactivate
        return None # Return nothing because there is no Stripe Price to update

    try: # Try to deactivate the old Stripe Price
        return stripe.Price.modify(price_id, active=False) # Set the old Stripe Price inactive
    except stripe.StripeError: # Catch Stripe SDK/API failures
        logger.exception("Stripe Price deactivation failed for price %s.", price_id) # Log the failure without blocking the new price
        return None # Continue safely even if the old price could not be deactivated


def deactivate_all_prices_for_product(product_id): # Define a helper that deactivates every active Price under a Product
    configure_stripe() # Configure Stripe with the secret key from the app environment

    if not product_id: # Check if there is no product ID
        return 0 # Return zero because no prices were updated

    deactivated_count = 0 # Track how many Stripe Prices were deactivated

    try: # Try to list active prices for this product
        prices = stripe.Price.list(product=product_id, active=True, limit=100) # Retrieve active Prices connected to the Product

        for price in prices.auto_paging_iter(): # Loop through all active Prices, including additional pages
            stripe.Price.modify(price.id, active=False) # Deactivate this Stripe Price
            deactivated_count += 1 # Increment the deactivated price count
    except stripe.StripeError as error: # Catch Stripe SDK/API failures
        logger.exception("Stripe Price cleanup failed for product %s.", product_id) # Log the cleanup failure
        raise StripeProductSyncError("Stripe Price cleanup failed. Check Stripe configuration and try again.") from error # Raise a safe cleanup error

    return deactivated_count # Return how many Prices were deactivated


def archive_or_delete_stripe_product(product_id): # Define a helper that archives or deletes one Stripe Product safely
    configure_stripe() # Configure Stripe with the secret key from the app environment

    if not product_id: # Check if there is no Product ID
        return None # Return nothing because there is no Stripe Product to clean

    try: # Try to inspect all Prices under the Product
        prices = list(stripe.Price.list(product=product_id, limit=100).auto_paging_iter()) # Retrieve all Prices connected to this Product
    except stripe.StripeError as error: # Catch Stripe SDK/API failures
        logger.exception("Stripe Price lookup failed for product %s.", product_id) # Log the lookup failure
        raise StripeProductSyncError("Stripe Product cleanup failed. Check Stripe configuration and try again.") from error # Raise a safe cleanup error

    if prices: # Check if the Product has any Prices attached
        deactivate_all_prices_for_product(product_id) # Deactivate all active Prices before archiving the Product

        try: # Try to archive the Stripe Product
            return stripe.Product.modify(product_id, active=False) # Archive the Product because Products with Prices should not be deleted
        except stripe.StripeError as error: # Catch Stripe SDK/API failures
            logger.exception("Stripe Product archival failed for product %s.", product_id) # Log the archival failure
            raise StripeProductSyncError("Stripe Product archival failed. Check Stripe configuration and try again.") from error # Raise a safe cleanup error

    try: # Try to delete a Product with no Prices attached
        return stripe.Product.delete(product_id) # Delete the Product only when Stripe allows deletion
    except stripe.StripeError as error: # Catch Stripe SDK/API failures
        logger.exception("Stripe Product deletion failed for product %s.", product_id) # Log the deletion failure
        raise StripeProductSyncError("Stripe Product deletion failed. Check Stripe configuration and try again.") from error # Raise a safe cleanup error


def ensure_stripe_product_and_price_for_drop(drop): # Define the main helper used after creating or editing a drop
    old_price_id = drop.stripe_price_id # Store the current Stripe Price ID before any possible replacement

    if not drop.stripe_product_id: # Check if the drop is missing a Stripe Product ID
        create_stripe_product_for_drop(drop) # Create and save the missing Stripe Product ID
    else: # Run this block when the Stripe Product already exists
        update_stripe_product_for_drop(drop) # Keep the Stripe Product name, description, and image updated

    if not stripe_price_matches_drop(drop): # Check if the saved Price is missing, mismatched, inactive, wrong currency, wrong Product, or wrong amount
        create_stripe_price_for_drop(drop) # Create and save a fresh matching USD Stripe Price
        deactivate_stripe_price(old_price_id) # Deactivate the previous Price after replacing it

    return drop # Return the synced drop object


def sync_stripe_after_drop_edit(drop, old_price=None): # Define a helper for edit behaviour while keeping the old route call compatible
    return ensure_stripe_product_and_price_for_drop(drop) # Reuse the same robust sync logic for edited drops


def archive_stripe_catalog_for_drop(drop): # Define a helper that cleans Stripe when a local drop is deleted
    return archive_or_delete_stripe_product(drop.stripe_product_id) # Archive or delete the Stripe Product connected to this drop


def archive_orphan_stripe_products_by_drop_number(drop_number): # Define a helper that archives Stripe Products when the local Drop was already deleted
    configure_stripe() # Configure Stripe with the secret key from the app environment
    archived_count = 0 # Track how many orphan Stripe Products were archived

    try: # Try to list active Stripe Products
        products = stripe.Product.list(active=True, limit=100) # Retrieve active Stripe Products
    except stripe.StripeError as error: # Catch Stripe SDK/API failures
        logger.exception("Stripe Product listing failed while cleaning orphan Drop #%s.", drop_number) # Log the listing failure
        raise StripeProductSyncError("Stripe orphan cleanup failed. Check Stripe configuration and try again.") from error # Raise a safe cleanup error

    for product in products.auto_paging_iter(): # Loop through active Stripe Products
        metadata_drop_number = product.metadata.get("drop_number") if product.metadata else None # Read the metadata drop number safely
        product_name = product.name or "" # Read the Stripe Product name safely

        if metadata_drop_number == drop_number or f"Drop #{drop_number}" in product_name: # Match Products connected to the deleted local drop
            archive_or_delete_stripe_product(product.id) # Archive or delete the orphan Stripe Product safely
            archived_count += 1 # Increment the orphan cleanup count

    return archived_count # Return how many orphan Stripe Products were cleaned