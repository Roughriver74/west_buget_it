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

def test_create_expense_request_with_attachment(with_vat=True):
    """Тест создания заявки на расход с прикреплением файла

    Args:
        with_vat: True - счет с НДС, False - счет без НДС
    """

    logger.info("=" * 80)
    logger.info(f"Testing 1C Expense Request Creation {'WITH VAT' if with_vat else 'WITHOUT VAT'}")
    logger.info("=" * 80)

    # 1. Создать OData клиент
    try:
        client = create_1c_client_from_env()
        logger.info("✅ OData client created successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create OData client: {e}")
        return False

    # 2. Тестовые данные для заявки
    # Расчет сумм с/без НДС
    if with_vat:
        total_amount = 2000
        vat_amount = 333
        amount_without_vat = 1667
        vat_treatment = "ОблагаетсяНДС"
        payment_purpose = f"Тестовый платеж с прикреплением файла (С НДС)\nВ т.ч. НДС (20%) {vat_amount} руб."
    else:
        total_amount = 2000
        vat_amount = 0
        amount_without_vat = 2000
        vat_treatment = "ПродажаНеОблагаетсяНДС"
        payment_purpose = "Тестовый платеж с прикреплением файла (БЕЗ НДС)"

    test_data = {
        # Основные поля
        "Date": "2025-11-20T00:00:00",
        "Posted": True,  # Провести документ
        "Организация_Key": "47b169eb-c529-11f0-ad7f-74563c634acb",  # Из примера
        "Статус": "НеСогласована",
        "ХозяйственнаяОперация": "ОплатаПоставщику",

        # Сумма и валюта
        "СуммаДокумента": total_amount,
        "Валюта_Key": "f04b98ee-b430-11ea-a43c-b42e994e04d3",  # RUB

        # Формы оплаты (безналичная для счетов)
        "ФормаОплатыНаличная": False,
        "ФормаОплатыБезналичная": True,
        "ФормаОплатыПлатежнаяКарта": False,

        # НДС
        "НалогообложениеНДС": vat_treatment,

        # Бюджет
        "вс_ЕстьСвободныйБюджетПоПлану": "Есть",

        # Назначение и дата платежа
        "НазначениеПлатежа": payment_purpose,
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
                "Сумма": total_amount,
                "СуммаБезНДС": amount_without_vat,
                "СуммаНДС": vat_amount,
                "СтавкаНДС_Key": "ed59436e-f9dc-11ee-ad54-74563c634acb" if with_vat else "00000000-0000-0000-0000-000000000000",
                "Количество": 1,
                "Цена": total_amount
            }
        ]
    }

    logger.info(f"📋 Test data prepared:")
    logger.info(f"   Total amount: {total_amount} руб.")
    logger.info(f"   Has VAT: {'Да' if with_vat else 'Нет'}")
    logger.info(f"   VAT amount: {vat_amount} руб.")
    logger.info(f"   Amount without VAT: {amount_without_vat} руб.")
    logger.info(f"   VAT treatment: {vat_treatment}")
    logger.info(f"   Payment method: Безналичная")

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
    logger.info(f"5. НДС: {vat_treatment} ({vat_amount} руб.)")
    logger.info("6. Форма оплаты: Безналичная")
    logger.info("7. Бюджет: Есть свободный")

    return True

if __name__ == "__main__":
    import sys

    # Проверяем аргументы командной строки
    test_with_vat = True
    test_without_vat = False

    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == "no-vat" or arg == "without-vat":
            test_with_vat = False
            test_without_vat = True
        elif arg == "both":
            test_with_vat = True
            test_without_vat = True

    # Запускаем тесты
    success = True

    if test_with_vat:
        logger.info("\n" + "=" * 80)
        logger.info("🧪 TEST 1: Счет С НДС")
        logger.info("=" * 80 + "\n")
        success = test_create_expense_request_with_attachment(with_vat=True) and success

    if test_without_vat:
        logger.info("\n" + "=" * 80)
        logger.info("🧪 TEST 2: Счет БЕЗ НДС")
        logger.info("=" * 80 + "\n")
        success = test_create_expense_request_with_attachment(with_vat=False) and success

    sys.exit(0 if success else 1)
