import { useEffect, useState } from 'react';
import {
  FaArrowLeft,
  FaCheck,
  FaClock,
  FaDrawPolygon,
  FaEnvelope,
  FaFingerprint,
  FaHistory,
  FaKey,
  FaKeyboard,
  FaLock,
  FaMicrophone,
  FaPlus,
  FaQrcode,
  FaShieldAlt,
  FaTrash,
  FaUser
} from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import api from '../services/api';
import './SettingsPage.css';

const SettingsPage = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('profile'); // ✅ Changed default to 'profile'
  const [removing, setRemoving] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      navigate('/login');
      return;
    }
    fetchUserProfile();
  }, [navigate]);

  const fetchUserProfile = async () => {
    try {
      const response = await api.get('/user/profile');
      setUser(response.data.user);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch profile:', error);
      setLoading(false);
    }
  };

  const enrollmentMethods = [
    {
      key: 'face',
      name: 'Face Recognition',
      description: 'Secure login using facial biometrics',
      icon: <FaFingerprint />,
      enrolled: user?.face_enrolled,
      color: '#3b82f6',
      route: '/enroll/face'
    },
    {
      key: 'voice',
      name: 'Voice Recognition',
      description: 'Authenticate with your unique voice pattern',
      icon: <FaMicrophone />,
      enrolled: user?.voice_enrolled,
      color: '#8b5cf6',
      route: '/enroll/voice'
    },
    {
      key: 'gesture',
      name: 'Gesture Pattern',
      description: 'Draw a secret pattern to unlock',
      icon: <FaDrawPolygon />,
      enrolled: user?.gesture_enrolled,
      color: '#ec4899',
      route: '/enroll/gesture'
    },
    {
      key: 'keystroke',
      name: 'Keystroke Dynamics',
      description: 'Your typing rhythm is your password',
      icon: <FaKeyboard />,
      enrolled: user?.keystroke_enrolled,
      color: '#10b981',
      route: '/enroll/keystroke'
    },
    {
      key: 'totp',
      name: 'Authenticator App',
      description: 'Time-based one-time passwords (TOTP)',
      icon: <FaQrcode />,
      enrolled: user?.otp_enrolled,
      color: '#f59e0b',
      route: '/enroll/otp'
    }
  ];

  const handleEnroll = (route) => {
    navigate(route);
  };

  const handleRemove = async (methodKey) => {
    const confirmRemove = window.confirm(
      `Are you sure you want to remove ${enrollmentMethods.find(m => m.key === methodKey)?.name}? This action cannot be undone.`
    );

    if (!confirmRemove) return;

    setRemoving(methodKey);
    try {
      await api.delete(`/user/unenroll/${methodKey}`);
      toast.success('Authentication method removed successfully');
      await fetchUserProfile();
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to remove method');
    } finally {
      setRemoving(null);
    }
  };

  const handleRegenerateBackupCodes = async () => {
    try {
      const response = await api.post('/user/backup-codes/regenerate');
      navigate('/backup-codes', { 
        state: { 
          backupCodes: response.data.backup_codes,
          fromRegenerate: true 
        } 
      });
    } catch (error) {
      toast.error('Failed to regenerate backup codes');
    }
  };

  const handleChangePassword = () => {
    toast.info('Change password functionality coming soon!');
  };

  const handleSessionManagement = () => {
    toast.info('Session management functionality coming soon!');
  };

  const handleLoginHistory = () => {
  navigate('/login-history');
};

  if (loading) {
    return (
      <div className="settings-loading">
        <div className="spinner"></div>
        <p>Loading settings...</p>
      </div>
    );
  }

  const enrolledCount = enrollmentMethods.filter(m => m.enrolled).length;

  return (
    <div className="settings-container">
      <div className="settings-header">
        <div className="header-top">
          <button onClick={() => navigate('/dashboard')} className="btn-back">
            <FaArrowLeft /> Back to Dashboard
          </button>
        </div>
        <div className="header-content">
          <div className="header-icon">
            <FaShieldAlt />
          </div>
          <h1>Security Settings</h1>
          <p>Manage your authentication methods and account security</p>
        </div>
      </div>

      <div className="settings-main">
        <div className="settings-sidebar">
          <div className="sidebar-tabs">
            {/* ✅ Reordered tabs: Profile, Security, Auth Methods, Backup Codes */}
            <button 
              className={`tab-button ${activeTab === 'profile' ? 'active' : ''}`}
              onClick={() => setActiveTab('profile')}
            >
              <FaUser />
              Profile
            </button>
            <button 
              className={`tab-button ${activeTab === 'security' ? 'active' : ''}`}
              onClick={() => setActiveTab('security')}
            >
              <FaLock />
              Security
            </button>
            <button 
              className={`tab-button ${activeTab === 'methods' ? 'active' : ''}`}
              onClick={() => setActiveTab('methods')}
            >
              <FaShieldAlt />
              Auth Methods
            </button>
            <button 
              className={`tab-button ${activeTab === 'backup' ? 'active' : ''}`}
              onClick={() => setActiveTab('backup')}
            >
              <FaKey />
              Backup Codes
            </button>
          </div>
        </div>

        <div className="settings-content">
          {/* ✅ PROFILE TAB - First */}
          {activeTab === 'profile' && (
            <div className="tab-panel">
              <div className="panel-header">
                <h2>Profile Information</h2>
                <p>Manage your account details</p>
              </div>

              <div className="profile-info">
                <div className="info-item">
                  <FaUser className="info-icon" />
                  <div className="info-content">
                    <label>Username</label>
                    <div className="info-value">{user?.username}</div>
                  </div>
                </div>

                <div className="info-item">
                  <FaEnvelope className="info-icon" />
                  <div className="info-content">
                    <label>Email Address</label>
                    <div className="info-value">{user?.email}</div>
                  </div>
                </div>

                <div className="info-item">
                  <FaShieldAlt className="info-icon" />
                  <div className="info-content">
                    <label>Account Status</label>
                    <div className="info-value">
                      <span className="status-badge active">Active</span>
                    </div>
                  </div>
                </div>

                <div className="info-item">
                  <FaCheck className="info-icon enrolled-icon" />
                  <div className="info-content">
                    <label>Enrolled Methods</label>
                    <div className="info-value">{enrolledCount} of {enrollmentMethods.length} methods</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ✅ SECURITY TAB - Second */}
          {activeTab === 'security' && (
            <div className="tab-panel">
              <div className="panel-header">
                <h2>Security Settings</h2>
                <p>Advanced security options</p>
              </div>

              <div className="security-options">
                <div className="security-item">
                  <div className="security-info">
                    <FaLock className="security-item-icon" />
                    <div>
                      <h3>Change Password</h3>
                      <p>Update your account password</p>
                    </div>
                  </div>
                  <button className="btn btn-secondary" onClick={handleChangePassword}>
                    Change
                  </button>
                </div>

                <div className="security-item">
                  <div className="security-info">
                    <FaClock className="security-item-icon" />
                    <div>
                      <h3>Session Management</h3>
                      <p>View and manage active sessions</p>
                    </div>
                  </div>
                  <button className="btn btn-secondary" onClick={handleSessionManagement}>
                    Manage
                  </button>
                </div>

                <div className="security-item">
                  <div className="security-info">
                    <FaHistory className="security-item-icon" />
                    <div>
                      <h3>Login History</h3>
                      <p>Review recent login attempts</p>
                    </div>
                  </div>
                  <button className="btn btn-secondary" onClick={handleLoginHistory}>
                    View
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ✅ AUTH METHODS TAB - Third */}
          {activeTab === 'methods' && (
            <div className="tab-panel">
              <div className="panel-header">
                <h2>Authentication Methods</h2>
                <p>{enrolledCount} of {enrollmentMethods.length} methods enrolled</p>
              </div>

              <div className="methods-grid">
                {enrollmentMethods.map((method) => (
                  <div key={method.key} className={`method-card ${method.enrolled ? 'enrolled' : ''}`}>
                    <div className="method-header">
                      <div 
                        className="method-icon-wrapper"
                        style={{ backgroundColor: `${method.color}15` }}
                      >
                        <div className="method-icon" style={{ color: method.color }}>
                          {method.icon}
                        </div>
                      </div>
                      {method.enrolled && (
                        <div className="enrolled-badge">
                          <FaCheck /> Enrolled
                        </div>
                      )}
                    </div>

                    <div className="method-body">
                      <h3>{method.name}</h3>
                      <p>{method.description}</p>
                    </div>

                    <div className="method-footer">
                      {method.enrolled ? (
                        <div className="method-actions-enrolled">
                          <button 
                            className="btn btn-outline btn-full"
                            onClick={() => handleEnroll(method.route)}
                          >
                            Re-enroll
                          </button>
                          <button 
                            className="btn btn-danger-outline btn-full"
                            onClick={() => handleRemove(method.key)}
                            disabled={removing === method.key}
                          >
                            {removing === method.key ? (
                              <>
                                <div className="btn-spinner"></div>
                                Removing...
                              </>
                            ) : (
                              <>
                                <FaTrash /> Remove
                              </>
                            )}
                          </button>
                        </div>
                      ) : (
                        <button 
                          className="btn btn-primary btn-full"
                          onClick={() => handleEnroll(method.route)}
                        >
                          <FaPlus /> Enroll Now
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ✅ BACKUP CODES TAB - Fourth */}
          {activeTab === 'backup' && (
            <div className="tab-panel">
              <div className="panel-header">
                <h2>Backup Codes</h2>
                <p>Emergency access codes for account recovery</p>
              </div>

              <div className="backup-codes-section">
                <div className="info-card">
                  <FaKey className="info-card-icon" />
                  <div className="info-card-content">
                    <h3>Backup Codes</h3>
                    <p>
                      Backup codes are single-use codes that allow you to access your account 
                      if you lose access to your authentication methods.
                    </p>
                  </div>
                </div>

                <button 
                  onClick={handleRegenerateBackupCodes}
                  className="btn btn-primary btn-large"
                >
                  <FaKey /> Generate New Backup Codes
                </button>

                <div className="warning-box">
                  <strong>⚠️ Important:</strong> Generating new codes will invalidate all previous backup codes.
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
