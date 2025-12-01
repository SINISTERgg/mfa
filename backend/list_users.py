from app import app, db
from models import User

with app.app_context():
    users = User.query.all()
    
    if users:
        print(f"\n📋 Found {len(users)} user(s) in database:\n")
        for user in users:
            print(f"  ID: {user.id}")
            print(f"  Username: {user.username}")
            print(f"  Email: {user.email}")
            print(f"  Created: {user.created_at if hasattr(user, 'created_at') else 'N/A'}")
            print("-" * 50)
    else:
        print("❌ No users found in database!")
