# 🔐 Advanced Multi-Factor Authentication System

A comprehensive biometric authentication system featuring Face Recognition, Voice Recognition, OTP/TOTP, Keystroke Dynamics, and Gesture Recognition.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![React](https://img.shields.io/badge/react-18.0+-blue.svg)

## ✨ Features

- 🖼️ **Face Recognition** - Using face_recognition library with 128-dimensional embeddings
- 🎤 **Voice Recognition** - Audio fingerprinting with strict verification (92% threshold)
- 📱 **OTP/TOTP** - Time-based one-time passwords with QR code enrollment
- ⌨️ **Keystroke Dynamics** - ML-based typing pattern analysis
- ✋ **Gesture Recognition** - Motion pattern authentication with canvas drawing
- 🔑 **Backup Codes** - Emergency access recovery codes
- 📊 **Login History** - Track authentication attempts and methods
- 🔒 **JWT Authentication** - Secure token-based session management

## 🏗️ Architecture

### Backend (Flask)

- Python 3.8+
- Flask REST API
- SQLAlchemy ORM
- JWT token authentication
- Biometric data processing services

### Frontend (React)

- React 18
- React Router for navigation
- Axios for API calls
- Modern responsive UI

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- pip (Python package manager)
- npm or yarn

### Backend Setup

cd backend

Create virtual environment
python -m venv venv

Activate virtual environment
Windows:
venv\Scripts\activate

macOS/Linux:
source venv/bin/activate

Install dependencies
pip install -r requirements.txt

Run the server
python app.py

text

Backend will run on `http://localhost:5000`

### Frontend Setup

cd frontend

Install dependencies
npm install

Start development server
npm start

text

Frontend will run on `http://localhost:3000`

## 🔧 Configuration

### Backend Environment Variables

Create `.env` file in `backend/` directory:

SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
DATABASE_URI=sqlite:///mfa_auth.db

text

### Frontend Environment Variables

Create `.env` file in `frontend/` directory:

REACT_APP_API_URL=http://localhost:5000

text

## 📚 API Documentation

### Authentication Endpoints

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login (step 1: password)
- `POST /api/auth/mfa/verify-face` - Verify face
- `POST /api/auth/mfa/verify-voice` - Verify voice
- `POST /api/auth/mfa/verify-otp` - Verify OTP
- `POST /api/auth/mfa/verify-gesture` - Verify gesture
- `POST /api/auth/mfa/verify-keystroke` - Verify keystroke
- `POST /api/auth/mfa/verify-backup-code` - Verify backup code

### User Endpoints

- `GET /api/user/profile` - Get user profile
- `POST /api/user/enroll/face` - Enroll face
- `POST /api/user/enroll/voice` - Enroll voice
- `POST /api/user/enroll/otp` - Enroll OTP
- `POST /api/user/enroll/gesture` - Enroll gesture
- `POST /api/user/enroll/keystroke` - Enroll keystroke
- `POST /api/user/unenroll/{method}` - Remove authentication method

## 🧪 Testing

### Register a User

1. Navigate to `http://localhost:3000/register`
2. Fill in username, email, and password
3. Save the backup codes provided

### Enroll Biometric Methods

1. Login with credentials
2. Go to Settings
3. Enroll desired authentication methods
4. Test each method during login

## 📁 Project Structure

mfa-authentication-system/
├── backend/
│ ├── routes/
│ │ ├── auth.py # Authentication routes
│ │ ├── user.py # User management routes
│ │ └── device.py # Device fingerprinting
│ ├── services/
│ │ ├── face_recognition.py # Face recognition service
│ │ ├── voice_recognition.py # Voice recognition service
│ │ ├── gesture_recognition.py # Gesture service
│ │ └── keystroke_service.py # Keystroke dynamics
│ ├── app.py # Flask application
│ ├── models.py # Database models
│ └── requirements.txt # Python dependencies
├── frontend/
│ ├── public/
│ ├── src/
│ │ ├── components/ # React components
│ │ ├── pages/ # Page components
│ │ ├── services/ # API services
│ │ └── context/ # React context
│ └── package.json # Node dependencies
└── README.md

text

## 🔒 Security Features

- Password hashing with Werkzeug
- JWT token-based authentication
- Biometric data encryption
- Secure session management
- Failed login attempt tracking
- Rate limiting (optional)
- CORS configuration

## 🚀 Deployment

### Backend Deployment

1. Set production environment variables
2. Use Gunicorn for production server
3. Configure reverse proxy (Nginx)
4. Enable HTTPS

### Frontend Deployment

1. Build production bundle: `npm run build`
2. Deploy to hosting service (Vercel, Netlify, etc.)
3. Configure API URL for production

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👤 Author

Hoysala Sathyanarayana - https://github.com/SINISTERgg

## 🙏 Acknowledgments

- face_recognition library by Adam Geitgey
- Flask framework
- React framework

- OpenCV for image processing
