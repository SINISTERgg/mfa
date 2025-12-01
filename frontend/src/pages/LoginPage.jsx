import { useState } from 'react';
import {
  FaEnvelope,
  FaFingerprint,
  FaLock,
  FaShieldAlt,
  FaSpinner
} from 'react-icons/fa';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import api from '../services/api';
import './LoginPage.css';

const LoginPage = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleLogin = async (e) => {
  e.preventDefault();
  setLoading(true);
  setError('');

  try {
    const response = await api.post('/auth/login', {
      email: formData.email,
      password: formData.password
    });

    // ✅ Check if MFA is required
    if (response.data.requires_mfa) {
      // Navigate to MFA selection page
      navigate('/mfa-select', {
        state: {
          mfa_token: response.data.mfa_token,
          enrolled_methods: response.data.enrolled_methods
        }
      });
    } else {
      // Direct login - no MFA required
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('refresh_token', response.data.refresh_token);
      
      toast.success('Login successful!');
      setTimeout(() => {
        navigate('/dashboard');
      }, 1000);
    }
  } catch (err) {
    const errorMessage = err.response?.data?.error || 'Login failed';
    setError(errorMessage);
    toast.error(errorMessage);
  } finally {
    setLoading(false);
  }
};
  return (
    <div className="auth-container">
      <div className="auth-background">
        <div className="gradient-orb orb-1"></div>
        <div className="gradient-orb orb-2"></div>
        <div className="gradient-orb orb-3"></div>
      </div>

      <div className="auth-content">
        <div className="auth-branding">
          <div className="brand-logo">
            <FaShieldAlt className="logo-icon" />
            <h1>MFA Auth</h1>
          </div>
          <h2 className="brand-title">
            Multi-Factor<br />
            <span className="gradient-text">Authentication</span>
          </h2>
          <p className="brand-description">
            Secure your account with advanced biometric and behavioral authentication methods.
          </p>
          
          <div className="features-list">
            <div className="feature-item">
              <FaFingerprint className="feature-icon" />
              <span>Biometric Security</span>
            </div>
            <div className="feature-item">
              <FaShieldAlt className="feature-icon" />
              <span>Military-Grade Encryption</span>
            </div>
            <div className="feature-item">
              <FaLock className="feature-icon" />
              <span>Zero-Knowledge Architecture</span>
            </div>
          </div>
        </div>

        <div className="auth-form-container">
          <div className="auth-card">
            <div className="auth-header">
              <h2>Welcome Back</h2>
              <p>Sign in to your account to continue</p>
            </div>

            <form onSubmit={handleLogin} className="auth-form">
              <div className="input-group">
                <label htmlFor="email">Email Address</label>
                <div className="input-wrapper">
                  <FaEnvelope className="input-icon" />
                  <input
                    type="email"
                    id="email"
                    name="email"
                    className="input-field"
                    placeholder="you@example.com"
                    value={formData.email}
                    onChange={handleInputChange}
                    required
                  />
                </div>
              </div>

              <div className="input-group">
                <label htmlFor="password">Password</label>
                <div className="input-wrapper">
                  <FaLock className="input-icon" />
                  <input
                    type="password"
                    id="password"
                    name="password"
                    className="input-field"
                    placeholder="Enter your password"
                    value={formData.password}
                    onChange={handleInputChange}
                    required
                  />
                </div>
              </div>

              {error && (
                <div className="auth-error-message">
                  {error}
                </div>
              )}

              <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
                {loading ? (
                  <>
                    <FaSpinner className="spinner-icon" />
                    Signing in...
                  </>
                ) : (
                  'Sign In'
                )}
              </button>
            </form>

            <div className="auth-footer">
              <p>
                Don't have an account?{' '}
                <Link to="/register" className="auth-link">Create Account</Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
