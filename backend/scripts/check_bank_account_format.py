"""
Проверить формат банковского счета в рабочей заявке 1С
"""

from app.services.odata_1c_client import create_1c_client_from_env
from loguru import logger
import json

client = create_1c_client_from_env()

# Получим заявку с непустым БанковскийСчетКонтрагента
response = client._make_request(
    method='GET',
    endpoint='Document_ЗаявкаНаРасходованиеДенежныхСредств',
    params={
        '$top': 10,
        '$orderby': 'Date desc',
        '$filter': "БанковскийСчетКонтрагента_Key ne guid'00000000-0000-0000-0000-000000000000'",
        '$format': 'json'
    }
)

if response and 'value' in response:
    logger.info(f"Found {len(response['value'])} requests with bank account")
    
    for item in response['value']:
        logger.info(f"\n📋 Request {item.get('Number')}:")
        logger.info(f"   БанковскийСчетКонтрагента_Key: {item.get('БанковскийСчетКонтрагента_Key')}")
        logger.info(f"   Контрагент_Key: {item.get('Контрагент_Key')}")
        
        # Попробуем получить информацию о банковском счете
        bank_account_key = item.get('БанковскийСчетКонтрагента_Key')
        if bank_account_key and bank_account_key != '00000000-0000-0000-0000-000000000000':
            try:
                bank_response = client._make_request(
                    method='GET',
                    endpoint=f"Catalog_БанковскиеСчетаКонтрагентов(guid'{bank_account_key}')",
                    params={'$format': 'json'}
                )
                logger.info(f"   Bank account details:")
                logger.info(json.dumps(bank_response, indent=2, ensure_ascii=False))
            except Exception as e:
                logger.warning(f"   Could not fetch bank account: {e}")
        
        # Только первую заявку детально
        break
else:
    logger.info("No requests with bank account found")
