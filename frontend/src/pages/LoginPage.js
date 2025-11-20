import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import FaceRecognition from '../components/FaceRecognition';
import GestureRecognition from '../components/GestureRecognition';
import KeystrokeDynamicsAdvanced from '../components/KeystrokeDynamicsAdvanced';
import VoiceRecognition from '../components/VoiceRecognition';
import { useAuth } from '../context/AuthContext';
import authService from '../services/authService';
import './LoginPage.css';

const LoginPage = () => {
  const navigate = useNavigate();
  const { login: authLogin } = useAuth();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  
  const [credentials, setCredentials] = useState({
    username: '',
    password: '',
  });
  
  const [mfaData, setMfaData] = useState({
    mfaToken: '',
    enrolledMethods: [],
    selectedMethod: null,
  });

  const [otpCode, setOtpCode] = useState('');
  const [backupCode, setBackupCode] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      console.log('🔐 [LOGIN] Attempting login...');
      const response = await authService.login(
        credentials.username,
        credentials.password
      );

      console.log('✅ [LOGIN] Response:', response);

      if (response.requires_mfa) {
        console.log('🔒 [MFA] MFA required');
        console.log('📋 [METHODS] Enrolled methods:', response.enrolled_methods);
        
        setMfaData({
          mfaToken: response.mfa_token,
          enrolledMethods: response.enrolled_methods || [],
          selectedMethod: null,
        });
        setStep(2);
        toast.success('Please select an authentication method');
      } else {
        navigate('/dashboard');
      }
    } catch (error) {
      console.error('❌ [LOGIN ERROR]', error);
      toast.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleMFAVerification = async (verificationData) => {
    console.log('\n' + '='.repeat(60));
    console.log('🔐 [MFA VERIFY] Starting verification');
    console.log('📋 [METHOD]', mfaData.selectedMethod);
    console.log('🔑 [TOKEN]', mfaData.mfaToken);
    
    setLoading(true);

    try {
      let response;

      switch (mfaData.selectedMethod) {
        case 'face':
          console.log('📸 [FACE] Sending face data...');
          console.log('📏 [SIZE]', verificationData?.length || 0, 'characters');
          
          response = await authService.verifyFace(
            mfaData.mfaToken, 
            verificationData
          );
          break;

        case 'voice':
          console.log('🎤 [VOICE] Sending voice data...');
          console.log('📏 [SIZE]', verificationData?.length || 0, 'characters');
          
          response = await authService.verifyVoice(
            mfaData.mfaToken, 
            verificationData
          );
          break;

        case 'otp':
          console.log('📱 [OTP] Verifying code:', verificationData);
          response = await authService.verifyOTP(mfaData.mfaToken, verificationData);
          break;

        case 'gesture':
          console.log('✋ [GESTURE] Sending gesture data...');
          response = await authService.verifyGesture(mfaData.mfaToken, verificationData);
          break;

        case 'keystroke':
          console.log('⌨️ [KEYSTROKE] Sending keystroke data...');
          response = await authService.verifyKeystroke(mfaData.mfaToken, verificationData);
          break;

        case 'backup_code':
          console.log('🔑 [BACKUP] Verifying code:', verificationData);
          response = await authService.verifyBackupCode(mfaData.mfaToken, verificationData);
          break;

        default:
          throw new Error('Invalid verification method');
      }

      console.log('✅ [RESPONSE]', response);

      if (response.access_token && response.user) {
        console.log('🎉 [SUCCESS] Login successful!');
        
        // Store tokens
        localStorage.setItem('access_token', response.access_token);
        localStorage.setItem('refresh_token', response.refresh_token);
        
        // Call AuthContext login
        authLogin(response.user, response.access_token);
        
        toast.success('Login successful!');
        console.log('🚀 [REDIRECT] Navigating to dashboard...');
        console.log('='.repeat(60) + '\n');
        
        navigate('/dashboard');
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (error) {
      console.error('❌ [ERROR]', error);
      console.log('='.repeat(60) + '\n');
      toast.error(error);
    } finally {
      setLoading(false);
    }
  };

  const renderMethodButton = (method) => {
    const methodConfig = {
      face: { icon: '🖼️', label: 'Face Recognition' },
      voice: { icon: '🎤', label: 'Voice Recognition' },
      otp: { icon: '📱', label: 'OTP Authenticator' },
      gesture: { icon: '✋', label: 'Gesture Recognition' },
      keystroke: { icon: '⌨️', label: 'Keystroke Dynamics' },
      backup_code: { icon: '🔑', label: 'Backup Code' },
    };

    const config = methodConfig[method] || { icon: '🔐', label: method };

    return (
      <button
        key={method}
        className="method-button"
        onClick={() => {
          console.log('✅ [SELECT] Method selected:', method);
          setMfaData({ ...mfaData, selectedMethod: method });
          setStep(3);
        }}
      >
        <span className="method-icon">{config.icon}</span>
        <span className="method-label">{config.label}</span>
      </button>
    );
  };

  const renderVerificationComponent = () => {
    switch (mfaData.selectedMethod) {
      case 'face':
        return (
          <FaceRecognition
            onCapture={(faceImage) => {
              console.log('📸 [CAPTURE] Face captured');
              console.log('📏 [SIZE]', faceImage?.length || 0, 'characters');
              handleMFAVerification(faceImage);
            }}
            buttonText={loading ? 'Verifying...' : 'Verify Face'}
          />
        );

      case 'voice':
        return (
          <VoiceRecognition
            onCapture={(voiceAudio) => {
              console.log('🎤 [CAPTURE] Voice captured');
              console.log('📏 [SIZE]', voiceAudio?.length || 0, 'characters');
              handleMFAVerification(voiceAudio);
            }}
            buttonText={loading ? 'Verifying...' : 'Verify Voice'}
          />
        );

      case 'otp':
        return (
          <div className="otp-verification">
            <p>Enter the 6-digit code from your authenticator app</p>
            <input
              type="text"
              value={otpCode}
              onChange={(e) => setOtpCode(e.target.value)}
              placeholder="000000"
              maxLength={6}
              className="otp-input"
            />
            <button
              onClick={() => handleMFAVerification(otpCode)}
              disabled={loading || otpCode.length !== 6}
              className="btn btn-primary"
            >
              {loading ? 'Verifying...' : 'Verify OTP'}
            </button>
          </div>
        );

      case 'gesture':
        return (
          <GestureRecognition
            onCapture={(gestureData) => handleMFAVerification(gestureData)}
            buttonText={loading ? 'Verifying...' : 'Verify Gesture'}
          />
        );

      case 'keystroke':
        return (
          <KeystrokeDynamicsAdvanced
            mode="verify"
            onCapture={(data) => handleMFAVerification(data)}
            buttonText={loading ? 'Verifying...' : 'Verify Keystroke'}
          />
        );

      case 'backup_code':
        return (
          <div className="backup-code-verification">
            <p>Enter one of your backup codes</p>
            <input
              type="text"
              value={backupCode}
              onChange={(e) => setBackupCode(e.target.value.toUpperCase())}
              placeholder="XXXXXXXX"
              maxLength={8}
              className="backup-code-input"
            />
            <button
              onClick={() => handleMFAVerification(backupCode)}
              disabled={loading || backupCode.length < 8}
              className="btn btn-primary"
            >
              {loading ? 'Verifying...' : 'Verify Backup Code'}
            </button>
          </div>
        );

      default:
        return <p>Please select a verification method</p>;
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <h1>Sign In</h1>
        <p className="subtitle">Welcome back! Please sign in to continue</p>

        <div className="progress-steps">
          <div className={`step ${step >= 1 ? 'active' : ''}`}>
            <div className="step-circle">{step > 1 ? '✓' : '1'}</div>
            <span>Login</span>
          </div>
          <div className={`step ${step >= 2 ? 'active' : ''}`}>
            <div className="step-circle">{step > 2 ? '✓' : '2'}</div>
            <span>Select Method</span>
          </div>
          <div className={`step ${step >= 3 ? 'active' : ''}`}>
            <div className="step-circle">3</div>
            <span>Verify</span>
          </div>
        </div>

        {step === 1 && (
          <form onSubmit={handleLogin} className="login-form">
            <div className="form-group">
              <input
                type="text"
                value={credentials.username}
                onChange={(e) =>
                  setCredentials({ ...credentials, username: e.target.value })
                }
                placeholder="Username"
                required
              />
            </div>
            <div className="form-group">
              <input
                type="password"
                value={credentials.password}
                onChange={(e) =>
                  setCredentials({ ...credentials, password: e.target.value })
                }
                placeholder="Password"
                required
              />
            </div>
            <button type="submit" disabled={loading} className="btn btn-primary">
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
            <div className="auth-links">
              <button
                type="button"
                onClick={() => navigate('/register')}
                className="link-button"
              >
                Don't have an account? Register
              </button>
            </div>
          </form>
        )}

        {step === 2 && (
          <div className="method-selection">
            <h3>Choose Authentication Method</h3>
            <div className="methods-grid">
              {mfaData.enrolledMethods.map((method) =>
                renderMethodButton(method)
              )}
            </div>
            <button
              onClick={() => setStep(1)}
              className="btn btn-secondary mt-20"
            >
              ← Back to Login
            </button>
          </div>
        )}

        {step === 3 && (
          <div className="verification">
            <h3>Verify with {mfaData.selectedMethod?.replace('_', ' ')}</h3>
            {renderVerificationComponent()}
            <button
              onClick={() => setStep(2)}
              className="btn btn-secondary mt-20"
            >
              ← Choose Different Method
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default LoginPage;
