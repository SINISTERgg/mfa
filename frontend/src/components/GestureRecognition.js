import { useEffect, useRef, useState } from 'react';
import './GestureRecognition.css';

const GestureRecognition = ({ onCapture, buttonText = 'Capture Gesture', mode = 'enroll' }) => {
  const canvasRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [points, setPoints] = useState([]);
  const [gestureStartTime, setGestureStartTime] = useState(null);
  const [error, setError] = useState('');
  const [status, setStatus] = useState('idle'); // idle, drawing, captured

  useEffect(() => {
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      ctx.strokeStyle = '#667eea';
      ctx.lineWidth = 3;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
    }
  }, []);

  const getCoordinates = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    
    if (e.touches && e.touches[0]) {
      return {
        x: e.touches[0].clientX - rect.left,
        y: e.touches[0].clientY - rect.top
      };
    }
    
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    };
  };

  const startDrawing = (e) => {
    e.preventDefault();
    setIsDrawing(true);
    setStatus('drawing');
    setGestureStartTime(Date.now());
    setError('');
    
    const { x, y } = getCoordinates(e);
    const newPoint = { x, y, timestamp: Date.now() };
    setPoints([newPoint]);
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.beginPath();
    ctx.moveTo(x, y);
    
    console.log('✋ [GESTURE] Started drawing');
  };

  const draw = (e) => {
    if (!isDrawing) return;
    e.preventDefault();
    
    const { x, y } = getCoordinates(e);
    const newPoint = { x, y, timestamp: Date.now() };
    
    setPoints(prevPoints => [...prevPoints, newPoint]);
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.lineTo(x, y);
    ctx.stroke();
  };

  const stopDrawing = (e) => {
    if (!isDrawing) return;
    e.preventDefault();
    
    setIsDrawing(false);
    setStatus('captured');
    
    const duration = Date.now() - gestureStartTime;
    console.log('✅ [GESTURE] Drawing completed');
    console.log(`📊 [STATS] Points: ${points.length}, Duration: ${duration}ms`);
    
    if (points.length < 10) {
      setError('Gesture too short. Please draw a more complex pattern.');
      clearCanvas();
      return;
    }
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setPoints([]);
    setStatus('idle');
    setError('');
    console.log('🗑️ [GESTURE] Canvas cleared');
  };

  const captureGesture = () => {
    if (points.length < 10) {
      setError('Please draw a gesture first');
      return;
    }
    
    console.log('📤 [CAPTURE] Sending gesture data...');
    console.log(`📏 [SIZE] ${points.length} points`);
    
    const gestureData = {
      points: points,
      duration: points[points.length - 1].timestamp - points[0].timestamp,
      canvas_width: canvasRef.current.width,
      canvas_height: canvasRef.current.height
    };
    
    if (onCapture) {
      onCapture(gestureData);
    }
    
    // Clear for next capture
    clearCanvas();
  };

  return (
    <div className="gesture-recognition">
      <div className="gesture-instructions">
        <h3>Draw Your Gesture Pattern</h3>
        <p>
          {mode === 'enroll' 
            ? 'Draw a unique gesture pattern on the canvas below. This will be your gesture authentication.'
            : 'Draw your registered gesture pattern to authenticate.'
          }
        </p>
        <div className="gesture-tips">
          <span className="tip">💡 Tip: Draw something unique and memorable</span>
          <span className="tip">✏️ Use mouse or touch to draw</span>
        </div>
      </div>

      <div className="gesture-canvas-container">
        <canvas
          ref={canvasRef}
          width={400}
          height={400}
          className="gesture-canvas"
          onMouseDown={startDrawing}
          onMouseMove={draw}
          onMouseUp={stopDrawing}
          onMouseLeave={stopDrawing}
          onTouchStart={startDrawing}
          onTouchMove={draw}
          onTouchEnd={stopDrawing}
        />
        
        {status === 'idle' && (
          <div className="canvas-overlay">
            <p>Click or tap to start drawing</p>
          </div>
        )}
        
        {status === 'drawing' && (
          <div className="drawing-indicator">
            <div className="pulse"></div>
            <span>Drawing... ({points.length} points)</span>
          </div>
        )}
      </div>

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      {points.length > 0 && (
        <div className="gesture-info">
          <span>Points: {points.length}</span>
          {gestureStartTime && status === 'captured' && (
            <span>Duration: {((points[points.length - 1].timestamp - points[0].timestamp) / 1000).toFixed(2)}s</span>
          )}
        </div>
      )}

      <div className="gesture-actions">
        <button
          onClick={captureGesture}
          disabled={points.length < 10}
          className="btn btn-primary"
        >
          {buttonText}
        </button>
        
        <button
          onClick={clearCanvas}
          disabled={points.length === 0}
          className="btn btn-secondary"
        >
          Clear
        </button>
      </div>
    </div>
  );
};

export default GestureRecognition;
  