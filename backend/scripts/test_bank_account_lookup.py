#!/usr/bin/env python3
"""
Тест поиска банковского счета контрагента в 1С
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.services.odata_1c_client import OData1CClient
from app.core.config import settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_bank_account_lookup():
    """
    Тест поиска банковского счета контрагента
    """
    print("\n" + "="*80)
    print("🏦 ТЕСТ ПОИСКА БАНКОВСКОГО СЧЕТА КОНТРАГЕНТА В 1С")
    print("="*80 + "\n")

    # 1. Создать клиент
    client = OData1CClient(
        base_url=settings.ODATA_1C_URL,
        username=settings.ODATA_1C_USERNAME,
        password=settings.ODATA_1C_PASSWORD
    )

    # 2. Проверить подключение
    print("📡 Проверка подключения к 1С...")
    if not client.test_connection():
        print("❌ Не удалось подключиться к 1С")
        return False

    print("✅ Подключение успешно\n")

    # 3. Использовать реальные данные из 1С
    # (Найдены через scripts/find_counterparty_with_account.py)
    counterparty_guid = "c069022c-6aa7-11e6-8d13-00155d006a03"
    test_account_number = "40702810709270005397"

    print(f"📋 Используем реальные данные из 1С:")
    print(f"   Owner GUID: {counterparty_guid}")
    print(f"   Номер счета: {test_account_number}\n")

    # 4. Тест поиска конкретного счета
    print(f"🔍 Тест поиска счета по номеру: {test_account_number}")
    try:

        found_account = client.get_bank_account_by_number_and_owner(
            account_number=test_account_number,
            owner_guid=counterparty_guid
        )

        if found_account:
            print(f"✅ Счет найден через метод get_bank_account_by_number_and_owner:")
            print(f"   Описание: {found_account.get('Description')}")
            print(f"   Ref_Key: {found_account.get('Ref_Key')}")
            print(f"   Номер: {found_account.get('НомерСчета')}")
            return True
        else:
            print(f"❌ Счет не найден через метод get_bank_account_by_number_and_owner")
            return False

    except Exception as e:
        print(f"❌ Ошибка при работе с банковскими счетами: {e}")
        logger.exception("Exception during bank account test")
        return False


def test_nonexistent_account():
    """
    Тест с несуществующим счетом (должен вернуть None)
    """
    print("\n" + "="*80)
    print("🧪 ТЕСТ С НЕСУЩЕСТВУЮЩИМ БАНКОВСКИМ СЧЕТОМ")
    print("="*80 + "\n")

    client = OData1CClient(
        base_url=settings.ODATA_1C_URL,
        username=settings.ODATA_1C_USERNAME,
        password=settings.ODATA_1C_PASSWORD
    )

    # Тест с несуществующим счетом
    fake_account = "99999999999999999999"
    fake_owner = "00000000-0000-0000-0000-000000000000"

    print(f"🔍 Поиск несуществующего счета: {fake_account}")

    result = client.get_bank_account_by_number_and_owner(
        account_number=fake_account,
        owner_guid=fake_owner
    )

    if result is None:
        print("✅ Корректно вернул None для несуществующего счета")
        return True
    else:
        print("❌ Некорректный результат - ожидался None")
        return False


if __name__ == "__main__":
    try:
        # Запустить тесты
        test1_passed = test_bank_account_lookup()
        test2_passed = test_nonexistent_account()

        # Итоги
        print("\n" + "="*80)
        print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
        print("="*80)
        print(f"Тест поиска существующего счета: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
        print(f"Тест несуществующего счета: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
        print("="*80 + "\n")

        if test1_passed and test2_passed:
            print("🎉 Все тесты прошли успешно!")
            sys.exit(0)
        else:
            print("❌ Некоторые тесты не прошли")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        logger.exception("Critical error during testing")
        sys.exit(1)
