import api from './api';

const authService = {
  register: async (username, email, password, fullName) => {
    const response = await api.post('/api/auth/register', {
      username,
      email,
      password,
      full_name: fullName,
    });
    return response.data;
  },

  login: async (username, password) => {
    const response = await api.post('/api/auth/login', {
      username,
      password,
    });
    
    if (response.data.mfa_token) {
      localStorage.setItem('mfa_token', response.data.mfa_token);
    }
    
    return response.data;
  },

  // ✅ FIXED: Send face_image
  verifyFace: async (mfaToken, faceImageBase64) => {
    console.log('📤 [API] Sending face verification...');
    console.log('🔑 [MFA TOKEN]', mfaToken);
    console.log('📸 [FACE IMAGE]', faceImageBase64.substring(0, 50) + '...');
    
    const response = await api.post('/api/auth/mfa/verify-face', {
      mfa_token: mfaToken,
      face_image: faceImageBase64  // ✅ Match backend expectation
    });
    return response.data;
  },

  // ✅ FIXED: Send voice_audio
  verifyVoice: async (mfaToken, voiceAudioBase64) => {
    console.log('📤 [API] Sending voice verification...');
    console.log('🔑 [MFA TOKEN]', mfaToken);
    console.log('🎤 [VOICE AUDIO]', voiceAudioBase64.substring(0, 50) + '...');
    
    const response = await api.post('/api/auth/mfa/verify-voice', {
      mfa_token: mfaToken,
      voice_audio: voiceAudioBase64  // ✅ Match backend expectation
    });
    return response.data;
  },

  verifyOTP: async (mfaToken, otpCode) => {
    const response = await api.post('/api/auth/mfa/verify-otp', {
      mfa_token: mfaToken,
      otp_code: otpCode,
    });
    return response.data;
  },

  verifyBackupCode: async (mfaToken, backupCode) => {
    const response = await api.post('/api/auth/mfa/verify-backup-code', {
      mfa_token: mfaToken,
      backup_code: backupCode,
    });
    return response.data;
  },

  verifyGesture: async (mfaToken, gestureData) => {
    const response = await api.post('/api/auth/mfa/verify-gesture', {
      mfa_token: mfaToken,
      gesture: gestureData,
    });
    return response.data;
  },

  verifyKeystroke: async (mfaToken, keystrokeData) => {
    const response = await api.post('/api/auth/mfa/verify-keystroke', {
      mfa_token: mfaToken,
      keystroke: keystrokeData.keystroke,
      passphrase: keystrokeData.passphrase,
    });
    return response.data;
  },

  refreshToken: async (refreshToken) => {
    const response = await api.post(
      '/api/auth/refresh',
      {},
      {
        headers: { Authorization: `Bearer ${refreshToken}` },
      }
    );
    return response.data;
  },

  logout: async () => {
    try {
      await api.post('/api/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    localStorage.removeItem('mfa_token');
  },
};

export default authService;
    