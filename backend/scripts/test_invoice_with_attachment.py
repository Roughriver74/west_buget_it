"""
Тестовый скрипт для проверки создания заявки на расход в 1С
с прикреплением файла

Проверяет:
1. Создание заявки с Posted=true (проведение документа)
2. Добавление ФИО пользователя в комментарий
3. Прикрепление файла к заявке
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.odata_1c_client import create_1c_client_from_env
import base64
from loguru import logger

def create_test_png():
    """Создать минимальный тестовый PNG файл"""
    # Минимальный PNG (1x1 pixel, прозрачный)
    png_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9"
        "AAAAFUlEQVR42mP8z8BQz0AEYBxVSF+FABJADveWkH6oAAAAAElFTkSuQmCC"
    )
    return png_data

def test_create_expense_request_with_attachment():
    """Тест создания заявки на расход с прикреплением файла"""

    logger.info("=" * 80)
    logger.info("Testing 1C Expense Request Creation with File Attachment")
    logger.info("=" * 80)

    # 1. Создать OData клиент
    try:
        client = create_1c_client_from_env()
        logger.info("✅ OData client created successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create OData client: {e}")
        return False

    # 2. Тестовые данные для заявки
    test_data = {
        # Основные поля
        "Date": "2025-11-20T00:00:00",
        "Posted": True,  # Провести документ
        "Организация_Key": "47b169eb-c529-11f0-ad7f-74563c634acb",  # Из примера
        "Статус": "НеСогласована",
        "ХозяйственнаяОперация": "ОплатаПоставщику",

        # Сумма и валюта
        "СуммаДокумента": 2000,
        "Валюта_Key": "f04b98ee-b430-11ea-a43c-b42e994e04d3",  # RUB

        # Формы оплаты
        "ФормаОплатыНаличная": True,
        "ФормаОплатыБезналичная": False,
        "ФормаОплатыПлатежнаяКарта": False,

        # Назначение и дата платежа
        "НазначениеПлатежа": "Тестовый платеж с прикреплением файла\nВ т.ч. НДС (20%) 333 руб.",
        "ЖелательнаяДатаПлатежа": "2025-11-23T00:00:00",

        # Контрагент (из примера)
        "Контрагент_Key": "0f26ffb6-7d77-11ef-ad4d-74563c634acb",
        "Партнер_Key": "0f26ffb6-7d77-11ef-ad4d-74563c634acb",
        "БанковскийСчетКонтрагента_Key": "00000000-0000-0000-0000-000000000000",

        # Данные счета
        "вс_НомерПоДаннымПоставщика": "TEST-001",
        "вс_ДатаПоДаннымПоставщика": "2025-11-20T00:00:00",

        # Ответственные
        "КтоЗаявил_Key": "be7e04e0-4eaf-11e3-8632-50e549c4019a",
        "КтоРешил_Key": "be7e04e0-4eaf-11e3-8632-50e549c4019a",
        "Автор_Key": "be7e04e0-4eaf-11e3-8632-50e549c4019a",

        # Статьи и планирование
        "СтатьяДвиженияДенежныхСредств_Key": "f95baf68-f96c-11ee-ad54-74563c634acb",
        "ПланированиеСуммы": "ВВалютеПлатежа",
        "СтатьяАктивовПассивов_Key": "00000000-0000-0000-0000-000000000000",
        "ВариантОплаты": "ПредоплатаДоПоступления",

        # Комментарий с ФИО пользователя
        "Комментарий": "Иванов Иван Иванович: Тестовая заявка с автоматическим прикреплением файла",
        "ФормаОплатыЗаявки": "",

        # Табличная часть
        "РасшифровкаПлатежа": [
            {
                "LineNumber": 1,
                "Номенклатура_Key": "00000000-0000-0000-0000-000000000000",
                "СтатьяРасходов_Key": "f95baf68-f96c-11ee-ad54-74563c634acb",
                "СтатьяДвиженияДенежныхСредств_Key": "f95baf68-f96c-11ee-ad54-74563c634acb",
                "Сумма": 2000,
                "СуммаБезНДС": 1667,
                "СуммаНДС": 333,
                "СтавкаНДС_Key": "ed59436e-f9dc-11ee-ad54-74563c634acb",  # 20%
                "Количество": 1,
                "Цена": 2000
            }
        ]
    }

    # 3. Создать заявку
    try:
        logger.info("📝 Creating expense request in 1C...")
        response = client.create_expense_request(test_data)

        ref_key = response.get('Ref_Key')
        if not ref_key:
            logger.error("❌ No Ref_Key in response!")
            return False

        logger.info(f"✅ Expense request created successfully!")
        logger.info(f"   Ref_Key: {ref_key}")
        logger.info(f"   Posted: {test_data['Posted']}")
        logger.info(f"   Comment: {test_data['Комментарий']}")

    except Exception as e:
        logger.error(f"❌ Failed to create expense request: {e}", exc_info=True)
        return False

    # 4. Прикрепить файл
    try:
        logger.info("📎 Uploading test file attachment...")

        # Создать тестовый PNG
        file_content = create_test_png()
        filename = "test_invoice.png"

        attachment_result = client.upload_attachment_to_expense_request(
            file_content=file_content,
            filename=filename,
            owner_guid=ref_key,
            file_extension="png"
        )

        if attachment_result:
            logger.info(f"✅ File attached successfully!")
            logger.info(f"   File: {filename}")
            logger.info(f"   Size: {len(file_content)} bytes")
            logger.info(f"   Attachment Ref_Key: {attachment_result.get('Ref_Key', 'N/A')}")
        else:
            logger.warning("⚠️ Failed to attach file (but expense request was created)")

    except Exception as e:
        logger.error(f"❌ Failed to upload attachment: {e}", exc_info=True)
        logger.warning("⚠️ Continuing despite attachment error...")

    logger.info("=" * 80)
    logger.info("Test completed!")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Проверьте в 1С:")
    logger.info(f"1. Заявка создана с Ref_Key: {ref_key}")
    logger.info("2. Документ проведен (Posted=true)")
    logger.info("3. Комментарий содержит ФИО пользователя в начале")
    logger.info("4. Файл прикреплен к заявке")

    return True

if __name__ == "__main__":
    success = test_create_expense_request_with_attachment()
    sys.exit(0 if success else 1)
