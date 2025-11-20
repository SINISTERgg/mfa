import React from 'react';
import { copyToClipboard, downloadTextFile } from '../utils/helpers';
import './BackupCodes.css';

const BackupCodes = ({ codes }) => {
  const handleCopyAll = () => {
    const text = codes.join('\n');
    copyToClipboard(text);
    alert('Backup codes copied to clipboard!');
  };

  const handleDownload = () => {
    const text = `MFA Backup Codes\n\nThese codes can be used to access your account if you lose access to your other authentication methods.\n\n${codes.join(
      '\n'
    )}\n\nKeep these codes safe and secure!`;
    downloadTextFile('mfa-backup-codes.txt', text);
  };

  return (
    <div className="backup-codes">
      <div className="backup-codes-header">
        <h3>Your Backup Codes</h3>
        <p>Save these codes in a safe place. Each code can only be used once.</p>
      </div>
      <div className="codes-grid">
        {codes.map((code, index) => (
          <div key={index} className="code-item">
            <span className="code-number">{index + 1}.</span>
            <code className="code-value">{code}</code>
          </div>
        ))}
      </div>
      <div className="codes-actions">
        <button onClick={handleCopyAll} className="btn btn-secondary">
          📋 Copy All
        </button>
        <button onClick={handleDownload} className="btn btn-primary">
          💾 Download
        </button>
      </div>
      <div className="codes-warning">
        <p>⚠️ Store these codes securely. They won't be shown again!</p>
      </div>
    </div>
  );
};

export default BackupCodes;
