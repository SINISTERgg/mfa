import React from 'react';
import './ProgressBar.css';

const ProgressBar = ({ currentStep, totalSteps, steps }) => {
  const progressPercentage = (currentStep / totalSteps) * 100;

  return (
    <div className="progress-bar-container">
      <div className="progress-bar-track">
        <div
          className="progress-bar-fill"
          style={{ width: `${progressPercentage}%` }}
        ></div>
      </div>
      <div className="progress-steps">
        {steps.map((step, index) => (
          <div
            key={index}
            className={`progress-step ${
              index + 1 <= currentStep ? 'active' : ''
            } ${index + 1 === currentStep ? 'current' : ''}`}
          >
            <div className="step-circle">
              {index + 1 < currentStep ? '✓' : index + 1}
            </div>
            <div className="step-label">{step}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProgressBar;
