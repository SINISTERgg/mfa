import { useRef, useState } from 'react';
import './KeystrokeDynamicsAdvanced.css';

const KeystrokeDynamicsAdvanced = ({ onCapture, buttonText = 'Enroll Pattern', mode = 'enroll' }) => {
  const [passphrase, setPassphrase] = useState('');
  const [samples, setSamples] = useState([]);
  const [currentSample, setCurrentSample] = useState(0);
  const [isCapturing, setIsCapturing] = useState(false);
  const [currentInput, setCurrentInput] = useState('');
  const [keystrokeData, setKeystrokeData] = useState([]);
  
  const lastKeyTime = useRef(null);
  const keyDownTimes = useRef({});
  const requiredSamples = mode === 'enroll' ? 5 : 1;

  const startCapture = () => {
    if (passphrase.length < 8) {
      alert('Passphrase must be at least 8 characters');
      return;
    }
    setIsCapturing(true);
    setCurrentSample(0);
    setSamples([]);
    setCurrentInput('');
    setKeystrokeData([]);
  };

  const handleKeyDown = (e) => {
    if (!isCapturing) return;
    
    const key = e.key;
    const timestamp = Date.now();
    
    // Record key down time
    keyDownTimes.current[key] = timestamp;
    
    // Calculate flight time (time since last key was released)
    const flightTime = lastKeyTime.current ? timestamp - lastKeyTime.current : 0;
    
    // Add timing data
    setKeystrokeData(prev => [
      ...prev,
      {
        key: key,
        timestamp: timestamp,
        flightTime: flightTime,
        holdTime: 0, // Will be updated on keyup
        sampleIndex: currentSample
      }
    ]);
  };

  const handleKeyUp = (e) => {
    if (!isCapturing) return;
    
    const key = e.key;
    const timestamp = Date.now();
    const keyDownTime = keyDownTimes.current[key];
    
    if (keyDownTime) {
      const holdTime = timestamp - keyDownTime;
      
      // Update the last keystroke data with hold time
      setKeystrokeData(prev => {
        const updated = [...prev];
        // Find the last occurrence of this key
        for (let i = updated.length - 1; i >= 0; i--) {
          if (updated[i].key === key && updated[i].holdTime === 0) {
            updated[i].holdTime = holdTime;
            break;
          }
        }
        return updated;
      });
      
      lastKeyTime.current = timestamp;
      delete keyDownTimes.current[key];
    }
  };

  const handleInputChange = (e) => {
    const value = e.target.value;
    setCurrentInput(value);
    
    // Check if sample is complete
    if (value === passphrase) {
      completeSample();
    }
  };

  const completeSample = () => {
    // Extract timings for this sample
    const sampleTimings = keystrokeData.filter(t => t.sampleIndex === currentSample);
    
    const newSample = {
      passphrase: passphrase,
      timings: sampleTimings,
      timestamp: Date.now()
    };
    
    const newSamples = [...samples, newSample];
    setSamples(newSamples);
    
    if (currentSample + 1 < requiredSamples) {
      // Move to next sample
      setCurrentSample(currentSample + 1);
      setCurrentInput('');
      setKeystrokeData([]);
      lastKeyTime.current = null;
      keyDownTimes.current = {};
    } else {
      // All samples collected
      finishCapture(newSamples);
    }
  };

  const finishCapture = async (allSamples) => {
    setIsCapturing(false);
    
    // Calculate pattern strength for feedback
    if (mode === 'enroll') {
      // Send to parent component
      onCapture({
        samples: allSamples,
        passphrase: passphrase
      });
    } else {
      // Verification mode - send single sample
      onCapture({
        keystroke: allSamples[0],
        passphrase: passphrase
      });
    }
  };

  const reset = () => {
    setPassphrase('');
    setSamples([]);
    setCurrentSample(0);
    setIsCapturing(false);
    setCurrentInput('');
    setKeystrokeData([]);
    lastKeyTime.current = null;
    keyDownTimes.current = {};
  };

  const getProgressPercentage = () => {
    return ((currentSample + (currentInput.length / passphrase.length)) / requiredSamples) * 100;
  };

  return (
    <div className="keystroke-dynamics-advanced">
      {!isCapturing ? (
        <div className="keystroke-setup">
          <div className="info-card">
            <h4>🎯 How Keystroke Dynamics Works:</h4>
            <ul>
              <li>Measures your unique typing rhythm and patterns</li>
              <li>Captures timing between keystrokes (flight time)</li>
              <li>Records how long you hold each key (dwell time)</li>
              <li>Creates a behavioral biometric profile</li>
            </ul>
          </div>
          
          <div className="form-group">
            <label htmlFor="passphrase">
              {mode === 'enroll' ? 'Create Your Passphrase:' : 'Enter Your Passphrase:'}
            </label>
            <input
              type="text"
              id="passphrase"
              value={passphrase}
              onChange={(e) => setPassphrase(e.target.value)}
              placeholder="Type a memorable phrase (min 8 characters)"
              className="passphrase-input"
              disabled={isCapturing}
            />
            <p className="hint">
              {mode === 'enroll' 
                ? 'Choose something easy to remember - you\'ll type it 5 times' 
                : 'Type the same passphrase you used during enrollment'}
            </p>
          </div>
          
          <button
            onClick={startCapture}
            disabled={passphrase.length < 8}
            className="btn btn-primary btn-large"
          >
            {mode === 'enroll' ? '🚀 Start Enrollment' : '🔐 Start Verification'}
          </button>
        </div>
      ) : (
        <div className="keystroke-capture">
          <div className="capture-header">
            <h3>
              {mode === 'enroll' 
                ? `Sample ${currentSample + 1} of ${requiredSamples}` 
                : 'Verify Your Pattern'}
            </h3>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${getProgressPercentage()}%` }}
              />
            </div>
          </div>
          
          <div className="typing-area">
            <p className="instruction">Type your passphrase naturally:</p>
            <div className="passphrase-display">
              <span className="passphrase-text">{passphrase}</span>
            </div>
            
            <input
              type="password"
              value={currentInput}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              onKeyUp={handleKeyUp}
              placeholder="Start typing..."
              className="typing-input"
              autoFocus
            />
            
            <div className="typing-feedback">
              <span className={`char-count ${currentInput.length === passphrase.length ? 'complete' : ''}`}>
                {currentInput.length} / {passphrase.length} characters
              </span>
              {currentInput === passphrase && (
                <span className="match-indicator">✓ Match!</span>
              )}
            </div>
          </div>
          
          {samples.length > 0 && mode === 'enroll' && (
            <div className="samples-collected">
              <p>✅ Samples collected: {samples.length}/{requiredSamples}</p>
            </div>
          )}
          
          <div className="capture-actions">
            <button onClick={reset} className="btn btn-secondary">
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default KeystrokeDynamicsAdvanced;
