import { Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// Import pages
import BackupCodesPage from './pages/BackupCodesPage';
import DashboardPage from './pages/DashboardPage';
import HomePage from './pages/HomePage';
import LoginHistoryPage from './pages/LoginHistoryPage';
import LoginPage from './pages/LoginPage';
import MFASelectPage from './pages/MFASelectPage';
import MFAVerifyPage from './pages/MFAVerifyPage';
import NotFoundPage from './pages/NotFoundPage';
import RegisterPage from './pages/RegisterPage';
import SettingsPage from './pages/SettingsPage';

// Import enrollment pages
import FaceEnrollPage from './pages/FaceEnrollPage';
import GestureEnrollPage from './pages/GestureEnrollPage';
import KeystrokeEnrollPage from './pages/KeystrokeEnrollPage';
import OTPEnrollPage from './pages/OTPEnrollPage';
import VoiceEnrollPage from './pages/VoiceEnrollPage';

function App() {
  return (
    <Router>
      <ToastContainer
        position="top-right"
        autoClose={3000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="light"
      />
      
      <Routes>
        {/* Main Pages */}
        <Route path="/mfa/verify" element={<MFAVerifyPage />} />
        <Route path="/mfa-select" element={<MFASelectPage />} />
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/backup-codes" element={<BackupCodesPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/login-history" element={<LoginHistoryPage />} />
        {/* Enrollment Pages */}
        <Route path="/enroll/face" element={<FaceEnrollPage />} />
        <Route path="/enroll/voice" element={<VoiceEnrollPage />} />
        <Route path="/enroll/gesture" element={<GestureEnrollPage />} />
        <Route path="/enroll/keystroke" element={<KeystrokeEnrollPage />} />
        <Route path="/enroll/otp" element={<OTPEnrollPage />} />
        {/* 404 */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Router>
  );
}

export default App;
