import requests  # Import requests so the app can call the Printify HTTP API
from flask import current_app  # Import current_app so the service can read Flask configuration values

from app.extensions import db  # Import the database object so synced drop changes can be saved


class PrintifyConfigError(Exception):  # Create a custom error for missing Printify configuration
    pass  # Keep the custom exception body empty because the class name explains the error type


class PrintifyAPIError(Exception):  # Create a custom error for failed Printify API responses
    pass  # Keep the custom exception body empty because the class name explains the error type


def get_printify_config():  # Define a helper function that reads Printify configuration from Flask config
    api_base_url = current_app.config.get("PRINTIFY_API_BASE_URL")  # Read the Printify base URL
    api_token = current_app.config.get("PRINTIFY_API_TOKEN")  # Read the Printify API token
    shop_id = current_app.config.get("PRINTIFY_SHOP_ID")  # Read the Printify shop ID

    if not api_base_url:  # Check if the API base URL is missing
        raise PrintifyConfigError("PRINTIFY_API_BASE_URL is not configured.")  # Raise a clear configuration error

    if not api_token:  # Check if the API token is missing
        raise PrintifyConfigError("PRINTIFY_API_TOKEN is not configured.")  # Raise a clear configuration error

    return api_base_url.rstrip("/"), api_token, shop_id  # Return the cleaned API base URL, token, and shop ID


def build_headers(api_token):  # Define a helper function that builds Printify request headers
    return {  # Return the headers dictionary
        "Authorization": f"Bearer {api_token}",  # Send the Printify API token as a bearer token
        "Content-Type": "application/json;charset=utf-8",  # Tell Printify that request bodies use UTF-8 JSON
        "Accept": "application/json",  # Tell Printify that the app expects JSON responses
        "User-Agent": "TheOnlyDropFlaskApp/1.0",  # Identify this backend app as required by Printify API rules
    }  # Close the headers dictionary


def printify_request(method, path, **kwargs):  # Define a reusable helper for making Printify API requests
    api_base_url, api_token, _shop_id = get_printify_config()  # Read Printify configuration values
    url = f"{api_base_url}/{path.lstrip('/')}"  # Build the full Printify API URL with exactly one slash between base URL and path
    headers = build_headers(api_token)  # Build the authorization headers

    try:  # Start a protected block for the HTTP request
        response = requests.request(  # Send the HTTP request to Printify
            method=method,  # Pass the HTTP method passed into the helper
            url=url,  # Use the full Printify API URL
            headers=headers,  # Send the bearer-token headers
            timeout=20,  # Avoid hanging forever if the API does not respond
            **kwargs,  # Pass through optional request arguments such as params or json
        )  # Close the requests call
    except requests.RequestException as error:  # Catch network-level request errors
        raise PrintifyAPIError(f"Printify request failed: {error}") from error  # Raise a clear application-level API error

    if not response.ok:  # Check if Printify returned an error HTTP status
        raise PrintifyAPIError(f"Printify API error {response.status_code}: {response.text}")  # Raise the status and response text for debugging

    if not response.content:  # Check if Printify returned an empty response body
        return {}  # Return an empty dictionary for empty successful responses

    return response.json()  # Parse and return the JSON responde body


def get_printify_shops():  # Define a service function that retrieves Printify shops
    return printify_request("GET", "shops.json")  # Call the Printify shops endpoint


def get_printify_products():  # Define a service function that retrieves all Printify products for the configured shop
    shop_id = require_printify_shop_id()  # Read and require the configured Printify shop ID
    return printify_request("GET", f"/shops/{shop_id}/products.json")  # Retrieve all Printify products from the configured shop


def require_printify_shop_id():  # Define a helper function that requires a configured shop ID
    _api_base_url, _api_token, shop_id = get_printify_config()  # Read the Printify configuration values

    if not shop_id:  # Check if the shop ID is missing
        raise PrintifyConfigError("PRINTIFY_SHOP_ID is not configured.")  # Raise a clear configuration error

    return shop_id  # Return the configured Printify shop ID


def get_printify_product(product_id):  # Define a service function that retrieves one Printify product
    shop_id = require_printify_shop_id()  # Read and require the configured Printify shop ID
    return printify_request("GET", f"shops/{shop_id}/products/{product_id}.json")  # Retrieve the selected Printify product


def parse_variant_ids(raw_variant_ids):  # Define a helper function that parses stored variant IDs from text
    if not raw_variant_ids:  # Check if no variant IDs were stored
        return []  # Return an empty list when there are no selected variants

    cleaned_parts = []  # Create an empty list for cleaned variant ID values

    for part in raw_variant_ids.replace("\n", ",").split(","):  # Split comma-separated and new-line separated values
        cleaned_part = part.strip()  # Remove surrounding whitespace from each valie

        if cleaned_part:  # Check if the cleaned value is not empty
            cleaned_parts.append(cleaned_part)  # Add the cleaned value to the list

    return cleaned_parts  # Return the cleaned variant ID list


def normalize_variant_ids(variant_ids):  # Define a helper function that formats variant IDs consistently
    return ", ".join(str(variant_id) for variant_id in variant_ids)  # Return a comma-separated variant ID string


def get_default_product_image(product):  # Define a helper function that finds the best product mockup image
    images = product.get("images", [])  # Read the product images list from the Printify response

    for image in images:  # Loop through all product images first
        if image.get("is_default"):  # Check if Printify marked this image as the primary/default mockup
            return image.get("src")  # Return the primary/default mockup image URL

    for image in images:  # Loop through all product images again
        image_src = image.get("src", "")  # Read the image URL or use an empty fallback
        if "camera_label=front" in image_src:  # Check if the image URL is clearly a front mockup
            return image_src  # Return the front mockup image URL

    for image in images:  # Loop through all product images again
        image_src = image.get("src", "")  # Read the image URL or use an empty fallback
        if image.get("position") == "front":  # Check if Printify marked this image position as front
            return image_src  # Return the front-position image URL

    if images:  # Check if any image exists at all
        return images[0].get("src")  # Return the first image URL as a final fallback

    return None  # Return None when the product has no images


def get_product_variant_summary(product, selected_variant_ids=None):  # Define a helper function that summarizes product variant availability
    selected_variant_ids = selected_variant_ids or []  # Use an empty list if no selected ID's were provided
    selected_variant_ids_as_text = {str(variant_id) for variant_id in selected_variant_ids}  # Normalize selected IDs to strings
    variants = product.get("variants", [])  # Read product variants from the Printify product response
    selected_variants = []  # Create a list for selected variants
    enabled_available_variants = []  # Create a list for variants that are enabled and available

    for variant in variants:  # Loop thorugh every variant from Printify
        variant_id_as_text = str(variant.get("id"))  # Convert the variant ID to text for comparison
        is_enabled = bool(variant.get("is_enabled"))  # Read whether the variant is enabled
        is_available = bool(variant.get("is_available"))  # Read whether the variant is available

        if is_enabled and is_available:  # Check if the variant can currently be sold
            enabled_available_variants.append(variant)  # Add the variant to the available list

        if selected_variant_ids_as_text and variant_id_as_text in selected_variant_ids_as_text:  # Check if this variant was selected for the drop
            selected_variants.append(variant)  # Add the variant to the selected list

    selected_available_variants = [  # Build a list of selected variants that are enabled and available
        variant  # Keep the current selected variant
        for variant in selected_variants  # Loop through each selected variant
        if variant.get("is_enabled") and variant.get("is_available")  # Keep only enabled and available selected variants
    ]  # Close the selected available variants list

    return {  # Return a structured variant summary
        "total_variants": len(variants),  # Store the total number of variants in the product
        "enabled_available_variants": enabled_available_variants,  # Store enabled and available variants
        "selected_variants": selected_variants,  # Store variants selected by the admin
        "selected_available_variants": selected_available_variants,  # Store selected variants that are currently available
    }  # Close the summary dictionary


def sync_drop_with_printify(drop):  # Define a service function that syncs one database drop with its Printify product
    if not drop.printify_product_id:  # Check if the drop has no Printify product ID
        raise PrintifyConfigError("This drop does not have a Printify product ID.")  # Raise a clear sync error

    product = get_printify_product(drop.printify_product_id)  # Retrieve the Printify product connected to this drop
    selected_variant_ids = parse_variant_ids(drop.printify_variant_ids)  # Parse the drop's selected variant IDs
    variant_summary = get_product_variant_summary(product, selected_variant_ids)  # Build a variant availability summary
    default_image_url = get_default_product_image(product)  # Find the best mockup image URL

    if default_image_url:  # Check if a Printify product image was found
        drop.image_url = default_image_url  # Store the Printify mockup image URL on the drop

    if selected_variant_ids:  # Check if the admin already selected variant IDs
        drop.printify_variant_ids = normalize_variant_ids(selected_variant_ids)  # Normalize the stored variant ID formatting

    db.session.commit()  # Save synced drop changes to the database

    return {  # Return a sync report for admin UI and CLI output
        "product": product,  # Include the raw product response for inspected fields
        "default_image_url": default_image_url,  # Include the synced product image URL
        "variant_summary": variant_summary,  # Include variant availability details
    }  # Close the sync report dictionary




