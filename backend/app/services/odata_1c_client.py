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

    def __init__(self, base_url: str, username: str = None, password: str = None,
                 custom_auth_token: str = None):
        """
        Initialize 1C OData client

        Args:
            base_url: Base URL for OData endpoint (e.g., http://10.10.100.77/trade/odata/standard.odata)
            username: Username for authentication (if not using custom_auth_token)
            password: Password for authentication (if not using custom_auth_token)
            custom_auth_token: Custom authorization token (e.g., "Basic base64string")
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()

        # Use custom auth token if provided, otherwise use username/password
        if custom_auth_token:
            self.session.headers.update({
                'Authorization': custom_auth_token,
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            })
            logger.info("Using custom authorization token")
        else:
            self.session.auth = HTTPBasicAuth(username, password)
            self.session.headers.update({
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            })
            logger.info(f"Using HTTPBasicAuth with username: {username}")

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
        only_posted: bool = True  # Deprecated, always filters for posted documents
    ) -> List[Dict[str, Any]]:
        """
        Получить поступления денежных средств из 1С

        Args:
            date_from: Начальная дата периода
            date_to: Конечная дата периода
            top: Количество записей (max 1000)
            skip: Пропустить N записей (для пагинации)
            only_posted: Deprecated (always True) - теперь всегда фильтрует проведенные документы через OData

        Returns:
            Список документов поступлений (только проведенные и не помеченные на удаление)

        Note:
            ОБЯЗАТЕЛЬНЫЕ фильтры применяются на уровне OData API:
            - Posted eq true (только проведённые документы)
            - DeletionMark eq false (не помеченные на удаление)
        """
        # Базовые параметры
        top_value = min(top, 1000)  # Ограничение 1С

        # Построить URL с параметрами
        # ВАЖНО: НЕ используем params словарь для $filter!
        # 1С не принимает фильтр через params, только встроенный в URL
        endpoint_with_params = f'Document_ПоступлениеБезналичныхДенежныхСредств?$top={top_value}&$format=json&$skip={skip}'

        # ОБЯЗАТЕЛЬНЫЕ фильтры для всех документов из 1С
        mandatory_filters = "Posted eq true and DeletionMark eq false"

        # Добавить OData $filter
        if date_from and date_to:
            # Используем точный фильтр по диапазону дат (Date >= start AND Date <= end)
            filter_str = f"{mandatory_filters} and Date ge datetime'{date_from.isoformat()}T00:00:00' and Date le datetime'{date_to.isoformat()}T23:59:59'"
            endpoint_with_params += f'&$filter={filter_str}'
            logger.info(f"Using OData filter: {filter_str}")
        elif date_from:
            # Только начальная дата - фильтруем начиная с даты
            filter_str = f"{mandatory_filters} and Date ge datetime'{date_from.isoformat()}T00:00:00'"
            endpoint_with_params += f'&$filter={filter_str}'
            logger.info(f"Using OData filter: {filter_str}")
        elif date_to:
            # Только конечная дата - фильтруем до даты
            filter_str = f"{mandatory_filters} and Date le datetime'{date_to.isoformat()}T23:59:59'"
            endpoint_with_params += f'&$filter={filter_str}'
            logger.info(f"Using OData filter: {filter_str}")
        else:
            # Без дат - только обязательные фильтры
            endpoint_with_params += f'&$filter={mandatory_filters}'
            logger.info(f"Using OData filter: {mandatory_filters}")

        logger.info(f"Fetching bank receipts: date_from={date_from}, date_to={date_to}, top={top}, skip={skip}")

        response = self._make_request(
            method='GET',
            endpoint=endpoint_with_params,
            params=None  # Не передаем params - всё уже в URL
        )

        results = response.get('value', [])

        # Фильтрация только невалидных дат (Posted и DeletionMark уже отфильтрованы на сервере)
        if results:
            results = [
                r for r in results
                if r.get('Date') and r.get('Date') != '0001-01-01T00:00:00'
            ]

        return results

    def get_bank_payments(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        top: int = 100,
        skip: int = 0,
        only_posted: bool = True  # Deprecated, always filters for posted documents
    ) -> List[Dict[str, Any]]:
        """
        Получить списания денежных средств из 1С

        Args:
            date_from: Начальная дата периода
            date_to: Конечная дата периода
            top: Количество записей (max 1000)
            skip: Пропустить N записей (для пагинации)
            only_posted: Deprecated (always True) - теперь всегда фильтрует проведенные документы через OData

        Returns:
            Список документов списаний (только проведенные и не помеченные на удаление)

        Note:
            ОБЯЗАТЕЛЬНЫЕ фильтры применяются на уровне OData API:
            - Posted eq true (только проведённые документы)
            - DeletionMark eq false (не помеченные на удаление)
        """
        # Базовые параметры
        top_value = min(top, 1000)

        # Построить URL с параметрами
        # ВАЖНО: НЕ используем params словарь для $filter!
        # 1С не принимает фильтр через params, только встроенный в URL
        endpoint_with_params = f'Document_СписаниеБезналичныхДенежныхСредств?$top={top_value}&$format=json&$skip={skip}'

        # ОБЯЗАТЕЛЬНЫЕ фильтры для всех документов из 1С
        mandatory_filters = "Posted eq true and DeletionMark eq false"

        # Добавить OData $filter
        if date_from and date_to:
            # Используем точный фильтр по диапазону дат (Date >= start AND Date <= end)
            filter_str = f"{mandatory_filters} and Date ge datetime'{date_from.isoformat()}T00:00:00' and Date le datetime'{date_to.isoformat()}T23:59:59'"
            endpoint_with_params += f'&$filter={filter_str}'
            logger.info(f"Using OData filter: {filter_str}")
        elif date_from:
            # Только начальная дата - фильтруем начиная с даты
            filter_str = f"{mandatory_filters} and Date ge datetime'{date_from.isoformat()}T00:00:00'"
            endpoint_with_params += f'&$filter={filter_str}'
            logger.info(f"Using OData filter: {filter_str}")
        elif date_to:
            # Только конечная дата - фильтруем до даты
            filter_str = f"{mandatory_filters} and Date le datetime'{date_to.isoformat()}T23:59:59'"
            endpoint_with_params += f'&$filter={filter_str}'
            logger.info(f"Using OData filter: {filter_str}")
        else:
            # Без дат - только обязательные фильтры
            endpoint_with_params += f'&$filter={mandatory_filters}'
            logger.info(f"Using OData filter: {mandatory_filters}")

        logger.info(f"Fetching bank payments: date_from={date_from}, date_to={date_to}, top={top}, skip={skip}")

        response = self._make_request(
            method='GET',
            endpoint=endpoint_with_params,
            params=None  # Не передаем params - всё уже в URL
        )

        results = response.get('value', [])

        # Фильтрация только невалидных дат (Posted и DeletionMark уже отфильтрованы на сервере)
        if results:
            results = [
                r for r in results
                if r.get('Date') and r.get('Date') != '0001-01-01T00:00:00'
            ]

        return results

    def get_cash_receipts(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        top: int = 100,
        skip: int = 0,
        only_posted: bool = True  # Deprecated, always filters for posted documents
    ) -> List[Dict[str, Any]]:
        """
        Получить приходные кассовые ордера (ПКО) из 1С

        Args:
            date_from: Начальная дата периода
            date_to: Конечная дата периода
            top: Количество записей (max 1000)
            skip: Пропустить N записей (для пагинации)
            only_posted: Deprecated (always True) - теперь всегда фильтрует проведенные документы через OData

        Returns:
            Список приходных кассовых ордеров (только проведенные и не помеченные на удаление)

        Note:
            ОБЯЗАТЕЛЬНЫЕ фильтры применяются на уровне OData API:
            - Posted eq true (только проведённые документы)
            - DeletionMark eq false (не помеченные на удаление)
        """
        # Базовые параметры
        top_value = min(top, 1000)  # Ограничение 1С

        # Построить URL с параметрами
        # ВАЖНО: НЕ используем params словарь для $filter!
        # 1С не принимает фильтр через params, только встроенный в URL
        endpoint_with_params = f'Document_ПриходныйКассовыйОрдер?$top={top_value}&$format=json&$skip={skip}'

        # ОБЯЗАТЕЛЬНЫЕ фильтры для всех документов из 1С
        mandatory_filters = "Posted eq true and DeletionMark eq false"

        # Добавить OData $filter
        if date_from and date_to:
            # Если указаны обе даты и они в одном месяце - фильтруем точно по месяцу
            if date_from.year == date_to.year and date_from.month == date_to.month:
                filter_str = f'{mandatory_filters} and year(Date) eq {date_from.year} and month(Date) eq {date_from.month}'
                endpoint_with_params += f'&$filter={filter_str}'
                logger.info(f"Using OData filter for cash receipts: {filter_str}")
            else:
                # Для диапазона используем фильтр по году
                year_filter = date_from.year - 1
                filter_str = f'{mandatory_filters} and year(Date) gt {year_filter}'
                endpoint_with_params += f'&$filter={filter_str}'
                logger.info(f"Using OData filter for cash receipts: {filter_str}")
        elif date_from:
            # Только начальная дата - фильтруем по году
            year_filter = date_from.year - 1
            filter_str = f'{mandatory_filters} and year(Date) gt {year_filter}'
            endpoint_with_params += f'&$filter={filter_str}'
            logger.info(f"Using OData filter for cash receipts: {filter_str}")
        else:
            # Без дат - только обязательные фильтры
            endpoint_with_params += f'&$filter={mandatory_filters}'
            logger.info(f"Using OData filter: {mandatory_filters}")

        logger.info(f"Fetching cash receipts (PKO): date_from={date_from}, date_to={date_to}, top={top}, skip={skip}")

        response = self._make_request(
            method='GET',
            endpoint=endpoint_with_params,
            params=None  # Не передаем params - всё уже в URL
        )

        results = response.get('value', [])

        # Фильтрация только невалидных дат (Posted и DeletionMark уже отфильтрованы на сервере)
        if results:
            results = [
                r for r in results
                if r.get('Date') and r.get('Date') != '0001-01-01T00:00:00'
            ]

        return results

    def get_cash_payments(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        top: int = 100,
        skip: int = 0,
        only_posted: bool = True  # Deprecated, always filters for posted documents
    ) -> List[Dict[str, Any]]:
        """
        Получить расходные кассовые ордера (РКО) из 1С

        Args:
            date_from: Начальная дата периода
            date_to: Конечная дата периода
            top: Количество записей (max 1000)
            skip: Пропустить N записей (для пагинации)
            only_posted: Deprecated (always True) - теперь всегда фильтрует проведенные документы через OData

        Returns:
            Список расходных кассовых ордеров (только проведенные и не помеченные на удаление)

        Note:
            ОБЯЗАТЕЛЬНЫЕ фильтры применяются на уровне OData API:
            - Posted eq true (только проведённые документы)
            - DeletionMark eq false (не помеченные на удаление)
        """
        # Базовые параметры
        top_value = min(top, 1000)

        # Построить URL с параметрами
        # ВАЖНО: НЕ используем params словарь для $filter!
        # 1С не принимает фильтр через params, только встроенный в URL
        endpoint_with_params = f'Document_РасходныйКассовыйОрдер?$top={top_value}&$format=json&$skip={skip}'

        # ОБЯЗАТЕЛЬНЫЕ фильтры для всех документов из 1С
        mandatory_filters = "Posted eq true and DeletionMark eq false"

        # Добавить OData $filter
        if date_from and date_to:
            # Если указаны обе даты и они в одном месяце - фильтруем точно по месяцу
            if date_from.year == date_to.year and date_from.month == date_to.month:
                filter_str = f'{mandatory_filters} and year(Date) eq {date_from.year} and month(Date) eq {date_from.month}'
                endpoint_with_params += f'&$filter={filter_str}'
                logger.info(f"Using OData filter for cash payments: {filter_str}")
            else:
                # Для диапазона используем фильтр по году
                year_filter = date_from.year - 1
                filter_str = f'{mandatory_filters} and year(Date) gt {year_filter}'
                endpoint_with_params += f'&$filter={filter_str}'
                logger.info(f"Using OData filter for cash payments: {filter_str}")
        elif date_from:
            # Только начальная дата - фильтруем по году
            year_filter = date_from.year - 1
            filter_str = f'{mandatory_filters} and year(Date) gt {year_filter}'
            endpoint_with_params += f'&$filter={filter_str}'
            logger.info(f"Using OData filter for cash payments: {filter_str}")
        else:
            # Без дат - только обязательные фильтры
            endpoint_with_params += f'&$filter={mandatory_filters}'
            logger.info(f"Using OData filter: {mandatory_filters}")

        logger.info(f"Fetching cash payments (RKO): date_from={date_from}, date_to={date_to}, top={top}, skip={skip}")

        response = self._make_request(
            method='GET',
            endpoint=endpoint_with_params,
            params=None  # Не передаем params - всё уже в URL
        )

        results = response.get('value', [])

        # Фильтрация только невалидных дат (Posted и DeletionMark уже отфильтрованы на сервере)
        if results:
            results = [
                r for r in results
                if r.get('Date') and r.get('Date') != '0001-01-01T00:00:00'
            ]

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

    def get_subdivision_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Получить подразделение по наименованию

        Args:
            name: Наименование подразделения (например: "Москва", "СПБ")

        Returns:
            Данные подразделения (включая Ref_Key) или None
        """
        if not name or not name.strip():
            return None

        try:
            # Фильтр по наименованию (Description или другое поле в 1С)
            filter_str = f"Description eq '{name}'"
            response = self._make_request(
                method='GET',
                endpoint=f"Catalog_Подразделения?$filter={filter_str}&$format=json&$top=1"
            )

            # Проверить результат
            if response and 'value' in response and len(response['value']) > 0:
                subdivision = response['value'][0]
                logger.info(f"Found subdivision '{name}' with GUID: {subdivision.get('Ref_Key')}")
                return subdivision
            else:
                logger.warning(f"Subdivision '{name}' not found in 1C")
                return None

        except Exception as e:
            logger.warning(f"Failed to fetch subdivision '{name}': {e}")
            return None

    def get_expense_requests(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        top: int = 100,
        skip: int = 0,
        only_posted: bool = True  # Deprecated, always filters for posted documents
    ) -> List[Dict[str, Any]]:
        """
        Получить заявки на расходование денежных средств из 1С

        Args:
            date_from: Начальная дата периода
            date_to: Конечная дата периода
            top: Количество записей (max 1000)
            skip: Пропустить N записей (для пагинации)
            only_posted: Deprecated (always True) - теперь всегда фильтрует проведенные документы через OData

        Returns:
            Список документов заявок на расход (только проведенные и не помеченные на удаление)

        Note:
            ОБЯЗАТЕЛЬНЫЕ фильтры применяются на уровне OData API:
            - Posted eq true (только проведённые документы)
            - DeletionMark eq false (не помеченные на удаление)
        """
        # Базовые параметры
        top_value = min(top, 1000)  # Ограничение 1С

        # Построить URL с параметрами
        # ВАЖНО: НЕ используем params словарь для $filter!
        # 1С не принимает фильтр через params, только встроенный в URL
        endpoint_with_params = f'Document_ЗаявкаНаРасходованиеДенежныхСредств?$top={top_value}&$format=json&$skip={skip}'

        # ОБЯЗАТЕЛЬНЫЕ фильтры для всех документов из 1С
        mandatory_filters = "Posted eq true and DeletionMark eq false"

        # Добавить OData $filter
        if date_from and date_to:
            # Используем точный фильтр по диапазону дат (Date >= start AND Date <= end)
            filter_str = f"{mandatory_filters} and Date ge datetime'{date_from.isoformat()}T00:00:00' and Date le datetime'{date_to.isoformat()}T23:59:59'"
            endpoint_with_params += f'&$filter={filter_str}'
            logger.info(f"Using OData filter: {filter_str}")
        elif date_from:
            # Только начальная дата - фильтруем начиная с даты
            filter_str = f"{mandatory_filters} and Date ge datetime'{date_from.isoformat()}T00:00:00'"
            endpoint_with_params += f'&$filter={filter_str}'
            logger.info(f"Using OData filter: {filter_str}")
        elif date_to:
            # Только конечная дата - фильтруем до даты
            filter_str = f"{mandatory_filters} and Date le datetime'{date_to.isoformat()}T23:59:59'"
            endpoint_with_params += f'&$filter={filter_str}'
            logger.info(f"Using OData filter: {filter_str}")
        else:
            # Без дат - только обязательные фильтры
            endpoint_with_params += f'&$filter={mandatory_filters}'
            logger.info(f"Using OData filter: {mandatory_filters}")

        logger.info(f"Fetching expense requests: date_from={date_from}, date_to={date_to}, top={top}, skip={skip}")

        response = self._make_request(
            method='GET',
            endpoint=endpoint_with_params,
            params=None  # Не передаем params - всё уже в URL
        )

        results = response.get('value', [])

        # Фильтрация только невалидных дат (Posted и DeletionMark уже отфильтрованы на сервере)
        if results:
            results = [
                r for r in results
                if r.get('Date') and r.get('Date') != '0001-01-01T00:00:00'
            ]

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

    def get_counterparty_by_inn(self, inn: str) -> Optional[Dict[str, Any]]:
        """
        Получить контрагента по ИНН

        Args:
            inn: ИНН контрагента

        Returns:
            Данные контрагента или None если не найден
        """
        if not inn:
            return None

        try:
            # OData $filter по полю ИНН (формат как в рабочем примере)
            filter_str = f"ИНН eq '{inn}'"
            endpoint_with_params = f"Catalog_Контрагенты?$top=1&$format=json&$filter={filter_str}"

            logger.info(f"Searching counterparty by INN: {inn}")
            logger.info(f"Request URL: {self.base_url}/{endpoint_with_params}")

            response = self._make_request(
                method='GET',
                endpoint=endpoint_with_params,
                params=None
            )

            logger.debug(f"Counterparty search response: {response}")

            results = response.get('value', [])
            if results:
                logger.info(f"Found counterparty with INN {inn}: {results[0].get('Description')}")
                return results[0]  # Возвращаем первого найденного
            else:
                logger.warning(f"Counterparty with INN {inn} not found in 1C")
                return None

        except Exception as e:
            logger.error(f"Failed to search counterparty by INN {inn}: {e}")
            return None

    def get_organization_by_inn(self, inn: str) -> Optional[Dict[str, Any]]:
        """
        Получить организацию по ИНН

        Args:
            inn: ИНН организации

        Returns:
            Данные организации или None если не найдена
        """
        if not inn:
            return None

        try:
            # OData $filter по полю ИНН (формат как в рабочем примере)
            filter_str = f"ИНН eq '{inn}'"
            endpoint_with_params = f"Catalog_Организации?$top=1&$format=json&$filter={filter_str}"

            logger.info(f"Searching organization by INN: {inn}")
            logger.info(f"Request URL: {self.base_url}/{endpoint_with_params}")

            response = self._make_request(
                method='GET',
                endpoint=endpoint_with_params,
                params=None
            )

            logger.debug(f"Organization search response: {response}")

            results = response.get('value', [])
            if results:
                logger.info(f"Found organization with INN {inn}: {results[0].get('Description')}")
                return results[0]  # Возвращаем первую найденную
            else:
                logger.warning(f"Organization with INN {inn} not found in 1C")
                return None

        except Exception as e:
            logger.error(f"Failed to search organization by INN {inn}: {e}")
            return None

    def create_expense_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Создать заявку на расходование денежных средств в 1С

        Args:
            data: Данные заявки в формате OData:
                {
                    "Дата": "2025-10-31T00:00:00",
                    "Организация_Key": "guid",
                    "Получатель_Key": "guid",
                    "СуммаДокумента": 2000.00,
                    "Валюта_Key": "guid",
                    "СтатьяДДС_Key": "guid",
                    "НазначениеПлатежа": "текст",
                    "ДатаПлатежа": "2025-11-03T00:00:00",
                    "ХозяйственнаяОперация": "ОплатаПоставщику"
                }

        Returns:
            Созданный документ с Ref_Key (GUID)

        Raises:
            requests.exceptions.RequestException: При ошибке создания
        """
        logger.info(f"Creating expense request in 1C: {data.get('НазначениеПлатежа', 'N/A')[:50]}...")

        try:
            response = self._make_request(
                method='POST',
                endpoint='Document_ЗаявкаНаРасходованиеДенежныхСредств',
                data=data
            )

            ref_key = response.get('Ref_Key')
            logger.info(f"Expense request created successfully with Ref_Key: {ref_key}")

            return response

        except Exception as e:
            logger.error(f"Failed to create expense request in 1C: {e}")
            raise

    def upload_attachment_base64(
        self,
        file_content: bytes,
        filename: str,
        owner_guid: str,
        file_extension: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Загрузить файл в 1С через Base64 encoding

        Args:
            file_content: Содержимое файла (bytes)
            filename: Имя файла
            owner_guid: GUID владельца (документа)
            file_extension: Расширение файла (без точки), например "pdf"

        Returns:
            Созданное вложение или None при ошибке

        Note:
            Ограничение размера файла ~4-6MB из-за Base64 overhead
        """
        if not file_content:
            logger.warning("File content is empty, skipping upload")
            return None

        # Проверка размера (макс 6MB в байтах)
        max_size = 6 * 1024 * 1024
        if len(file_content) > max_size:
            logger.warning(f"File too large ({len(file_content)} bytes), max {max_size} bytes. Skipping upload.")
            return None

        try:
            # Кодирование в Base64
            base64_content = base64.b64encode(file_content).decode('utf-8')

            # Определить расширение если не указано
            if not file_extension and '.' in filename:
                file_extension = filename.split('.')[-1].lower()

            # Данные для создания вложения
            # ВАЖНО: Структура может отличаться в зависимости от конфигурации 1С
            # Обычно используется InformationRegister_ПрисоединенныеФайлы
            attachment_data = {
                "Наименование": filename,
                "ДвоичныеДанные": base64_content,
                "Владелец_Key": owner_guid,
                "Расширение": file_extension or "pdf"
            }

            logger.info(f"Uploading attachment: {filename} ({len(file_content)} bytes) to owner {owner_guid}")

            # ПРИМЕЧАНИЕ: Endpoint может отличаться в зависимости от конфигурации 1С
            # Возможные варианты:
            # - InformationRegister_ПрисоединенныеФайлы
            # - Catalog_ПрисоединенныеФайлы
            # - Catalog_ХранилищеФайлов
            response = self._make_request(
                method='POST',
                endpoint='InformationRegister_ПрисоединенныеФайлы',
                data=attachment_data
            )

            logger.info(f"Attachment uploaded successfully")
            return response

        except Exception as e:
            logger.error(f"Failed to upload attachment: {e}")
            # Не прерываем процесс если не удалось загрузить файл
            return None

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
