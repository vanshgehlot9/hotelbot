import os
import sys
from dotenv import load_dotenv

# Ensure we can import from app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from app.core.security import get_password_hash
from app.db.firebase import get_db

def main():
    print("=== Super Admin Registration ===")
    if len(sys.argv) < 3:
        print("Usage: python create_superadmin.py <email> <password>")
        return
        
    email = sys.argv[1].strip()
    password = sys.argv[2].strip()
    if len(password) < 6:
        print("Password must be at least 6 characters.")
        return
        
    db = get_db()
    if not db:
        print("Failed to connect to Firestore.")
        return
        
    hashed = get_password_hash(password)
    
    user_doc = {
        "email": email,
        "hashed_password": hashed,
        "role": "superadmin",
        "tenant_id": "platform"
    }
    
    db.collection("users").document(email).set(user_doc)
    print(f"\n✅ Super Admin account created successfully for {email}!")

if __name__ == "__main__":
    main()
