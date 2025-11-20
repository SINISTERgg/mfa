import re

try:
    from email_validator import validate_email as email_validate, EmailNotValidError # type: ignore
    _EMAIL_VALIDATOR_AVAILABLE = True
except Exception:
    # Fallback basic validator if email_validator package is not installed
    _EMAIL_VALIDATOR_AVAILABLE = False
    email_validate = None
    class EmailNotValidError(ValueError):
        pass


def validate_email(email):
    """Validate email format"""
    if _EMAIL_VALIDATOR_AVAILABLE:
        try:
            # Validate and normalize the email
            valid = email_validate(email)
            return True, valid.email
        except EmailNotValidError as e:
            return False, str(e)

    # Basic fallback validation
    if not email:
        return False, "Email is required"

    # Simple regex to check basic email structure
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        return False, "Invalid email format"

    return True, email.lower()


def validate_username(username):
    """Validate username format"""
    if not username:
        return False, "Username is required"
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    
    if len(username) > 80:
        return False, "Username must not exceed 80 characters"
    
    # Allow alphanumeric, underscore, and dash
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain letters, numbers, underscores, and dashes"
    
    return True, username


def validate_password(password):
    """Validate password strength"""
    if not password:
        return False, "Password is required"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    if len(password) > 128:
        return False, "Password must not exceed 128 characters"
    
    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    # Check for at least one lowercase letter
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    # Check for at least one digit
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    # Check for at least one special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is valid"


def validate_otp_code(code):
    """Validate OTP code format"""
    if not code:
        return False, "OTP code is required"
    
    # OTP should be 6 digits
    if not re.match(r'^\d{6}$', code):
        return False, "OTP code must be 6 digits"
    
    return True, code


def validate_backup_code(code):
    """Validate backup code format"""
    if not code:
        return False, "Backup code is required"
    
    # Format: XXXX-XXXX (8 hex characters with dash)
    if not re.match(r'^[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}$', code):
        return False, "Invalid backup code format"
    
    return True, code.upper()


def validate_device_fingerprint(fingerprint):
    """Validate device fingerprint format"""
    if not fingerprint:
        return False, "Device fingerprint is required"
    
    if len(fingerprint) < 10:
        return False, "Invalid device fingerprint"
    
    return True, fingerprint
