"""Setup database and create admin user"""
import sys
from app.db.session import SessionLocal, init_db
from app.models.admin_user import AdminUser
from app.core.security import hash_password

def setup_database():
    """Initialize database tables"""
    try:
        print("Initializing database tables...")
        init_db()
        print("✓ Database tables created successfully")
        return True
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        return False

def create_admin_user(username="admin", password="admin123"):
    """Create admin user if it doesn't exist"""
    db = SessionLocal()
    try:
        # Check if user exists
        existing = db.query(AdminUser).filter(AdminUser.username == username).first()
        if existing:
            print(f"✓ Admin user '{username}' already exists")
            return True
        
        # Create admin user
        admin = AdminUser(
            username=username,
            password_hash=hash_password(password)
        )
        db.add(admin)
        db.commit()
        print(f"✓ Admin user created successfully!")
        print(f"  Username: {username}")
        print(f"  Password: {password}")
        print("\n⚠️  Please change the default password after first login!")
        return True
    except Exception as e:
        print(f"✗ Error creating admin user: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 50)
    print("Database Setup Script")
    print("=" * 50)
    
    # Setup database
    if not setup_database():
        sys.exit(1)
    
    # Create admin user
    if not create_admin_user():
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("Setup completed successfully!")
    print("=" * 50)

