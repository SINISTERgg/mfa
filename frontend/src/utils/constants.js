export const MFA_METHODS = {
  FACE: 'face',
  VOICE: 'voice',
  OTP: 'otp',
  BACKUP_CODE: 'backup_code',
  BIOMETRIC: 'biometric',
};

export const AUTH_STEPS = {
  LOGIN: 'login',
  MFA_REQUIRED: 'mfa_required',
  MFA_VERIFICATION: 'mfa_verification',
  SUCCESS: 'success',
};

export const DEVICE_TYPES = {
  DESKTOP: 'desktop',
  MOBILE: 'mobile',
  TABLET: 'tablet',
};

export const MESSAGES = {
  LOGIN_SUCCESS: 'Login successful!',
  REGISTER_SUCCESS: 'Registration successful!',
  MFA_REQUIRED: 'Please complete MFA verification',
  FACE_ENROLLED: 'Face recognition enrolled successfully',
  VOICE_ENROLLED: 'Voice recognition enrolled successfully',
  OTP_ENROLLED: 'OTP enrolled successfully',
  PROFILE_UPDATED: 'Profile updated successfully',
  DEVICE_TRUSTED: 'Device marked as trusted',
  DEVICE_DELETED: 'Device deleted successfully',
  ERROR_OCCURRED: 'An error occurred. Please try again.',
};

