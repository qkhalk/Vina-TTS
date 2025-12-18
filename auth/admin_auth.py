import os
from typing import Optional


def get_admin_password() -> Optional[str]:
    """Get admin password from environment variable."""
    return os.getenv("ADMIN_PASSWORD")


def verify_admin_password(password: str) -> bool:
    """
    Verify admin password against environment variable.
    
    Args:
        password: Password to verify
        
    Returns:
        True if password matches, False otherwise
    """
    admin_password = get_admin_password()
    
    if admin_password is None:
        raise ValueError(
            "ADMIN_PASSWORD environment variable is not set. "
            "Please set it before starting the application."
        )
    
    return password == admin_password


def require_admin_password():
    """
    Check if admin password is configured.
    Raises ValueError if not set.
    """
    admin_password = get_admin_password()
    if admin_password is None or len(admin_password) < 12:
        raise ValueError(
            "ADMIN_PASSWORD must be set and at least 12 characters long. "
            "Example: ADMIN_PASSWORD=your-secure-password-here"
        )
