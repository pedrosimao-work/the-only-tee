import json  # Import json so multiple mockup image URLs can be stored as JSON text
import requests  # Import requests so the app can call the Printify HTTP API
from flask import current_app  # Import current_app so the service can read Flask configuration values

from app.extensions import db  # Import the database object so synced drop changes can be saved
from app.constants import DROP_SIZE_ORDER  # Import the preferred storefront size order



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


def get_product_mockup_images(product, limit=4):  # Define a helper function that returns the best mockup image in display order
    images = product.get("images", [])  # Read the product images list from the Printify response
    default_images = []  # Create a list for Printify primary/default images
    other_images = []  # Create a list for non-primary mockup images
    selected_urls = []  # Create a final list for unique mockup image URLs

    for image in images:  # Loop through every Printify image
        image_src = image.get("src")  # Read the image URL from the Printify image object

        if not image_src:  # Check if this image has no usable URL
            continue

        if image.get("is_default"):  # Check if Printify marked this image as the primary/default mockup
            default_images.append(image_src)  # Add the primary/default image first
        else:  # Run this block for normal mockup images
            other_images.append(image_src)  # Add the non-primary image to the secondary list

    for image_src in default_images + other_images:  # Loop through primary images first, then the remaining images in Printify order
        if image_src not in selected_urls:  # Check if this URL has not already been added
            selected_urls.append(image_src)  # Add the unique mockup image URL to the final list

        if len(selected_urls) == limit:  # Check if the carousel image limit has been reached
            break  # Stop collecting image URLs

    return selected_urls  # Return the selected mockup imaged URLs


def get_variant_size(variant):  # Define a helper function that extracts the size label from a Printify variant
    variant_title = variant.get("title", "")  # Read the Printify variant title safely

    if "/" in variant_title:  # Check if the title uses the usual "Color / Size" format
        return variant_title.split("/")[-1].strip()  # Return the final part as the size label

    return variant_title.strip()  # Return the full title as a fallback size label


def sort_size_variant_map(size_variant_map):  # Define a helper function that sorts the size-to-variant map
    sorted_map = {}  # Create an empty dictionary for ordered size entries

    for size in DROP_SIZE_ORDER:  # Loop through the preferred storefront size order
        if size in size_variant_map:  # Check if this size exists in the generated map
            sorted_map[size] = size_variant_map[size]  # Add this size in the preferred order

    for size in sorted(size_variant_map):  # Loop through any remaining unexpected sizes alphabetically
        if size not in sorted_map:  # Check if this size has not already been added
            sorted_map[size] = size_variant_map[size]  # Add the remaining size at the end

    return sorted_map  # Return the sorted size-to-variant map


def build_size_variant_map(product, selected_variant_ids):  # Define a helper function that maps storefront sizes to Printify variant IDs
    if isinstance(selected_variant_ids, str):  # Check if selected variant IDs were passed as stored text
        selected_variant_ids = parse_variant_ids(selected_variant_ids)  # Convert stored text into a clean list of variant IDs

    selected_variant_ids_as_text = {str(variant_id).strip() for variant_id in selected_variant_ids}  # Convert selected variant IDs into a text set for fast comparison
    size_variant_map = {}  # Create an empty dictionary for size-to-variant mapping

    for variant in product.get("variants", []):  # Loop through every Printify variant on the product
        variant_id = str(variant.get("id")).strip()  # Read the variant ID as clean text for comparison

        if variant_id not in selected_variant_ids_as_text:  # Check if this variant is not selected for this monthly drop
            continue  # Skip variants that do not belong to the selected color and sizes

        if not variant.get("is_enabled"):  # Check if the Printify variant is not enabled
            continue  # Skip disabled variants

        if not variant.get("is_available"):  # Check if the Printify variant is not available
            continue  # Skip unavailable variants

        variant_size = get_variant_size(variant)  # Extract the customer-facing size from the Printify variant title

        if not variant_size:  # Check if no size could be extracted
            continue  # Skip variants without a usable size

        if variant_size not in size_variant_map:  # Check if this size has not already been mapped
            size_variant_map[variant_size] = variant_id  # Store the Printify variant ID for this size

    return sort_size_variant_map(size_variant_map)  # Return the size map in storefront order


def get_product_variant_summary(product, selected_variant_ids=None):  # Define a helper function that summarizes product variant availability
    selected_variant_ids = selected_variant_ids or []  # Use an empty list if no selected IDs were provided
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
    size_variant_map = build_size_variant_map(product, drop.printify_variant_ids)  # Build a size-to-Printify-variant map from selected available variants
    mockup_image_urls = get_product_mockup_images(product)  # Collect the best Printify mockup image URLs for the drop carousel
    default_image_url = mockup_image_urls[0] if mockup_image_urls else get_default_product_image(product)  # Use the first carousel image as the primary image

    if default_image_url:  # Check if a Printify product image was found
        drop.image_url = default_image_url  # Store the primary Printify mockup image URL on the drop

    if mockup_image_urls:  # Check if Printify returned usable mockup image URLs
        drop.mockup_image_urls = json.dumps(mockup_image_urls)  # Store multiple mockup image URLs as JSON text

    if selected_variant_ids:  # Check if the admin already selected variant IDs
        drop.printify_variant_ids = normalize_variant_ids(selected_variant_ids)  # Normalize the stored variant ID formatting

    if size_variant_map:  # Check if usable size variants were found
        drop.printify_size_variant_map = json.dumps(size_variant_map)  # Store the size-to-variant map as JSON text

    db.session.commit()  # Save synced drop changes to the database

    return {  # Return a sync report for admin UI and CLI output
        "product": product,  # Include the raw product response for inspected fields
        "default_image_url": default_image_url,  # Include the synced product image URL
        "mockup_image_urls": mockup_image_urls,  # Include all synced mockup image URLs
        "variant_summary": variant_summary,  # Include variant availability details
        "size_variant_map": size_variant_map,  # Include the synced size-to-variant map
    }  # Close the sync report dictionary




