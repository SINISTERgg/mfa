
import base64
import io

import pyotp
import qrcode
from flask import current_app


class OTPService:
    """
    Stateless TOTP helper.
    - generate_secret()        -> new Base32 secret
    - build_provisioning_uri  -> otpauth:// URI for Google Authenticator etc.
    - build_qr_data_url       -> data:image/png;base64,... for frontend
    - verify_otp              -> validate a user-entered code
    - current_code            -> for diagnostics only (do not expose to clients)
    """

    def __init__(self):
        # Defaults; can be overridden by Flask config
        self.default_issuer = "MFA Auth System"
        # window = 1 means current time slice ±1 slice (about ±30s if period=30)
        self.default_valid_window = 1

    # ---------- internal helpers ----------

    def _issuer(self) -> str:
        if not current_app:
            return self.default_issuer
        return current_app.config.get("OTP_ISSUER_NAME", self.default_issuer)

    def _valid_window(self) -> int:
        if not current_app:
            return self.default_valid_window
        return int(current_app.config.get("OTP_VALIDITY_WINDOW", self.default_valid_window))

    # ---------- public API ----------

    @staticmethod
    def generate_secret() -> str:
        """
        Generate a new Base32 TOTP secret.
        Store this EXACT string in the database (e.g. user.otp_secret).
        """
        return pyotp.random_base32()

    def build_provisioning_uri(self, secret: str, account_name: str) -> str:
        """
        Create an otpauth:// URI for QR enrollment.

        :param secret: Base32 TOTP secret stored for the user
        :param account_name: usually user email or username
        """
        if not secret:
            raise ValueError("Missing TOTP secret")

        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=account_name, issuer_name=self._issuer())

    @staticmethod
    def build_qr_data_url(provisioning_uri: str) -> str:
        """
        Generate a data URL PNG QR code from a provisioning URI.
        Safe to send directly to the frontend.
        """
        if not provisioning_uri:
            raise ValueError("Missing provisioning URI")

        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_bytes = buffer.getvalue()

        b64 = base64.b64encode(img_bytes).decode("utf-8")
        return f"data:image/png;base64,{b64}"

    def verify_otp(self, secret: str, otp_code: str) -> bool:
        """
        Verify a user-supplied OTP code.

        :param secret: Base32 TOTP secret from the user's record
        :param otp_code: 6‑digit code entered by the user
        """
        if not secret or not otp_code:
            return False

        try:
            totp = pyotp.TOTP(secret)
            # valid_window extends acceptance to ±window time-steps
            return bool(totp.verify(otp_code.strip(), valid_window=self._valid_window()))
        except Exception:
            # Any decoding / format error -> treat as invalid
            return False

    @staticmethod
    def current_code(secret: str) -> str:
        """
        Return the current OTP (for debugging in server logs only).
        Never expose this to the client.
        """
        if not secret:
            raise ValueError("Missing TOTP secret")
        return pyotp.TOTP(secret).now()


otp_service = OTPService()
