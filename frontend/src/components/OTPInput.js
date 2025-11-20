import React, { useState, useRef } from 'react';
import './OTPInput.css';

const OTPInput = ({ length = 6, onComplete }) => {
  const [otp, setOtp] = useState(new Array(length).fill(''));
  const inputRefs = useRef([]);

  const handleChange = (index, value) => {
    if (isNaN(value)) return;

    const newOtp = [...otp];
    newOtp[index] = value.substring(value.length - 1);
    setOtp(newOtp);

    // Auto-focus next input
    if (value && index < length - 1) {
      inputRefs.current[index + 1].focus();
    }

    // Check if OTP is complete
    const otpString = newOtp.join('');
    if (otpString.length === length) {
      onComplete(otpString);
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1].focus();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pasteData = e.clipboardData.getData('text').slice(0, length);
    const newOtp = [...otp];

    for (let i = 0; i < pasteData.length; i++) {
      if (isNaN(pasteData[i])) continue;
      newOtp[i] = pasteData[i];
    }

    setOtp(newOtp);

    // Focus last filled input or next empty
    const lastFilledIndex = Math.min(pasteData.length, length - 1);
    inputRefs.current[lastFilledIndex].focus();

    // Check if OTP is complete
    const otpString = newOtp.join('');
    if (otpString.length === length) {
      onComplete(otpString);
    }
  };

  return (
    <div className="otp-input-container">
      {otp.map((digit, index) => (
        <input
          key={index}
          ref={(ref) => (inputRefs.current[index] = ref)}
          type="text"
          inputMode="numeric"
          maxLength={1}
          value={digit}
          onChange={(e) => handleChange(index, e.target.value)}
          onKeyDown={(e) => handleKeyDown(index, e)}
          onPaste={handlePaste}
          className="otp-input"
        />
      ))}
    </div>
  );
};

export default OTPInput;
