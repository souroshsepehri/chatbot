"""Script to create initial admin user"""
from app.db.session import SessionLocal
from app.models.admin_user import AdminUser
from app.core.security import hash_password

db = SessionLocal()

username = input("Enter admin username (default: admin): ").strip() or "admin"
password = input("Enter admin password (default: admin123): ").strip() or "admin123"

# Check if user exists
existing = db.query(AdminUser).filter(AdminUser.username == username).first()
if existing:
    print(f"User '{username}' already exists!")
    db.close()
    exit(1)

admin = AdminUser(
    username=username,
    password_hash=hash_password(password)
)
db.add(admin)
db.commit()

print(f"Admin user created successfully!")
print(f"Username: {username}")
print(f"Password: {password}")
print("\n⚠️  Please change the default password after first login!")

db.close()

