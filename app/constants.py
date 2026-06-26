DROP_STATUS_DRAFT = "draft"  # Store the draft status used before a drop becomes publicly active
DROP_STATUS_ACTIVE = "active"  # Store the active status used for the current public drop
DROP_STATUS_ARCHIVED = "archived"  # Store the archived status used after a drop leaves the active page


VALID_DROP_STATUSES = (  # Store all valid drop statuses in one reusable tuple
    DROP_STATUS_DRAFT,  # Allow the draft lifecycle status
    DROP_STATUS_ACTIVE,  # Allow the active lifecycle status
    DROP_STATUS_ARCHIVED,  # Allow the archived lifecycle status
)  # Close the valid statuses tuple


