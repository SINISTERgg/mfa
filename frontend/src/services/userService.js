import api from './api';

const userService = {
  getProfile: async () => {
    const response = await api.get('/api/user/profile');
    return response.data;
  },

  updateProfile: async (fullName, email) => {
    const response = await api.put('/api/user/profile', {
      full_name: fullName,
      email,
    });
    return response.data;
  },

  enrollFace: async (faceImageBase64) => {
    console.log('📤 [ENROLL FACE] Sending...');
    console.log('📏 [SIZE]', faceImageBase64.length, 'characters');
    
    const response = await api.post('/api/user/enroll/face', {
      face_image: faceImageBase64
    });
    
    return response.data;
  },

  // ✅ FIXED: Send voice as JSON, not FormData
  enrollVoice: async (voiceAudioBase64) => {
    console.log('📤 [ENROLL VOICE] Sending...');
    console.log('📏 [SIZE]', voiceAudioBase64.length, 'characters');
    
    const response = await api.post('/api/user/enroll/voice', {
      voice_audio: voiceAudioBase64  // Send as JSON
    });
    
    return response.data;
  },

  enrollOTP: async () => {
    const response = await api.post('/api/user/enroll/otp');
    return response.data;
  },

  verifyOTPEnrollment: async (otpCode) => {
    const response = await api.post('/api/user/verify/otp', {
      otp_code: otpCode,
    });
    return response.data;
  },

  enrollGesture: async (gestureData) => {
    console.log('📤 [ENROLL GESTURE] Sending...');
    console.log('📏 [POINTS]', gestureData.points.length);
    
    const response = await api.post('/api/user/enroll/gesture', {
      gesture: gestureData,
    });
    return response.data;
  },

  enrollKeystroke: async (samples, passphrase) => {
    const response = await api.post('/api/user/enroll/keystroke', {
      samples: samples,
      passphrase: passphrase
    });
    return response.data;
  },

  unenrollMethod: async (method) => {
    const response = await api.post(`/api/user/unenroll/${method}`);
    return response.data;
  },

  getBackupCodes: async () => {
    const response = await api.get('/api/user/backup-codes');
    return response.data;
  },

  regenerateBackupCodes: async () => {
    const response = await api.post('/api/user/backup-codes/regenerate');
    return response.data;
  },

  getLoginHistory: async (limit = 20) => {
    const response = await api.get(`/api/user/login-history?limit=${limit}`);
    return response.data;
  },
};

export default userService;
