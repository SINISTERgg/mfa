import { useRef, useState } from 'react';
import './VoiceRecognition.css';

const VoiceRecognition = ({ onCapture, buttonText = 'Capture Voice' }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [error, setError] = useState('');
  const [recordingTime, setRecordingTime] = useState(0);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);

  const startRecording = async () => {
    try {
      console.log('🎤 [RECORD] Starting recording...');
      
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];
      
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };
      
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
        console.log('✅ [RECORD] Recording stopped');
        console.log('📏 [SIZE]', blob.size, 'bytes');
        
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.start();
      setIsRecording(true);
      setError('');
      setRecordingTime(0);
      
      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
      
      console.log('🎤 [RECORD] Recording started');
    } catch (err) {
      console.error('❌ [ERROR]', err);
      setError('Microphone access denied. Please allow microphone permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }
  };

  const captureVoice = async () => {
    if (!audioBlob) {
      setError('Please record audio first');
      return;
    }

    console.log('📤 [CAPTURE] Converting audio to base64...');
    
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64Audio = reader.result;
      console.log('✅ [CAPTURE] Conversion complete');
      console.log('📏 [SIZE]', base64Audio.length, 'characters');
      
      if (onCapture) {
        onCapture(base64Audio);
      }
      
      // Reset
      setAudioBlob(null);
      setRecordingTime(0);
    };
    
    reader.readAsDataURL(audioBlob);
  };

  const clearRecording = () => {
    setAudioBlob(null);
    setRecordingTime(0);
    setError('');
  };

  return (
    <div className="voice-recognition">
      <div className="voice-instructions">
        <h3>Record Your Voice</h3>
        <p>Speak clearly for 3-5 seconds. Say a phrase you'll remember.</p>
      </div>

      <div className="recording-visualizer">
        {isRecording ? (
          <div className="recording-active">
            <div className="pulse-ring"></div>
            <div className="pulse-ring delay-1"></div>
            <div className="pulse-ring delay-2"></div>
            <div className="mic-icon">🎤</div>
            <div className="recording-time">{recordingTime}s</div>
          </div>
        ) : audioBlob ? (
          <div className="recording-ready">
            <div className="check-icon">✅</div>
            <p>Recording ready ({recordingTime}s)</p>
          </div>
        ) : (
          <div className="recording-idle">
            <div className="mic-icon-large">🎤</div>
            <p>Click to start recording</p>
          </div>
        )}
      </div>

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      <div className="voice-actions">
        {!isRecording && !audioBlob && (
          <button
            onClick={startRecording}
            className="btn btn-primary"
          >
            Start Recording
          </button>
        )}

        {isRecording && (
          <button
            onClick={stopRecording}
            className="btn btn-danger"
          >
            Stop Recording
          </button>
        )}

        {audioBlob && (
          <>
            <button
              onClick={captureVoice}
              className="btn btn-primary"
            >
              {buttonText}
            </button>
            <button
              onClick={clearRecording}
              className="btn btn-secondary"
            >
              Clear
            </button>
          </>
        )}
      </div>
    </div>
  );
};

export default VoiceRecognition;
