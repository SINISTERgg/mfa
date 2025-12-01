import { useEffect, useState } from 'react';
import {
  FaArrowLeft,
  FaCheck,
  FaCheckCircle,
  FaExclamationCircle,
  FaKeyboard,
  FaRedo,
  FaShieldAlt
} from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import api from '../services/api';
import './KeystrokeEnrollPage.css';

const KeystrokeEnrollPage = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [passphrase] = useState('');
  const [attempts, setAttempts] = useState([]);
  const [currentInput, setCurrentInput] = useState('');
  const [keystrokeData, setKeystrokeData] = useState([]);
  const [enrolling, setEnrolling] = useState(false);
  const [attemptNumber, setAttemptNumber] = useState(1);

  const REQUIRED_ATTEMPTS = 3;
  const DEFAULT_PASSPHRASE = 'the quick brown fox jumps over the lazy dog';

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      navigate('/login');
    }
  }, [navigate]);

  const handleKeyDown = (e) => {
    const key = e.key;
    const timestamp = Date.now();
    
    setKeystrokeData(prev => [...prev, {
      type: 'keydown',
      key: key,
      timestamp: timestamp
    }]);
  };

  const handleKeyUp = (e) => {
    const key = e.key;
    const timestamp = Date.now();
    
    setKeystrokeData(prev => [...prev, {
      type: 'keyup',
      key: key,
      timestamp: timestamp
    }]);
  };

  const handleInputChange = (e) => {
    setCurrentInput(e.target.value);
  };

  const handleSubmitAttempt = () => {
    const targetPhrase = passphrase || DEFAULT_PASSPHRASE;
    
    if (currentInput.trim() !== targetPhrase) {
      toast.error('Text does not match the passphrase. Please type it exactly.');
      return;
    }

    if (keystrokeData.length < 10) {
      toast.error('Not enough keystroke data captured. Please try again.');
      return;
    }

    const newAttempts = [...attempts, keystrokeData];
    setAttempts(newAttempts);
    
    setCurrentInput('');
    setKeystrokeData([]);
    
    if (newAttempts.length >= REQUIRED_ATTEMPTS) {
      setStep(2);
    } else {
      setAttemptNumber(attemptNumber + 1);
      toast.success(`Attempt ${newAttempts.length}/${REQUIRED_ATTEMPTS} captured!`);
    }
  };

  const retakeAttempts = () => {
    setAttempts([]);
    setCurrentInput('');
    setKeystrokeData([]);
    setAttemptNumber(1);
    setStep(1);
  };

  const handleEnroll = async () => {
    if (attempts.length < REQUIRED_ATTEMPTS) {
      toast.error(`Please complete ${REQUIRED_ATTEMPTS} typing samples`);
      return;
    }

    setEnrolling(true);
    try {
      await api.post('/user/enroll/keystroke', {
        samples: attempts,
        passphrase: passphrase || DEFAULT_PASSPHRASE
      });

      setStep(3);
      toast.success('✅ Keystroke dynamics enrolled successfully!');
      
      setTimeout(() => {
        navigate('/settings');
      }, 2000);
    } catch (error) {
      toast.error(error.response?.data?.error || 'Enrollment failed');
      setEnrolling(false);
    }
  };

  return (
    <div className="keystroke-enroll-container">
      <div className="enroll-header">
        <button onClick={() => navigate('/settings')} className="btn-back-modern">
          <FaArrowLeft /> Back to Settings
        </button>
        <div className="header-badge">
          <FaShieldAlt /> Secure Enrollment
        </div>
      </div>

      <div className="enroll-main">
        <div className="enroll-card">
          <div className="card-header-modern">
            <div className="header-icon-large keystroke-icon">
              <FaKeyboard />
            </div>
            <h1>Keystroke Dynamics Enrollment</h1>
            <p>Your unique typing pattern for authentication</p>
          </div>

          <div className="progress-steps-modern">
            <div className={`step-item ${step >= 1 ? 'active' : ''} ${step > 1 ? 'completed' : ''}`}>
              <div className="step-circle">
                {step > 1 ? <FaCheck /> : '1'}
              </div>
              <div className="step-label">Type Pattern</div>
            </div>
            <div className="step-line"></div>
            <div className={`step-item ${step >= 2 ? 'active' : ''} ${step > 2 ? 'completed' : ''}`}>
              <div className="step-circle">
                {step > 2 ? <FaCheck /> : '2'}
              </div>
              <div className="step-label">Verify</div>
            </div>
            <div className="step-line"></div>
            <div className={`step-item ${step >= 3 ? 'active' : ''}`}>
              <div className="step-circle">3</div>
              <div className="step-label">Complete</div>
            </div>
          </div>

          <div className="keystroke-section-modern">
            {step === 1 && (
              <div className="typing-area">
                <div className="attempt-counter">
                  <div className="counter-circles">
                    {[...Array(REQUIRED_ATTEMPTS)].map((_, i) => (
                      <div 
                        key={i} 
                        className={`counter-circle ${i < attempts.length ? 'completed' : ''} ${i === attempts.length ? 'active' : ''}`}
                      >
                        {i < attempts.length ? <FaCheck /> : i + 1}
                      </div>
                    ))}
                  </div>
                  <p className="counter-text">
                    Type the passphrase ({attempts.length}/{REQUIRED_ATTEMPTS})
                  </p>
                </div>

                <div className="passphrase-display">
                  <div className="passphrase-label">
                    <FaExclamationCircle /> Please type this exactly:
                  </div>
                  <div className="passphrase-text">
                    {passphrase || DEFAULT_PASSPHRASE}
                  </div>
                </div>

                <div className="typing-input-container">
                  <textarea
                    value={currentInput}
                    onChange={handleInputChange}
                    onKeyDown={handleKeyDown}
                    onKeyUp={handleKeyUp}
                    placeholder="Start typing the passphrase..."
                    className="typing-input"
                    rows={4}
                  />
                  <div className="input-stats">
                    <div className="stat-item">
                      <span className="stat-label">Characters:</span>
                      <span className="stat-value">{currentInput.length}</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Keystrokes:</span>
                      <span className="stat-value">{keystrokeData.length}</span>
                    </div>
                  </div>
                </div>

                <div className="typing-actions">
                  <button 
                    onClick={() => {
                      setCurrentInput('');
                      setKeystrokeData([]);
                    }}
                    className="btn-clear"
                  >
                    <FaRedo /> Clear
                  </button>
                  <button 
                    onClick={handleSubmitAttempt}
                    disabled={!currentInput.trim()}
                    className="btn-submit"
                  >
                    <FaCheck /> Submit Attempt
                  </button>
                </div>
              </div>
            )}

            {step === 2 && (
              <div className="preview-area">
                <h3 className="preview-title">Your Typing Patterns</h3>
                <div className="keystroke-preview-grid">
                  {attempts.map((attempt, index) => (
                    <div key={index} className="keystroke-preview-item">
                      <div className="preview-number">Attempt {index + 1}</div>
                      <div className="preview-stats">
                        <div className="preview-stat">
                          <span className="stat-label">Keystrokes:</span>
                          <span className="stat-value">{attempt.length}</span>
                        </div>
                      </div>
                      <div className="preview-check">
                        <FaCheckCircle />
                      </div>
                    </div>
                  ))}
                </div>
                <div className="passphrase-verification">
                  <FaCheckCircle className="verify-icon" />
                  <p>All typing patterns captured successfully!</p>
                  <div className="passphrase-used">
                    Passphrase: {passphrase || DEFAULT_PASSPHRASE}
                  </div>
                </div>
              </div>
            )}

            {step === 3 && (
              <div className="success-animation">
                <div className="success-checkmark">
                  <FaCheckCircle />
                </div>
                <h2>Enrollment Complete!</h2>
                <p>Your keystroke pattern has been successfully enrolled</p>
                <div className="success-details">
                  <div className="detail-item">
                    <FaShieldAlt /> Secure encryption enabled
                  </div>
                  <div className="detail-item">
                    <FaCheckCircle /> {REQUIRED_ATTEMPTS} patterns stored safely
                  </div>
                </div>
              </div>
            )}
          </div>

          {step < 3 && (
            <div className="instructions-modern">
              <div className="instructions-header">
                <FaExclamationCircle /> <span>Instructions</span>
              </div>
              <div className="instructions-grid">
                <div className="instruction-item">
                  <div className="instruction-icon">⌨️</div>
                  <span>Type at your natural speed and rhythm</span>
                </div>
                <div className="instruction-item">
                  <div className="instruction-icon">🔄</div>
                  <span>Repeat the same text {REQUIRED_ATTEMPTS} times</span>
                </div>
                <div className="instruction-item">
                  <div className="instruction-icon">✍️</div>
                  <span>Type the passphrase exactly as shown</span>
                </div>
                <div className="instruction-item">
                  <div className="instruction-icon">🎯</div>
                  <span>Stay consistent with your typing style</span>
                </div>
              </div>
            </div>
          )}

          <div className="action-buttons-modern">
            {step === 2 && (
              <div className="button-group-modern">
                <button 
                  onClick={retakeAttempts}
                  className="btn-secondary-modern"
                >
                  <FaRedo /> Type Again
                </button>
                <button 
                  onClick={handleEnroll}
                  disabled={enrolling}
                  className="btn-primary-modern"
                >
                  {enrolling ? (
                    <>
                      <div className="btn-spinner"></div>
                      Enrolling...
                    </>
                  ) : (
                    <>
                      <FaCheck /> Confirm & Enroll
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default KeystrokeEnrollPage;
