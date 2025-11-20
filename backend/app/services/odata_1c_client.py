"""
1C OData Integration Service

Сервис для интеграции с 1С через стандартный интерфейс OData
"""

import logging
import base64
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from pathlib import Path
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
        self.custom_auth_token = custom_auth_token
        self.session = requests.Session()

        # Use custom auth token if provided, otherwise use username/password
        if custom_auth_token:
            self.session.headers.update({
                'Authorization': custom_auth_token,
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            })
            logger.debug("Using custom authorization token")
        else:
            self.session.auth = HTTPBasicAuth(username, password)
            self.session.headers.update({
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            })
            logger.debug(f"Using HTTPBasicAuth with username: {username}")

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
        # Для POST запросов используем http.client (как в работающем test_invoice.py)
        # чтобы избежать двойного кодирования URL от requests library
        if method == 'POST' and data:
            import http.client
            import json as json_lib
            from urllib.parse import quote, urlparse

            # Парсим base_url для получения host и base path
            parsed = urlparse(self.base_url)

            # Кодируем endpoint (кириллицу)
            encoded_endpoint = quote(endpoint, safe='/:?=.$&_')
            # Формируем полный путь: base_path + endpoint + query params
            # Например: /trade/odata/standard.odata/Document_ЗаявкаНаРасходованиеДенежныхСредств?$format=json
            # FIX: Не дублируем parsed.path если он уже есть в base_url
            full_endpoint = f"{parsed.path.rstrip('/')}/{encoded_endpoint.lstrip('/')}?$format=json"

            # Создаем connection
            conn = http.client.HTTPConnection(parsed.netloc, timeout=timeout)

            try:
                # Готовим payload
                payload = json_lib.dumps(data, ensure_ascii=False).encode('utf-8')

                # Подготовка Authorization header
                if self.custom_auth_token:
                    auth_header = self.custom_auth_token
                elif self.username is not None and self.password is not None:
                    # Генерируем Basic Auth header вручную (как в test_invoice.py)
                    auth_string = f"{self.username}:{self.password}"
                    auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('ascii')
                    auth_header = f"Basic {auth_b64}"
                else:
                    auth_header = self.session.headers.get('Authorization')
                    if not auth_header:
                        raise ValueError("Authorization is not configured for 1C OData POST request")

                # Отправляем запрос
                conn.request(
                    method,
                    full_endpoint,
                    payload,
                    {
                        'Authorization': auth_header,
                        'Content-Type': 'application/json; charset=utf-8'
                    }
                )

                # Получаем ответ
                http_response = conn.getresponse()
                response_data = http_response.read()

                # Проверяем статус
                if http_response.status >= 400:
                    error_text = response_data.decode('utf-8')
                    logger.error(f"HTTP error: {http_response.status} {http_response.reason}")
                    # FIX: Правильно формируем URL для логирования
                    logger.error(f"URL: {parsed.scheme}://{parsed.netloc}{full_endpoint}")
                    logger.error(f"Response: {error_text}")
                    raise requests.exceptions.HTTPError(
                        f"{http_response.status} {http_response.reason}",
                        response=type('obj', (object,), {
                            'status_code': http_response.status,
                            'text': error_text,
                            'content': response_data
                        })()
                    )

                # Парсим JSON
                if response_data:
                    return json_lib.loads(response_data.decode('utf-8'))
                return {}

            finally:
                conn.close()

        # Для GET и других запросов используем requests как раньше
        from urllib.parse import quote
        encoded_endpoint = quote(endpoint.lstrip('/'), safe='/:?=.$&_')
        url = f"{self.base_url}/{encoded_endpoint}"

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
            # Детальное логирование ошибки от 1С
            error_details = "N/A"
            if e.response is not None:
                try:
                    # Попытаться декодировать как JSON
                    error_json = e.response.json()
                    error_details = f"JSON: {error_json}"
                except:
                    # Если не JSON, показать текст
                    error_details = f"Text: {e.response.text[:500]}" if e.response.text else "Empty response"

                logger.error(f"HTTP error: {e}")
                logger.error(f"URL: {url}")
                logger.error(f"Status code: {e.response.status_code}")
                logger.error(f"Response: {error_details}")
                logger.error(f"Response headers: {dict(e.response.headers)}")
            else:
                logger.error(f"HTTP error: {e}, URL: {url}, Response: N/A")
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
        elif date_from:
            # Только начальная дата - фильтруем начиная с даты
            filter_str = f"{mandatory_filters} and Date ge datetime'{date_from.isoformat()}T00:00:00'"
            endpoint_with_params += f'&$filter={filter_str}'
        elif date_to:
            # Только конечная дата - фильтруем до даты
            filter_str = f"{mandatory_filters} and Date le datetime'{date_to.isoformat()}T23:59:59'"
            endpoint_with_params += f'&$filter={filter_str}'
        else:
            # Без дат - только обязательные фильтры
            filter_str = mandatory_filters
            endpoint_with_params += f'&$filter={mandatory_filters}'

        logger.debug(f"Fetching bank receipts: date_from={date_from}, date_to={date_to}, top={top}, skip={skip}, filter={filter_str}")

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
        elif date_from:
            # Только начальная дата - фильтруем начиная с даты
            filter_str = f"{mandatory_filters} and Date ge datetime'{date_from.isoformat()}T00:00:00'"
            endpoint_with_params += f'&$filter={filter_str}'
        elif date_to:
            # Только конечная дата - фильтруем до даты
            filter_str = f"{mandatory_filters} and Date le datetime'{date_to.isoformat()}T23:59:59'"
            endpoint_with_params += f'&$filter={filter_str}'
        else:
            # Без дат - только обязательные фильтры
            filter_str = mandatory_filters
            endpoint_with_params += f'&$filter={mandatory_filters}'

        logger.debug(f"Fetching bank payments: date_from={date_from}, date_to={date_to}, top={top}, skip={skip}, filter={filter_str}")

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
                # Removed duplicate log
            else:
                # Для диапазона используем фильтр по году
                year_filter = date_from.year - 1
                filter_str = f'{mandatory_filters} and year(Date) gt {year_filter}'
                endpoint_with_params += f'&$filter={filter_str}'
                # Removed duplicate log
        elif date_from:
            # Только начальная дата - фильтруем по году
            year_filter = date_from.year - 1
            filter_str = f'{mandatory_filters} and year(Date) gt {year_filter}'
            endpoint_with_params += f'&$filter={filter_str}'
            # Removed duplicate log
        else:
            # Без дат - только обязательные фильтры
            endpoint_with_params += f'&$filter={mandatory_filters}'
            logger.debug(f"Using OData filter: {mandatory_filters}")

        logger.debug(f"Fetching cash receipts: date_from={date_from}, date_to={date_to}, top={top}, skip={skip}")

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
                # Removed duplicate log
            else:
                # Для диапазона используем фильтр по году
                year_filter = date_from.year - 1
                filter_str = f'{mandatory_filters} and year(Date) gt {year_filter}'
                endpoint_with_params += f'&$filter={filter_str}'
                # Removed duplicate log
        elif date_from:
            # Только начальная дата - фильтруем по году
            year_filter = date_from.year - 1
            filter_str = f'{mandatory_filters} and year(Date) gt {year_filter}'
            endpoint_with_params += f'&$filter={filter_str}'
            # Removed duplicate log
        else:
            # Без дат - только обязательные фильтры
            endpoint_with_params += f'&$filter={mandatory_filters}'
            logger.debug(f"Using OData filter: {mandatory_filters}")

        logger.debug(f"Fetching cash payments: date_from={date_from}, date_to={date_to}, top={top}, skip={skip}")

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
        Получить подразделение по наименованию из справочника СтруктураПредприятия

        Args:
            name: Наименование подразделения (например: "(ДЕМО) IT", "Москва")

        Returns:
            Данные подразделения (включая Ref_Key) или None
        """
        if not name or not name.strip():
            return None

        try:
            # Фильтр по наименованию (Description в справочнике СтруктураПредприятия)
            filter_str = f"Description eq '{name}'"
            endpoint_with_params = f"Catalog_СтруктураПредприятия?$format=json&$filter={filter_str}&$top=1"

            logger.debug(f"Searching subdivision by name: '{name}'")
            logger.debug(f"Request URL: {self.base_url}/{endpoint_with_params}")

            response = self._make_request(
                method='GET',
                endpoint=endpoint_with_params
            )

            # Проверить результат
            if response and 'value' in response and len(response['value']) > 0:
                subdivision = response['value'][0]
                logger.debug(f"Found subdivision '{name}' with GUID: {subdivision.get('Ref_Key')}")
                return subdivision
            else:
                logger.warning(f"Subdivision '{name}' not found in 1C Catalog_СтруктураПредприятия")
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
            logger.debug(f"Using OData filter: {filter_str}")
        elif date_from:
            # Только начальная дата - фильтруем начиная с даты
            filter_str = f"{mandatory_filters} and Date ge datetime'{date_from.isoformat()}T00:00:00'"
            endpoint_with_params += f'&$filter={filter_str}'
            logger.debug(f"Using OData filter: {filter_str}")
        elif date_to:
            # Только конечная дата - фильтруем до даты
            filter_str = f"{mandatory_filters} and Date le datetime'{date_to.isoformat()}T23:59:59'"
            endpoint_with_params += f'&$filter={filter_str}'
            logger.debug(f"Using OData filter: {filter_str}")
        else:
            # Без дат - только обязательные фильтры
            endpoint_with_params += f'&$filter={mandatory_filters}'
            logger.debug(f"Using OData filter: {mandatory_filters}")

        logger.debug(f"Fetching expense requests: date_from={date_from}, date_to={date_to}, top={top}, skip={skip}")

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

        logger.debug(f"Fetching organizations: top={top}, skip={skip}")

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
        top: int = 1000,
        skip: int = 0,
        include_folders: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Получить статьи движения денежных средств из 1С

        Args:
            top: Количество записей (max 1000, default 1000)
            skip: Пропустить N записей (для пагинации)
            include_folders: Включать папки (группы) в результат

        Returns:
            Список статей ДДС (только активные, не помеченные на удаление)

        Note:
            Применяется фильтр DeletionMark eq false для загрузки только активных категорий
        """
        top_value = min(top, 1000)

        # ОБЯЗАТЕЛЬНЫЙ фильтр: только активные (не помеченные на удаление)
        filter_str = "DeletionMark eq false"
        endpoint_with_params = f'Catalog_СтатьиДвиженияДенежныхСредств?$top={top_value}&$format=json&$skip={skip}&$filter={filter_str}'

        logger.debug(f"Fetching cash flow categories: top={top_value}, skip={skip}, filter={filter_str}")

        response = self._make_request(
            method='GET',
            endpoint=endpoint_with_params,
            params=None
        )

        results = response.get('value', [])

        # Фильтровать по папкам если нужно
        if not include_folders:
            results = [r for r in results if not r.get('IsFolder', False)]

        logger.info(f"Fetched {len(results)} cash flow categories (active only)")

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

            logger.debug(f"Searching counterparty by INN: {inn}")
            logger.debug(f"Request URL: {self.base_url}/{endpoint_with_params}")

            response = self._make_request(
                method='GET',
                endpoint=endpoint_with_params,
                params=None
            )

            logger.debug(f"Counterparty search response: {response}")

            results = response.get('value', [])
            if results:
                logger.debug(f"Found counterparty with INN {inn}: {results[0].get('Description')}")
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

            logger.debug(f"Searching organization by INN: {inn}")
            logger.debug(f"Request URL: {self.base_url}/{endpoint_with_params}")

            response = self._make_request(
                method='GET',
                endpoint=endpoint_with_params,
                params=None
            )

            logger.debug(f"Organization search response: {response}")

            results = response.get('value', [])
            if results:
                logger.debug(f"Found organization with INN {inn}: {results[0].get('Description')}")
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

        # Детальное логирование JSON payload перед отправкой
        import json
        try:
            json_payload = json.dumps(data, ensure_ascii=False, indent=2)
            logger.debug(f"JSON payload being sent to 1C:\n{json_payload}")
        except Exception as log_err:
            logger.warning(f"Failed to serialize payload for logging: {log_err}")

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
        file_extension: Optional[str] = None,
        endpoint: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Загрузить файл в 1С через Base64 encoding

        Args:
            file_content: Содержимое файла (bytes)
            filename: Имя файла
            owner_guid: GUID владельца (документа)
            file_extension: Расширение файла (без точки), например "pdf"
            endpoint: Кастомный endpoint (по умолчанию из настроек)

        Returns:
            Созданное вложение или None при ошибке

        Note:
            Ограничение размера файла ~4-6MB из-за Base64 overhead
        """
        if not file_content:
            logger.warning("File content is empty, skipping upload")
            return None

        # Получаем настройки из config
        from app.core.config import settings
        max_size = settings.ODATA_1C_MAX_FILE_SIZE
        upload_endpoint = endpoint or settings.ODATA_1C_ATTACHMENT_ENDPOINT

        # Проверка размера
        if len(file_content) > max_size:
            logger.warning(
                f"File too large ({len(file_content)} bytes = {len(file_content) / 1024 / 1024:.2f}MB), "
                f"max {max_size} bytes = {max_size / 1024 / 1024}MB. Skipping upload."
            )
            return None

        try:
            # Кодирование в Base64
            base64_content = base64.b64encode(file_content).decode('utf-8')
            base64_size = len(base64_content)

            # Определить расширение если не указано
            if not file_extension and '.' in filename:
                file_extension = filename.split('.')[-1].lower()

            # Данные для создания вложения
            # ВАЖНО: Структура может отличаться в зависимости от конфигурации 1С
            attachment_data = {
                "Наименование": filename,
                "ДвоичныеДанные": base64_content,
                "Владелец_Key": owner_guid,
                "Расширение": file_extension or "pdf"
            }

            logger.info(
                f"📎 Uploading attachment to 1C:\n"
                f"   Filename: {filename}\n"
                f"   Extension: {file_extension or 'pdf'}\n"
                f"   Original size: {len(file_content)} bytes ({len(file_content) / 1024:.1f} KB)\n"
                f"   Base64 size: {base64_size} bytes ({base64_size / 1024:.1f} KB)\n"
                f"   Owner GUID: {owner_guid}\n"
                f"   Endpoint: {upload_endpoint}"
            )

            # ПРИМЕЧАНИЕ: Endpoint может отличаться в зависимости от конфигурации 1С
            # Возможные варианты:
            # - InformationRegister_ПрисоединенныеФайлы (по умолчанию)
            # - Catalog_ПрисоединенныеФайлы
            # - Catalog_ХранилищеФайлов
            response = self._make_request(
                method='POST',
                endpoint=upload_endpoint,
                data=attachment_data
            )

            logger.info(f"✅ Attachment uploaded successfully: {response}")
            return response

        except Exception as e:
            logger.error(f"❌ Failed to upload attachment: {e}", exc_info=True)
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


_ODATA_ENV_LOADED = False


def _ensure_odata_env_loaded():
    """
    Ensure .env files are loaded so os.getenv picks up OData credentials.
    """
    global _ODATA_ENV_LOADED
    if _ODATA_ENV_LOADED:
        return

    try:
        from dotenv import load_dotenv
    except ImportError:
        _ODATA_ENV_LOADED = True
        return

    service_path = Path(__file__).resolve()
    backend_dir = service_path.parents[2]  # .../backend
    project_root = backend_dir.parent

    env_candidates = [
        project_root / ".env",
        backend_dir / ".env"
    ]

    for env_path in env_candidates:
        if env_path.is_file():
            load_dotenv(env_path, override=False)

    _ODATA_ENV_LOADED = True


def create_1c_client_from_env() -> OData1CClient:
    """
    Создать клиент 1С OData из переменных окружения

    Environment variables:
        ODATA_1C_URL: Base URL for OData
        ODATA_1C_USERNAME: Username (used if custom token is not set)
        ODATA_1C_PASSWORD: Password (used if custom token is not set)
        ODATA_1C_CUSTOM_AUTH_TOKEN: Optional full Authorization header value (e.g. \"Basic ...\")

    Returns:
        Configured OData1CClient instance
    """
    import os

    _ensure_odata_env_loaded()

    url = os.getenv('ODATA_1C_URL', 'http://10.10.100.77/trade/odata/standard.odata')
    username = os.getenv('ODATA_1C_USERNAME', 'odata.user')
    password = os.getenv('ODATA_1C_PASSWORD', 'ak228Hu2hbs28')
    custom_auth = os.getenv('ODATA_1C_CUSTOM_AUTH_TOKEN')

    client_kwargs: Dict[str, Any] = {'base_url': url}

    if custom_auth:
        client_kwargs['custom_auth_token'] = custom_auth.strip()
    else:
        client_kwargs['username'] = username
        client_kwargs['password'] = password

    return OData1CClient(**client_kwargs)
