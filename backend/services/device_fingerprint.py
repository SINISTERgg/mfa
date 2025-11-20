from datetime import datetime, timedelta
from flask import current_app
from models import DeviceFingerprint, db
from utils.security import hash_fingerprint
import user_agents


class DeviceFingerprintService:
    """Service for device fingerprint operations"""
    
    def __init__(self):
        self.trust_duration = None
    
    def _load_config(self):
        """Load configuration from app context"""
        if current_app:
            self.trust_duration = current_app.config.get('DEVICE_TRUST_DURATION', 2592000)
    
    def create_or_update_device(self, user_id, fingerprint_data, ip_address, user_agent_string):
        """
        Create or update device fingerprint
        
        Args:
            user_id: User ID
            fingerprint_data: Device fingerprint string
            ip_address: IP address
            user_agent_string: User agent string
        
        Returns:
            DeviceFingerprint: Device object
        """
        self._load_config()
        
        # Hash the fingerprint
        fingerprint_hash = hash_fingerprint(fingerprint_data)
        
        # Parse user agent
        user_agent = user_agents.parse(user_agent_string)
        
        # Check if device exists
        device = DeviceFingerprint.query.filter_by(
            user_id=user_id,
            fingerprint_hash=fingerprint_hash
        ).first()
        
        if device:
            # Update existing device
            device.last_seen = datetime.utcnow()
            device.ip_address = ip_address
        else:
            # Create new device
            device = DeviceFingerprint(
                user_id=user_id,
                fingerprint_hash=fingerprint_hash,
                device_name=self._generate_device_name(user_agent),
                device_type=self._get_device_type(user_agent),
                browser=user_agent.browser.family,
                os=user_agent.os.family,
                ip_address=ip_address
            )
            db.session.add(device)
        
        db.session.commit()
        
        return device
    
    def is_trusted_device(self, user_id, fingerprint_data):
        """
        Check if device is trusted
        
        Args:
            user_id: User ID
            fingerprint_data: Device fingerprint string
        
        Returns:
            tuple: (is_trusted, device)
        """
        fingerprint_hash = hash_fingerprint(fingerprint_data)
        
        device = DeviceFingerprint.query.filter_by(
            user_id=user_id,
            fingerprint_hash=fingerprint_hash,
            is_trusted=True
        ).first()
        
        if device and device.is_trust_valid():
            return True, device
        
        return False, device
    
    def trust_device(self, device_id, user_id):
        """
        Mark device as trusted
        
        Args:
            device_id: Device ID
            user_id: User ID
        
        Returns:
            tuple: (success, error_message)
        """
        self._load_config()
        
        device = DeviceFingerprint.query.filter_by(
            id=device_id,
            user_id=user_id
        ).first()
        
        if not device:
            return False, "Device not found"
        
        device.is_trusted = True
        device.trust_expires_at = datetime.utcnow() + timedelta(seconds=self.trust_duration)
        
        db.session.commit()
        
        return True, None
    
    def revoke_device_trust(self, device_id, user_id):
        """
        Revoke device trust
        
        Args:
            device_id: Device ID
            user_id: User ID
        
        Returns:
            tuple: (success, error_message)
        """
        device = DeviceFingerprint.query.filter_by(
            id=device_id,
            user_id=user_id
        ).first()
        
        if not device:
            return False, "Device not found"
        
        device.is_trusted = False
        device.trust_expires_at = None
        
        db.session.commit()
        
        return True, None
    
    def get_user_devices(self, user_id):
        """Get all devices for a user"""
        devices = DeviceFingerprint.query.filter_by(user_id=user_id).order_by(
            DeviceFingerprint.last_seen.desc()
        ).all()
        
        return devices
    
    def delete_device(self, device_id, user_id):
        """Delete a device"""
        device = DeviceFingerprint.query.filter_by(
            id=device_id,
            user_id=user_id
        ).first()
        
        if not device:
            return False, "Device not found"
        
        db.session.delete(device)
        db.session.commit()
        
        return True, None
    
    def _generate_device_name(self, user_agent):
        """Generate a friendly device name"""
        browser = user_agent.browser.family
        os = user_agent.os.family
        
        return f"{browser} on {os}"
    
    def _get_device_type(self, user_agent):
        """Determine device type"""
        if user_agent.is_mobile:
            return "mobile"
        elif user_agent.is_tablet:
            return "tablet"
        else:
            return "desktop"
