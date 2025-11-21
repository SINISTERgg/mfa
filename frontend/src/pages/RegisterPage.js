import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import authService from '../services/authService';
import './RegisterPage.css';

const RegisterPage = () => {
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    fullName: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [backupCodes, setBackupCodes] = useState(null);
  const [showBackupCodes, setShowBackupCodes] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const validateForm = () => {
    const { username, email, password, confirmPassword } = formData;

    // Username validation
    if (!username || username.length < 3) {
      toast.error('Username must be at least 3 characters');
      return false;
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email || !emailRegex.test(email)) {
      toast.error('Please enter a valid email address');
      return false;
    }

    // Password validation
    if (!password || password.length < 6) {
      toast.error('Password must be at least 6 characters');
      return false;
    }

    // Confirm password
    if (password !== confirmPassword) {
      toast.error('Passwords do not match');
      return false;
    }

    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate form
    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      console.log('📝 [REGISTER] Starting registration...');
      
      const response = await authService.register(
        formData.username,
        formData.email,
        formData.password,
        formData.fullName
      );

      console.log('✅ [REGISTER] Registration successful');

      // Show backup codes
      if (response.backup_codes) {
        setBackupCodes(response.backup_codes);
        setShowBackupCodes(true);
        toast.success('Registration successful! Please save your backup codes.');
      } else {
        toast.success('Registration successful!');
        navigate('/login');
      }

    } catch (error) {
      console.error('❌ [REGISTER ERROR]', error);
      toast.error(error.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyBackupCodes = () => {
    if (backupCodes) {
      const codesText = backupCodes.join('\n');
      navigator.clipboard.writeText(codesText);
      toast.success('Backup codes copied to clipboard!');
    }
  };

  const handleDownloadBackupCodes = () => {
    if (backupCodes) {
      const codesText = backupCodes.join('\n');
      const blob = new Blob([codesText], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `backup-codes-${formData.username}.txt`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success('Backup codes downloaded!');
    }
  };

  const handleContinue = () => {
    toast.success('Registration complete! You can now login.');
    navigate('/login');
  };

  if (showBackupCodes) {
    return (
      <div className="register-page">
        <div className="register-container">
          <div className="backup-codes-modal">
            <h2>🔑 Save Your Backup Codes</h2>
            <p className="backup-warning">
              ⚠️ Save these codes in a safe place. You'll need them if you lose access to your authentication methods.
            </p>

            <div className="backup-codes-grid">
              {backupCodes.map((code, index) => (
                <div key={index} className="backup-code-item">
                  <span className="code-number">{index + 1}.</span>
                  <code>{code}</code>
                </div>
              ))}
            </div>

            <div className="backup-actions">
              <button
                onClick={handleCopyBackupCodes}
                className="btn btn-secondary"
              >
                📋 Copy All
              </button>
              <button
                onClick={handleDownloadBackupCodes}
                className="btn btn-secondary"
              >
                💾 Download
              </button>
              <button
                onClick={handleContinue}
                className="btn btn-primary"
              >
                Continue to Login →
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="register-page">
      <div className="register-container">
        <div className="register-header">
          <h1>Create Account</h1>
          <p>Sign up for multi-factor authentication</p>
        </div>

        <form onSubmit={handleSubmit} className="register-form">
          <div className="form-group">
            <label htmlFor="username">Username *</label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              placeholder="Choose a username"
              required
              minLength={3}
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">Email *</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="your.email@example.com"
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="fullName">Full Name (Optional)</label>
            <input
              type="text"
              id="fullName"
              name="fullName"
              value={formData.fullName}
              onChange={handleChange}
              placeholder="John Doe"
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password *</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="At least 6 characters"
              required
              minLength={6}
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password *</label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              placeholder="Re-enter password"
              required
              minLength={6}
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-block"
            disabled={loading}
          >
            {loading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>

        <div className="register-footer">
          <p>
            Already have an account?{' '}
            <Link to="/login">Login here</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
