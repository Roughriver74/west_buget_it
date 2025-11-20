#!/usr/bin/env python3
"""
Тестовый скрипт для проверки загрузки файлов в 1С через OData
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.odata_1c_client import OData1CClient
import base64
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_file_upload():
    """
    Тест загрузки файла в 1С

    Требования:
    1. Должен быть создан документ "Заявка на расходование ДС" в 1С
    2. Нужен Ref_Key этого документа
    """

    # Инициализация клиента
    client = OData1CClient()

    print("=" * 80)
    print("ТЕСТ ЗАГРУЗКИ ФАЙЛА В 1С ЧЕРЕЗ ODATA")
    print("=" * 80)

    # 1. Проверка подключения
    print("\n1. Проверка подключения к 1С...")
    if not client.test_connection():
        print("❌ Не удалось подключиться к 1С")
        return False
    print("✅ Подключение успешно")

    # 2. Получаем список документов заявок (для получения Ref_Key)
    print("\n2. Получение списка заявок на расход...")
    try:
        expenses = client.get_expense_requests(
            date_from=None,
            date_to=None,
            top=5,
            skip=0,
            only_posted=False
        )

        if not expenses:
            print("❌ Нет заявок в 1С. Создайте хотя бы одну заявку через UI или API.")
            return False

        print(f"✅ Найдено заявок: {len(expenses)}")

        # Берем первую заявку для теста
        test_expense = expenses[0]
        ref_key = test_expense.get('Ref_Key')
        number = test_expense.get('Number', 'N/A')

        print(f"\n📄 Тестовая заявка:")
        print(f"   Номер: {number}")
        print(f"   Ref_Key: {ref_key}")

    except Exception as e:
        logger.error(f"Ошибка получения заявок: {e}")
        print(f"❌ Не удалось получить список заявок: {e}")
        return False

    # 3. Создаем тестовый файл
    print("\n3. Создание тестового файла...")
    test_content = b"Test PDF content for 1C attachment upload test"
    test_filename = "test_invoice.pdf"

    print(f"   Файл: {test_filename}")
    print(f"   Размер: {len(test_content)} bytes")

    # 4. Загрузка файла
    print("\n4. Загрузка файла в 1С...")
    try:
        result = client.upload_attachment_base64(
            file_content=test_content,
            filename=test_filename,
            owner_guid=ref_key,
            file_extension="pdf"
        )

        if result:
            print("✅ Файл успешно загружен в 1С!")
            print(f"   Response: {result}")
            return True
        else:
            print("❌ Не удалось загрузить файл (вернулся None)")
            return False

    except Exception as e:
        logger.error(f"Ошибка загрузки файла: {e}", exc_info=True)
        print(f"❌ Ошибка загрузки: {e}")
        return False


def test_different_endpoints():
    """
    Проверяет разные варианты endpoint для файлов
    """
    client = OData1CClient()

    print("\n" + "=" * 80)
    print("ПРОВЕРКА РАЗНЫХ ENDPOINTS ДЛЯ ФАЙЛОВ")
    print("=" * 80)

    endpoints_to_test = [
        'InformationRegister_ПрисоединенныеФайлы',
        'Catalog_ПрисоединенныеФайлы',
        'Catalog_ХранилищеФайлов',
    ]

    # Получаем тестовый Ref_Key
    try:
        expenses = client.get_expense_requests(top=1)
        if not expenses:
            print("❌ Нет заявок для теста")
            return

        ref_key = expenses[0].get('Ref_Key')
        test_content = b"Test content"

        for endpoint in endpoints_to_test:
            print(f"\n🔍 Тестируем endpoint: {endpoint}")

            attachment_data = {
                "Наименование": "test.pdf",
                "ДвоичныеДанные": base64.b64encode(test_content).decode('utf-8'),
                "Владелец_Key": ref_key,
                "Расширение": "pdf"
            }

            try:
                response = client._make_request(
                    method='POST',
                    endpoint=endpoint,
                    data=attachment_data
                )
                print(f"✅ Endpoint {endpoint} работает!")
                print(f"   Response: {response}")

            except Exception as e:
                print(f"❌ Endpoint {endpoint} не работает: {e}")

    except Exception as e:
        print(f"❌ Ошибка теста: {e}")


if __name__ == "__main__":
    print("\n🚀 Запуск тестов загрузки файлов в 1С\n")

    # Тест 1: Базовая загрузка
    success = test_file_upload()

    # Тест 2: Проверка разных endpoints (опционально)
    user_input = input("\n\nПроверить разные endpoints для файлов? (y/n): ")
    if user_input.lower() == 'y':
        test_different_endpoints()

    print("\n" + "=" * 80)
    if success:
        print("✅ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО")
    else:
        print("❌ ТЕСТЫ НЕ ПРОЙДЕНЫ")
    print("=" * 80)
