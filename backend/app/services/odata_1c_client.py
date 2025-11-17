"""
1C OData Integration Service

Сервис для интеграции с 1С через стандартный интерфейс OData
"""

import logging
import base64
from typing import Optional, Dict, Any, List
from datetime import datetime, date
import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


class OData1CClient:
    """Client for 1C OData API integration"""

    def __init__(self, base_url: str, username: str, password: str):
        """
        Initialize 1C OData client

        Args:
            base_url: Base URL for OData endpoint (e.g., http://10.10.100.77/trade/odata/standard.odata)
            username: Username for authentication
            password: Password for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(username, password)
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Make HTTP request to OData API

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            data: Request body data
            timeout: Request timeout in seconds

        Returns:
            Response data as dictionary

        Raises:
            requests.exceptions.RequestException: On request errors
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                timeout=timeout
            )
            response.raise_for_status()

            # Handle empty responses
            if not response.content:
                return {}

            return response.json()

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}, URL: {url}, Response: {e.response.text if e.response else 'N/A'}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}, URL: {url}")
            raise
        except ValueError as e:
            logger.error(f"JSON decode error: {e}, Response: {response.text}")
            raise

    def get_bank_receipts(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        top: int = 100,
        skip: int = 0,
        only_posted: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Получить поступления денежных средств из 1С

        Args:
            date_from: Начальная дата периода (используется $filter если задан только год)
            date_to: Конечная дата периода (фильтруется на клиенте)
            top: Количество записей (max 1000)
            skip: Пропустить N записей (для пагинации)
            only_posted: Только проведенные документы (фильтруется на клиенте)

        Returns:
            Список документов поступлений

        Note:
            Если указан только date_from с началом года, использует OData $filter: year(Date) gt YYYY.
            Важно: фильтр должен быть встроен в URL, а не передан через params словарь!
        """
        # Базовые параметры
        top_value = min(top, 1000)  # Ограничение 1С

        # Построить URL с параметрами
        # ВАЖНО: НЕ используем params словарь для $filter!
        # 1С не принимает фильтр через params, только встроенный в URL
        endpoint_with_params = f'Document_ПоступлениеБезналичныхДенежныхСредств?$top={top_value}&$format=json&$skip={skip}'

        # Добавить OData $filter
        if date_from and date_to:
            # Используем точный фильтр по диапазону дат (Date >= start AND Date <= end)
            filter_str = f"Date ge datetime'{date_from.isoformat()}T00:00:00' and Date le datetime'{date_to.isoformat()}T23:59:59'"
            endpoint_with_params += f'&$filter={filter_str}'
            logger.info(f"Using OData filter: {filter_str}")
        elif date_from:
            # Только начальная дата - фильтруем начиная с даты
            filter_str = f"Date ge datetime'{date_from.isoformat()}T00:00:00'"
            endpoint_with_params += f'&$filter={filter_str}'
            logger.info(f"Using OData filter: {filter_str}")
        elif date_to:
            # Только конечная дата - фильтруем до даты
            filter_str = f"Date le datetime'{date_to.isoformat()}T23:59:59'"
            endpoint_with_params += f'&$filter={filter_str}'
            logger.info(f"Using OData filter: {filter_str}")

        logger.info(f"Fetching bank receipts: date_from={date_from}, date_to={date_to}, top={top}, skip={skip}")

        response = self._make_request(
            method='GET',
            endpoint=endpoint_with_params,
            params=None  # Не передаем params - всё уже в URL
        )

        results = response.get('value', [])

        # Фильтрация только невалидных дат (OData фильтр уже применён на сервере)
        if results:
            results = [
                r for r in results
                if r.get('Date') and r.get('Date') != '0001-01-01T00:00:00'
            ]

        # Фильтр по проведенным документам
        if only_posted and results and 'Posted' in results[0]:
            results = [r for r in results if r.get('Posted') == True]

        return results

    def get_bank_payments(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        top: int = 100,
        skip: int = 0,
        only_posted: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Получить списания денежных средств из 1С

        Args:
            date_from: Начальная дата периода (используется $filter если задан только год)
            date_to: Конечная дата периода (фильтруется на клиенте)
            top: Количество записей (max 1000)
            skip: Пропустить N записей (для пагинации)
            only_posted: Только проведенные документы (фильтруется на клиенте)

        Returns:
            Список документов списаний

        Note:
            Если указан только date_from с началом года, использует OData $filter: year(Date) gt YYYY.
            Важно: фильтр должен быть встроен в URL, а не передан через params словарь!
        """
        # Базовые параметры
        top_value = min(top, 1000)

        # Построить URL с параметрами
        # ВАЖНО: НЕ используем params словарь для $filter!
        # 1С не принимает фильтр через params, только встроенный в URL
        endpoint_with_params = f'Document_СписаниеБезналичныхДенежныхСредств?$top={top_value}&$format=json&$skip={skip}'

        # Добавить OData $filter
        if date_from and date_to:
            # Используем точный фильтр по диапазону дат (Date >= start AND Date <= end)
            filter_str = f"Date ge datetime'{date_from.isoformat()}T00:00:00' and Date le datetime'{date_to.isoformat()}T23:59:59'"
            endpoint_with_params += f'&$filter={filter_str}'
            logger.info(f"Using OData filter: {filter_str}")
        elif date_from:
            # Только начальная дата - фильтруем начиная с даты
            filter_str = f"Date ge datetime'{date_from.isoformat()}T00:00:00'"
            endpoint_with_params += f'&$filter={filter_str}'
            logger.info(f"Using OData filter: {filter_str}")
        elif date_to:
            # Только конечная дата - фильтруем до даты
            filter_str = f"Date le datetime'{date_to.isoformat()}T23:59:59'"
            endpoint_with_params += f'&$filter={filter_str}'
            logger.info(f"Using OData filter: {filter_str}")

        logger.info(f"Fetching bank payments: date_from={date_from}, date_to={date_to}, top={top}, skip={skip}")

        response = self._make_request(
            method='GET',
            endpoint=endpoint_with_params,
            params=None  # Не передаем params - всё уже в URL
        )

        results = response.get('value', [])

        # Фильтрация только невалидных дат (OData фильтр уже применён на сервере)
        if results:
            results = [
                r for r in results
                if r.get('Date') and r.get('Date') != '0001-01-01T00:00:00'
            ]

        # Фильтр по проведенным документам
        if only_posted and results and 'Posted' in results[0]:
            results = [r for r in results if r.get('Posted') == True]

        return results

    def get_cash_receipts(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        top: int = 100,
        skip: int = 0,
        only_posted: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Получить приходные кассовые ордера (ПКО) из 1С

        Args:
            date_from: Начальная дата периода (используется $filter если задан только год)
            date_to: Конечная дата периода (фильтруется на клиенте)
            top: Количество записей (max 1000)
            skip: Пропустить N записей (для пагинации)
            only_posted: Только проведенные документы (фильтруется на клиенте)

        Returns:
            Список приходных кассовых ордеров

        Note:
            Если указан только date_from с началом года, использует OData $filter: year(Date) gt YYYY.
            Важно: фильтр должен быть встроен в URL, а не передан через params словарь!
        """
        # Базовые параметры
        top_value = min(top, 1000)  # Ограничение 1С

        # Построить URL с параметрами
        # ВАЖНО: НЕ используем params словарь для $filter!
        # 1С не принимает фильтр через params, только встроенный в URL
        endpoint_with_params = f'Document_ПриходныйКассовыйОрдер?$top={top_value}&$format=json&$skip={skip}'

        # Добавить OData $filter
        if date_from and date_to:
            # Если указаны обе даты и они в одном месяце - фильтруем точно по месяцу
            if date_from.year == date_to.year and date_from.month == date_to.month:
                filter_str = f'year(Date) eq {date_from.year} and month(Date) eq {date_from.month}'
                endpoint_with_params += f'&$filter={filter_str}'
                logger.info(f"Using OData filter for cash receipts: {filter_str}")
            else:
                # Для диапазона используем фильтр по году
                year_filter = date_from.year - 1
                endpoint_with_params += f'&$filter=year(Date) gt {year_filter}'
                logger.info(f"Using OData filter for cash receipts: year(Date) gt {year_filter}")
        elif date_from:
            # Только начальная дата - фильтруем по году
            year_filter = date_from.year - 1
            endpoint_with_params += f'&$filter=year(Date) gt {year_filter}'
            logger.info(f"Using OData filter for cash receipts: year(Date) gt {year_filter}")

        logger.info(f"Fetching cash receipts (PKO): date_from={date_from}, date_to={date_to}, top={top}, skip={skip}")

        response = self._make_request(
            method='GET',
            endpoint=endpoint_with_params,
            params=None  # Не передаем params - всё уже в URL
        )

        results = response.get('value', [])

        # Фильтрация только невалидных дат (OData фильтр уже применён на сервере)
        if results:
            results = [
                r for r in results
                if r.get('Date') and r.get('Date') != '0001-01-01T00:00:00'
            ]

        # Фильтр по проведенным документам
        if only_posted and results and 'Posted' in results[0]:
            results = [r for r in results if r.get('Posted') == True]

        return results

    def get_cash_payments(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        top: int = 100,
        skip: int = 0,
        only_posted: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Получить расходные кассовые ордера (РКО) из 1С

        Args:
            date_from: Начальная дата периода (используется $filter если задан только год)
            date_to: Конечная дата периода (фильтруется на клиенте)
            top: Количество записей (max 1000)
            skip: Пропустить N записей (для пагинации)
            only_posted: Только проведенные документы (фильтруется на клиенте)

        Returns:
            Список расходных кассовых ордеров

        Note:
            Если указан только date_from с началом года, использует OData $filter: year(Date) gt YYYY.
            Важно: фильтр должен быть встроен в URL, а не передан через params словарь!
        """
        # Базовые параметры
        top_value = min(top, 1000)

        # Построить URL с параметрами
        # ВАЖНО: НЕ используем params словарь для $filter!
        # 1С не принимает фильтр через params, только встроенный в URL
        endpoint_with_params = f'Document_РасходныйКассовыйОрдер?$top={top_value}&$format=json&$skip={skip}'

        # Добавить OData $filter
        if date_from and date_to:
            # Если указаны обе даты и они в одном месяце - фильтруем точно по месяцу
            if date_from.year == date_to.year and date_from.month == date_to.month:
                filter_str = f'year(Date) eq {date_from.year} and month(Date) eq {date_from.month}'
                endpoint_with_params += f'&$filter={filter_str}'
                logger.info(f"Using OData filter for cash payments: {filter_str}")
            else:
                # Для диапазона используем фильтр по году
                year_filter = date_from.year - 1
                endpoint_with_params += f'&$filter=year(Date) gt {year_filter}'
                logger.info(f"Using OData filter for cash payments: year(Date) gt {year_filter}")
        elif date_from:
            # Только начальная дата - фильтруем по году
            year_filter = date_from.year - 1
            endpoint_with_params += f'&$filter=year(Date) gt {year_filter}'
            logger.info(f"Using OData filter for cash payments: year(Date) gt {year_filter}")

        logger.info(f"Fetching cash payments (RKO): date_from={date_from}, date_to={date_to}, top={top}, skip={skip}")

        response = self._make_request(
            method='GET',
            endpoint=endpoint_with_params,
            params=None  # Не передаем params - всё уже в URL
        )

        results = response.get('value', [])

        # Фильтрация только невалидных дат (OData фильтр уже применён на сервере)
        if results:
            results = [
                r for r in results
                if r.get('Date') and r.get('Date') != '0001-01-01T00:00:00'
            ]

        # Фильтр по проведенным документам
        if only_posted and results and 'Posted' in results[0]:
            results = [r for r in results if r.get('Posted') == True]

        return results

    def get_counterparty_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Получить контрагента по ключу

        Args:
            key: GUID контрагента

        Returns:
            Данные контрагента или None
        """
        if not key or key == "00000000-0000-0000-0000-000000000000":
            return None

        try:
            response = self._make_request(
                method='GET',
                endpoint=f"Catalog_Контрагенты(guid'{key}')",
                params={'$format': 'json'}
            )
            return response
        except Exception as e:
            logger.warning(f"Failed to fetch counterparty {key}: {e}")
            return None

    def get_organization_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Получить организацию по ключу

        Args:
            key: GUID организации

        Returns:
            Данные организации или None
        """
        if not key or key == "00000000-0000-0000-0000-000000000000":
            return None

        try:
            response = self._make_request(
                method='GET',
                endpoint=f"Catalog_Организации(guid'{key}')",
                params={'$format': 'json'}
            )
            return response
        except Exception as e:
            logger.warning(f"Failed to fetch organization {key}: {e}")
            return None

    def get_expense_requests(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        top: int = 100,
        skip: int = 0,
        only_posted: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Получить заявки на расходование денежных средств из 1С

        Args:
            date_from: Начальная дата периода (используется $filter если задан только год)
            date_to: Конечная дата периода (фильтруется на клиенте)
            top: Количество записей (max 1000)
            skip: Пропустить N записей (для пагинации)
            only_posted: Только проведенные документы (фильтруется на клиенте)

        Returns:
            Список документов заявок на расход

        Note:
            Если указан только date_from с началом года, использует OData $filter: year(Date) gt YYYY.
            Важно: фильтр должен быть встроен в URL, а не передан через params словарь!
        """
        # Базовые параметры
        top_value = min(top, 1000)  # Ограничение 1С

        # Построить URL с параметрами
        # ВАЖНО: НЕ используем params словарь для $filter!
        # 1С не принимает фильтр через params, только встроенный в URL
        endpoint_with_params = f'Document_ЗаявкаНаРасходованиеДенежныхСредств?$top={top_value}&$format=json&$skip={skip}'

        # Добавить OData $filter
        if date_from and date_to:
            # Используем точный фильтр по диапазону дат (Date >= start AND Date <= end)
            filter_str = f"Date ge datetime'{date_from.isoformat()}T00:00:00' and Date le datetime'{date_to.isoformat()}T23:59:59'"
            endpoint_with_params += f'&$filter={filter_str}'
            logger.info(f"Using OData filter: {filter_str}")
        elif date_from:
            # Только начальная дата - фильтруем начиная с даты
            filter_str = f"Date ge datetime'{date_from.isoformat()}T00:00:00'"
            endpoint_with_params += f'&$filter={filter_str}'
            logger.info(f"Using OData filter: {filter_str}")
        elif date_to:
            # Только конечная дата - фильтруем до даты
            filter_str = f"Date le datetime'{date_to.isoformat()}T23:59:59'"
            endpoint_with_params += f'&$filter={filter_str}'
            logger.info(f"Using OData filter: {filter_str}")

        logger.info(f"Fetching expense requests: date_from={date_from}, date_to={date_to}, top={top}, skip={skip}")

        response = self._make_request(
            method='GET',
            endpoint=endpoint_with_params,
            params=None  # Не передаем params - всё уже в URL
        )

        results = response.get('value', [])

        # Фильтрация только невалидных дат (OData фильтр уже применён на сервере)
        if results:
            results = [
                r for r in results
                if r.get('Date') and r.get('Date') != '0001-01-01T00:00:00'
            ]

        # Фильтр по проведенным документам
        if only_posted and results and 'Posted' in results[0]:
            results = [r for r in results if r.get('Posted') == True]

        return results

    def get_organizations(
        self,
        top: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Получить список организаций из 1С

        Args:
            top: Количество записей (max 1000)
            skip: Пропустить N записей (для пагинации)

        Returns:
            Список организаций
        """
        top_value = min(top, 1000)

        endpoint_with_params = f'Catalog_Организации?$top={top_value}&$format=json&$skip={skip}'

        logger.info(f"Fetching organizations: top={top}, skip={skip}")

        response = self._make_request(
            method='GET',
            endpoint=endpoint_with_params,
            params=None
        )

        results = response.get('value', [])
        logger.info(f"Fetched {len(results)} organizations")

        return results

    def get_cash_flow_categories(
        self,
        top: int = 100,
        skip: int = 0,
        include_folders: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Получить статьи движения денежных средств из 1С

        Args:
            top: Количество записей (max 1000)
            skip: Пропустить N записей (для пагинации)
            include_folders: Включать папки (группы) в результат

        Returns:
            Список статей ДДС
        """
        top_value = min(top, 1000)

        endpoint_with_params = f'Catalog_СтатьиДвиженияДенежныхСредств?$top={top_value}&$format=json&$skip={skip}'

        logger.info(f"Fetching cash flow categories: top={top}, skip={skip}")

        response = self._make_request(
            method='GET',
            endpoint=endpoint_with_params,
            params=None
        )

        results = response.get('value', [])

        # Фильтровать по папкам если нужно
        if not include_folders:
            results = [r for r in results if not r.get('IsFolder', False)]

        logger.info(f"Fetched {len(results)} cash flow categories")

        return results

    def test_connection(self) -> bool:
        """
        Проверить подключение к 1С OData

        Returns:
            True если подключение успешно
        """
        try:
            response = self._make_request(
                method='GET',
                endpoint='',
                params={'$format': 'json'},
                timeout=10
            )
            logger.info("1C OData connection test successful")
            return True
        except Exception as e:
            logger.error(f"1C OData connection test failed: {e}")
            return False


def create_1c_client_from_env() -> OData1CClient:
    """
    Создать клиент 1С OData из переменных окружения

    Environment variables:
        ODATA_1C_URL: Base URL for OData
        ODATA_1C_USERNAME: Username
        ODATA_1C_PASSWORD: Password

    Returns:
        Configured OData1CClient instance
    """
    import os

    url = os.getenv('ODATA_1C_URL', 'http://10.10.100.77/trade/odata/standard.odata')
    username = os.getenv('ODATA_1C_USERNAME', 'odata.user')
    password = os.getenv('ODATA_1C_PASSWORD', 'ak228Hu2hbs28')

    return OData1CClient(
        base_url=url,
        username=username,
        password=password
    )
