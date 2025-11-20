#!/usr/bin/env python3
"""
Seed script for timesheet test data
Creates sample timesheets with daily records for testing
"""

import sys
from pathlib import Path
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4
import random

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.db.models import (
    WorkTimesheet, DailyWorkRecord, Employee, Department,
    TimesheetStatusEnum, EmployeeStatusEnum
)


def seed_timesheets(year: int = 2025, month: int = 11):
    """
    Seed timesheets for a given month

    Args:
        year: Year to seed
        month: Month to seed (1-12)
    """
    # Create database connection
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        print(f"\n=== Seeding Timesheets for {month}/{year} ===\n")

        # Get all departments
        departments = db.query(Department).all()

        if not departments:
            print("❌ No departments found! Please seed departments first.")
            return

        print(f"Found {len(departments)} departments")

        total_timesheets = 0
        total_records = 0

        # For each department, get employees and create timesheets
        for dept in departments:
            print(f"\n📂 Department: {dept.name}")

            # Get active employees
            employees = db.query(Employee).filter(
                Employee.department_id == dept.id,
                Employee.status == EmployeeStatusEnum.ACTIVE
            ).all()

            if not employees:
                print(f"  ⚠️  No active employees in {dept.name}")
                continue

            print(f"  Found {len(employees)} active employees")

            # Create timesheets for each employee
            for emp in employees:
                # Check if timesheet already exists
                existing = db.query(WorkTimesheet).filter(
                    WorkTimesheet.employee_id == emp.id,
                    WorkTimesheet.year == year,
                    WorkTimesheet.month == month
                ).first()

                if existing:
                    print(f"  ⏭️  Timesheet already exists for {emp.full_name}")
                    continue

                # Create timesheet
                timesheet = WorkTimesheet(
                    id=uuid4(),
                    employee_id=emp.id,
                    department_id=dept.id,
                    year=year,
                    month=month,
                    status=random.choice([
                        TimesheetStatusEnum.DRAFT,
                        TimesheetStatusEnum.DRAFT,
                        TimesheetStatusEnum.APPROVED,
                    ]),  # More drafts than approved
                    total_days_worked=0,
                    total_hours_worked=Decimal("0")
                )

                db.add(timesheet)
                db.flush()  # Get timesheet.id

                # Create daily records for the month
                start_date = date(year, month, 1)

                # Get number of days in month
                if month == 12:
                    end_date = date(year + 1, 1, 1)
                else:
                    end_date = date(year, month + 1, 1)

                days_in_month = (end_date - start_date).days

                total_days = 0
                total_hours = Decimal("0")

                for day_offset in range(days_in_month):
                    work_date = start_date + timedelta(days=day_offset)
                    day_of_week = work_date.isoweekday()  # 1=Mon, 7=Sun

                    # Skip weekends (5=Sat, 6=Sun)
                    is_working_day = day_of_week < 6

                    if not is_working_day:
                        continue

                    # Generate realistic hours (7-9 hours per day with some variation)
                    # 90% chance of full day, 10% chance of partial/no hours
                    if random.random() < 0.9:
                        hours = Decimal(str(random.choice([7, 7.5, 8, 8, 8, 8.5, 9])))
                    else:
                        hours = Decimal(str(random.choice([0, 4, 4.5, 5, 6])))

                    # Occasional overtime
                    overtime = Decimal("0")
                    if random.random() < 0.1:  # 10% chance
                        overtime = Decimal(str(random.choice([1, 1.5, 2])))

                    # Break hours (lunch)
                    break_hours = Decimal("1") if hours > 6 else Decimal("0")

                    # Create record
                    record = DailyWorkRecord(
                        id=uuid4(),
                        timesheet_id=timesheet.id,
                        work_date=work_date,
                        is_working_day=is_working_day,
                        hours_worked=hours,
                        break_hours=break_hours,
                        overtime_hours=overtime,
                        notes=None,
                        department_id=dept.id
                    )

                    db.add(record)

                    if is_working_day:
                        total_days += 1
                        total_hours += hours

                # Update timesheet totals
                timesheet.total_days_worked = total_days
                timesheet.total_hours_worked = total_hours

                print(f"  ✅ Created timesheet for {emp.full_name}: {total_days} days, {float(total_hours):.1f} hours")
                total_timesheets += 1
                total_records += total_days

        # Commit all changes
        db.commit()

        print(f"\n✅ Seeding completed successfully!")
        print(f"   Created {total_timesheets} timesheets")
        print(f"   Created {total_records} daily records")

    except Exception as e:
        print(f"\n❌ Error seeding timesheets: {e}")
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    # Check for command line arguments
    year = 2025
    month = 11

    if len(sys.argv) > 1:
        year = int(sys.argv[1])
    if len(sys.argv) > 2:
        month = int(sys.argv[2])

    print(f"""
    ╔══════════════════════════════════════╗
    ║   Timesheet Data Seeder              ║
    ║   Year: {year}                        ║
    ║   Month: {month}                      ║
    ╚══════════════════════════════════════╝
    """)

    seed_timesheets(year, month)
