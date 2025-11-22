#!/usr/bin/env python3
"""
Быстрый тест функционала 1С OData
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.odata_1c_client import OData1CClient
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_1c_connection():
    """Проверка всего функционала 1С"""

    print("=" * 80)
    print("🧪 БЫСТРЫЙ ТЕСТ ФУНКЦИОНАЛА 1С ODATA")
    print("=" * 80)

    # 1. Инициализация клиента
    print("\n1️⃣  Инициализация OData клиента...")
    try:
        from app.core.config import settings

        print(f"   URL: {settings.ODATA_1C_URL}")
        print(f"   User: {settings.ODATA_1C_USERNAME}")

        client = OData1CClient(
            base_url=settings.ODATA_1C_URL,
            username=settings.ODATA_1C_USERNAME,
            password=settings.ODATA_1C_PASSWORD
        )
        print("✅ Клиент создан")
    except Exception as e:
        print(f"❌ Ошибка создания клиента: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 2. Проверка подключения
    print("\n2️⃣  Проверка подключения к 1С...")
    try:
        if client.test_connection():
            print("✅ Подключение успешно")
        else:
            print("❌ Не удалось подключиться к 1С")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

    # 3. Получение организаций
    print("\n3️⃣  Получение списка организаций из 1С...")
    try:
        orgs = client.get_organizations(top=3)
        if orgs:
            print(f"✅ Получено организаций: {len(orgs)}")
            for org in orgs[:2]:
                print(f"   - {org.get('Description', 'N/A')} (ИНН: {org.get('ИНН', 'N/A')})")
        else:
            print("⚠️  Организации не найдены")
    except Exception as e:
        print(f"❌ Ошибка получения организаций: {e}")

    # 4. Получение категорий (статей ДДС)
    print("\n4️⃣  Получение категорий (статей ДДС) из 1С...")
    try:
        categories = client.get_cash_flow_categories(top=5)
        if categories:
            print(f"✅ Получено категорий: {len(categories)}")
            for cat in categories[:3]:
                print(f"   - {cat.get('Description', 'N/A')}")
        else:
            print("⚠️  Категории не найдены")
    except Exception as e:
        print(f"❌ Ошибка получения категорий: {e}")

    # 5. Получение заявок на расход
    print("\n5️⃣  Получение заявок на расход из 1С...")
    try:
        from datetime import date, timedelta
        date_from = date.today() - timedelta(days=30)
        date_to = date.today()

        expenses = client.get_expense_requests(
            date_from=date_from,
            date_to=date_to,
            top=5,
            only_posted=False
        )

        if expenses:
            print(f"✅ Получено заявок: {len(expenses)}")
            for exp in expenses[:2]:
                print(f"   - №{exp.get('Number', 'N/A')}, "
                      f"Сумма: {exp.get('СуммаДокумента', 0):.2f} руб.")
        else:
            print("⚠️  Заявки не найдены")
    except Exception as e:
        print(f"❌ Ошибка получения заявок: {e}")

    # 6. Тест создания заявки (ОПЦИОНАЛЬНО)
    print("\n6️⃣  Тест создания заявки на расход...")
    create_test = input("   Создать тестовую заявку в 1С? (y/n): ")

    if create_test.lower() == 'y':
        try:
            # Получаем данные для создания
            if not orgs:
                print("❌ Нет организаций для теста")
                return False

            if not categories:
                print("❌ Нет категорий для теста")
                return False

            org_guid = orgs[0].get('Ref_Key')
            category_guid = categories[0].get('Ref_Key')

            print(f"\n   Создаем заявку:")
            print(f"   - Организация: {orgs[0].get('Description', 'N/A')}")
            print(f"   - Категория: {categories[0].get('Description', 'N/A')}")
            print(f"   - Сумма: 1000.00 руб.")

            test_data = {
                "Дата": date.today().isoformat() + "T00:00:00",
                "Организация_Key": org_guid,
                "СуммаДокумента": 1000.00,
                "СтатьяДДС_Key": category_guid,
                "НазначениеПлатежа": "Тестовая заявка из IT Budget Manager",
                "ХозяйственнаяОперация": "ОплатаПоставщику"
            }

            response = client.create_expense_request(test_data)
            ref_key = response.get('Ref_Key')

            print(f"✅ Заявка создана!")
            print(f"   Ref_Key: {ref_key}")

            # 7. Тест загрузки файла (если создали заявку)
            print("\n7️⃣  Тест загрузки файла к заявке...")
            upload_test = input("   Загрузить тестовый файл к заявке? (y/n): ")

            if upload_test.lower() == 'y':
                test_content = b"Test file content for 1C attachment upload"
                test_filename = "test_document.pdf"

                print(f"\n   Загружаем файл:")
                print(f"   - Имя: {test_filename}")
                print(f"   - Размер: {len(test_content)} bytes")
                print(f"   - Владелец (Ref_Key): {ref_key}")

                attachment_result = client.upload_attachment_base64(
                    file_content=test_content,
                    filename=test_filename,
                    owner_guid=ref_key,
                    file_extension="pdf"
                )

                if attachment_result:
                    print(f"✅ Файл успешно загружен!")
                    print(f"   Response: {attachment_result}")
                else:
                    print("⚠️  Не удалось загрузить файл (проверьте логи)")

        except Exception as e:
            print(f"❌ Ошибка создания заявки: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 80)
    print("✅ ТЕСТ ЗАВЕРШЕН")
    print("=" * 80)

    return True


if __name__ == "__main__":
    try:
        test_1c_connection()
    except KeyboardInterrupt:
        print("\n\n⚠️  Тест прерван пользователем")
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
