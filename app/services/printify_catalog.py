from app.models import Drop # Import Drop so Printify products already connected to drops can be excluded
from app.services.printify import PrintifyAPIError, PrintifyConfigError, printify_request, require_printify_shop_id # Import Printify helpers for shop/product API access


class PrintifyProductSelectionError(RuntimeError): # Define a custom error for invalid Printify product selections
    pass # Keep the custom exception body empty because the message comes from raise statements


def get_product_image_url(product): # Define a helper that extracts a small product mockup image URL
    images = product.get("images") or [] # Read the Printify images list or use an empty fallback

    if not images: # Check if the product has no images
        return None # Return no image URL

    first_image = images[0] # Read the first image object from Printify

    if isinstance(first_image, dict): # Check if the image is a dictionary object
        return first_image.get("src") or first_image.get("url") # Return the most likely image URL field

    return None # Return no image URL if the image format is unexpected


def get_enabled_available_variant_ids(product): # Define a helper that extracts available variant IDs from a Printify product
    variant_ids = [] # Create an empty list for selected variant IDs

    for variant in product.get("variants", []): # Loop through product variants returned by Printify
        is_enabled = variant.get("is_enabled", False) # Read whether this variant is enabled
        is_available = variant.get("is_available", False) # Read whether this variant is available

        if is_enabled and is_available: # Keep only variants that are both enabled and available
            variant_ids.append(str(variant["id"])) # Store the variant ID as text

    return variant_ids # Return all usable variant IDs


def get_connected_printify_product_ids(current_drop=None): # Define a helper that finds Printify product IDs already connected locally
    query = Drop.query.filter(Drop.printify_product_id.isnot(None)) # Query drops that already have Printify product IDs

    if current_drop is not None and current_drop.id is not None: # Check if we are editing an existing drop
        query = query.filter(Drop.id != current_drop.id) # Exclude the current drop so its current product remains selectable

    return {drop.printify_product_id for drop in query.all() if drop.printify_product_id} # Return connected product IDs as a set


def build_printify_product_choice(product): # Define a helper that converts one Printify product into picker data
    return { # Return a template-friendly product choice dictionary
        "id": product.get("id"), # Store the Printify product ID
        "title": product.get("title", "Untitled Printify Product"), # Store the Printify product title for display only
        "image_url": get_product_image_url(product), # Store the first mockup image URL if available
    } # Close the product choice dictionary


def list_available_printify_products(current_drop=None): # Define a helper that lists Printify products not connected to other drops
    shop_id = require_printify_shop_id() # Read the configured Printify shop ID
    response = printify_request("GET", f"/shops/{shop_id}/products.json") # Retrieve products from the configured Printify shop
    connected_product_ids = get_connected_printify_product_ids(current_drop=current_drop) # Read locally connected Printify product IDs
    available_products = [] # Create an empty list for selectable Printify products

    for product in response.get("data", []): # Loop through Printify products returned by the API
        product_id = product.get("id") # Read this Printify product ID

        if not product_id: # Check if the product has no ID
            continue # Skip invalid product data

        if product_id in connected_product_ids: # Check if another local drop already uses this Printify product
            continue # Skip products already connected to another drop

        available_products.append(build_printify_product_choice(product)) # Add the product to the picker choices

    return available_products # Return selectable Printify products


def get_printify_product(product_id): # Define a helper that retrieves one full Printify product
    if not product_id: # Check if no product ID was selected
        return None # Return no product

    shop_id = require_printify_shop_id() # Read the configured Printify shop ID
    return printify_request("GET", f"/shops/{shop_id}/products/{product_id}.json") # Retrieve one full Printify product from the shop


def ensure_printify_product_is_available(product_id, current_drop=None): # Define a helper that prevents duplicate Printify product assignment
    if not product_id: # Check if no Printify product was selected
        return None # Return no blocking drop

    query = Drop.query.filter(Drop.printify_product_id == product_id) # Find drops already connected to this Printify product

    if current_drop is not None and current_drop.id is not None: # Check if this is an edit flow
        query = query.filter(Drop.id != current_drop.id) # Ignore the current drop's own existing product

    existing_drop = query.first() # Retrieve the first conflicting local drop

    if existing_drop: # Check if another drop already uses this product
        raise PrintifyProductSelectionError(f"That Printify product is already connected to Drop #{existing_drop.drop_number}.") # Stop duplicate assignment

    return None # Return no conflict


def clear_printify_product_selection(drop): # Define a helper that clears Printify fields from a drop
    drop.printify_product_id = None # Clear the Printify product ID
    drop.printify_variant_ids = None # Clear selected Printify variant IDs
    drop.printify_size_variant_map = None # Clear the size-to-variant map
    drop.image_url = None # Clear the primary synced mockup image
    drop.mockup_image_urls = None # Clear synced mockup carousel image URLs


def apply_printify_product_selection(drop, product_id): # Define a helper that applies a selected Printify product to a local drop
    cleaned_product_id = product_id.strip() if product_id else None # Clean the submitted Printify product ID
    current_product_id = drop.printify_product_id # Store the current Printify product ID before changing it

    if not cleaned_product_id: # Check if the admin selected no Printify product
        clear_printify_product_selection(drop) # Clear existing Printify connection fields
        return None # Return no Printify product

    ensure_printify_product_is_available(cleaned_product_id, current_drop=drop) # Prevent assigning a product already connected to another drop

    product = get_printify_product(cleaned_product_id) # Retrieve the full Printify product data
    variant_ids = get_enabled_available_variant_ids(product) # Extract enabled and available variant IDs

    if not variant_ids: # Check if no usable variants were found
        raise PrintifyProductSelectionError("The selected Printify product has no enabled and available variants.") # Stop invalid product assignment

    if current_product_id != cleaned_product_id: # Check if the admin selected a different Printify product
        clear_printify_product_selection(drop) # Clear stale mockups, old size mapping, and old variant data before applying the new product

    drop.printify_product_id = cleaned_product_id # Save the selected Printify product ID
    drop.printify_variant_ids = ", ".join(variant_ids) # Save the selected variant IDs automatically

    return product # Return the retrieved Printify product
