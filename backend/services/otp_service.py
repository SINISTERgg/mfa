import pyotp
import qrcode
import io
import base64
from flask import current_app


class OTPService:
    """Service for OTP (TOTP) operations"""
    
    def __init__(self):
        self.issuer_name = None
        self.validity_window = None
    
    def _load_config(self):
        """Load configuration from app context"""
        if current_app:
            self.issuer_name = current_app.config.get('OTP_ISSUER_NAME', 'MFA Auth System')
            self.validity_window = current_app.config.get('OTP_VALIDITY_WINDOW', 2)
    
    def generate_secret(self):
        """Generate a new OTP secret"""
        return pyotp.random_base32()
    
    def generate_provisioning_uri(self, secret, username):
        """
        Generate provisioning URI for QR code
        
        Args:
            secret: OTP secret
            username: User's username
        
        Returns:
            str: Provisioning URI
        """
        self._load_config()
        
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(
            name=username,
            issuer_name=self.issuer_name
        )
        
        return uri
    
    def generate_qr_code(self, provisioning_uri):
        """
        Generate QR code image from provisioning URI
        
        Args:
            provisioning_uri: TOTP provisioning URI
        
        Returns:
            str: Base64 encoded QR code image
        """
        try:
            # Create QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            # Generate image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            return None
    
    def verify_otp(self, secret, otp_code):
        """
        Verify OTP code
        
        Args:
            secret: User's OTP secret
            otp_code: OTP code to verify
        
        Returns:
            bool: True if valid, False otherwise
        """
        self._load_config()
        
        try:
            totp = pyotp.TOTP(secret)
            
            # Verify with validity window (allows codes from adjacent time windows)
            is_valid = totp.verify(otp_code, valid_window=self.validity_window)
            
            return is_valid
            
        except Exception:
            return False
    
    def get_current_otp(self, secret):
        """
        Get current OTP code (for testing purposes)
        
        Args:
            secret: OTP secret
        
        Returns:
            str: Current OTP code
        """
        totp = pyotp.TOTP(secret)
        return totp.now()
