#!/usr/bin/env python3
"""
Найти контрагента с банковским счетом для тестирования
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.services.odata_1c_client import OData1CClient
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_counterparty_with_account():
    """Найти контрагента, у которого есть банковский счет"""

    client = OData1CClient(
        base_url=settings.ODATA_1C_URL,
        username=settings.ODATA_1C_USERNAME,
        password=settings.ODATA_1C_PASSWORD
    )

    # Получить несколько банковских счетов
    print("🔍 Получение банковских счетов из 1С...")
    endpoint = "Catalog_БанковскиеСчетаКонтрагентов?$top=10&$format=json"
    response = client._make_request(method='GET', endpoint=endpoint)

    accounts = response.get('value', [])
    print(f"✅ Найдено счетов: {len(accounts)}\n")

    for i, account in enumerate(accounts, 1):
        account_number = account.get('НомерСчета', '')
        # Try Owner_Key first, then Owner (string)
        owner_key = account.get('Owner_Key') or account.get('Owner', '')
        # If Owner is a dict, get Ref_Key from it
        if isinstance(owner_key, dict):
            owner_key = owner_key.get('Ref_Key', '')
        description = account.get('Description', '')

        print(f"📋 Банковский счет {i}:")
        print(f"   Номер: {account_number}")
        print(f"   Описание: {description}")
        print(f"   Owner_Key: {owner_key}")
        print(f"   Full data: {account}")

        if not account_number:
            print("   ⚠️ Нет номера счета, пропускаем")
            print()
            continue

        if not owner_key:
            print("   ⚠️ Нет Owner_Key, пропускаем")
            print()
            continue

        print(f"   ✅ Это подходящий счет для тестирования!")
        print(f"   Номер счета: {account_number}")
        print(f"   Owner GUID: {owner_key}")
        return {
            'inn': 'N/A',
            'account_number': account_number,
            'owner_guid': owner_key,
            'name': 'N/A'
        }

        # Получить информацию о контрагенте
        try:
            counterparty_endpoint = f"Catalog_Контрагенты(guid'{owner_key}')?$format=json"
            counterparty = client._make_request(method='GET', endpoint=counterparty_endpoint)

            counterparty_name = counterparty.get('Description', '')
            counterparty_inn = counterparty.get('ИНН', '')

            print(f"   Контрагент: {counterparty_name}")
            print(f"   ИНН: {counterparty_inn}")

            if counterparty_inn:
                print(f"\n✅ Найден подходящий контрагент для тестирования!")
                print(f"   ИНН: {counterparty_inn}")
                print(f"   Номер счета: {account_number}")
                print(f"   Owner GUID: {owner_key}")
                return {
                    'inn': counterparty_inn,
                    'account_number': account_number,
                    'owner_guid': owner_key,
                    'name': counterparty_name
                }
        except Exception as e:
            logger.error(f"Ошибка при получении контрагента: {e}")
            continue

        print()

    print("❌ Не найдено подходящих контрагентов")
    return None


if __name__ == "__main__":
    result = find_counterparty_with_account()
    if result:
        print("\n" + "="*80)
        print("📝 ДАННЫЕ ДЛЯ ТЕСТИРОВАНИЯ:")
        print("="*80)
        print(f"INN = \"{result['inn']}\"")
        print(f"ACCOUNT = \"{result['account_number']}\"")
        print(f"OWNER_GUID = \"{result['owner_guid']}\"")
        print(f"NAME = \"{result['name']}\"")
        print("="*80)
