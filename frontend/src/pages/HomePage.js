import { useNavigate } from 'react-router-dom';
import './HomePage.css';

const HomePage = () => {
  const navigate = useNavigate();

  return (
    <div className="home-page">
      <div className="home-container">
        <header className="home-header">
          <h1>Multi-Factor Authentication System</h1>
          <p>Secure your account with advanced biometric authentication</p>
        </header>

        <div className="auth-buttons">
          <button 
            className="btn btn-primary btn-large"
            onClick={() => navigate('/login')}
          >
            Sign In
          </button>
          <button 
            className="btn btn-secondary btn-large"
            onClick={() => navigate('/register')}
          >
            Register
          </button>
        </div>

        <div className="features-grid">
          <div className="feature-card">
            <span className="feature-icon">🖼️</span>
            <h3>Face Recognition</h3>
            <p>Advanced facial recognition powered by Deepface</p>
          </div>

          <div className="feature-card">
            <span className="feature-icon">🎤</span>
            <h3>Voice Recognition</h3>
            <p>Secure voice authentication with AI technology</p>
          </div>

          <div className="feature-card">
            <span className="feature-icon">📱</span>
            <h3>OTP Authentication</h3>
            <p>Time-based one-time passwords for extra security</p>
          </div>

          <div className="feature-card">
            <span className="feature-icon">🔑</span>
            <h3>Backup Codes</h3>
            <p>Recovery codes for account access</p>
          </div>

          <div className="feature-card">
            <span className="feature-icon">💻</span>
            <h3>Device Trust</h3>
            <p>Automatically trust your devices</p>
          </div>

          <div className="feature-card">
            <span className="feature-icon">🛡️</span>
            <h3>Secure by Default</h3>
            <p>Enterprise-grade security protection</p>
          </div>
        </div>

        <button 
          className="btn btn-outline"
          onClick={() => navigate('/dashboard')}
        >
          Go to Dashboard
        </button>
      </div>
    </div>
  );
};

export default HomePage;
