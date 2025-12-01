import {
  FaArrowRight,
  FaCheckCircle,
  FaDrawPolygon,
  FaFingerprint,
  FaKeyboard,
  FaLock,
  FaMicrophone,
  FaQrcode,
  FaShieldAlt
} from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';
import './HomePage.css';

const HomePage = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: <FaFingerprint />,
      title: 'Face Recognition',
      description: 'Advanced facial biometric authentication',
      color: '#3b82f6'
    },
    {
      icon: <FaMicrophone />,
      title: 'Voice Recognition',
      description: 'Unique voice pattern verification',
      color: '#8b5cf6'
    },
    {
      icon: <FaDrawPolygon />,
      title: 'Gesture Pattern',
      description: 'Custom gesture-based security',
      color: '#ec4899'
    },
    {
      icon: <FaKeyboard />,
      title: 'Keystroke Dynamics',
      description: 'Typing pattern authentication',
      color: '#10b981'
    },
    {
      icon: <FaQrcode />,
      title: 'TOTP Authenticator',
      description: 'Time-based one-time passwords',
      color: '#f59e0b'
    }
  ];

  const benefits = [
    'Military-grade encryption',
    'Zero-knowledge architecture',
    'Multi-layer security',
    'Real-time threat detection',
    'Biometric verification',
    'Secure session management'
  ];

  return (
    <div className="home-container">
      {/* Hero Section */}
      <div className="hero-section">
        <div className="hero-background">
          <div className="gradient-orb orb-1"></div>
          <div className="gradient-orb orb-2"></div>
          <div className="gradient-orb orb-3"></div>
        </div>

        <div className="hero-content">
          <div className="hero-badge">
            <FaShieldAlt /> Secure Authentication Platform
          </div>
          
          <h1 className="hero-title">
            Next-Generation<br />
            <span className="gradient-text">Multi-Factor Authentication</span>
          </h1>
          
          <p className="hero-description">
            Protect your digital identity with advanced biometric and behavioral authentication. 
            Experience security that's both robust and seamless.
          </p>

          <div className="hero-actions">
            <button onClick={() => navigate('/register')} className="btn btn-primary btn-large">
              Get Started Free
              <FaArrowRight />
            </button>
            <button onClick={() => navigate('/login')} className="btn btn-secondary btn-large">
              Sign In
            </button>
          </div>

          <div className="hero-stats">
            <div className="stat-item">
              <div className="stat-number">99.9%</div>
              <div className="stat-label">Accuracy Rate</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">5</div>
              <div className="stat-label">Auth Methods</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">&lt;2s</div>
              <div className="stat-label">Verification Time</div>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="features-section">
        <div className="section-header">
          <h2 className="section-title">Authentication Methods</h2>
          <p className="section-description">
            Choose from multiple authentication factors to create your perfect security setup
          </p>
        </div>

        <div className="features-grid">
          {features.map((feature, index) => (
            <div key={index} className="feature-card" style={{ animationDelay: `${index * 0.1}s` }}>
              <div className="feature-icon-wrapper" style={{ backgroundColor: `${feature.color}15` }}>
                <div className="feature-icon" style={{ color: feature.color }}>
                  {feature.icon}
                </div>
              </div>
              <h3 className="feature-title">{feature.title}</h3>
              <p className="feature-description">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Benefits Section */}
      <div className="benefits-section">
        <div className="benefits-content">
          <div className="benefits-left">
            <h2 className="section-title">Why Choose Our Platform?</h2>
            <p className="section-description">
              Enterprise-grade security designed for everyone. Protect what matters most with cutting-edge authentication technology.
            </p>
            
            <div className="benefits-list">
              {benefits.map((benefit, index) => (
                <div key={index} className="benefit-item">
                  <FaCheckCircle className="benefit-icon" />
                  <span>{benefit}</span>
                </div>
              ))}
            </div>

            <button onClick={() => navigate('/register')} className="btn btn-primary btn-large">
              Create Your Account
              <FaArrowRight />
            </button>
          </div>

          <div className="benefits-right">
            <div className="security-visual">
              <div className="security-layer layer-1">
                <FaShieldAlt />
              </div>
              <div className="security-layer layer-2">
                <FaLock />
              </div>
              <div className="security-layer layer-3">
                <FaFingerprint />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="cta-section">
        <div className="cta-content">
          <h2>Ready to Secure Your Account?</h2>
          <p>Join thousands of users protecting their digital identity with advanced MFA</p>
          <button onClick={() => navigate('/register')} className="btn btn-primary btn-large">
            Get Started Now
            <FaArrowRight />
          </button>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
