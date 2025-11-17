"""
Проверка доступности данных в 1С за разные периоды
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date, timedelta
from app.services.odata_1c_client import OData1CClient


def check_period(client, period_name, date_from, date_to):
    """Проверить наличие данных за период"""
    print(f"\n📅 {period_name}: {date_from} to {date_to}")
    print("-" * 60)

    try:
        # Поступления
        receipts = client.get_bank_receipts(
            date_from=date_from,
            date_to=date_to,
            top=5
        )

        # Списания
        payments = client.get_bank_payments(
            date_from=date_from,
            date_to=date_to,
            top=5
        )

        total = len(receipts) + len(payments)

        if total > 0:
            print(f"✅ Found {len(receipts)} receipts + {len(payments)} payments = {total} total")

            if receipts:
                first = receipts[0]
                print(f"   First receipt: {first.get('Date', 'N/A')[:10]}, {first.get('СуммаДокумента', 0)}₽")

            if payments:
                first = payments[0]
                print(f"   First payment: {first.get('Date', 'N/A')[:10]}, {first.get('СуммаДокумента', 0)}₽")
        else:
            print("⚠️  No data for this period")

        return total

    except Exception as e:
        print(f"❌ Error: {e}")
        return 0


def main():
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║      1C OData - Data Availability Check                           ║
╚═══════════════════════════════════════════════════════════════════╝
    """)

    # Создать клиент
    print("Creating 1C OData client...")
    client = OData1CClient(
        base_url="http://10.10.100.77/trade/odata/standard.odata",
        username="odata.user",
        password="ak228Hu2hbs28"
    )

    print("Testing connection...")
    if not client.test_connection():
        print("❌ ERROR: Connection failed!")
        return

    print("✅ Connection successful!")

    # Проверить разные периоды
    today = date.today()

    periods = [
        ("Last 7 days", today - timedelta(days=7), today),
        ("Last 30 days", today - timedelta(days=30), today),
        ("Last 90 days", today - timedelta(days=90), today),
        ("2025 YTD", date(2025, 1, 1), today),
        ("November 2024", date(2024, 11, 1), date(2024, 11, 30)),
        ("October 2024", date(2024, 10, 1), date(2024, 10, 31)),
        ("September 2024", date(2024, 9, 1), date(2024, 9, 30)),
        ("2024 YTD", date(2024, 1, 1), today),
        ("2023 Full Year", date(2023, 1, 1), date(2023, 12, 31)),
        ("2022 Full Year", date(2022, 1, 1), date(2022, 12, 31)),
    ]

    print("\n" + "=" * 70)
    print("CHECKING DATA AVAILABILITY")
    print("=" * 70)

    results = {}
    for period_name, date_from, date_to in periods:
        count = check_period(client, period_name, date_from, date_to)
        results[period_name] = count

    # Итоги
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    has_data = [name for name, count in results.items() if count > 0]
    no_data = [name for name, count in results.items() if count == 0]

    if has_data:
        print(f"\n✅ Periods with data ({len(has_data)}):")
        for name in has_data:
            print(f"   - {name}: {results[name]} transactions")

    if no_data:
        print(f"\n⚠️  Periods with no data ({len(no_data)}):")
        for name in no_data:
            print(f"   - {name}")

    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)

    if has_data:
        # Найти самый ранний период с данными
        earliest = None
        for period_name, date_from, date_to in periods:
            if results[period_name] > 0:
                if earliest is None or date_from < earliest[1]:
                    earliest = (period_name, date_from, date_to)

        if earliest:
            print(f"\n💡 Earliest period with data: {earliest[0]}")
            print(f"   From: {earliest[1]}")
            print(f"   To: {earliest[2]}")
            print(f"\nTo sync this period, run:")
            print(f"   python scripts/sync_1c_custom.py --from {earliest[1]} --to {earliest[2]}")
    else:
        print("\n⚠️  No data found in any tested period")
        print("Possible issues:")
        print("   - 1C configuration doesn't expose bank documents")
        print("   - Wrong document types")
        print("   - Access permissions")

    print()


if __name__ == "__main__":
    main()
