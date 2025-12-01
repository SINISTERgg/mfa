import { useEffect, useRef, useState } from 'react';
import {
  FaArrowLeft,
  FaCamera,
  FaCheck,
  FaCheckCircle,
  FaExclamationCircle,
  FaRedo,
  FaShieldAlt
} from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import Webcam from 'react-webcam';
import api from '../services/api';
import './FaceEnrollPage.css';

const FaceEnrollPage = () => {
  const navigate = useNavigate();
  const webcamRef = useRef(null);
  const [step, setStep] = useState(1);
  const [capturedImage, setCapturedImage] = useState(null);
  const [enrolling, setEnrolling] = useState(false);
  const [cameraReady, setCameraReady] = useState(false);
  
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      navigate('/login');
    }
  }, [navigate]);

 
  const captureImage = () => {
    const imageSrc = webcamRef.current.getScreenshot();
    if (imageSrc) {
      setCapturedImage(imageSrc);
      setStep(2);
      // ✅ REMOVED: setFaceDetected(true);
    }
  };

const retakePhoto = () => {
    setCapturedImage(null);
    // ✅ REMOVED: setFaceDetected(null);
    setStep(1);
  };
  const handleEnroll = async () => {
    if (!capturedImage) {
      toast.error('Please capture your face first');
      return;
    }

    setEnrolling(true);
    try {
      await api.post('/user/enroll/face', {
        face_image: capturedImage
      });

      setStep(3);
      toast.success('✅ Face enrolled successfully!');
      
      setTimeout(() => {
        navigate('/settings');
      }, 2000);
    } catch (error) {
      toast.error(error.response?.data?.error || 'Enrollment failed');
      setEnrolling(false);
    }
  };

  return (
    <div className="face-enroll-container">
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
          {/* Header */}
          <div className="card-header-modern">
            <div className="header-icon-large">
              <FaCamera />
            </div>
            <h1>Face Recognition Enrollment</h1>
            <p>Capture your face for biometric authentication</p>
          </div>

          {/* Progress Steps */}
          <div className="progress-steps-modern">
            <div className={`step-item ${step >= 1 ? 'active' : ''} ${step > 1 ? 'completed' : ''}`}>
              <div className="step-circle">
                {step > 1 ? <FaCheck /> : '1'}
              </div>
              <div className="step-label">Capture</div>
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

          {/* Camera/Preview Area */}
          <div className="camera-section-modern">
            {step === 1 && (
              <div className="camera-container-modern">
                <Webcam
                  ref={webcamRef}
                  audio={false}
                  screenshotFormat="image/jpeg"
                  videoConstraints={{
                    width: 1280,
                    height: 720,
                    facingMode: 'user'
                  }}
                  onUserMedia={() => setCameraReady(true)}
                  className="webcam-modern"
                />
                <div className="face-overlay-modern">
                  <svg viewBox="0 0 200 250" className="face-guide">
                    <ellipse cx="100" cy="125" rx="80" ry="100" 
                      fill="none" 
                      stroke="rgba(59, 130, 246, 0.8)" 
                      strokeWidth="3"
                      strokeDasharray="10,5"
                    />
                  </svg>
                </div>
                {!cameraReady && (
                  <div className="camera-loading">
                    <div className="spinner-large"></div>
                    <p>Initializing camera...</p>
                  </div>
                )}
              </div>
            )}

            {step === 2 && capturedImage && (
              <div className="preview-container-modern">
                <img src={capturedImage} alt="Captured face" className="preview-image-modern" />
                <div className="face-overlay-modern">
                  <svg viewBox="0 0 200 250" className="face-guide">
                    <ellipse cx="100" cy="125" rx="80" ry="100" 
                      fill="none" 
                      stroke="rgba(16, 185, 129, 0.8)" 
                      strokeWidth="3"
                    />
                  </svg>
                </div>
              </div>
            )}

            {step === 3 && (
              <div className="success-animation">
                <div className="success-checkmark">
                  <FaCheckCircle />
                </div>
                <h2>Enrollment Complete!</h2>
                <p>Your face has been successfully enrolled</p>
                <div className="success-details">
                  <div className="detail-item">
                    <FaShieldAlt /> Secure encryption enabled
                  </div>
                  <div className="detail-item">
                    <FaCheckCircle /> Biometric data stored safely
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Instructions */}
          {step < 3 && (
            <div className="instructions-modern">
              <div className="instructions-header">
                <FaExclamationCircle /> <span>Instructions</span>
              </div>
              <div className="instructions-grid">
                <div className="instruction-item">
                  <div className="instruction-icon">✓</div>
                  <span>Position your face in the center of the frame</span>
                </div>
                <div className="instruction-item">
                  <div className="instruction-icon">💡</div>
                  <span>Ensure good lighting on your face</span>
                </div>
                <div className="instruction-item">
                  <div className="instruction-icon">👁️</div>
                  <span>Look directly at the camera</span>
                </div>
                <div className="instruction-item">
                  <div className="instruction-icon">👓</div>
                  <span>Remove glasses or accessories if possible</span>
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="action-buttons-modern">
            {step === 1 && (
              <button 
                onClick={captureImage}
                disabled={!cameraReady}
                className="btn-primary-modern btn-large"
              >
                <FaCamera /> Capture Photo
              </button>
            )}

            {step === 2 && (
              <div className="button-group-modern">
                <button 
                  onClick={retakePhoto}
                  className="btn-secondary-modern"
                >
                  <FaRedo /> Retake Photo
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

export default FaceEnrollPage;
