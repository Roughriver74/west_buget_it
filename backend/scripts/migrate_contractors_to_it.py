#!/usr/bin/env python3
"""Migrate contractors from 'del' department to 'IT Отдел WEST' department"""

import sys
sys.path.insert(0, '/Users/evgenijsikunov/projects/west/west_buget_it/backend')

from app.db.session import SessionLocal
from app.db.models import Contractor, Department

def migrate_contractors():
    """Migrate all contractors from 'del' to 'IT Отдел WEST'"""

    db = SessionLocal()

    try:
        # Find the departments
        del_dept = db.query(Department).filter(Department.name == "del").first()
        it_dept = db.query(Department).filter(Department.name == "IT Отдел WEST").first()

        if not del_dept:
            print("❌ Error: 'del' department not found")
            return

        if not it_dept:
            print("❌ Error: 'IT Отдел WEST' department not found")
            return

        print(f"\n📊 Department Information:")
        print(f"  Source: {del_dept.name} (ID: {del_dept.id})")
        print(f"  Target: {it_dept.name} (ID: {it_dept.id})")
        print()

        # Find all contractors in 'del' department
        contractors_to_migrate = db.query(Contractor).filter(
            Contractor.department_id == del_dept.id
        ).all()

        count = len(contractors_to_migrate)

        if count == 0:
            print("ℹ️  No contractors found in 'del' department")
            return

        print(f"Found {count} contractors to migrate:")
        print()

        # Show contractors
        for idx, contractor in enumerate(contractors_to_migrate, 1):
            print(f"  {idx}. {contractor.name} (ID: {contractor.id})")

        print()
        print("🔄 Migrating contractors...")

        # Migrate contractors
        migrated_count = 0
        for contractor in contractors_to_migrate:
            contractor.department_id = it_dept.id
            migrated_count += 1

        db.commit()

        print(f"\n✅ Successfully migrated {migrated_count} contractors from '{del_dept.name}' to '{it_dept.name}'")

        # Verify migration
        remaining_in_del = db.query(Contractor).filter(
            Contractor.department_id == del_dept.id
        ).count()

        now_in_it = db.query(Contractor).filter(
            Contractor.department_id == it_dept.id
        ).count()

        print(f"\n📈 Final Statistics:")
        print(f"  Contractors in '{del_dept.name}': {remaining_in_del}")
        print(f"  Contractors in '{it_dept.name}': {now_in_it}")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error during migration: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  Contractor Migration Script")
    print("  From: 'del' → To: 'IT Отдел WEST'")
    print("="*60 + "\n")

    migrate_contractors()

    print("\n" + "="*60 + "\n")
