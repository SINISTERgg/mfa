import { useEffect, useState } from 'react';
import {
  FaArrowRight,
  FaCheck,
  FaCopy,
  FaDownload,
  FaPrint,
  FaSave,
  FaShieldAlt
} from 'react-icons/fa';
import { useLocation, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import './BackupCodesPage.css';

const BackupCodesPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [copied, setCopied] = useState(false);
  const [saved, setSaved] = useState(false);
  const [backupCodes, setBackupCodes] = useState([]);

  useEffect(() => {
    const codes = location.state?.backupCodes || 
                  JSON.parse(localStorage.getItem('backup_codes') || '[]');
    
    setBackupCodes(codes);
    
    if (codes.length === 0) {
      navigate('/settings');
    }
  }, [location, navigate]);

  const handleCopy = () => {
    const codesText = backupCodes.join('\n');
    navigator.clipboard.writeText(codesText);
    setCopied(true);
    toast.success('Copied to clipboard!');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const codesText = `MFA BACKUP CODES
Generated: ${new Date().toLocaleString()}
DO NOT SHARE THESE CODES

${backupCodes.map((code, index) => `${String(index + 1).padStart(2, '0')}. ${code}`).join('\n')}

IMPORTANT:
- Each code can only be used once
- Store these codes in a secure location
- Treat them like passwords
- You can regenerate new codes from settings
`;
    
    const blob = new Blob([codesText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `mfa-backup-codes-${new Date().getTime()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    toast.success('Backup codes downloaded!');
    setSaved(true);
  };

  const handleSaveToFile = () => {
    handleDownload();
  };

  const handlePrint = () => {
    window.print();
    toast.info('Print dialog opened');
  };

  const handleContinue = () => {
    if (!saved) {
      const confirmed = window.confirm(
        'Have you saved your backup codes? You won\'t be able to see them again!'
      );
      if (!confirmed) return;
    }
    
    localStorage.removeItem('backup_codes');
    navigate('/settings');
  };

  return (
    <div className="backup-codes-container">
      <div className="backup-codes-background">
        <div className="gradient-orb orb-1"></div>
        <div className="gradient-orb orb-2"></div>
      </div>

      <div className="backup-codes-content">
        <div className="backup-codes-card">
          <div className="backup-header">
            <div className="backup-icon">
              <FaShieldAlt />
            </div>
            <h1>Save Your Backup Codes</h1>
            <p>Keep these codes safe - they're your emergency access keys</p>
          </div>

          <div className="warning-banner">
            <span className="warning-icon">⚠️</span>
            <div>
              <strong>Important:</strong> Each code can only be used once. 
              Store them in a secure location like a password manager or save them to a file.
            </div>
          </div>

          <div className="codes-grid">
            {backupCodes.map((code, index) => (
              <div key={index} className="code-item">
                <span className="code-number">{String(index + 1).padStart(2, '0')}</span>
                <span className="code-value">{code}</span>
              </div>
            ))}
          </div>

          <div className="backup-actions">
            <button onClick={handleCopy} className="btn btn-secondary">
              {copied ? (
                <>
                  <FaCheck /> Copied!
                </>
              ) : (
                <>
                  <FaCopy /> Copy All
                </>
              )}
            </button>
            <button onClick={handleSaveToFile} className="btn btn-primary">
              <FaSave /> {saved ? 'Saved!' : 'Save to File'}
            </button>
            <button onClick={handleDownload} className="btn btn-secondary">
              <FaDownload /> Download TXT
            </button>
            <button onClick={handlePrint} className="btn btn-secondary print-btn">
              <FaPrint /> Print
            </button>
          </div>

          <button 
            onClick={handleContinue} 
            className={`btn btn-full btn-continue ${saved ? 'btn-primary' : 'btn-warning'}`}
          >
            {saved ? (
              <>
                Continue to Settings
                <FaArrowRight />
              </>
            ) : (
              <>
                ⚠️ Continue Without Saving
                <FaArrowRight />
              </>
            )}
          </button>

          <div className="backup-footer">
            <p>
              <strong>Tip:</strong> You can regenerate new codes anytime from your settings, 
              which will invalidate these codes. We recommend saving them to a password manager 
              like LastPass, 1Password, or Bitwarden.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BackupCodesPage;
