import { useEffect, useState } from 'react';
import {
  FaArrowLeft,
  FaDrawPolygon,
  FaFingerprint,
  FaKey,
  FaKeyboard,
  FaMicrophone,
  FaQrcode,
  FaShieldAlt
} from 'react-icons/fa';
import { useLocation, useNavigate } from 'react-router-dom';
import './MFASelectPage.css';

const MFASelectPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [mfaToken, setMfaToken] = useState('');
  const [enrolledMethods, setEnrolledMethods] = useState([]);

  useEffect(() => {
    // Get MFA data from navigation state
    const token = location.state?.mfa_token;
    const methods = location.state?.enrolled_methods || [];

    if (!token || methods.length === 0) {
      navigate('/login');
      return;
    }

    setMfaToken(token);
    setEnrolledMethods(methods);
  }, [location, navigate]);

  const methodsConfig = {
    face: {
      name: 'Face Recognition',
      description: 'Verify using facial biometrics',
      icon: <FaFingerprint />,
      color: '#3b82f6',
      route: '/mfa/verify/face'
    },
    voice: {
      name: 'Voice Recognition',
      description: 'Authenticate with your voice',
      icon: <FaMicrophone />,
      color: '#8b5cf6',
      route: '/mfa/verify/voice'
    },
    gesture: {
      name: 'Gesture Pattern',
      description: 'Draw your secret pattern',
      icon: <FaDrawPolygon />,
      color: '#ec4899',
      route: '/mfa/verify/gesture'
    },
    keystroke: {
      name: 'Keystroke Dynamics',
      description: 'Type your passphrase',
      icon: <FaKeyboard />,
      color: '#10b981',
      route: '/mfa/verify/keystroke'
    },
    totp: {
      name: 'Authenticator App',
      description: 'Enter TOTP code',
      icon: <FaQrcode />,
      color: '#f59e0b',
      route: '/mfa/verify/totp'
    }
  };

 const handleMethodSelect = (method) => {
  navigate('/mfa/verify', { 
    state: { 
      mfa_token: mfaToken,
      method: method  // ✅ Pass the selected method
    } 
  });
};

const handleBackupCode = () => {
  navigate('/mfa/verify', { 
    state: { 
      mfa_token: mfaToken,
      method: 'backup'  // ✅ Pass backup as method
    } 
  });
};


  return (
    <div className="mfa-select-container">
      <div className="mfa-select-background">
        <div className="gradient-orb orb-1"></div>
        <div className="gradient-orb orb-2"></div>
        <div className="gradient-orb orb-3"></div>
      </div>

      <div className="mfa-select-content">
        <button onClick={() => navigate('/login')} className="btn-back-mfa">
          <FaArrowLeft /> Back to Login
        </button>

        <div className="mfa-select-header">
          <div className="shield-icon">
            <FaShieldAlt />
          </div>
          <h1>Multi-Factor Authentication</h1>
          <p>Choose a method to verify your identity</p>
        </div>

        <div className="methods-grid">
          {enrolledMethods.map((methodKey) => {
            const method = methodsConfig[methodKey];
            if (!method) return null;

            return (
              <button
                key={methodKey}
                onClick={() => handleMethodSelect(methodKey)}
                className="method-card-button"
              >
                <div 
                  className="method-icon-circle"
                  style={{ backgroundColor: `${method.color}15` }}
                >
                  <div 
                    className="method-icon"
                    style={{ color: method.color }}
                  >
                    {method.icon}
                  </div>
                </div>
                <h3>{method.name}</h3>
                <p>{method.description}</p>
                <div 
                  className="method-arrow"
                  style={{ color: method.color }}
                >
                  →
                </div>
              </button>
            );
          })}
        </div>

        <div className="backup-option">
          <div className="divider">
            <span>OR</span>
          </div>
          <button onClick={handleBackupCode} className="backup-button">
            <FaKey className="backup-icon" />
            <div className="backup-text">
              <strong>Use Backup Code</strong>
              <span>Enter a one-time recovery code</span>
            </div>
          </button>
        </div>

        <div className="security-notice">
          <FaShieldAlt className="notice-icon" />
          <p>
            Your connection is encrypted and secure. Choose the authentication method 
            you have access to right now.
          </p>
        </div>
      </div>
    </div>
  );
};

export default MFASelectPage;
