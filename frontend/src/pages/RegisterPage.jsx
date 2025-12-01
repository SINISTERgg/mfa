import { useState } from 'react';
import {
  FaCheckCircle,
  FaEnvelope,
  FaLock,
  FaShieldAlt,
  FaSpinner,
  FaUser
} from 'react-icons/fa';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import api from '../services/api';
import './RegisterPage.css';

const RegisterPage = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [loading, setLoading] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(0);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });

    if (name === 'password') {
      calculatePasswordStrength(value);
    }
  };

  const calculatePasswordStrength = (password) => {
    let strength = 0;
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
    if (/\d/.test(password)) strength++;
    if (/[^a-zA-Z0-9]/.test(password)) strength++;
    setPasswordStrength(strength);
  };

  const getPasswordStrengthLabel = () => {
    if (passwordStrength === 0) return { text: 'Too weak', color: '#ef4444' };
    if (passwordStrength <= 2) return { text: 'Weak', color: '#f59e0b' };
    if (passwordStrength <= 3) return { text: 'Good', color: '#10b981' };
    return { text: 'Strong', color: '#059669' };
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);

    // Validate passwords match
    if (formData.password !== formData.confirmPassword) {
      toast.error('Passwords do not match');
      setLoading(false);
      return;
    }

    // Validate password strength
    if (passwordStrength < 2) {
      toast.error('Password is too weak. Please use a stronger password.');
      setLoading(false);
      return;
    }

    try {
      const response = await api.post('/auth/register', {
        username: formData.username,
        email: formData.email,
        password: formData.password
      });

      // ✅ Show success message
      toast.success('🎉 Registration successful! Redirecting...', {
        position: 'top-right',
        autoClose: 2000
      });

      // ✅ Save tokens
      if (response.data.access_token) {
        localStorage.setItem('access_token', response.data.access_token);
        localStorage.setItem('refresh_token', response.data.refresh_token);
        
        // ✅ Save backup codes if provided
        if (response.data.backup_codes) {
          localStorage.setItem('backup_codes', JSON.stringify(response.data.backup_codes));
        }
        
        // ✅ Redirect after 2 seconds
        setTimeout(() => {
          // Navigate to backup codes page if available, otherwise settings
          if (response.data.backup_codes) {
            navigate('/backup-codes', { 
              state: { 
                backupCodes: response.data.backup_codes,
                fromRegistration: true 
              } 
            });
          } else {
            navigate('/settings');
          }
        }, 2000);
      }
    } catch (err) {
      // ✅ Show error message
      const errorMessage = err.response?.data?.error || 'Registration failed. Please try again.';
      toast.error(errorMessage, {
        position: 'top-right',
        autoClose: 5000
      });
      console.error('Registration error:', err);
    } finally {
      setLoading(false);
    }
  };

  const strengthLabel = getPasswordStrengthLabel();

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
            Create Your<br />
            <span className="gradient-text">Secure Account</span>
          </h2>
          <p className="brand-description">
            Join thousands of users protecting their accounts with advanced multi-factor authentication.
          </p>
          
          <div className="features-list">
            <div className="feature-item">
              <FaCheckCircle className="feature-icon" />
              <span>5 Authentication Methods</span>
            </div>
            <div className="feature-item">
              <FaCheckCircle className="feature-icon" />
              <span>Bank-Level Security</span>
            </div>
            <div className="feature-item">
              <FaCheckCircle className="feature-icon" />
              <span>Easy Setup in 5 Minutes</span>
            </div>
          </div>
        </div>

        <div className="auth-form-container">
          <div className="auth-card">
            <div className="auth-header">
              <h2>Create Account</h2>
              <p>Set up your secure authentication profile</p>
            </div>

            <form onSubmit={handleRegister} className="auth-form">
              <div className="input-group">
                <label htmlFor="username">Username</label>
                <div className="input-wrapper">
                  <FaUser className="input-icon" />
                  <input
                    type="text"
                    id="username"
                    name="username"
                    className="input-field"
                    placeholder="Choose a username"
                    value={formData.username}
                    onChange={handleInputChange}
                    required
                  />
                </div>
              </div>

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
                    placeholder="Create a strong password"
                    value={formData.password}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                {formData.password && (
                  <div className="password-strength">
                    <div className="strength-bar">
                      <div 
                        className="strength-fill"
                        style={{ 
                          width: `${(passwordStrength / 5) * 100}%`,
                          backgroundColor: strengthLabel.color
                        }}
                      ></div>
                    </div>
                    <span style={{ color: strengthLabel.color }}>
                      {strengthLabel.text}
                    </span>
                  </div>
                )}
              </div>

              <div className="input-group">
                <label htmlFor="confirmPassword">Confirm Password</label>
                <div className="input-wrapper">
                  <FaLock className="input-icon" />
                  <input
                    type="password"
                    id="confirmPassword"
                    name="confirmPassword"
                    className="input-field"
                    placeholder="Confirm your password"
                    value={formData.confirmPassword}
                    onChange={handleInputChange}
                    required
                  />
                </div>
              </div>

              <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
                {loading ? (
                  <>
                    <FaSpinner className="spinner-icon" />
                    Creating Account...
                  </>
                ) : (
                  'Create Account'
                )}
              </button>
            </form>

            <div className="auth-footer">
              <p>
                Already have an account?{' '}
                <Link to="/login" className="auth-link">Sign In</Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
