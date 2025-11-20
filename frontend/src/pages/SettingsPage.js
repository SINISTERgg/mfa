import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import BackupCodes from '../components/BackupCodes';
import DeviceManagement from '../components/DeviceManagement';
import FaceRecognition from '../components/FaceRecognition';
import GestureRecognition from '../components/GestureRecognition';
import KeystrokeDynamicsAdvanced from '../components/KeystrokeDynamicsAdvanced';
import OTPInput from '../components/OTPInput';
import QRCodeDisplay from '../components/QRCodeDisplay';
import VoiceRecognition from '../components/VoiceRecognition';
import { useAuth } from '../context/AuthContext';
import userService from '../services/userService';
import './SettingsPage.css';

const SettingsPage = () => {
  const navigate = useNavigate();
  const { user, updateUser } = useAuth();
  const [activeTab, setActiveTab] = useState('profile');
  const [loading, setLoading] = useState(false);

  // Profile state
  const [profileData, setProfileData] = useState({
    fullName: user?.full_name || '',
    email: user?.email || '',
  });

  // OTP enrollment state
  const [otpSecret, setOtpSecret] = useState('');
  const [otpQRCode, setOtpQRCode] = useState('');
  const [showOTPVerification, setShowOTPVerification] = useState(false);

  // Backup codes state
  const [newBackupCodes, setNewBackupCodes] = useState(null);

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await userService.updateProfile(
        profileData.fullName,
        profileData.email
      );
      updateUser(response.user);
      toast.success('Profile updated successfully');
    } catch (error) {
      toast.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleFaceEnroll = async (faceImage) => {
    setLoading(true);
    try {
      const response = await userService.enrollFace(faceImage);
      updateUser(response.user);
      toast.success('Face enrolled successfully');
    } catch (error) {
      toast.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleVoiceEnroll = async (voiceAudio) => {
    setLoading(true);
    try {
      const response = await userService.enrollVoice(voiceAudio);
      updateUser(response.user);
      toast.success('Voice enrolled successfully');
    } catch (error) {
      toast.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleOTPEnroll = async () => {
    setLoading(true);
    try {
      const response = await userService.enrollOTP();
      setOtpSecret(response.secret);
      setOtpQRCode(response.qr_code);
      setShowOTPVerification(true);
      toast.info('Scan the QR code and verify with your authenticator app');
    } catch (error) {
      toast.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleOTPVerify = async (otpCode) => {
    setLoading(true);
    try {
      const response = await userService.verifyOTPEnrollment(otpCode);
      updateUser(response.user);
      toast.success('OTP enrolled successfully');
      setShowOTPVerification(false);
      setOtpSecret('');
      setOtpQRCode('');
    } catch (error) {
      toast.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleGestureEnroll = async (gestureData) => {
    setLoading(true);
    try {
      const response = await userService.enrollGesture(gestureData);
      updateUser(response.user);
      toast.success('Gesture pattern enrolled successfully! ✋');
    } catch (error) {
      toast.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleKeystrokeEnroll = async (data) => {
  setLoading(true);
  try {
    console.log('Sending keystroke data:', data); // Debug log
    
    const response = await userService.enrollKeystroke(
      data.samples,  // ✅ Send samples array
      data.passphrase
    );
    
    updateUser(response.user);
    
    // Show strength analysis
    if (response.analysis) {
      toast.success(
        `Pattern enrolled! Strength: ${response.analysis.strength} (${(response.analysis.score * 100).toFixed(0)}%)`,
        { autoClose: 5000 }
      );
    } else {
      toast.success('Keystroke pattern enrolled successfully! ⌨️');
    }
  } catch (error) {
    console.error('Enrollment error:', error);
    toast.error(error);
  } finally {
    setLoading(false);
  }
};


  const handleUnenroll = async (method) => {
    if (
      window.confirm(
        `Are you sure you want to disable ${method} authentication?`
      )
    ) {
      setLoading(true);
      try {
        const response = await userService.unenrollMethod(method);
        updateUser(response.user);
        toast.success(`${method} authentication disabled`);
      } catch (error) {
        toast.error(error);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleRegenerateBackupCodes = async () => {
    if (
      window.confirm(
        'Are you sure? This will invalidate all existing backup codes.'
      )
    ) {
      setLoading(true);
      try {
        const response = await userService.regenerateBackupCodes();
        setNewBackupCodes(response.backup_codes);
        toast.success('Backup codes regenerated successfully');
      } catch (error) {
        toast.error(error);
      } finally {
        setLoading(false);
      }
    }
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'profile':
        return (
          <div className="tab-content">
            <h3>Profile Information</h3>
            <form onSubmit={handleProfileUpdate}>
              <div className="form-group">
                <label>Full Name</label>
                <input
                  type="text"
                  value={profileData.fullName}
                  onChange={(e) =>
                    setProfileData({ ...profileData, fullName: e.target.value })
                  }
                  placeholder="Enter your full name"
                />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={profileData.email}
                  onChange={(e) =>
                    setProfileData({ ...profileData, email: e.target.value })
                  }
                  placeholder="Enter your email"
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="btn btn-primary"
              >
                {loading ? 'Updating...' : 'Update Profile'}
              </button>
            </form>
          </div>
        );

      case 'face':
        return (
          <div className="tab-content">
            <h3>Face Recognition</h3>
            {user?.face_enrolled ? (
              <div>
                <div className="enrolled-message">
                  <span className="badge badge-success">Enrolled ✓</span>
                  <p>Face recognition is currently enabled for your account</p>
                </div>
                <button
                  onClick={() => handleUnenroll('face')}
                  className="btn btn-danger"
                  disabled={loading}
                >
                  Disable Face Recognition
                </button>
              </div>
            ) : (
              <div>
                <p>Enroll your face for biometric authentication</p>
                <FaceRecognition
                  onCapture={handleFaceEnroll}
                  buttonText={loading ? 'Enrolling...' : 'Enroll Face'}
                />
              </div>
            )}
          </div>
        );

      case 'voice':
        return (
          <div className="tab-content">
            <h3>Voice Recognition</h3>
            {user?.voice_enrolled ? (
              <div>
                <div className="enrolled-message">
                  <span className="badge badge-success">Enrolled ✓</span>
                  <p>Voice recognition is currently enabled for your account</p>
                </div>
                <button
                  onClick={() => handleUnenroll('voice')}
                  className="btn btn-danger"
                  disabled={loading}
                >
                  Disable Voice Recognition
                </button>
              </div>
            ) : (
              <div>
                <p>Enroll your voice for biometric authentication</p>
                <VoiceRecognition
                  onCapture={handleVoiceEnroll}
                  buttonText={loading ? 'Enrolling...' : 'Enroll Voice'}
                />
              </div>
            )}
          </div>
        );

      case 'otp':
        return (
          <div className="tab-content">
            <h3>OTP Authenticator</h3>
            {user?.otp_enrolled ? (
              <div>
                <div className="enrolled-message">
                  <span className="badge badge-success">Enrolled ✓</span>
                  <p>OTP authentication is currently enabled for your account</p>
                </div>
                <button
                  onClick={() => handleUnenroll('otp')}
                  className="btn btn-danger"
                  disabled={loading}
                >
                  Disable OTP Authentication
                </button>
              </div>
            ) : showOTPVerification ? (
              <div>
                <QRCodeDisplay value={otpQRCode} secret={otpSecret} />
                <div className="mt-20">
                  <h4 className="text-center">Verify Setup</h4>
                  <p className="text-center">
                    Enter the 6-digit code from your authenticator app
                  </p>
                  <OTPInput onComplete={handleOTPVerify} />
                </div>
              </div>
            ) : (
              <div>
                <p>Set up OTP authentication with an authenticator app</p>
                <button
                  onClick={handleOTPEnroll}
                  className="btn btn-primary"
                  disabled={loading}
                >
                  {loading ? 'Generating...' : 'Setup OTP'}
                </button>
              </div>
            )}
          </div>
        );

      case 'gesture':
        return (
          <div className="tab-content">
            <h3>✋ Gesture Recognition</h3>
            {user?.gesture_enrolled ? (
              <div>
                <div className="enrolled-message">
                  <span className="badge badge-success">Enrolled ✓</span>
                  <p>Gesture pattern is currently enabled for your account</p>
                </div>
                <button
                  onClick={() => handleUnenroll('gesture')}
                  className="btn btn-danger"
                  disabled={loading}
                >
                  Disable Gesture Recognition
                </button>
              </div>
            ) : (
              <div>
                <div className="info-box">
                  <h4>📝 How it works:</h4>
                  <ol>
                    <li>Draw a unique pattern on the canvas</li>
                    <li>The system will capture your gesture dynamics</li>
                    <li>Use the same gesture pattern to login in the future</li>
                  </ol>
                </div>
                <GestureRecognition
                  onCapture={handleGestureEnroll}
                  buttonText={loading ? 'Enrolling...' : 'Enroll Gesture'}
                />
              </div>
            )}
          </div>
        );

     case 'keystroke':
  return (
    <div className="tab-content">
      <h3>⌨️ Advanced Keystroke Dynamics</h3>
      {user?.keystroke_enrolled ? (
        <div>
          <div className="enrolled-message">
            <span className="badge badge-success">Enrolled ✓</span>
            <p>Keystroke pattern is currently enabled for your account</p>
          </div>
          <button
            onClick={() => handleUnenroll('keystroke')}
            className="btn btn-danger"
            disabled={loading}
          >
            Disable Keystroke Dynamics
          </button>
        </div>
      ) : (
        <div>
          <KeystrokeDynamicsAdvanced
            mode="enroll"
            onCapture={handleKeystrokeEnroll}
            buttonText={loading ? 'Enrolling...' : 'Enroll Pattern'}
          />
        </div>
      )}
    </div>
  );

      case 'backup':
        return (
          <div className="tab-content">
            <h3>Backup Codes</h3>
            {newBackupCodes ? (
              <BackupCodes codes={newBackupCodes} />
            ) : (
              <div>
                <p>
                  Generate new backup codes to access your account if you lose
                  access to your authentication methods.
                </p>
                <button
                  onClick={handleRegenerateBackupCodes}
                  className="btn btn-primary"
                  disabled={loading}
                >
                  {loading ? 'Generating...' : 'Regenerate Backup Codes'}
                </button>
              </div>
            )}
          </div>
        );

      case 'devices':
        return (
          <div className="tab-content">
            <h3>Manage Devices</h3>
            <DeviceManagement />
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="settings-page">
      <div className="settings-container">
        <div className="settings-header">
          <button onClick={() => navigate('/dashboard')} className="back-button">
            ← Back to Dashboard
          </button>
          <h1>Settings</h1>
        </div>

        <div className="settings-layout">
          <div className="settings-sidebar">
            <button
              className={`tab-button ${activeTab === 'profile' ? 'active' : ''}`}
              onClick={() => setActiveTab('profile')}
            >
              👤 Profile
            </button>
            <button
              className={`tab-button ${activeTab === 'face' ? 'active' : ''}`}
              onClick={() => setActiveTab('face')}
            >
              🖼️ Face Recognition
            </button>
            <button
              className={`tab-button ${activeTab === 'voice' ? 'active' : ''}`}
              onClick={() => setActiveTab('voice')}
            >
              🎤 Voice Recognition
            </button>
            <button
              className={`tab-button ${activeTab === 'otp' ? 'active' : ''}`}
              onClick={() => setActiveTab('otp')}
            >
              📱 OTP Authenticator
            </button>
            <button
              className={`tab-button ${activeTab === 'gesture' ? 'active' : ''}`}
              onClick={() => setActiveTab('gesture')}
            >
              ✋ Gesture Recognition
            </button>
            <button
              className={`tab-button ${activeTab === 'keystroke' ? 'active' : ''}`}
              onClick={() => setActiveTab('keystroke')}
            >
              ⌨️ Keystroke Dynamics
            </button>
            <button
              className={`tab-button ${activeTab === 'backup' ? 'active' : ''}`}
              onClick={() => setActiveTab('backup')}
            >
              🔑 Backup Codes
            </button>
            <button
              className={`tab-button ${activeTab === 'devices' ? 'active' : ''}`}
              onClick={() => setActiveTab('devices')}
            >
              🖥️ Devices
            </button>
          </div>

          <div className="settings-content card">{renderTabContent()}</div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
