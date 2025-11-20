import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { toast } from 'react-toastify';
import authService from '../services/authService';
import BackupCodes from '../components/BackupCodes';
import { validateEmail, validateUsername, validatePassword } from '../utils/helpers';

const RegisterPage = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    fullName: '',
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [backupCodes, setBackupCodes] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  const validate = () => {
    const newErrors = {};

    if (!formData.username) {
      newErrors.username = 'Username is required';
    } else if (!validateUsername(formData.username)) {
      newErrors.username = 'Username must be 3-80 characters (letters, numbers, _, -)';
    }

    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!validateEmail(formData.email)) {
      newErrors.email = 'Invalid email format';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else {
      const passwordValidation = validatePassword(formData.password);
      if (!passwordValidation.valid) {
        newErrors.password = 'Password must be at least 8 characters with uppercase, lowercase, number, and special character';
      }
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validate()) return;

    setLoading(true);

    try {
      const response = await authService.register(
        formData.username,
        formData.email,
        formData.password,
        formData.fullName
      );

      toast.success('Registration successful!');
      setBackupCodes(response.backup_codes);
    } catch (error) {
      toast.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleContinue = () => {
    navigate('/login');
  };

  if (backupCodes) {
    return (
      <div className="auth-container">
        <div className="auth-card" style={{ maxWidth: '700px' }}>
          <BackupCodes codes={backupCodes} />
          <button onClick={handleContinue} className="btn btn-primary mt-20">
            Continue to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Create Account</h2>
        <p>Sign up to get started with secure MFA</p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Full Name</label>
            <input
              type="text"
              name="fullName"
              value={formData.fullName}
              onChange={handleChange}
              placeholder="Enter your full name"
            />
          </div>

          <div className="form-group">
            <label>Username *</label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              className={errors.username ? 'error' : ''}
              placeholder="Choose a username"
              required
            />
            {errors.username && (
              <span className="form-error">{errors.username}</span>
            )}
          </div>

          <div className="form-group">
            <label>Email *</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className={errors.email ? 'error' : ''}
              placeholder="Enter your email"
              required
            />
            {errors.email && <span className="form-error">{errors.email}</span>}
          </div>

          <div className="form-group">
            <label>Password *</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className={errors.password ? 'error' : ''}
              placeholder="Create a strong password"
              required
            />
            {errors.password && (
              <span className="form-error">{errors.password}</span>
            )}
          </div>

          <div className="form-group">
            <label>Confirm Password *</label>
            <input
              type="password"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              className={errors.confirmPassword ? 'error' : ''}
              placeholder="Confirm your password"
              required
            />
            {errors.confirmPassword && (
              <span className="form-error">{errors.confirmPassword}</span>
            )}
          </div>

          <button type="submit" disabled={loading} className="btn btn-primary">
            {loading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>

        <p className="text-center mt-20">
          Already have an account?{' '}
          <Link to="/login" className="link">
            Sign In
          </Link>
        </p>
      </div>
    </div>
  );
};

export default RegisterPage;
