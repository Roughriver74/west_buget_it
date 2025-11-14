"""
Bitrix24 integration service for task creation.
Создает задачи в Битрикс24 при утверждении заявок на оплату.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import httpx

from app.db.models import Expense, Attachment
from app.core.config import settings


logger = logging.getLogger(__name__)


class BitrixService:
    """Service for Bitrix24 REST API integration"""

    def __init__(self):
        # Bitrix24 webhook URL (должен быть настроен в .env)
        self.webhook_url = os.getenv("BITRIX24_WEBHOOK_URL")
        if not self.webhook_url:
            logger.warning("BITRIX24_WEBHOOK_URL not configured")

        # Настройки по умолчанию
        self.default_responsible_id = os.getenv("BITRIX24_DEFAULT_RESPONSIBLE_ID")  # ID ответственного
        self.default_group_id = os.getenv("BITRIX24_DEFAULT_GROUP_ID")  # ID группы/проекта
        self.default_deadline_days = int(os.getenv("BITRIX24_TASK_DEADLINE_DAYS", "3"))  # Срок задачи

    async def create_payment_task(
        self,
        expense: Expense,
        responsible_id: Optional[int] = None,
        group_id: Optional[int] = None,
        attachments: Optional[List[Attachment]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Создает задачу на оплату счета в Битрикс24.

        Args:
            expense: Заявка на расход
            responsible_id: ID ответственного (если None - использует default)
            group_id: ID группы/проекта (если None - использует default)
            attachments: Список вложений

        Returns:
            Словарь с результатом создания задачи или None при ошибке
        """
        if not self.webhook_url:
            logger.error("Cannot create Bitrix24 task: BITRIX24_WEBHOOK_URL not configured")
            return None

        try:
            # Формируем название задачи
            title = self._generate_task_title(expense)

            # Формируем описание задачи
            description = self._generate_task_description(expense)

            # Формируем дату дедлайна
            deadline = self._calculate_deadline(expense)

            # Базовые параметры задачи
            task_data = {
                "TITLE": title,
                "DESCRIPTION": description,
                "RESPONSIBLE_ID": responsible_id or self.default_responsible_id,
                "DEADLINE": deadline.strftime("%Y-%m-%dT%H:%M:%S") if deadline else None,
            }

            # Добавляем группу/проект
            if group_id or self.default_group_id:
                task_data["GROUP_ID"] = group_id or self.default_group_id

            # Добавляем элементы CRM (связь с контрагентом)
            if expense.contractor_id:
                task_data["UF_CRM_TASK"] = self._format_crm_entities(expense)

            # Добавляем кастомные поля
            custom_fields = self._generate_custom_fields(expense)
            task_data.update(custom_fields)

            # Создаем задачу
            task_result = await self._call_api("tasks.task.add", {"fields": task_data})

            if not task_result:
                return None

            task_id = task_result.get("task", {}).get("id")

            # Добавляем чек-лист (если есть)
            if task_id:
                await self._add_checklist(task_id, expense)

            # Добавляем файлы (если есть)
            if task_id and attachments:
                await self._add_attachments(task_id, attachments)

            return {
                "task_id": task_id,
                "task_url": f"{self._get_bitrix_domain()}/company/personal/user/0/tasks/task/view/{task_id}/",
                "result": task_result
            }

        except Exception as e:
            logger.error(f"Error creating Bitrix24 task for expense {expense.id}: {e}")
            return None

    def _generate_task_title(self, expense: Expense) -> str:
        """Генерирует название задачи"""
        contractor_name = expense.contractor.name if expense.contractor else "Контрагент не указан"
        return f"Оплата счета №{expense.number} от {contractor_name}"

    def _generate_task_description(self, expense: Expense) -> str:
        """Генерирует описание задачи с деталями"""
        contractor_name = expense.contractor.name if expense.contractor else "Не указан"
        contractor_inn = expense.contractor.inn if expense.contractor else "Не указан"
        organization_name = expense.organization.name if expense.organization else "Не указана"
        category_name = expense.category.name if expense.category else "Не указана"

        description = f"""<b>Заявка на оплату №{expense.number}</b>

<b>Сумма:</b> {expense.amount:,.2f} ₽
<b>Дата заявки:</b> {expense.request_date.strftime("%d.%m.%Y")}
<b>Плановая дата оплаты:</b> {expense.payment_date.strftime("%d.%m.%Y") if expense.payment_date else "Не указана"}

<b>Контрагент:</b> {contractor_name}
<b>ИНН контрагента:</b> {contractor_inn}

<b>Наша организация:</b> {organization_name}
<b>Статья расходов:</b> {category_name}
"""

        if expense.comment:
            description += f"\n<b>Комментарий:</b>\n{expense.comment}\n"

        if expense.requester:
            description += f"\n<b>Заявитель:</b> {expense.requester}\n"

        description += f"\n<b>Ссылка на заявку в системе:</b> {self._generate_expense_link(expense.id)}"

        return description

    def _calculate_deadline(self, expense: Expense) -> Optional[datetime]:
        """Рассчитывает дедлайн задачи"""
        if expense.payment_date:
            return expense.payment_date

        # Если даты оплаты нет, ставим дедлайн через N дней
        from datetime import timedelta
        return datetime.now() + timedelta(days=self.default_deadline_days)

    def _format_crm_entities(self, expense: Expense) -> List[str]:
        """
        Форматирует элементы CRM для связи с контрагентом.
        Формат: ["CO_12345"] где CO - компания, 12345 - ID в Битрикс24
        """
        # Здесь нужно сопоставить contractor_id из нашей системы с ID компании в Битрикс24
        # Это можно сделать через:
        # 1. Поле bitrix_company_id в таблице contractors
        # 2. Или через поиск по ИНН в Битрикс24

        # Пока возвращаем пустой список - требуется настройка маппинга
        # TODO: Реализовать маппинг contractors -> Bitrix24 companies
        return []

    def _generate_custom_fields(self, expense: Expense) -> Dict[str, Any]:
        """
        Генерирует кастомные поля для задачи.

        Примеры кастомных полей из скриншота:
        - UF_AUTO_... - Наша юрлица
        - UF_AUTO_... - Отдел постановщика
        """
        custom_fields = {}

        # Наша юрлица (organization_id)
        # Нужно узнать ID кастомного поля в Битрикс24
        if expense.organization_id:
            # custom_fields["UF_AUTO_ORGANIZATION"] = expense.organization_id
            pass

        # Отдел постановщика (department_id)
        if expense.department_id:
            # custom_fields["UF_AUTO_DEPARTMENT"] = expense.department_id
            pass

        # TODO: Настроить маппинг кастомных полей
        # Получить список доступных полей: tasks.task.getFields

        return custom_fields

    async def _add_checklist(self, task_id: int, expense: Expense) -> bool:
        """
        Добавляет чек-лист к задаче.
        Стандартный чек-лист для оплаты счета.
        """
        checklist_items = [
            "Проверить реквизиты контрагента",
            "Проверить наличие оригинала счета",
            "Согласовать оплату с руководителем",
            f"Перечислить {expense.amount:,.2f} ₽",
            "Получить подтверждение оплаты от банка",
        ]

        # Если есть файлы, добавляем пункт
        if expense.attachments:
            checklist_items.insert(1, "Проверить скан-копию счета")

        try:
            for i, item_title in enumerate(checklist_items, start=1):
                await self._call_api("task.checklistitem.add", {
                    "taskId": task_id,
                    "fields": {
                        "TITLE": item_title,
                        "SORT_INDEX": i * 10,
                    }
                })
            return True
        except Exception as e:
            logger.error(f"Error adding checklist to task {task_id}: {e}")
            return False

    async def _add_attachments(self, task_id: int, attachments: List[Attachment]) -> bool:
        """
        Добавляет вложения к задаче.

        Note: Для загрузки файлов в Битрикс24 нужно:
        1. Прочитать файл с диска
        2. Закодировать в base64
        3. Отправить через task.commentitem.add с FILE
        """
        try:
            import base64

            for attachment in attachments:
                file_path = attachment.file_path
                if not os.path.exists(file_path):
                    logger.warning(f"Attachment file not found: {file_path}")
                    continue

                # Читаем файл и кодируем в base64
                with open(file_path, 'rb') as f:
                    file_content = base64.b64encode(f.read()).decode('utf-8')

                # Добавляем файл как комментарий с вложением
                await self._call_api("task.commentitem.add", {
                    "taskId": task_id,
                    "fields": {
                        "POST_MESSAGE": f"Файл: {attachment.filename}",
                        "UF_TASK_WEBDAV_FILES": [{
                            "name": attachment.filename,
                            "type": attachment.content_type or "application/octet-stream",
                            "content": file_content,
                        }]
                    }
                })

            return True
        except Exception as e:
            logger.error(f"Error adding attachments to task {task_id}: {e}")
            return False

    async def _call_api(self, method: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Вызов REST API Битрикс24.

        Args:
            method: Метод API (например, "tasks.task.add")
            params: Параметры метода

        Returns:
            Результат вызова или None при ошибке
        """
        if not self.webhook_url:
            return None

        url = f"{self.webhook_url}/{method}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=params)
                response.raise_for_status()

                data = response.json()

                if data.get("error"):
                    logger.error(f"Bitrix24 API error: {data.get('error_description')}")
                    return None

                return data.get("result")

        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling Bitrix24 API {method}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error calling Bitrix24 API {method}: {e}")
            return None

    def _get_bitrix_domain(self) -> str:
        """Извлекает домен Битрикс24 из webhook URL"""
        if not self.webhook_url:
            return "https://your-domain.bitrix24.ru"

        # Webhook URL формата: https://your-domain.bitrix24.ru/rest/1/xxxxx/
        parts = self.webhook_url.split("/rest/")
        return parts[0] if parts else "https://your-domain.bitrix24.ru"

    def _generate_expense_link(self, expense_id: int) -> str:
        """Генерирует ссылку на заявку в системе управления бюджетом"""
        # TODO: Заменить на реальный URL фронтенда
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        return f"{frontend_url}/expenses/{expense_id}"


# Singleton instance
bitrix_service = BitrixService()
