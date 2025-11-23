import { QRCodeSVG } from 'qrcode.react';
import './QRCodeDisplay.css';

const QRCodeDisplay = ({ value, secret }) => {
  const copySecret = () => {
    navigator.clipboard.writeText(secret);
    alert('Secret copied to clipboard!');
  };

  return (
    <div className="qrcode-display">
      <div className="qrcode-container">
        <QRCodeSVG value={value} />
      </div>
      <div className="qrcode-instructions">
        <p>Scan this QR code with your authenticator app:</p>
        <ul>
          <li>Google Authenticator</li>
          <li>Authy</li>
          <li>Microsoft Authenticator</li>
        </ul>
      </div>
      {secret && (
        <div className="secret-key">
          <p>Or enter this secret key manually:</p>
          <div className="secret-box">
            <code>{secret}</code>
            <button onClick={copySecret} className="btn-copy">
              📋 Copy
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default QRCodeDisplay;
