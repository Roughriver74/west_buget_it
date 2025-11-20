"""
Скрипт для проверки допустимых значений перечисления ТипыНалогообложенияНДС в 1С
"""

from app.services.odata_1c_client import create_1c_client_from_env
from loguru import logger
import json

def check_vat_enum():
    """Проверить значения перечисления НДС"""
    
    try:
        client = create_1c_client_from_env()
        logger.info("✅ OData client created successfully")
        
        # Попробуем получить значения перечисления через $metadata
        logger.info("\n📋 Checking НалогообложениеНДС enum values...")
        
        # Вариант 1: Попробуем получить существующие заявки и посмотреть на значения
        logger.info("\n1. Fetching existing expense requests to see НалогообложениеНДС values...")
        
        response = client._make_request(
            method='GET',
            endpoint='Document_ЗаявкаНаРасходованиеДенежныхСредств',
            params={
                '$top': 5,
                '$select': 'Ref_Key,Number,НалогообложениеНДС',
                '$format': 'json'
            }
        )
        
        if response and 'value' in response:
            logger.info(f"\nFound {len(response['value'])} expense requests:")
            for item in response['value']:
                vat_value = item.get('НалогообложениеНДС', 'N/A')
                logger.info(f"  • Request {item.get('Number')}: НалогообложениеНДС = {vat_value}")
        
        # Вариант 2: Попробуем напрямую получить перечисление
        logger.info("\n2. Trying to fetch Enum_ТипыНалогообложенияНДС...")
        
        try:
            enum_response = client._make_request(
                method='GET',
                endpoint='Enum_ТипыНалогообложенияНДС',
                params={'$format': 'json', '$top': 20}
            )
            
            if enum_response:
                logger.info(f"\n✅ Enum values found:")
                logger.info(json.dumps(enum_response, indent=2, ensure_ascii=False))
        except Exception as e:
            logger.warning(f"Could not fetch enum directly: {e}")
        
        # Вариант 3: Попробуем $metadata
        logger.info("\n3. Trying to get metadata...")
        try:
            metadata = client._make_request(
                method='GET',
                endpoint='$metadata',
                params={}
            )
            
            if metadata:
                # Ищем упоминание ТипыНалогообложенияНДС
                metadata_str = str(metadata)
                if 'ТипыНалогообложенияНДС' in metadata_str:
                    logger.info("✅ Found ТипыНалогообложенияНДС in metadata")
                    # Найдем этот фрагмент
                    start = metadata_str.find('ТипыНалогообложенияНДС')
                    if start != -1:
                        fragment = metadata_str[max(0, start-200):min(len(metadata_str), start+500)]
                        logger.info(f"Fragment: {fragment}")
        except Exception as e:
            logger.warning(f"Could not fetch metadata: {e}")
            
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)

if __name__ == "__main__":
    check_vat_enum()
