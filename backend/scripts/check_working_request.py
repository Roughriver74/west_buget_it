"""
Проверим рабочую заявку, которую пользователь создал вручную
"""

from app.services.odata_1c_client import create_1c_client_from_env
from loguru import logger
import json

client = create_1c_client_from_env()

# Получим последнюю заявку с максимальной детализацией
response = client._make_request(
    method='GET',
    endpoint='Document_ЗаявкаНаРасходованиеДенежныхСредств',
    params={
        '$top': 1,
        '$orderby': 'Date desc',
        '$format': 'json'
    }
)

if response and 'value' in response and len(response['value']) > 0:
    item = response['value'][0]
    
    logger.info("📋 Last expense request structure:")
    logger.info(json.dumps(item, indent=2, ensure_ascii=False))
    
    # Особое внимание к полям НДС и форм оплаты
    logger.info(f"\n🔍 Key fields:")
    logger.info(f"  НалогообложениеНДС: '{item.get('НалогообложениеНДС', 'NOT SET')}'")
    logger.info(f"  ФормаОплатыНаличная: {item.get('ФормаОплатыНаличная', 'NOT SET')}")
    logger.info(f"  ФормаОплатыБезналичная: {item.get('ФормаОплатыБезналичная', 'NOT SET')}")
    logger.info(f"  ФормаОплатыПлатежнаяКарта: {item.get('ФормаОплатыПлатежнаяКарта', 'NOT SET')}")
    logger.info(f"  вс_ЕстьСвободныйБюджетПоПлану: '{item.get('вс_ЕстьСвободныйБюджетПоПлану', 'NOT SET')}'")
