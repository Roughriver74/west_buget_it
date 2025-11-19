"""
KPI Audit Service

Provides audit logging for KPI record changes to track history and maintain compliance.
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal

from app.db.models import AuditLog, AuditActionEnum, EmployeeKPI, User


class KPIAuditService:
    """Service for auditing KPI changes"""

    def __init__(self, db: Session):
        self.db = db

    def _serialize_value(self, value: Any) -> Any:
        """
        Convert value to JSON-serializable format.

        Args:
            value: Value to serialize

        Returns:
            JSON-serializable value
        """
        if value is None:
            return None
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, (int, float, str, bool)):
            return value
        if hasattr(value, 'value'):  # Enum
            return value.value
        return str(value)

    def _get_relevant_fields(self) -> List[str]:
        """
        Get list of EmployeeKPI fields to track in audit.

        Returns:
            List of field names
        """
        return [
            'employee_id',
            'year',
            'month',
            'kpi_percentage',
            'depremium_threshold',
            'depremium_applied',
            'monthly_bonus_type',
            'quarterly_bonus_type',
            'annual_bonus_type',
            'monthly_bonus_base',
            'quarterly_bonus_base',
            'annual_bonus_base',
            'monthly_bonus_calculated',
            'quarterly_bonus_calculated',
            'annual_bonus_calculated',
            'monthly_bonus_fixed_part',
            'quarterly_bonus_fixed_part',
            'annual_bonus_fixed_part',
            'status',
            'notes'
        ]

    def _extract_changes(
        self,
        old_record: Optional[EmployeeKPI],
        new_record: EmployeeKPI
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract changed fields between old and new record.

        Args:
            old_record: Previous state (None for CREATE)
            new_record: New state

        Returns:
            Dictionary of changes: {field: {"old": old_value, "new": new_value}}
        """
        changes = {}
        relevant_fields = self._get_relevant_fields()

        for field in relevant_fields:
            new_value = getattr(new_record, field, None)
            old_value = getattr(old_record, field, None) if old_record else None

            # Compare values
            if old_value != new_value:
                changes[field] = {
                    "old": self._serialize_value(old_value),
                    "new": self._serialize_value(new_value)
                }

        return changes

    def _generate_description(
        self,
        action: AuditActionEnum,
        employee_kpi: EmployeeKPI,
        changes: Optional[Dict] = None
    ) -> str:
        """
        Generate human-readable description of the audit event.

        Args:
            action: Action performed
            employee_kpi: EmployeeKPI record
            changes: Dictionary of changes (for UPDATE)

        Returns:
            Human-readable description
        """
        # Get employee info
        from app.db.models import Employee
        employee = self.db.query(Employee).filter(Employee.id == employee_kpi.employee_id).first()
        employee_name = employee.full_name if employee else f"Employee#{employee_kpi.employee_id}"

        period = f"{employee_kpi.year}-{employee_kpi.month:02d}"

        if action == AuditActionEnum.CREATE:
            return f"Создана запись KPI для {employee_name} за {period}"

        elif action == AuditActionEnum.UPDATE:
            if changes:
                changed_fields = ", ".join(changes.keys())
                return f"Обновлена запись KPI для {employee_name} за {period}. Изменены поля: {changed_fields}"
            else:
                return f"Обновлена запись KPI для {employee_name} за {period}"

        elif action == AuditActionEnum.DELETE:
            return f"Удалена запись KPI для {employee_name} за {period}"

        elif action == AuditActionEnum.APPROVE:
            return f"Утверждена запись KPI для {employee_name} за {period}"

        elif action == AuditActionEnum.REJECT:
            return f"Отклонена запись KPI для {employee_name} за {period}"

        return f"{action.value} KPI record for {employee_name} ({period})"

    def log_create(
        self,
        employee_kpi: EmployeeKPI,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Log creation of EmployeeKPI record.

        Args:
            employee_kpi: Created EmployeeKPI record
            user: User who created the record
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created AuditLog record
        """
        changes = self._extract_changes(None, employee_kpi)
        description = self._generate_description(AuditActionEnum.CREATE, employee_kpi)

        audit_log = AuditLog(
            user_id=user.id,
            action=AuditActionEnum.CREATE,
            entity_type="EmployeeKPI",
            entity_id=employee_kpi.id,
            description=description,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            department_id=employee_kpi.department_id,
            timestamp=datetime.utcnow()
        )

        self.db.add(audit_log)
        self.db.commit()

        return audit_log

    def log_update(
        self,
        old_record: EmployeeKPI,
        new_record: EmployeeKPI,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[AuditLog]:
        """
        Log update of EmployeeKPI record.

        Args:
            old_record: Previous state of the record
            new_record: New state of the record
            user: User who updated the record
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created AuditLog record or None if no changes detected
        """
        changes = self._extract_changes(old_record, new_record)

        if not changes:
            return None  # No changes detected

        description = self._generate_description(AuditActionEnum.UPDATE, new_record, changes)

        audit_log = AuditLog(
            user_id=user.id,
            action=AuditActionEnum.UPDATE,
            entity_type="EmployeeKPI",
            entity_id=new_record.id,
            description=description,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            department_id=new_record.department_id,
            timestamp=datetime.utcnow()
        )

        self.db.add(audit_log)
        self.db.commit()

        return audit_log

    def log_delete(
        self,
        employee_kpi: EmployeeKPI,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Log deletion of EmployeeKPI record.

        Args:
            employee_kpi: Deleted EmployeeKPI record
            user: User who deleted the record
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created AuditLog record
        """
        # Capture final state before deletion
        final_state = {}
        for field in self._get_relevant_fields():
            value = getattr(employee_kpi, field, None)
            final_state[field] = self._serialize_value(value)

        description = self._generate_description(AuditActionEnum.DELETE, employee_kpi)

        audit_log = AuditLog(
            user_id=user.id,
            action=AuditActionEnum.DELETE,
            entity_type="EmployeeKPI",
            entity_id=employee_kpi.id,
            description=description,
            changes={"deleted_record": final_state},
            ip_address=ip_address,
            user_agent=user_agent,
            department_id=employee_kpi.department_id,
            timestamp=datetime.utcnow()
        )

        self.db.add(audit_log)
        self.db.commit()

        return audit_log

    def log_approve(
        self,
        employee_kpi: EmployeeKPI,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Log approval of EmployeeKPI record.

        Args:
            employee_kpi: Approved EmployeeKPI record
            user: User who approved the record
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created AuditLog record
        """
        description = self._generate_description(AuditActionEnum.APPROVE, employee_kpi)

        audit_log = AuditLog(
            user_id=user.id,
            action=AuditActionEnum.APPROVE,
            entity_type="EmployeeKPI",
            entity_id=employee_kpi.id,
            description=description,
            changes={
                "status": {
                    "old": "UNDER_REVIEW",
                    "new": "APPROVED"
                },
                "reviewed_by": user.id,
                "reviewed_at": datetime.utcnow().isoformat()
            },
            ip_address=ip_address,
            user_agent=user_agent,
            department_id=employee_kpi.department_id,
            timestamp=datetime.utcnow()
        )

        self.db.add(audit_log)
        self.db.commit()

        return audit_log

    def log_reject(
        self,
        employee_kpi: EmployeeKPI,
        user: User,
        rejection_reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Log rejection of EmployeeKPI record.

        Args:
            employee_kpi: Rejected EmployeeKPI record
            user: User who rejected the record
            rejection_reason: Reason for rejection
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created AuditLog record
        """
        description = self._generate_description(AuditActionEnum.REJECT, employee_kpi)

        audit_log = AuditLog(
            user_id=user.id,
            action=AuditActionEnum.REJECT,
            entity_type="EmployeeKPI",
            entity_id=employee_kpi.id,
            description=description,
            changes={
                "status": {
                    "old": "UNDER_REVIEW",
                    "new": "REJECTED"
                },
                "reviewed_by": user.id,
                "reviewed_at": datetime.utcnow().isoformat(),
                "rejection_reason": rejection_reason
            },
            ip_address=ip_address,
            user_agent=user_agent,
            department_id=employee_kpi.department_id,
            timestamp=datetime.utcnow()
        )

        self.db.add(audit_log)
        self.db.commit()

        return audit_log

    def get_audit_history(
        self,
        employee_kpi_id: int,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get audit history for a specific EmployeeKPI record.

        Args:
            employee_kpi_id: ID of EmployeeKPI record
            limit: Maximum number of records to return

        Returns:
            List of AuditLog records, ordered by timestamp descending
        """
        return self.db.query(AuditLog).filter(
            AuditLog.entity_type == "EmployeeKPI",
            AuditLog.entity_id == employee_kpi_id
        ).order_by(AuditLog.timestamp.desc()).limit(limit).all()

    def get_user_kpi_actions(
        self,
        user_id: int,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get all KPI-related actions by a specific user.

        Args:
            user_id: User ID
            limit: Maximum number of records to return

        Returns:
            List of AuditLog records, ordered by timestamp descending
        """
        return self.db.query(AuditLog).filter(
            AuditLog.entity_type == "EmployeeKPI",
            AuditLog.user_id == user_id
        ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
