import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { useAuth } from '../context/AuthContext';
import userService from '../services/userService';
import './DashboardPage.css';

const DashboardPage = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [loginHistory, setLoginHistory] = useState([]);
  const [backupCodesStatus, setBackupCodesStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [historyResponse, codesResponse] = await Promise.all([
        userService.getLoginHistory(10),
        userService.getBackupCodes(),
      ]);

      setLoginHistory(historyResponse.history || []);
      setBackupCodesStatus(codesResponse);
    } catch (error) {
      console.error('Dashboard error:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      toast.success('Logged out successfully');
      navigate('/login');
    } catch (error) {
      toast.error('Logout failed');
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  if (loading) {
    return (
      <div className="dashboard-page">
        <div className="loading">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <div className="dashboard-container">
        <div className="dashboard-header">
          <div>
            <h1>Welcome back, {user?.full_name || user?.username}! 👋</h1>
            <p>Manage your account security and settings</p>
          </div>
          <button onClick={handleLogout} className="btn btn-secondary">
            Logout
          </button>
        </div>

        <div className="dashboard-grid">
          <div className="card">
            <h3>Account Information</h3>
            <div className="info-row">
              <span className="info-label">Username:</span>
              <span className="info-value">{user?.username}</span>
            </div>
            <div className="info-row">
              <span className="info-label">Email:</span>
              <span className="info-value">{user?.email}</span>
            </div>
            <div className="info-row">
              <span className="info-label">Member since:</span>
              <span className="info-value">{formatDate(user?.created_at)}</span>
            </div>
            <div className="info-row">
              <span className="info-label">Last login:</span>
              <span className="info-value">{formatDate(user?.last_login)}</span>
            </div>
            <button
              onClick={() => navigate('/settings')}
              className="btn btn-primary mt-20"
            >
              Edit Profile
            </button>
          </div>

          <div className="card">
            <h3>MFA Methods</h3>
            <div className="mfa-status-list">
              <div className="mfa-status-item">
                <div className="mfa-status-info">
                  <span className="mfa-icon">🖼️</span>
                  <span className="mfa-name">Face Recognition</span>
                </div>
                {user?.face_enrolled ? (
                  <span className="badge badge-success">Enabled</span>
                ) : (
                  <span className="badge badge-danger">Disabled</span>
                )}
              </div>
              <div className="mfa-status-item">
                <div className="mfa-status-info">
                  <span className="mfa-icon">🎤</span>
                  <span className="mfa-name">Voice Recognition</span>
                </div>
                {user?.voice_enrolled ? (
                  <span className="badge badge-success">Enabled</span>
                ) : (
                  <span className="badge badge-danger">Disabled</span>
                )}
              </div>
              <div className="mfa-status-item">
                <div className="mfa-status-info">
                  <span className="mfa-icon">📱</span>
                  <span className="mfa-name">OTP Authenticator</span>
                </div>
                {user?.otp_enrolled ? (
                  <span className="badge badge-success">Enabled</span>
                ) : (
                  <span className="badge badge-danger">Disabled</span>
                )}
              </div>
              <div className="mfa-status-item">
                <div className="mfa-status-info">
                  <span className="mfa-icon">✋</span>
                  <span className="mfa-name">Gesture Recognition</span>
                </div>
                {user?.gesture_enrolled ? (
                  <span className="badge badge-success">Enabled</span>
                ) : (
                  <span className="badge badge-danger">Disabled</span>
                )}
              </div>
              <div className="mfa-status-item">
                <div className="mfa-status-info">
                  <span className="mfa-icon">⌨️</span>
                  <span className="mfa-name">Keystroke Dynamics</span>
                </div>
                {user?.keystroke_enrolled ? (
                  <span className="badge badge-success">Enabled</span>
                ) : (
                  <span className="badge badge-danger">Disabled</span>
                )}
              </div>
            </div>
            <button
              onClick={() => navigate('/settings')}
              className="btn btn-primary mt-20"
            >
              Manage MFA Methods
            </button>
          </div>

          {backupCodesStatus && (
            <div className="card">
              <h3>Backup Codes</h3>
              <div className="backup-codes-stats">
                <div className="stat">
                  <span className="stat-value">{backupCodesStatus.total}</span>
                  <span className="stat-label">Total Codes</span>
                </div>
                <div className="stat">
                  <span className="stat-value">{backupCodesStatus.remaining}</span>
                  <span className="stat-label">Remaining</span>
                </div>
                <div className="stat">
                  <span className="stat-value">{backupCodesStatus.used}</span>
                  <span className="stat-label">Used</span>
                </div>
              </div>
              {backupCodesStatus.remaining < 3 && (
                <p className="warning-text">
                  ⚠️ You're running low on backup codes!
                </p>
              )}
              <button
                onClick={() => navigate('/settings')}
                className="btn btn-primary mt-20"
              >
                Regenerate Codes
              </button>
            </div>
          )}

          <div className="card full-width">
            <h3>Recent Login Activity</h3>
            {loginHistory.length === 0 ? (
              <p className="no-data">No login history available</p>
            ) : (
              <div className="login-history-list">
                {loginHistory.map((log) => (
                  <div key={log.id} className="login-history-item">
                    <div className="login-info">
                      <div className="login-method">
                        {log.mfa_method === 'face' && '🖼️ Face Recognition'}
                        {log.mfa_method === 'voice' && '🎤 Voice Recognition'}
                        {log.mfa_method === 'otp' && '📱 OTP'}
                        {log.mfa_method === 'gesture' && '✋ Gesture'}
                        {log.mfa_method === 'keystroke' && '⌨️ Keystroke'}
                        {log.mfa_method === 'backup_code' && '🔑 Backup Code'}
                        {!log.mfa_method && '❌ Failed Attempt'}
                      </div>
                      <div className="login-details">
                        <span>{log.ip_address || 'Unknown'}</span>
                        <span className="separator">•</span>
                        <span>{formatDate(log.login_time)}</span>
                      </div>
                    </div>
                    {log.success ? (
                      <span className="badge badge-success">Success</span>
                    ) : (
                      <span className="badge badge-danger">Failed</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
