"""
Скрипт для проверки структуры справочников 1С:
- Catalog_Организации (Organizations)
- Catalog_СтатьиДвиженияДенежныхСредств (Cash Flow Categories)
"""

import sys
import os
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.odata_1c_client import create_1c_client_from_env
import json


def check_organizations():
    """Проверить структуру справочника Организации"""
    print("\n" + "="*80)
    print("CHECKING Catalog_Организации (Organizations)")
    print("="*80)

    client = create_1c_client_from_env()

    # Test connection
    if not client.test_connection():
        print("❌ Failed to connect to 1C OData")
        return

    print("✅ Connection successful\n")

    # Fetch first 5 organizations
    try:
        print("Fetching organizations (first 5)...")
        response = client._make_request(
            method='GET',
            endpoint='Catalog_Организации',
            params={
                '$format': 'json',
                '$top': 5
            }
        )

        orgs = response.get('value', [])
        print(f"Found {len(orgs)} organizations\n")

        if orgs:
            # Show first organization structure
            print("SAMPLE ORGANIZATION STRUCTURE:")
            print(json.dumps(orgs[0], indent=2, ensure_ascii=False))

            # Show available fields
            print("\nAVAILABLE FIELDS:")
            for key in orgs[0].keys():
                value = orgs[0][key]
                value_type = type(value).__name__
                print(f"  - {key}: {value_type}")

            # Show all organizations
            print("\n" + "-"*80)
            print("ALL ORGANIZATIONS (first 5):")
            print("-"*80)
            for i, org in enumerate(orgs, 1):
                print(f"\n{i}. {org.get('Description', 'N/A')}")
                print(f"   Ref_Key: {org.get('Ref_Key')}")
                print(f"   Code: {org.get('Code')}")
                print(f"   ИНН: {org.get('ИНН', 'N/A')}")
                print(f"   КПП: {org.get('КПП', 'N/A')}")
                print(f"   IsFolder: {org.get('IsFolder', False)}")

    except Exception as e:
        print(f"❌ Error fetching organizations: {e}")


def check_cash_flow_categories():
    """Проверить структуру справочника Статьи движения денежных средств"""
    print("\n" + "="*80)
    print("CHECKING Catalog_СтатьиДвиженияДенежныхСредств (Cash Flow Categories)")
    print("="*80)

    client = create_1c_client_from_env()

    # Fetch first 20 categories (to see hierarchy)
    try:
        print("Fetching cash flow categories (first 20)...")
        response = client._make_request(
            method='GET',
            endpoint='Catalog_СтатьиДвиженияДенежныхСредств',
            params={
                '$format': 'json',
                '$top': 20
            }
        )

        categories = response.get('value', [])
        print(f"Found {len(categories)} categories\n")

        if categories:
            # Show first category structure
            print("SAMPLE CATEGORY STRUCTURE:")
            print(json.dumps(categories[0], indent=2, ensure_ascii=False))

            # Show available fields
            print("\nAVAILABLE FIELDS:")
            for key in categories[0].keys():
                value = categories[0][key]
                value_type = type(value).__name__
                print(f"  - {key}: {value_type}")

            # Analyze hierarchy (folders vs items)
            print("\n" + "-"*80)
            print("HIERARCHY STRUCTURE:")
            print("-"*80)

            folders = [c for c in categories if c.get('IsFolder', False)]
            items = [c for c in categories if not c.get('IsFolder', False)]

            print(f"\nFolders (departments): {len(folders)}")
            for folder in folders:
                print(f"  📁 {folder.get('Description', 'N/A')} (Code: {folder.get('Code')})")
                print(f"      Ref_Key: {folder.get('Ref_Key')}")
                print(f"      Parent: {folder.get('Parent_Key', 'N/A')}")

            print(f"\nItems (categories): {len(items)}")
            for item in items[:10]:  # Show first 10 items
                parent_key = item.get('Parent_Key')
                parent_name = 'ROOT'
                if parent_key and parent_key != '00000000-0000-0000-0000-000000000000':
                    # Find parent
                    parent = next((c for c in categories if c.get('Ref_Key') == parent_key), None)
                    if parent:
                        parent_name = parent.get('Description', 'Unknown')

                print(f"  📄 {item.get('Description', 'N/A')} (Code: {item.get('Code')})")
                print(f"      Ref_Key: {item.get('Ref_Key')}")
                print(f"      Parent: {parent_name}")
                print(f"      ВидСтатьиДДС: {item.get('ВидСтатьиДДС', 'N/A')}")

            # Check if there's a ВидСтатьиДДС field (expense type)
            if items and 'ВидСтатьиДДС' in items[0]:
                print("\n" + "-"*80)
                print("EXPENSE TYPES (ВидСтатьиДДС):")
                print("-"*80)
                expense_types = set()
                for item in items:
                    if 'ВидСтатьиДДС' in item:
                        expense_types.add(item.get('ВидСтатьиДДС'))

                for exp_type in sorted(expense_types):
                    count = sum(1 for i in items if i.get('ВидСтатьиДДС') == exp_type)
                    print(f"  - {exp_type}: {count} items")

    except Exception as e:
        print(f"❌ Error fetching cash flow categories: {e}")


def main():
    """Main function"""
    print("\n" + "="*80)
    print("1C CATALOGS STRUCTURE ANALYSIS")
    print("="*80)

    # Check both catalogs
    check_organizations()
    check_cash_flow_categories()

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
