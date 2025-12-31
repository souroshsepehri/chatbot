"""
Script to clear Knowledge Base and Category data from the database.

Usage:
    python scripts/clear_kb_data.py --yes

This script requires explicit confirmation via --yes flag to avoid accidental data loss.
"""

import sys
import argparse
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.kb_category import KBCategory
from app.models.kb_qa import KBQA


def clear_kb_data(db: Session) -> tuple[int, int]:
    """
    Clear all KB QA items and Categories from the database.
    
    Returns:
        Tuple of (deleted_qa_count, deleted_category_count)
    """
    # Delete all QA items first (they reference categories)
    qa_count = db.query(KBQA).count()
    db.query(KBQA).delete()
    
    # Delete all categories
    category_count = db.query(KBCategory).count()
    db.query(KBCategory).delete()
    
    return qa_count, category_count


def main():
    parser = argparse.ArgumentParser(
        description="Clear Knowledge Base and Category data from the database"
    )
    parser.add_argument(
        '--yes',
        action='store_true',
        required=True,
        help='Required flag to confirm deletion. Prevents accidental data loss.'
    )
    
    args = parser.parse_args()
    
    if not args.yes:
        print("❌ Error: --yes flag is required to confirm deletion.")
        print("   Usage: python scripts/clear_kb_data.py --yes")
        sys.exit(1)
    
    print("=" * 60)
    print("Clear Knowledge Base and Category Data")
    print("=" * 60)
    print()
    print("⚠️  WARNING: This will delete ALL KB QA items and Categories!")
    print("   This action cannot be undone.")
    print()
    
    db: Session = SessionLocal()
    try:
        # Count existing data
        qa_count = db.query(KBQA).count()
        category_count = db.query(KBCategory).count()
        
        print(f"📊 Current data:")
        print(f"   - KB QA Items: {qa_count}")
        print(f"   - Categories: {category_count}")
        print()
        
        if qa_count == 0 and category_count == 0:
            print("✓ Database is already empty. Nothing to delete.")
            return
        
        # Clear the data
        print("🗑️  Deleting data...")
        deleted_qa, deleted_categories = clear_kb_data(db)
        db.commit()
        
        print()
        print("✅ Data cleared successfully!")
        print(f"   - Deleted QA Items: {deleted_qa}")
        print(f"   - Deleted Categories: {deleted_categories}")
        print()
        print("✓ Knowledge Base and Categories are now empty.")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error during deletion: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

