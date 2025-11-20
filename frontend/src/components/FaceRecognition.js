import { useEffect, useRef, useState } from 'react';
import './FaceRecognition.css';

const FaceRecognition = ({ onCapture, buttonText = 'Capture Face' }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const [capturing, setCapturing] = useState(false);
  const [error, setError] = useState('');
  const [cameraReady, setCameraReady] = useState(false);

  useEffect(() => {
    let mounted = true;

    const startCamera = async () => {
      try {
        console.log('📷 [CAMERA] Requesting camera access...');
        
        const mediaStream = await navigator.mediaDevices.getUserMedia({
          video: { 
            width: { ideal: 640 },
            height: { ideal: 480 },
            facingMode: 'user'
          },
          audio: false
        });

        if (!mounted) {
          mediaStream.getTracks().forEach(track => track.stop());
          return;
        }

        console.log('✅ [CAMERA] Stream obtained');
        streamRef.current = mediaStream;
        
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
          
          videoRef.current.onloadedmetadata = () => {
            console.log('✅ [VIDEO] Metadata loaded');
            
            if (videoRef.current && mounted) {
              videoRef.current.play()
                .then(() => {
                  console.log('✅ [VIDEO] Playing');
                  if (mounted) {
                    setCameraReady(true);
                    setError('');
                  }
                })
                .catch(err => {
                  console.error('❌ [VIDEO] Play failed:', err);
                  if (mounted) {
                    setError('Failed to play video stream');
                  }
                });
            }
          };
        }
        
        console.log('✅ [CAMERA] Setup complete');
        
      } catch (err) {
        console.error('❌ [CAMERA ERROR]', err);
        
        if (!mounted) return;
        
        if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
          setError('Camera permission denied. Please allow camera access.');
        } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
          setError('No camera found. Please connect a camera.');
        } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
          setError('Camera is already in use.');
        } else {
          setError(`Camera error: ${err.message}`);
        }
      }
    };

    startCamera();

    return () => {
      mounted = false;
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => {
          track.stop();
          console.log('📷 [CAMERA] Track stopped');
        });
        streamRef.current = null;
      }
      setCameraReady(false);
    };
  }, []); // Run once on mount

  const captureImage = async () => {
    if (!videoRef.current || !canvasRef.current) {
      setError('Camera not ready');
      return;
    }

    if (!cameraReady) {
      setError('Please wait for camera to initialize');
      return;
    }

    setCapturing(true);
    setError('');

    try {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const context = canvas.getContext('2d');

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      console.log('📸 [CAPTURE] Video dimensions:', video.videoWidth, 'x', video.videoHeight);

      if (video.videoWidth === 0 || video.videoHeight === 0) {
        throw new Error('Video not ready - dimensions are 0');
      }

      context.drawImage(video, 0, 0, canvas.width, canvas.height);
      const base64Image = canvas.toDataURL('image/jpeg', 0.95);

      console.log('✅ [CAPTURE] Success');
      console.log('📏 [SIZE]', base64Image.length, 'characters');

      if (onCapture) {
        onCapture(base64Image);
      }
    } catch (err) {
      console.error('❌ [CAPTURE ERROR]', err);
      setError('Failed to capture image. Please try again.');
    } finally {
      setCapturing(false);
    }
  };

  const retryCamera = () => {
    setError('');
    setCameraReady(false);
    window.location.reload(); // Simple but effective
  };

  return (
    <div className="face-recognition">
      <div className="camera-container">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="camera-video"
        />
        <canvas ref={canvasRef} style={{ display: 'none' }} />
        
        {!cameraReady && !error && (
          <div className="camera-loading">
            <div className="spinner"></div>
            <p>Initializing camera...</p>
          </div>
        )}
      </div>

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      {!error && cameraReady && (
        <p className="camera-status">
          ✅ Camera ready
        </p>
      )}

      <button
        onClick={captureImage}
        disabled={capturing || !cameraReady || !!error}
        className="btn btn-primary capture-btn"
      >
        {capturing ? '📸 Capturing...' : buttonText}
      </button>

      {error && (
        <button
          onClick={retryCamera}
          className="btn btn-secondary capture-btn"
        >
          🔄 Retry Camera
        </button>
      )}
    </div>
  );
};

export default FaceRecognition;
