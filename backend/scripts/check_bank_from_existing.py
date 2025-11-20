"""
Проверить банковский счет из существующей заявки
"""

from app.services.odata_1c_client import create_1c_client_from_env
from loguru import logger
import json

client = create_1c_client_from_env()

# Получим одну заявку
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
    
    logger.info(f"📋 Request {item.get('Number')}:")
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
            logger.info(f"\n💳 Bank account details:")
            logger.info(json.dumps(bank_response, indent=2, ensure_ascii=False))
        except Exception as e:
            logger.warning(f"Could not fetch bank account: {e}")
    else:
        logger.info("   Bank account is empty GUID")
        
        # Попробуем получить счета контрагента
        counterparty_key = item.get('Контрагент_Key')
        if counterparty_key:
            try:
                logger.info(f"\n🔍 Searching bank accounts for counterparty {counterparty_key}...")
                accounts = client._make_request(
                    method='GET',
                    endpoint='Catalog_БанковскиеСчетаКонтрагентов',
                    params={
                        '$top': 5,
                        '$format': 'json'
                    }
                )
                
                if accounts and 'value' in accounts:
                    logger.info(f"\nFound {len(accounts['value'])} bank accounts:")
                    for acc in accounts['value'][:3]:
                        logger.info(f"  • {acc.get('Description', 'N/A')}: {acc.get('НомерСчета', 'N/A')}")
            except Exception as e:
                logger.warning(f"Could not fetch bank accounts: {e}")
