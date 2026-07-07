DROP_STATUS_DRAFT = "draft"  # Store the draft status used before a drop becomes publicly active
DROP_STATUS_ACTIVE = "active"  # Store the active status used for the current public drop
DROP_STATUS_ARCHIVED = "archived"  # Store the archived status used after a drop leaves the active page


VALID_DROP_STATUSES = (  # Store all valid drop statuses in one reusable tuple
    DROP_STATUS_DRAFT,  # Allow the draft lifecycle status
    DROP_STATUS_ACTIVE,  # Allow the active lifecycle status
    DROP_STATUS_ARCHIVED,  # Allow the archived lifecycle status
)  # Close the valid statuses tuple


BRAND_NAME = "The Only Drop"  # Store the public brand name used accross the website
BRAND_NAME_UPPER = "THE ONLY DROP"  # Store the uppercase brand named used in navigation and footer
PRIMARY_DOMAIN = "the-only-drop.com"  # Store the planned production domain for the project
PRODUCT_CATEGORY_SINGULAR = "T-shirt"  # Store the current singular product category
PRODUCT_CATEGORY_PLURAL = "T-shirts"  # Store the current plural product category
DROP_CADENCE_LABEL = "Monthly Drop"  # Store the public cadence label for current drops
BRAND_TAGLINE = "One monthly design. Available while stock lasts. Archived forever."  # Store the main product positioning line