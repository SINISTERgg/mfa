import { useEffect, useRef, useState } from 'react';
import {
  FaArrowLeft,
  FaCamera,
  FaCheckCircle,
  FaDrawPolygon,
  FaEraser,
  FaKey,
  FaKeyboard,
  FaMicrophone,
  FaQrcode,
  FaRedo,
  FaSpinner,
  FaStop
} from 'react-icons/fa';
import { useLocation, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import Webcam from 'react-webcam';
import OTPInput from '../components/OTPInput';
import api from '../services/api';
import './MFAVerifyPage.css';

const MFAVerifyPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Common state
  const [mfaToken, setMfaToken] = useState('');
  const [selectedMethod, setSelectedMethod] = useState(null);
  const [verifying, setVerifying] = useState(false);
  
  // Face state
  const webcamRef = useRef(null);
  const [capturedImage, setCapturedImage] = useState(null);
  
  // Voice state
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);
  const [recording, setRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);
  
  // Gesture state
  const canvasRef = useRef(null);
  const [drawing, setDrawing] = useState(false);
  const [gestureData, setGestureData] = useState(null);
  const [points, setPoints] = useState([]);
  
  // Keystroke state
  const [passphrase] = useState('the quick brown fox jumps over the lazy dog');
  const [inputValue, setInputValue] = useState('');
  const [keystrokeSample, setKeystrokeSample] = useState([]);
  const lastKeyTimeRef = useRef(0);
  
  // OTP state
  const [otpCode, setOtpCode] = useState('');
  
  // Backup code state
  const [backupCode, setBackupCode] = useState('');

  useEffect(() => {
    const token = location.state?.mfa_token;
    const method = location.state?.method;
    
    if (!token) {
      navigate('/login');
      return;
    }
    
    setMfaToken(token);
    if (method) {
      setSelectedMethod(method);
    }
  }, [location, navigate]);

  useEffect(() => {
    if (selectedMethod === 'gesture' && canvasRef.current) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      ctx.strokeStyle = '#ec4899';
      ctx.lineWidth = 3;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
    }
  }, [selectedMethod]);

  // ==================== FACE METHODS ====================
  const capturePhoto = () => {
    const imageSrc = webcamRef.current.getScreenshot();
    setCapturedImage(imageSrc);
  };

  const retakeFace = () => {
    setCapturedImage(null);
  };

  const verifyFace = async () => {
    if (!capturedImage) {
      toast.error('Please capture a photo first');
      return;
    }

    setVerifying(true);
    try {
      const response = await api.post('/auth/mfa/verify-face', {
        mfa_token: mfaToken,
        face_image: capturedImage
      });

      handleSuccessfulAuth(response.data);
    } catch (error) {
      toast.error(error.response?.data?.error || 'Face verification failed');
      setVerifying(false);
    }
  };

  // ==================== VOICE METHODS ====================
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      chunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorderRef.current.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/wav' });
        setAudioBlob(blob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setRecording(true);
      setRecordingTime(0);
      
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
    } catch (error) {
      toast.error('Microphone access denied');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.stop();
      setRecording(false);
      clearInterval(timerRef.current);
    }
  };

  const verifyVoice = async () => {
    if (!audioBlob) {
      toast.error('Please record your voice first');
      return;
    }

    setVerifying(true);
    try {
      const reader = new FileReader();
      reader.readAsDataURL(audioBlob);
      reader.onloadend = async () => {
        const response = await api.post('/auth/mfa/verify-voice', {
          mfa_token: mfaToken,
          voice_audio: reader.result
        });
        handleSuccessfulAuth(response.data);
      };
    } catch (error) {
      toast.error(error.response?.data?.error || 'Voice verification failed');
      setVerifying(false);
    }
  };

  // ==================== GESTURE METHODS ====================
  const startDrawing = (e) => {
    setDrawing(true);
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const ctx = canvas.getContext('2d');
    ctx.beginPath();
    ctx.moveTo(x, y);
    
    setPoints([{ x, y, timestamp: Date.now() }]);
  };

  const draw = (e) => {
    if (!drawing) return;
    
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const ctx = canvas.getContext('2d');
    ctx.lineTo(x, y);
    ctx.stroke();
    
    setPoints(prev => [...prev, { x, y, timestamp: Date.now() }]);
  };

  const stopDrawing = () => {
    if (drawing && points.length > 10) {
      setDrawing(false);
      setGestureData({ points });
    } else if (drawing) {
      toast.warning('Please draw a longer pattern');
      setDrawing(false);
    }
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setPoints([]);
    setGestureData(null);
  };

  const verifyGesture = async () => {
    if (!gestureData || points.length < 10) {
      toast.error('Please draw your gesture pattern');
      return;
    }

    setVerifying(true);
    try {
      const response = await api.post('/auth/mfa/verify-gesture', {
        mfa_token: mfaToken,
        gesture: gestureData
      });
      handleSuccessfulAuth(response.data);
    } catch (error) {
      toast.error(error.response?.data?.error || 'Gesture verification failed');
      setVerifying(false);
    }
  };

  // ==================== KEYSTROKE METHODS ====================
  const handleKeyDown = (e) => {
    const keyData = {
      key: e.key,
      keyCode: e.keyCode,
      timestamp: Date.now(),
      type: 'keydown'
    };
    setKeystrokeSample(prev => [...prev, keyData]);
    lastKeyTimeRef.current = Date.now();
  };

  const handleKeyUp = (e) => {
    const keyData = {
      key: e.key,
      keyCode: e.keyCode,
      timestamp: Date.now(),
      type: 'keyup',
      duration: Date.now() - lastKeyTimeRef.current
    };
    setKeystrokeSample(prev => [...prev, keyData]);
  };

  const handleInputChange = (e) => {
    setInputValue(e.target.value);
  };

  const verifyKeystroke = async () => {
    if (inputValue !== passphrase) {
      toast.error('Please type the complete passphrase correctly');
      return;
    }

    setVerifying(true);
    try {
      const response = await api.post('/auth/mfa/verify-keystroke', {
        mfa_token: mfaToken,
        keystroke: keystrokeSample,
        passphrase: passphrase
      });
      handleSuccessfulAuth(response.data);
    } catch (error) {
      toast.error(error.response?.data?.error || 'Keystroke verification failed');
      setVerifying(false);
    }
  };

  // ==================== OTP METHODS ====================
   const verifyOTP = async () => {
    if (!otpCode || otpCode.length !== 6) {
      toast.error('Please enter a valid 6-digit code');
      return;
    }

    setVerifying(true);
    try {
      const response = await api.post('/auth/mfa/verify-otp', {
        mfa_token: mfaToken,
        otp_code: otpCode
      });
      handleSuccessfulAuth(response.data);
    } catch (error) {
      toast.error(error.response?.data?.error || 'OTP verification failed');
      setVerifying(false);
    }
  };

  // ==================== BACKUP CODE METHODS ====================
  const verifyBackupCode = async () => {
    if (!backupCode || backupCode.length < 6) {
      toast.error('Please enter a valid backup code');
      return;
    }

    setVerifying(true);
    try {
      const response = await api.post('/auth/mfa/verify-backup-code', {
        mfa_token: mfaToken,
        backup_code: backupCode
      });
      handleSuccessfulAuth(response.data);
    } catch (error) {
      toast.error(error.response?.data?.error || 'Backup code verification failed');
      setVerifying(false);
    }
  };

  // ==================== COMMON METHODS ====================
  const handleSuccessfulAuth = (data) => {
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    toast.success('✅ Authentication successful!');
    setTimeout(() => {
      navigate('/dashboard');
    }, 1500);
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const methods = {
    face: {
      name: 'Face Recognition',
      icon: <FaCamera />,
      color: '#3b82f6'
    },
    voice: {
      name: 'Voice Recognition',
      icon: <FaMicrophone />,
      color: '#8b5cf6'
    },
    gesture: {
      name: 'Gesture Pattern',
      icon: <FaDrawPolygon />,
      color: '#ec4899'
    },
    keystroke: {
      name: 'Keystroke Dynamics',
      icon: <FaKeyboard />,
      color: '#10b981'
    },
    totp: {
      name: 'Authenticator App',
      icon: <FaQrcode />,
      color: '#f59e0b'
    },
    backup: {
      name: 'Backup Code',
      icon: <FaKey />,
      color: '#ef4444'
    }
  };

  if (!selectedMethod) {
    return (
      <div className="mfa-verify-container">
        <div className="mfa-verify-background">
          <div className="gradient-orb orb-1"></div>
          <div className="gradient-orb orb-2"></div>
        </div>
        <div className="mfa-verify-content">
          <div className="loading-state">
            <FaSpinner className="spinner-icon" />
            <p>Loading...</p>
          </div>
        </div>
      </div>
    );
  }

  const currentMethod = methods[selectedMethod];

  return (
    <div className="mfa-verify-container">
      <div className="mfa-verify-background">
        <div className="gradient-orb orb-1"></div>
        <div className="gradient-orb orb-2"></div>
      </div>

      <div className="mfa-verify-content">
        <button onClick={() => navigate('/mfa-select', { state: { mfa_token: mfaToken } })} className="btn-back">
          <FaArrowLeft /> Back to Methods
        </button>

        <div className="verify-header">
          <div className="method-badge" style={{ backgroundColor: `${currentMethod.color}15`, color: currentMethod.color }}>
            {currentMethod.icon}
            <span>{currentMethod.name}</span>
          </div>
          <h1>Verify Your Identity</h1>
          <p>Complete the verification to access your account</p>
        </div>

        <div className="verify-card">
          {/* FACE VERIFICATION */}
          {selectedMethod === 'face' && (
            <div className="verification-content">
              <div className="camera-container">
                {!capturedImage ? (
                  <div className="webcam-wrapper">
                    <Webcam
                      ref={webcamRef}
                      audio={false}
                      screenshotFormat="image/jpeg"
                      className="webcam-feed"
                      videoConstraints={{ width: 1280, height: 720, facingMode: 'user' }}
                    />
                    <div className="face-overlay">
                      <div className="face-guide"></div>
                    </div>
                  </div>
                ) : (
                  <div className="preview-wrapper">
                    <img src={capturedImage} alt="Captured" className="captured-image" />
                    <div className="success-badge">
                      <FaCheckCircle /> Photo Captured
                    </div>
                  </div>
                )}
              </div>
              <div className="action-buttons">
                {!capturedImage ? (
                  <button onClick={capturePhoto} className="btn btn-primary btn-large">
                    <FaCamera /> Capture Photo
                  </button>
                ) : (
                  <>
                    <button onClick={retakeFace} className="btn btn-secondary btn-large">
                      <FaRedo /> Retake
                    </button>
                    <button onClick={verifyFace} className="btn btn-primary btn-large" disabled={verifying}>
                      {verifying ? <><FaSpinner className="spinner-icon" /> Verifying...</> : <><FaCheckCircle /> Verify</>}
                    </button>
                  </>
                )}
              </div>
            </div>
          )}

          {/* VOICE VERIFICATION */}
          {selectedMethod === 'voice' && (
            <div className="verification-content">
              <div className="voice-area">
                {recording ? (
                  <div className="recording-active">
                    <div className="pulse-circle">
                      <FaMicrophone className="mic-icon" />
                    </div>
                    <div className="recording-time">{formatTime(recordingTime)}</div>
                    <div className="recording-indicator">
                      <span className="recording-dot"></span>
                      Recording...
                    </div>
                  </div>
                ) : audioBlob ? (
                  <div className="recording-complete">
                    <div className="success-circle">
                      <FaCheckCircle className="check-icon" />
                    </div>
                    <audio controls src={URL.createObjectURL(audioBlob)} className="audio-player" />
                  </div>
                ) : (
                  <div className="recording-idle">
                    <div className="mic-circle">
                      <FaMicrophone className="mic-icon-large" />
                    </div>
                    <p>Click below to start recording</p>
                  </div>
                )}
              </div>
              <div className="passphrase-display">
                <h4>📝 Read this phrase:</h4>
                <div className="passphrase-text">"My voice is my password, verify me."</div>
              </div>
              <div className="action-buttons">
                {!audioBlob ? (
                  <button 
                    onClick={recording ? stopRecording : startRecording}
                    className={`btn btn-large ${recording ? 'btn-danger' : 'btn-primary'}`}
                  >
                    {recording ? <><FaStop /> Stop Recording</> : <><FaMicrophone /> Start Recording</>}
                  </button>
                ) : (
                  <button onClick={verifyVoice} className="btn btn-primary btn-large" disabled={verifying}>
                    {verifying ? <><FaSpinner className="spinner-icon" /> Verifying...</> : <><FaCheckCircle /> Verify</>}
                  </button>
                )}
              </div>
            </div>
          )}

          {/* GESTURE VERIFICATION */}
          {selectedMethod === 'gesture' && (
            <div className="verification-content">
              <div className="canvas-wrapper">
                <canvas
                  ref={canvasRef}
                  width={600}
                  height={400}
                  className="gesture-canvas"
                  onMouseDown={startDrawing}
                  onMouseMove={draw}
                  onMouseUp={stopDrawing}
                  onMouseLeave={stopDrawing}
                />
                {!gestureData && (
                  <div className="canvas-overlay">
                    <p>Draw your secret pattern</p>
                  </div>
                )}
                {gestureData && (
                  <div className="gesture-success">
                    <FaCheckCircle /> Pattern Captured
                  </div>
                )}
              </div>
              <div className="action-buttons">
                {!gestureData ? (
                  <button onClick={clearCanvas} className="btn btn-secondary btn-large">
                    <FaEraser /> Clear Canvas
                  </button>
                ) : (
                  <>
                    <button onClick={clearCanvas} className="btn btn-secondary btn-large">
                      <FaRedo /> Draw Again
                    </button>
                    <button onClick={verifyGesture} className="btn btn-primary btn-large" disabled={verifying}>
                      {verifying ? <><FaSpinner className="spinner-icon" /> Verifying...</> : <><FaCheckCircle /> Verify</>}
                    </button>
                  </>
                )}
              </div>
            </div>
          )}

          {/* KEYSTROKE VERIFICATION */}
          {selectedMethod === 'keystroke' && (
            <div className="verification-content">
              <div className="passphrase-display-large">
                <h4>Type this phrase:</h4>
                <div className="passphrase-text-large">
                  {passphrase.split('').map((char, index) => (
                    <span 
                      key={index}
                      className={`char ${index < inputValue.length ? 'typed' : ''} ${inputValue[index] !== char && index < inputValue.length ? 'error' : ''}`}
                    >
                      {char}
                    </span>
                  ))}
                </div>
              </div>
              <input
                type="text"
                className="typing-input"
                value={inputValue}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                onKeyUp={handleKeyUp}
                placeholder="Start typing here..."
                autoFocus
              />
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${(inputValue.length / passphrase.length) * 100}%` }}></div>
              </div>
              <div className="action-buttons">
                <button 
                  onClick={verifyKeystroke} 
                  className="btn btn-primary btn-large" 
                  disabled={verifying || inputValue !== passphrase}
                >
                  {verifying ? <><FaSpinner className="spinner-icon" /> Verifying...</> : <><FaCheckCircle /> Verify</>}
                </button>
              </div>
            </div>
          )}

           {/* OTP VERIFICATION */}
{selectedMethod === 'totp' && (
  <div className="verification-content">
    <div className="otp-section">
      <FaQrcode className="otp-icon" />
      <h3>Enter the 6-digit code from your authenticator app</h3>

      <OTPInput
        value={otpCode}
        onChange={setOtpCode}
      />
    </div>

    <div className="action-buttons">
      <button
        onClick={verifyOTP}
        className="btn btn-primary btn-large"
        disabled={verifying || otpCode.length !== 6}
      >
        {verifying ? (
          <>
            <FaSpinner className="spinner-icon" /> Verifying...
          </>
        ) : (
          <>
            <FaCheckCircle /> Verify
          </>
        )}
      </button>
    </div>
  </div>
)}


          {/* BACKUP CODE VERIFICATION */}
          {selectedMethod === 'backup' && (
            <div className="verification-content">
              <div className="backup-section">
                <FaKey className="backup-icon" />
                <h3>Enter your backup code</h3>
                <input
                  type="text"
                  className="backup-input"
                  value={backupCode}
                  onChange={(e) => setBackupCode(e.target.value.toUpperCase())}
                  placeholder="XXXXXXXX"
                  autoFocus
                />
                <p className="backup-hint">Each code can only be used once</p>
              </div>
              <div className="action-buttons">
                <button 
                  onClick={verifyBackupCode} 
                  className="btn btn-primary btn-large" 
                  disabled={verifying || backupCode.length < 6}
                >
                  {verifying ? <><FaSpinner className="spinner-icon" /> Verifying...</> : <><FaCheckCircle /> Verify</>}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MFAVerifyPage;
