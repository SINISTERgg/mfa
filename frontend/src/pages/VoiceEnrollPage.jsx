import { useEffect, useRef, useState } from 'react';
import {
  FaArrowLeft,
  FaCheck,
  FaCheckCircle,
  FaExclamationCircle,
  FaMicrophone,
  FaPlay,
  FaRedo,
  FaShieldAlt,
  FaStop
} from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import api from '../services/api';
import './VoiceEnrollPage.css';

const VoiceEnrollPage = () => {
  const navigate = useNavigate();
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  
  const [step, setStep] = useState(1); // 1: Record, 2: Verify, 3: Complete
  const [recording, setRecording] = useState(false);
  const [recordedAudio, setRecordedAudio] = useState(null);
  const [audioBlob, setAudioBlob] = useState(null);
  const [enrolling, setEnrolling] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const passphrase = "The quick brown fox jumps over the lazy dog";

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      navigate('/login');
    }
  }, [navigate]);

  useEffect(() => {
    let interval;
    if (recording) {
      interval = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
    } else {
      setRecordingTime(0);
    }
    return () => clearInterval(interval);
  }, [recording]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        const audioUrl = URL.createObjectURL(audioBlob);
        setRecordedAudio(audioUrl);
        setAudioBlob(audioBlob);
        setStep(2);
        
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setRecording(true);
    } catch (error) {
      toast.error('Microphone access denied');
      console.error('Error accessing microphone:', error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  };

  const retakeRecording = () => {
    setRecordedAudio(null);
    setAudioBlob(null);
    setStep(1);
    setRecordingTime(0);
  };

  const playAudio = () => {
    if (recordedAudio) {
      const audio = new Audio(recordedAudio);
      setIsPlaying(true);
      audio.play();
      audio.onended = () => setIsPlaying(false);
    }
  };

  const handleEnroll = async () => {
    if (!audioBlob) {
      toast.error('Please record your voice first');
      return;
    }

    setEnrolling(true);
    try {
      const reader = new FileReader();
      reader.readAsDataURL(audioBlob);
      reader.onloadend = async () => {
        const base64Audio = reader.result;

        await api.post('/user/enroll/voice', {
          voice_audio: base64Audio
        });

        setStep(3);
        toast.success('✅ Voice enrolled successfully!');
        
        setTimeout(() => {
          navigate('/settings');
        }, 2000);
      };
    } catch (error) {
      toast.error(error.response?.data?.error || 'Enrollment failed');
      setEnrolling(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="voice-enroll-container">
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
            <div className="header-icon-large voice-icon">
              <FaMicrophone />
            </div>
            <h1>Voice Recognition Enrollment</h1>
            <p>Record your voice for biometric authentication</p>
          </div>

          {/* Progress Steps */}
          <div className="progress-steps-modern">
            <div className={`step-item ${step >= 1 ? 'active' : ''} ${step > 1 ? 'completed' : ''}`}>
              <div className="step-circle">
                {step > 1 ? <FaCheck /> : '1'}
              </div>
              <div className="step-label">Record</div>
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

          {/* Recording Area */}
          <div className="recording-section-modern">
            {step === 1 && (
              <div className="recording-area">
                <div className="passphrase-box">
                  <div className="passphrase-label">
                    <FaExclamationCircle /> Please read aloud:
                  </div>
                  <div className="passphrase-text">
                    "{passphrase}"
                  </div>
                </div>

                <div className="microphone-visual">
                  <div className={`mic-circle ${recording ? 'recording' : ''}`}>
                    <FaMicrophone className="mic-icon" />
                  </div>
                  {recording && (
                    <div className="recording-waves">
                      <div className="wave"></div>
                      <div className="wave"></div>
                      <div className="wave"></div>
                    </div>
                  )}
                </div>

                {recording && (
                  <div className="recording-timer">
                    <div className="timer-dot"></div>
                    Recording: {formatTime(recordingTime)}
                  </div>
                )}
              </div>
            )}

            {step === 2 && recordedAudio && (
              <div className="preview-area">
                <div className="audio-preview">
                  <div className="audio-player-visual">
                    <div className={`play-button ${isPlaying ? 'playing' : ''}`} onClick={playAudio}>
                      <FaPlay />
                    </div>
                    <div className="audio-waveform">
                      <div className="waveform-bars">
                        {[...Array(20)].map((_, i) => (
                          <div key={i} className="waveform-bar" style={{
                            height: `${Math.random() * 60 + 40}%`
                          }}></div>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="audio-duration">
                    Duration: {formatTime(recordingTime)}
                  </div>
                </div>

                <div className="passphrase-verification">
                  <FaCheckCircle className="verify-icon" />
                  <p>Voice sample recorded successfully!</p>
                  <div className="passphrase-spoken">
                    "{passphrase}"
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
                <p>Your voice has been successfully enrolled</p>
                <div className="success-details">
                  <div className="detail-item">
                    <FaShieldAlt /> Secure encryption enabled
                  </div>
                  <div className="detail-item">
                    <FaCheckCircle /> Voice pattern stored safely
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
                  <div className="instruction-icon">🎤</div>
                  <span>Speak clearly into the microphone</span>
                </div>
                <div className="instruction-item">
                  <div className="instruction-icon">📖</div>
                  <span>Read the passphrase naturally</span>
                </div>
                <div className="instruction-item">
                  <div className="instruction-icon">🔇</div>
                  <span>Find a quiet environment</span>
                </div>
                <div className="instruction-item">
                  <div className="instruction-icon">🗣️</div>
                  <span>Use your normal speaking voice</span>
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="action-buttons-modern">
            {step === 1 && (
              <button 
                onClick={recording ? stopRecording : startRecording}
                className={`btn-primary-modern btn-large ${recording ? 'recording-btn' : ''}`}
              >
                {recording ? (
                  <>
                    <FaStop /> Stop Recording
                  </>
                ) : (
                  <>
                    <FaMicrophone /> Start Recording
                  </>
                )}
              </button>
            )}

            {step === 2 && (
              <div className="button-group-modern">
                <button 
                  onClick={retakeRecording}
                  className="btn-secondary-modern"
                >
                  <FaRedo /> Record Again
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

export default VoiceEnrollPage;
