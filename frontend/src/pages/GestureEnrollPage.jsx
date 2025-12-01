import { useEffect, useRef, useState } from 'react';
import {
  FaArrowLeft,
  FaCheck,
  FaCheckCircle,
  FaExclamationCircle,
  FaHandPaper,
  FaMousePointer,
  FaRedo,
  FaShieldAlt
} from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import api from '../services/api';
import './GestureEnrollPage.css';

const GestureEnrollPage = () => {
  const navigate = useNavigate();
  const canvasRef = useRef(null);
  const [step, setStep] = useState(1);
  const [attempts, setAttempts] = useState([]);
  const [currentGesture, setCurrentGesture] = useState([]);
  const [isDrawing, setIsDrawing] = useState(false);
  const [enrolling, setEnrolling] = useState(false);

  const REQUIRED_ATTEMPTS = 3;

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      navigate('/login');
    }
  }, [navigate]);

  const startDrawing = (e) => {
    setIsDrawing(true);
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    setCurrentGesture([{ x, y, timestamp: Date.now() }]);
    
    const ctx = canvas.getContext('2d');
    ctx.beginPath();
    ctx.moveTo(x, y);
  };

  const draw = (e) => {
    if (!isDrawing) return;
    
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    setCurrentGesture(prev => [...prev, { x, y, timestamp: Date.now() }]);
    
    const ctx = canvas.getContext('2d');
    ctx.lineTo(x, y);
    ctx.strokeStyle = '#f59e0b';
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    ctx.stroke();
  };

  const stopDrawing = () => {
    if (!isDrawing) return;
    setIsDrawing(false);
    
    if (currentGesture.length > 10) {
      const newAttempts = [...attempts, currentGesture];
      setAttempts(newAttempts);
      
      if (newAttempts.length >= REQUIRED_ATTEMPTS) {
        setStep(2);
      } else {
        toast.success(`Gesture ${newAttempts.length}/${REQUIRED_ATTEMPTS} captured!`);
      }
    } else {
      toast.error('Gesture too short. Please draw a longer pattern.');
    }
    
    setCurrentGesture([]);
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setCurrentGesture([]);
  };

  const redrawAttempt = (gesture) => {
    clearCanvas();
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    ctx.beginPath();
    ctx.moveTo(gesture[0].x, gesture[0].y);
    
    gesture.forEach(point => {
      ctx.lineTo(point.x, point.y);
    });
    
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    ctx.stroke();
  };

  const retakeGestures = () => {
    setAttempts([]);
    setCurrentGesture([]);
    setStep(1);
    clearCanvas();
  };

  const handleEnroll = async () => {
  if (attempts.length < REQUIRED_ATTEMPTS) {
    toast.error(`Please complete ${REQUIRED_ATTEMPTS} gesture samples`);
    return;
  }

  setEnrolling(true);
  try {
    // Flatten all attempts into a single points array
    const allPoints = attempts.flat();

    await api.post('/user/enroll/gesture', {
      points: allPoints,
    });

    setStep(3);
    toast.success('✅ Gesture pattern enrolled successfully!');
    setTimeout(() => {
      navigate('/settings');
    }, 2000);
  } catch (error) {
    toast.error(error.response?.data?.error || 'Enrollment failed');
    setEnrolling(false);
  }
};

  return (
    <div className="gesture-enroll-container">
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
            <div className="header-icon-large gesture-icon">
              <FaHandPaper />
            </div>
            <h1>Gesture Recognition Enrollment</h1>
            <p>Draw your unique gesture pattern for authentication</p>
          </div>

          <div className="progress-steps-modern">
            <div className={`step-item ${step >= 1 ? 'active' : ''} ${step > 1 ? 'completed' : ''}`}>
              <div className="step-circle">
                {step > 1 ? <FaCheck /> : '1'}
              </div>
              <div className="step-label">Draw Pattern</div>
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

          <div className="gesture-section-modern">
            {step === 1 && (
              <div className="drawing-area">
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
                    Draw your gesture pattern ({attempts.length}/{REQUIRED_ATTEMPTS})
                  </p>
                </div>

                <div className="canvas-container">
                  <canvas
                    ref={canvasRef}
                    width={600}
                    height={400}
                    onMouseDown={startDrawing}
                    onMouseMove={draw}
                    onMouseUp={stopDrawing}
                    onMouseLeave={stopDrawing}
                    className="gesture-canvas"
                  />
                  {!isDrawing && currentGesture.length === 0 && attempts.length === 0 && (
                    <div className="canvas-placeholder">
                      <FaMousePointer className="placeholder-icon" />
                      <p>Click and drag to draw your gesture pattern</p>
                    </div>
                  )}
                </div>

                {currentGesture.length > 0 && (
                  <button onClick={clearCanvas} className="btn-clear">
                    <FaRedo /> Clear
                  </button>
                )}
              </div>
            )}

            {step === 2 && (
              <div className="preview-area">
                <h3 className="preview-title">Your Gesture Patterns</h3>
                <div className="gesture-preview-grid">
                  {attempts.map((gesture, index) => (
                    <div 
                      key={index} 
                      className="gesture-preview-item"
                      onClick={() => redrawAttempt(gesture)}
                    >
                      <div className="preview-number">Pattern {index + 1}</div>
                      <div className="preview-check">
                        <FaCheckCircle />
                      </div>
                    </div>
                  ))}
                </div>
                <div className="preview-canvas-container">
                  <canvas
                    ref={canvasRef}
                    width={600}
                    height={400}
                    className="gesture-canvas preview"
                  />
                  <p className="preview-hint">Click on a pattern above to preview it</p>
                </div>
              </div>
            )}

            {step === 3 && (
              <div className="success-animation">
                <div className="success-checkmark">
                  <FaCheckCircle />
                </div>
                <h2>Enrollment Complete!</h2>
                <p>Your gesture pattern has been successfully enrolled</p>
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
                  <div className="instruction-icon">✍️</div>
                  <span>Draw a unique pattern you can remember</span>
                </div>
                <div className="instruction-item">
                  <div className="instruction-icon">🔄</div>
                  <span>Repeat the same pattern {REQUIRED_ATTEMPTS} times</span>
                </div>
                <div className="instruction-item">
                  <div className="instruction-icon">📏</div>
                  <span>Make it complex but memorable</span>
                </div>
                <div className="instruction-item">
                  <div className="instruction-icon">⚡</div>
                  <span>Draw at your natural speed</span>
                </div>
              </div>
            </div>
          )}

          <div className="action-buttons-modern">
            {step === 2 && (
              <div className="button-group-modern">
                <button 
                  onClick={retakeGestures}
                  className="btn-secondary-modern"
                >
                  <FaRedo /> Draw Again
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

export default GestureEnrollPage;
        