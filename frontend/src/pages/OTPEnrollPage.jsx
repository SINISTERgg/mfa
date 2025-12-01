// src/pages/OTPEnrollPage.jsx
import { useEffect, useState } from 'react';
import {
  FaArrowLeft,
  FaCheck,
  FaMobileAlt,
  FaShieldAlt
} from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import OTPInput from '../components/OTPInput';
import '../components/OTPInput.css';
import api from '../services/api';
import './OTPEnrollPage.css';

function OTPEnrollPage() {
  const navigate = useNavigate();

  const [step, setStep] = useState(1);
  const [qrCode, setQrCode] = useState('');
  const [secret, setSecret] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [loading, setLoading] = useState(true);
  const [enrolling, setEnrolling] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      navigate('/login');
      return;
    }
    fetchQRCode();
  }, [navigate]);

  async function fetchQRCode() {
    try {
      setLoading(true);
      const res = await api.get('/user/otp/generate');
      setQrCode(res.data.qr_code);
      setSecret(res.data.secret);
      setLoading(false);
    } catch (err) {
      setLoading(false);
      toast.error('Could not generate QR code');
    }
  }

  function handleCopySecret() {
    if (!secret) return;
    navigator.clipboard.writeText(secret);
    toast.success('Secret copied');
  }

  async function handleVerify() {
    if (otpCode.length !== 6) {
      toast.error('Enter the 6‑digit code from your app');
      return;
    }

    setEnrolling(true);
    try {
      await api.post('/user/enroll/otp', { otp_code: otpCode });
      setStep(3);
      toast.success('Authenticator app enrolled');
      setTimeout(() => navigate('/settings'), 2000);
    } catch (err) {
      setEnrolling(false);
      toast.error(err.response?.data?.error || 'Verification failed');
    }
  }

  return (
    <div className="otp-enroll-container">
      {/* Top bar */}
      <div className="enroll-header">
        <button
          type="button"
          className="btn-back-modern"
          onClick={() => navigate('/settings')}
        >
          <FaArrowLeft /> Back to Settings
        </button>
        <div className="header-badge">
          <FaShieldAlt /> Secure Enrollment
        </div>
      </div>

      <div className="enroll-main">
        <div className="enroll-card">
          {/* Title */}
          <div className="card-header-modern">
            <div className="header-icon-large otp-icon">
              <FaMobileAlt />
            </div>
            <h1>Authenticator App Enrollment</h1>
            <p>Use a TOTP app (like Google Authenticator) for extra security.</p>
          </div>

          {/* Steps */}
          <div className="progress-steps-modern">
            <div className={`step-item ${step >= 1 ? 'active' : ''} ${step > 1 ? 'completed' : ''}`}>
              <div className="step-circle">{step > 1 ? <FaCheck /> : '1'}</div>
              <div className="step-label">Scan</div>
            </div>
            <div className="step-line" />
            <div className={`step-item ${step >= 2 ? 'active' : ''} ${step > 2 ? 'completed' : ''}`}>
              <div className="step-circle">{step > 2 ? <FaCheck /> : '2'}</div>
              <div className="step-label">Verify</div>
            </div>
            <div className="step-line" />
            <div className={`step-item ${step >= 3 ? 'active' : ''}`}>
              <div className="step-circle">3</div>
              <div className="step-label">Done</div>
            </div>
          </div>

          <div className="otp-section-modern">
            {/* STEP 1: QR + secret (unchanged) */}
            {step === 1 && (
              <div className="scan-area">
                <div className="qr-code-container">
                  {loading ? (
                    <div className="loading-spinner">Loading...</div>
                  ) : (
                    <img src={qrCode} alt="QR Code" className="qr-code-image" />
                  )}
                </div>
                <p className="scan-instruction">Scan with your authenticator app</p>
                <div className="secret-backup">
                  <p>Or enter this key manually:</p>
                  <div className="secret-display">
                    <code>{secret}</code>
                    <button
                      type="button"
                      className="btn-copy"
                      onClick={handleCopySecret}
                    >
                      Copy
                    </button>
                  </div>
                </div>
                <button
                  type="button"
                  className="btn-primary-modern"
                  onClick={() => setStep(2)}
                >
                  <FaCheck /> Next
                </button>
              </div>
            )}

            {/* STEP 2: enter OTP with 6 inputs */}
            {step === 2 && (
              <div className="verification-area">
                <div className="verification-icon">
                  <FaMobileAlt />
                </div>
                <h3 className="verification-title">Enter 6‑digit code</h3>
                <p className="verification-subtitle">
                  Type the current code shown in your authenticator app.
                </p>

                <div className="otp-input-container">
                  {/* optional hidden input to support paste / one-time-code */}
                  <input
                    type="text"
                    value={otpCode}
                    onChange={e =>
                      setOtpCode(e.target.value.replace(/\D/g, '').slice(0, 6))
                    }
                    maxLength={6}
                    className="otp-input-hidden"
                    autoComplete="one-time-code"
                  />

                  <OTPInput value={otpCode} onChange={setOtpCode} />
                </div>

                <div className="verification-actions">
                  <button
                    type="button"
                    className="btn-secondary-modern"
                    onClick={() => setStep(1)}
                  >
                    <FaArrowLeft /> Back
                  </button>
                  <button
                    type="button"
                    className="btn-primary-modern"
                    disabled={enrolling || otpCode.length !== 6}
                    onClick={handleVerify}
                  >
                    {enrolling ? (
                      <>
                        <div className="btn-spinner" />
                        Verifying…
                      </>
                    ) : (
                      <>
                        <FaCheck /> Verify &amp; Enroll
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}

            {/* STEP 3: success (unchanged) */}
            {step === 3 && (
              /* ... your existing STEP 3 code here ... */
              <></>
            )}
          </div>

          {/* Instructions block (unchanged) */}
          {step < 3 && (
            /* ... your existing instructions code here ... */
            <></>
          )}
        </div>
      </div>
    </div>
  );
}

export default OTPEnrollPage;
