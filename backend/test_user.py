import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import everything we need
from models import User, db

# Try to import the Flask app
try:
    from app import app
except ImportError:
    try:
        from app import application as app
    except ImportError:
        try:
            from app import create_app
            app = create_app()
        except ImportError:
            print("❌ Could not import Flask app!")
            print("Please check your app.py file.")
            sys.exit(1)

# Now test with app context
with app.app_context():
    print("\n" + "="*60)
    print("🔍 CHECKING DATABASE FOR USERS")
    print("="*60 + "\n")
    
    # Get all users
    all_users = User.query.all()
    
    if not all_users:
        print("❌ No users found in database!")
        print("\nTry registering a user first from the frontend.")
    else:
        print(f"📋 Found {len(all_users)} user(s):\n")
        
        for user in all_users:
            print(f"{'='*60}")
            print(f"  ID: {user.id}")
            print(f"  Username: {user.username}")
            print(f"  Email: {user.email}")
            print(f"  Password Hash: {user.password_hash[:30]}...")
            
            # Test specific user
            if user.email == 'test@example.com':
                print(f"\n  🔑 Testing password 'Admin@123':")
                result = user.check_password('Admin@123')
                print(f"     Result: {'✅ CORRECT' if result else '❌ INCORRECT'}")
            
            # Check enrolled methods
            print(f"\n  🔐 Enrolled MFA Methods:")
            print(f"     Face: {user.face_enrolled}")
            print(f"     Voice: {user.voice_enrolled}")
            print(f"     Gesture: {user.gesture_enrolled}")
            print(f"     Keystroke: {user.keystroke_enrolled}")
            print(f"     TOTP: {user.totp_enabled}")
            print(f"{'='*60}\n")
    
    print("\n" + "="*60)
    print("DONE")
    print("="*60 + "\n")
