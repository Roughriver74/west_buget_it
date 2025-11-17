"""
Test script for 1C Expense Requests OData integration

This script tests the connection to 1C and fetches sample expense request documents
to verify field mapping before running full sync.
"""

import os
import sys
from datetime import date, datetime
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.odata_1c_client import OData1CClient


def test_connection():
    """Test connection to 1C OData"""
    print("=" * 80)
    print("Testing 1C OData Connection")
    print("=" * 80)

    # Get credentials from environment
    odata_url = os.getenv('ODATA_1C_URL', 'http://10.10.100.77/trade/odata/standard.odata')
    odata_username = os.getenv('ODATA_1C_USERNAME', 'odata.user')
    odata_password = os.getenv('ODATA_1C_PASSWORD', 'ak228Hu2hbs28')

    print(f"\nOData URL: {odata_url}")
    print(f"Username: {odata_username}")
    print(f"Password: {'*' * len(odata_password)}")

    # Create client
    client = OData1CClient(
        base_url=odata_url,
        username=odata_username,
        password=odata_password
    )

    # Test connection
    print("\nTesting connection...")
    if client.test_connection():
        print("✅ Connection successful!")
        return client
    else:
        print("❌ Connection failed!")
        return None


def fetch_sample_expenses(client: OData1CClient):
    """Fetch sample expense request documents"""
    print("\n" + "=" * 80)
    print("Fetching Sample Expense Request Documents")
    print("=" * 80)

    # Fetch last 30 days
    date_to = date.today()
    date_from = date(date_to.year, date_to.month, 1)  # First day of current month

    print(f"\nDate range: {date_from} to {date_to}")
    print("Fetching up to 5 documents...")

    try:
        expenses = client.get_expense_requests(
            date_from=date_from,
            date_to=date_to,
            top=5,
            skip=0,
            only_posted=False  # Get all documents to see structure
        )

        print(f"\n✅ Fetched {len(expenses)} document(s)")

        if not expenses:
            print("\n⚠️  No expense documents found in the specified period.")
            print("Try adjusting the date range or check if documents exist in 1C.")
            return

        # Display first document structure
        print("\n" + "=" * 80)
        print("Sample Document Structure (First Document)")
        print("=" * 80)

        first_doc = expenses[0]
        print("\nAvailable fields:")
        for key, value in sorted(first_doc.items()):
            # Truncate long values
            str_value = str(value)
            if len(str_value) > 100:
                str_value = str_value[:97] + "..."
            print(f"  {key:30} : {str_value}")

        # Display all documents summary
        print("\n" + "=" * 80)
        print("All Documents Summary")
        print("=" * 80)

        for i, doc in enumerate(expenses, 1):
            print(f"\n{i}. Document")
            print(f"   Ref_Key:     {doc.get('Ref_Key', 'N/A')}")
            print(f"   Number:      {doc.get('Number') or doc.get('Номер', 'N/A')}")
            print(f"   Date:        {doc.get('Date', 'N/A')}")
            print(f"   Amount:      {doc.get('Сумма') or doc.get('СуммаДокумента', 'N/A')}")
            print(f"   Posted:      {doc.get('Posted', 'N/A')}")
            print(f"   Organization: {doc.get('Организация_Key', 'N/A')}")
            print(f"   Counterparty: {doc.get('Контрагент_Key', 'N/A')}")

            # Check for comment field variants
            comment = (
                doc.get('Комментарий') or
                doc.get('Comment') or
                doc.get('НазначениеПлатежа') or
                'N/A'
            )
            if len(comment) > 80:
                comment = comment[:77] + "..."
            print(f"   Comment:     {comment}")

        print("\n" + "=" * 80)
        print("Field Mapping Verification")
        print("=" * 80)

        print("\nExpected fields for mapping:")
        required_fields = [
            'Ref_Key',
            'Number or Номер',
            'Date',
            'Сумма or СуммаДокумента',
            'Организация_Key',
            'Posted'
        ]

        optional_fields = [
            'Контрагент_Key',
            'Комментарий or Comment',
            'Инициатор or Заявитель'
        ]

        print("\nRequired fields:")
        for field in required_fields:
            print(f"  ✓ {field}")

        print("\nOptional fields:")
        for field in optional_fields:
            print(f"  • {field}")

        # Check if all required fields are present
        print("\n" + "=" * 80)
        print("Validation")
        print("=" * 80)

        missing_fields = []
        for doc in expenses:
            doc_missing = []

            if not doc.get('Ref_Key'):
                doc_missing.append('Ref_Key')

            if not (doc.get('Number') or doc.get('Номер')):
                doc_missing.append('Number/Номер')

            if not doc.get('Date'):
                doc_missing.append('Date')

            if not (doc.get('Сумма') or doc.get('СуммаДокумента')):
                doc_missing.append('Сумма/СуммаДокумента')

            if doc_missing:
                missing_fields.append({
                    'doc_ref': doc.get('Ref_Key', 'unknown'),
                    'missing': doc_missing
                })

        if missing_fields:
            print("\n⚠️  Warning: Some documents are missing required fields:")
            for item in missing_fields:
                print(f"\n  Document {item['doc_ref']}:")
                for field in item['missing']:
                    print(f"    ❌ Missing: {field}")
        else:
            print("\n✅ All documents have required fields!")

        print("\n" + "=" * 80)
        print("Test Organization/Contractor Lookup")
        print("=" * 80)

        # Test fetching organization details
        if first_doc.get('Организация_Key'):
            org_key = first_doc['Организация_Key']
            print(f"\nFetching organization: {org_key}")

            org_data = client.get_organization_by_key(org_key)
            if org_data:
                print("✅ Organization found:")
                print(f"   Name:      {org_data.get('Наименование', 'N/A')}")
                print(f"   ShortName: {org_data.get('НаименованиеСокращенное', 'N/A')}")
                print(f"   INN:       {org_data.get('ИНН', 'N/A')}")
                print(f"   KPP:       {org_data.get('КПП', 'N/A')}")
            else:
                print("❌ Organization not found")

        # Test fetching contractor details
        if first_doc.get('Контрагент_Key'):
            contractor_key = first_doc['Контрагент_Key']
            print(f"\nFetching contractor: {contractor_key}")

            contractor_data = client.get_counterparty_by_key(contractor_key)
            if contractor_data:
                print("✅ Contractor found:")
                print(f"   Name: {contractor_data.get('Наименование', 'N/A')}")
                print(f"   INN:  {contractor_data.get('ИНН', 'N/A')}")
                print(f"   KPP:  {contractor_data.get('КПП', 'N/A')}")
            else:
                print("❌ Contractor not found")

    except Exception as e:
        print(f"\n❌ Error fetching expenses: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main test function"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "1C Expense Sync Test Script" + " " * 31 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")

    # Test connection
    client = test_connection()
    if not client:
        print("\n❌ Cannot proceed without connection. Exiting.")
        return

    # Fetch and analyze sample expenses
    fetch_sample_expenses(client)

    print("\n" + "=" * 80)
    print("Test Complete!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Review the field structure above")
    print("2. Verify the mapping in expense_1c_sync.py")
    print("3. Test the sync via API endpoint: POST /api/v1/expenses/sync/1c")
    print("\n")


if __name__ == "__main__":
    main()
