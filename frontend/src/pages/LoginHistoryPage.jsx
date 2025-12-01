import { useEffect, useState } from 'react';
import {
  FaArrowLeft,
  FaCheckCircle,
  FaClock,
  FaDesktop,
  FaFilter,
  FaHistory,
  FaMapMarkerAlt,
  FaSearch,
  FaShieldAlt,
  FaTimesCircle
} from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import api from '../services/api';
import './LoginHistoryPage.css';

const LoginHistoryPage = () => {
  const navigate = useNavigate();
  const [loginHistory, setLoginHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all, success, failed
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      navigate('/login');
      return;
    }
    fetchLoginHistory();
  }, [navigate]);

  const fetchLoginHistory = async () => {
    try {
      const response = await api.get('/user/login-history?limit=50');
      setLoginHistory(response.data.history || []);
      setLoading(false);
    } catch (error) {
      toast.error('Failed to fetch login history');
      setLoading(false);
    }
  };

  const getMethodIcon = (method) => {
    const icons = {
      'password': '🔑',
      'face': '👤',
      'voice': '🎤',
      'gesture': '✍️',
      'keystroke': '⌨️',
      'totp': '🔢',
      'backup': '🔐'
    };
    return icons[method] || '🔒';
  };

  const getMethodName = (method) => {
    const names = {
      'password': 'Password',
      'face': 'Face Recognition',
      'voice': 'Voice Recognition',
      'gesture': 'Gesture Pattern',
      'keystroke': 'Keystroke Dynamics',
      'totp': 'TOTP',
      'backup': 'Backup Code'
    };
    return names[method] || method;
  };

  const formatDate = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    
    return date.toLocaleString();
  };

  const filteredHistory = loginHistory.filter(log => {
    const matchesFilter = filter === 'all' || 
                         (filter === 'success' && log.success) || 
                         (filter === 'failed' && !log.success);
    
    const matchesSearch = searchTerm === '' || 
                         log.ip_address?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         log.user_agent?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         getMethodName(log.method_type)?.toLowerCase().includes(searchTerm.toLowerCase());
    
    return matchesFilter && matchesSearch;
  });

  const stats = {
    total: loginHistory.length,
    successful: loginHistory.filter(l => l.success).length,
    failed: loginHistory.filter(l => !l.success).length,
    avgConfidence: loginHistory.length > 0 
      ? (loginHistory.reduce((sum, l) => sum + (l.confidence || 0), 0) / loginHistory.length).toFixed(1)
      : 0
  };

  if (loading) {
    return (
      <div className="login-history-loading">
        <div className="spinner"></div>
        <p>Loading login history...</p>
      </div>
    );
  }

  return (
    <div className="login-history-container">
      <div className="login-history-header">
        <div className="header-top">
          <button onClick={() => navigate('/settings')} className="btn-back">
            <FaArrowLeft /> Back to Settings
          </button>
        </div>
        <div className="header-content">
          <div className="header-icon">
            <FaHistory />
          </div>
          <h1>Login History</h1>
          <p>Review all recent login attempts and security events</p>
        </div>
      </div>

      <div className="login-history-main">
        <div className="stats-grid">
          <div className="stat-card total">
            <div className="stat-icon">
              <FaHistory />
            </div>
            <div className="stat-info">
              <div className="stat-value">{stats.total}</div>
              <div className="stat-label">Total Attempts</div>
            </div>
          </div>

          <div className="stat-card success">
            <div className="stat-icon">
              <FaCheckCircle />
            </div>
            <div className="stat-info">
              <div className="stat-value">{stats.successful}</div>
              <div className="stat-label">Successful</div>
            </div>
          </div>

          <div className="stat-card failed">
            <div className="stat-icon">
              <FaTimesCircle />
            </div>
            <div className="stat-info">
              <div className="stat-value">{stats.failed}</div>
              <div className="stat-label">Failed</div>
            </div>
          </div>

          <div className="stat-card confidence">
            <div className="stat-icon">
              <FaShieldAlt />
            </div>
            <div className="stat-info">
              <div className="stat-value">{stats.avgConfidence}%</div>
              <div className="stat-label">Avg Confidence</div>
            </div>
          </div>
        </div>

        <div className="history-controls">
          <div className="search-box">
            <FaSearch className="search-icon" />
            <input
              type="text"
              placeholder="Search by IP, device, or method..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
          </div>

          <div className="filter-buttons">
            <button 
              className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
              onClick={() => setFilter('all')}
            >
              <FaFilter /> All
            </button>
            <button 
              className={`filter-btn ${filter === 'success' ? 'active' : ''}`}
              onClick={() => setFilter('success')}
            >
              <FaCheckCircle /> Success
            </button>
            <button 
              className={`filter-btn ${filter === 'failed' ? 'active' : ''}`}
              onClick={() => setFilter('failed')}
            >
              <FaTimesCircle /> Failed
            </button>
          </div>
        </div>

        <div className="history-content">
          {filteredHistory.length === 0 ? (
            <div className="no-history">
              <FaHistory className="no-history-icon" />
              <h3>No login attempts found</h3>
              <p>No matching records for the selected filters</p>
            </div>
          ) : (
            <div className="history-list">
              {filteredHistory.map((log, index) => (
                <div key={index} className={`history-item ${log.success ? 'success' : 'failed'}`}>
                  <div className="history-status">
                    {log.success ? (
                      <div className="status-icon success-icon">
                        <FaCheckCircle />
                      </div>
                    ) : (
                      <div className="status-icon failed-icon">
                        <FaTimesCircle />
                      </div>
                    )}
                  </div>

                  <div className="history-details">
                    <div className="history-row-1">
                      <div className="history-method">
                        <span className="method-icon">{getMethodIcon(log.method_type)}</span>
                        <span className="method-name">{getMethodName(log.method_type)}</span>
                        {log.confidence && (
                          <span className="confidence-badge">
                            {log.confidence.toFixed(0)}% confidence
                          </span>
                        )}
                      </div>
                      <div className="history-time">
                        <FaClock className="time-icon" />
                        {formatDate(log.login_time)}
                      </div>
                    </div>

                    <div className="history-row-2">
                      <div className="history-info">
                        <FaMapMarkerAlt className="info-icon" />
                        <span>{log.ip_address || 'Unknown IP'}</span>
                      </div>
                      <div className="history-info device-info">
                        <FaDesktop className="info-icon" />
                        <span>{log.user_agent ? log.user_agent.substring(0, 60) + '...' : 'Unknown Device'}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LoginHistoryPage;
