import { useEffect, useState } from 'react';
import {
  FaCheckCircle,
  FaClock,
  FaDrawPolygon,
  FaFingerprint,
  FaKeyboard,
  FaMicrophone,
  FaQrcode,
  FaShieldAlt,
  FaSignOutAlt,
  FaTimesCircle,
} from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import './DashboardPage.css';

const DashboardPage = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [profileRes, historyRes] = await Promise.all([
          api.get('/user/profile'),
          api.get('/user/login-history?limit=10'),
        ]);
        setUser(profileRes.data.user);
        setHistory(historyRes.data.history || []);
      } catch (err) {
        navigate('/login');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [navigate]);

  const handleLogout = async () => {
    try {
      await api.post('/auth/logout');
    } catch (_) {}
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    navigate('/login');
  };

  if (loading || !user) {
    return (
      <div className="dashboard-shell">
        <div className="dashboard-loading">Loading dashboard...</div>
      </div>
    );
  }

  const methods = [
    {
      key: 'face',
      label: 'Face Recognition',
      enrolled: user.face_enrolled,
      icon: <FaFingerprint />,
    },
    {
      key: 'voice',
      label: 'Voice Recognition',
      enrolled: user.voice_enrolled,
      icon: <FaMicrophone />,
    },
    {
      key: 'gesture',
      label: 'Gesture Pattern',
      enrolled: user.gesture_enrolled,
      icon: <FaDrawPolygon />,
    },
    {
      key: 'keystroke',
      label: 'Keystroke Dynamics',
      enrolled: user.keystroke_enrolled,
      icon: <FaKeyboard />,
    },
    {
      key: 'totp',
      label: 'TOTP Authenticator',
      enrolled: user.otp_enrolled,
      icon: <FaQrcode />,
    },
  ];

  const enrolledCount = methods.filter(m => m.enrolled).length;
  const securityScore = Math.round((enrolledCount / methods.length) * 100);

  return (
    <div className="dashboard-shell">
      {/* Top bar */}
      <header className="dashboard-header">
        <div>
          <div className="dashboard-welcome">
            Welcome back, <span>{user.username}</span>
          </div>
          <div className="dashboard-subtitle">
            Security Clearance: Level {Math.min(5, enrolledCount)}
          </div>
        </div>
        <div className="dashboard-header-right">
          <div className="dashboard-time">
            <FaClock />
            <span>{new Date().toLocaleTimeString()}</span>
          </div>
          <button
            className="dashboard-settings-btn"
            onClick={() => navigate('/settings')}
          >
            <FaShieldAlt />
            Security Settings
          </button>
          <button className="dashboard-logout-btn" onClick={handleLogout}>
            <FaSignOutAlt />
            Sign Out
          </button>
        </div>
      </header>

      {/* Main grid */}
      <main className="dashboard-grid">
        {/* Left column: overview + logs */}
        <section className="dashboard-column">
          <div className="dashboard-status-cards">
            <div className="status-card">
              <div className="status-title">Password</div>
              <div className="status-tag success">
                <FaCheckCircle /> Verified
              </div>
              <div className="status-meta">
                Last login:{' '}
                {user.last_login
                  ? new Date(user.last_login).toLocaleString()
                  : 'Never'}
              </div>
            </div>
            <div className="status-card">
              <div className="status-title">Biometrics</div>
              <div className={`status-tag ${enrolledCount ? 'success' : 'muted'}`}>
                {enrolledCount ? <FaCheckCircle /> : <FaTimesCircle />}
                {enrolledCount ? 'Configured' : 'Not configured'}
              </div>
              <div className="status-meta">
                {enrolledCount} of {methods.length} methods enrolled
              </div>
            </div>
            <div className="status-card">
              <div className="status-title">Session</div>
              <div className="status-tag success">
                <FaShieldAlt /> Active
              </div>
              <div className="status-meta">
                IP: 127.0.0.1 (local dev)
              </div>
            </div>
          </div>

          <div className="dashboard-card full">
            <div className="card-header">
              <h2>Recent Access Logs</h2>
              <button
                className="text-link"
                onClick={() => navigate('/settings', { state: { tab: 'history' } })}
              >
                View all
              </button>
            </div>
            <div className="logs-list">
              {history.length === 0 && (
                <div className="logs-empty">No login activity yet.</div>
              )}
              {history.map(item => (
                <div key={item.id} className="log-row">
                  <div className="log-status">
                    {item.success ? (
                      <span className="dot success" />
                    ) : (
                      <span className="dot danger" />
                    )}
                    <span className="log-method">{item.method_type}</span>
                  </div>
                  <div className="log-meta">
                    <span>
                      {item.login_time
                        ? new Date(item.login_time).toLocaleString()
                        : ''}
                    </span>
                    <span>{item.ip_address}</span>
                    <span className="log-agent">
                      {item.user_agent?.slice(0, 40) || ''}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Right column: methods + score */}
        <aside className="dashboard-column narrow">
          <div className="dashboard-card">
            <div className="card-header">
              <h2>Enrolled Methods</h2>
            </div>
            <div className="methods-list">
              {methods.map(m => (
                <button
                  key={m.key}
                  className={`method-row ${m.enrolled ? 'enrolled' : 'not-enrolled'}`}
                  onClick={() =>
                    navigate('/settings', { state: { tab: 'methods', focus: m.key } })
                  }
                >
                  <div className="method-icon-wrapper">{m.icon}</div>
                  <div className="method-content">
                    <div className="method-title">{m.label}</div>
                    <div className={`method-status ${m.enrolled ? 'ok' : 'warn'}`}>
                      {m.enrolled ? 'Enrolled' : 'Not enrolled'}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div className="dashboard-card score-card">
            <h2>Security Score</h2>
            <div className="score-circle">
              <div className="score-number">{securityScore}</div>
              <div className="score-label">Security</div>
            </div>
            <p className="score-caption">
              {securityScore === 100
                ? 'Perfect: all methods enrolled.'
                : 'Add more methods in Settings to increase your score.'}
            </p>
            <button
              className="primary-btn full"
              onClick={() => navigate('/settings')}
            >
              Manage Security
            </button>
          </div>
        </aside>
      </main>
    </div>
  );
};

export default DashboardPage;
