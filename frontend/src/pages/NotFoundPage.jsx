import {
  FaArrowLeft,
  FaExclamationTriangle,
  FaHome,
  FaShieldAlt
} from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';
import './NotFoundPage.css';

const NotFoundPage = () => {
  const navigate = useNavigate();

  return (
    <div className="notfound-container">
      <div className="notfound-background">
        <div className="gradient-orb orb-1"></div>
        <div className="gradient-orb orb-2"></div>
      </div>

      <div className="notfound-content">
        <div className="notfound-icon">
          <FaExclamationTriangle />
        </div>

        <div className="error-code">404</div>
        
        <h1 className="notfound-title">Page Not Found</h1>
        
        <p className="notfound-description">
          Oops! The page you're looking for doesn't exist or has been moved. 
          Let's get you back on track.
        </p>

        <div className="notfound-actions">
          <button onClick={() => navigate(-1)} className="btn btn-secondary btn-large">
            <FaArrowLeft />
            Go Back
          </button>
          <button onClick={() => navigate('/')} className="btn btn-primary btn-large">
            <FaHome />
            Back to Home
          </button>
        </div>

        <div className="notfound-footer">
          <FaShieldAlt className="footer-icon" />
          <span>MFA Authentication System</span>
        </div>
      </div>
    </div>
  );
};

export default NotFoundPage;
