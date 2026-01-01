"""
Database seeding script for demo data

Usage:
    python -m app.db.seed
"""

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.kb_qa import KBQA
from app.models.website_source import WebsiteSource
import sys


def seed_qa_items(db: Session):
    """Seed QA items - returns 0 (no demo data seeded)"""
    # No demo data - start with empty KB
    print("  - No demo QA items seeded (starting with empty KB)")
    return 0


def seed_website_source(db: Session):
    """Seed website source - returns None (no demo data seeded)"""
    # No demo data - start with empty website sources
    print("  - No demo website sources seeded (starting with empty sources)")
    return None


def main():
    """Main seeding function"""
    print("🌱 Starting database seeding...\n")
    
    db: Session = SessionLocal()
    try:
        # Seed QA items
        print("❓ Seeding QA items...")
        seed_qa_items(db)
        db.commit()
        print()
        
        # Seed website source
        print("🌐 Seeding website source...")
        seed_website_source(db)
        db.commit()
        print()
        
        print("✅ Database seeding completed successfully!")
        print("\n📊 Summary:")
        print(f"   - QA Items: {db.query(KBQA).count()}")
        print(f"   - Website Sources: {db.query(WebsiteSource).count()}")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()



