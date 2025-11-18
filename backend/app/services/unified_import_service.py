"""
Unified Import Service

Combines dynamic parser, config manager, and database operations
to provide universal import functionality for any entity.
"""

from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.services.dynamic_import_service import (
    DynamicImportService,
    ValidationMessage,
    ValidationSeverity
)
from app.services.import_config_manager import (
    ImportConfig,
    get_import_config_manager
)
from app.db.models import (
    BudgetCategory,
    BudgetPlan,
    BudgetPlanDetail,
    BudgetVersion,
    Contractor,
    Organization,
    Employee,
    EmployeeStatusEnum,
    PayrollPlan,
    Expense,
    RevenueStream,
    RevenueCategory,
    RevenuePlanDetail,
    RevenuePlanVersion,
    User,
    ExpenseTypeEnum,
    ExpenseStatusEnum,
    BudgetStatusEnum
)

logger = logging.getLogger(__name__)


class UnifiedImportService:
    """Universal import service for all entities"""

    # Map entity names to SQLAlchemy models
    ENTITY_MODELS = {
        "budget_categories": BudgetCategory,
        "budget_plans": BudgetPlan,
        "budget_plan_details": BudgetPlanDetail,
        "contractors": Contractor,
        "organizations": Organization,
        "employees": Employee,
        "payroll_plans": PayrollPlan,
        "expenses": Expense,
        "revenue_streams": RevenueStream,
        "revenue_categories": RevenueCategory,
        "revenue_plan_details": RevenuePlanDetail,
    }

    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user
        self.parser = DynamicImportService()
        self.config_manager = get_import_config_manager()

    def get_available_entities(self) -> List[Dict[str, Any]]:
        """Get list of entities available for import"""
        return self.config_manager.get_all_entities_info(language="ru")

    def preview_import(
        self,
        entity_type: str,
        file_content: bytes,
        sheet_name: str | int = 0,
        header_row: int = 0
    ) -> Dict[str, Any]:
        """
        Preview import file before processing

        Returns:
            - File structure analysis
            - Suggested column mapping
            - Data preview
        """
        # Get configuration
        config = self.config_manager.get_config(entity_type)
        if not config:
            return {
                "success": False,
                "error": f"Unknown entity type: {entity_type}"
            }

        # Read and analyze Excel file
        result = self.parser.read_excel(
            file_content=file_content,
            sheet_name=sheet_name,
            header_row=header_row,
            max_rows=100  # Preview first 100 rows
        )

        if not result["success"]:
            return result

        # Suggest column mapping based on config WITH aliases
        target_fields = config.get_target_field_names()
        alias_map = config.get_alias_map()  # Get aliases from config
        suggested_mapping = self.parser.suggest_mapping(target_fields, alias_map)

        return {
            "success": True,
            "entity_type": entity_type,
            "entity_display_name": config.display_name.get("ru", entity_type),
            "file_info": {
                "sheet_names": result["sheet_names"],
                "selected_sheet": result["selected_sheet"],
                "total_rows": result["total_rows"],
                "total_columns": result["total_columns"]
            },
            "columns": result["columns"],
            "preview_rows": result["preview_rows"],
            "suggested_mapping": suggested_mapping,
            "required_fields": config.get_required_fields(),
            "config_fields": [
                {
                    "name": f["name"],
                    "display_name": f["display_name"]["ru"],
                    "type": f["type"],
                    "required": f.get("required", False)
                }
                for f in config.fields
            ]
        }

    def validate_import(
        self,
        entity_type: str,
        file_content: bytes,
        column_mapping: Dict[str, str],
        sheet_name: str | int = 0,
        header_row: int = 0,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Validate import data without saving to database

        Args:
            entity_type: Entity to import (e.g., "employees")
            file_content: Excel file bytes
            column_mapping: {excel_column: entity_field}
            sheet_name: Sheet name or index
            header_row: Header row index

        Returns:
            Validation results with errors/warnings
        """
        # Determine department context for validation
        target_department_id = department_id if department_id is not None else self.current_user.department_id

        # Get configuration
        config = self.config_manager.get_config(entity_type)
        if not config:
            return {
                "success": False,
                "error": f"Unknown entity type: {entity_type}"
            }

        # Read Excel file
        result = self.parser.read_excel(
            file_content=file_content,
            sheet_name=sheet_name,
            header_row=header_row
        )

        if not result["success"]:
            return result

        # Map columns
        mapping_result = self.parser.map_columns(column_mapping)
        if not mapping_result["success"]:
            return mapping_result

        mapped_data = mapping_result["mapped_data"]
        self._normalize_field_types(config, mapped_data)
        validation_messages = mapping_result["validation_messages"]

        # Build validation rules from config
        validation_rules = self._build_validation_rules(config)

        # Validate data
        config_validation = self.parser.validate_data(mapped_data, validation_rules)
        validation_messages.extend([msg.to_dict() for msg in config_validation])

        # Business logic validation
        business_validation = self._validate_business_rules(
            entity_type=entity_type,
            config=config,
            mapped_data=mapped_data,
            department_id=target_department_id
        )
        validation_messages.extend(business_validation)

        # Count errors/warnings
        errors = [m for m in validation_messages if m.get("severity") == "error"]
        warnings = [m for m in validation_messages if m.get("severity") == "warning"]

        return {
            "success": True,
            "is_valid": len(errors) == 0,
            "total_rows": len(mapped_data),
            "validation_summary": {
                "errors": len(errors),
                "warnings": len(warnings),
                "valid_rows": len(mapped_data) - len(set(e["row"] for e in errors))
            },
            "validation_messages": validation_messages[:100],  # First 100 messages
            "preview_data": mapped_data[:10]  # First 10 rows
        }

    def execute_import(
        self,
        entity_type: str,
        file_content: bytes,
        column_mapping: Dict[str, str],
        sheet_name: str | int = 0,
        header_row: int = 0,
        skip_errors: bool = False,
        dry_run: bool = False,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute import and save to database

        Args:
            entity_type: Entity to import
            file_content: Excel file bytes
            column_mapping: {excel_column: entity_field}
            sheet_name: Sheet name or index
            header_row: Header row index
            skip_errors: Skip rows with errors (default: False)
            dry_run: Validate only, don't save (default: False)
            department_id: Department ID to import to (default: current user's department)

        Returns:
            Import results with statistics
        """
        # First validate
        validation_result = self.validate_import(
            entity_type=entity_type,
            file_content=file_content,
            column_mapping=column_mapping,
            sheet_name=sheet_name,
            header_row=header_row,
            department_id=department_id
        )

        if not validation_result["success"]:
            return validation_result

        if not validation_result["is_valid"] and not skip_errors:
            return {
                "success": False,
                "error": "Validation failed. Set skip_errors=True to import valid rows only.",
                "validation_result": validation_result
            }

        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "would_import": validation_result["validation_summary"]["valid_rows"],
                "validation_result": validation_result
            }

        # Get configuration
        config = self.config_manager.get_config(entity_type)

        # Re-read and map data (already validated)
        self.parser.read_excel(file_content, sheet_name, header_row)
        mapping_result = self.parser.map_columns(column_mapping)
        mapped_data = mapping_result["mapped_data"]
        self._normalize_field_types(config, mapped_data)

        # Filter out rows with errors if skip_errors=True
        if skip_errors:
            error_rows = set(
                m["row"] for m in validation_result["validation_messages"]
                if m["severity"] == "error"
            )
            mapped_data = [
                row for row in mapped_data
                if row["_row_number"] not in error_rows
            ]

        # Execute import
        try:
            result = self._import_entities(entity_type, config, mapped_data, department_id)

            if result["success"]:
                self.db.commit()
            else:
                self.db.rollback()

            return result

        except Exception as e:
            self.db.rollback()
            logger.error(f"Import failed: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Import failed: {str(e)}"
            }

    def _build_validation_rules(self, config: ImportConfig) -> Dict[str, Any]:
        """Build validation rules from config"""
        rules = {}

        for field in config.fields:
            field_name = field["name"]
            field_rules = {}

            if field.get("required"):
                field_rules["required"] = True

            field_type = field.get("type")
            if field_type == "string":
                field_rules["type"] = str
                if "min_length" in field:
                    field_rules["min_length"] = field["min_length"]
                if "max_length" in field:
                    field_rules["max_length"] = field["max_length"]
                if "pattern" in field:
                    field_rules["pattern"] = field["pattern"]

            elif field_type == "integer":
                field_rules["type"] = int
                if "min" in field:
                    field_rules["min"] = field["min"]
                if "max" in field:
                    field_rules["max"] = field["max"]

            elif field_type == "decimal":
                field_rules["type"] = (int, float)
                if "min" in field:
                    field_rules["min"] = field["min"]
                if "max" in field:
                    field_rules["max"] = field["max"]

            elif field_type == "boolean":
                field_rules["type"] = bool

            elif field_type == "enum":
                if "enum" in field:
                    field_rules["enum"] = field["enum"]

            rules[field_name] = field_rules

        return rules

    def _validate_business_rules(
        self,
        entity_type: str,
        config: ImportConfig,
        mapped_data: List[Dict[str, Any]],
        department_id: int
    ) -> List[Dict[str, Any]]:
        """Validate business-specific rules"""
        messages = []

        # Check for duplicate keys if updating
        if config.allows_update():
            update_key = config.get_update_key()
            if update_key:
                seen_keys = set()
                key_fields = [update_key] if isinstance(update_key, str) else update_key

                for row in mapped_data:
                    key_values = tuple(row.get(k) for k in key_fields)
                    if key_values in seen_keys:
                        messages.append({
                            "row": row["_row_number"],
                            "column": ", ".join(key_fields),
                            "severity": "error",
                            "message": f"Duplicate key: {key_values}",
                            "value": None
                        })
                    seen_keys.add(key_values)

        # Entity-specific validations
        if entity_type == "payroll_plans":
            messages.extend(self._validate_payroll_plans(mapped_data, department_id))
        elif entity_type == "expenses":
            messages.extend(self._validate_expenses(mapped_data, department_id))
        elif entity_type == "budget_plans":
            messages.extend(self._validate_budget_plans(mapped_data, department_id))
        elif entity_type == "budget_plan_details":
            messages.extend(self._validate_budget_plan_details(mapped_data, department_id))
        elif entity_type == "revenue_plan_details":
            messages.extend(self._validate_revenue_plan_details(mapped_data, department_id))

        return messages

    def _validate_payroll_plans(self, data: List[Dict[str, Any]], department_id: int) -> List[Dict[str, Any]]:
        """Validate payroll plans business rules"""
        messages = []

        for row in data:
            row_num = row["_row_number"]

            # Check employee exists
            employee_name = row.get("employee_name")
            if employee_name:
                employee = self.db.query(Employee).filter(
                    Employee.full_name == employee_name,
                    Employee.department_id == department_id,
                    Employee.status == EmployeeStatusEnum.ACTIVE
                ).first()

                if not employee:
                    messages.append({
                        "row": row_num,
                        "column": "employee_name",
                        "severity": "error",
                        "message": f"Employee '{employee_name}' not found in your department",
                        "value": employee_name
                    })

        return messages

    def _validate_expenses(self, data: List[Dict[str, Any]], department_id: int) -> List[Dict[str, Any]]:
        """Validate expenses business rules"""
        messages = []

        for row in data:
            row_num = row["_row_number"]

            # Payment date must be after request date
            request_date = row.get("request_date")
            payment_date = row.get("payment_date")

            if request_date and payment_date:
                if payment_date < request_date:
                    messages.append({
                        "row": row_num,
                        "column": "payment_date",
                        "severity": "warning",
                        "message": "Payment date is before request date",
                        "value": None
                    })

            # PAID status requires payment_date
            status = row.get("status")
            if status == "PAID" and not payment_date:
                messages.append({
                    "row": row_num,
                    "column": "payment_date",
                    "severity": "error",
                    "message": "PAID status requires payment_date",
                    "value": None
                })

        return messages

    def _validate_budget_plans(self, data: List[Dict[str, Any]], department_id: int) -> List[Dict[str, Any]]:
        """Validate budget plans business rules"""
        messages = []

        for row in data:
            row_num = row["_row_number"]

            # Check category exists
            category_name = row.get("category_name")
            if category_name:
                category = self.db.query(BudgetCategory).filter(
                    BudgetCategory.name == category_name,
                    BudgetCategory.department_id == department_id,
                    BudgetCategory.is_active == True
                ).first()

                if not category:
                    messages.append({
                        "row": row_num,
                        "column": "category_name",
                        "severity": "error",
                        "message": f"Category '{category_name}' not found in your department",
                        "value": category_name
                    })

            # Check amount consistency
            planned = row.get("planned_amount", 0) or 0
            capex = row.get("capex_planned", 0) or 0
            opex = row.get("opex_planned", 0) or 0

            if capex or opex:
                total = capex + opex
                if abs(total - planned) > 0.01:  # Allow small floating point differences
                    messages.append({
                        "row": row_num,
                        "column": "planned_amount",
                        "severity": "warning",
                        "message": f"planned_amount ({planned}) should equal capex_planned + opex_planned ({total})",
                        "value": None
                    })

        return messages

    def _validate_budget_plan_details(self, data: List[Dict[str, Any]], department_id: int) -> List[Dict[str, Any]]:
        """Validate budget plan details business rules"""
        messages = []

        for row in data:
            row_num = row["_row_number"]

            # Check version exists and is editable
            version_id = row.get("version_id")
            if version_id:
                version = self.db.query(BudgetVersion).filter(
                    BudgetVersion.id == version_id
                ).first()

                if not version:
                    messages.append({
                        "row": row_num,
                        "column": "version_id",
                        "severity": "error",
                        "message": f"Budget version {version_id} not found",
                        "value": version_id
                    })
                elif version.status not in ["DRAFT", "IN_REVIEW"]:
                    messages.append({
                        "row": row_num,
                        "column": "version_id",
                        "severity": "error",
                        "message": f"Budget version {version_id} is {version.status}, cannot edit",
                        "value": version_id
                    })

            # Check category exists
            category_name = row.get("category_name")
            if category_name:
                category = self.db.query(BudgetCategory).filter(
                    BudgetCategory.name == category_name,
                    BudgetCategory.department_id == department_id
                ).first()

                if not category:
                    messages.append({
                        "row": row_num,
                        "column": "category_name",
                        "severity": "error",
                        "message": f"Category '{category_name}' not found",
                        "value": category_name
                    })

        return messages

    def _validate_revenue_plan_details(self, data: List[Dict[str, Any]], department_id: int) -> List[Dict[str, Any]]:
        """Validate revenue plan details business rules"""
        messages = []

        for row in data:
            row_num = row["_row_number"]

            # Check version exists
            version_id = row.get("version_id")
            if version_id:
                version = self.db.query(RevenuePlanVersion).filter(
                    RevenuePlanVersion.id == version_id
                ).first()

                if not version:
                    messages.append({
                        "row": row_num,
                        "column": "version_id",
                        "severity": "error",
                        "message": f"Revenue plan version {version_id} not found",
                        "value": version_id
                    })
                elif version.status not in ["DRAFT", "IN_REVIEW"]:
                    messages.append({
                        "row": row_num,
                        "column": "version_id",
                        "severity": "error",
                        "message": f"Revenue plan version {version_id} is {version.status}, cannot edit",
                        "value": version_id
                    })

            # Check at least one of stream or category is provided
            stream_name = row.get("revenue_stream_name")
            category_name = row.get("revenue_category_name")

            if not stream_name and not category_name:
                messages.append({
                    "row": row_num,
                    "column": "revenue_stream_name",
                    "severity": "error",
                    "message": "At least one of revenue_stream or revenue_category must be provided",
                    "value": None
                })

            # Validate stream if provided
            if stream_name:
                stream = self.db.query(RevenueStream).filter(
                    RevenueStream.name == stream_name,
                    RevenueStream.department_id == department_id
                ).first()

                if not stream:
                    messages.append({
                        "row": row_num,
                        "column": "revenue_stream_name",
                        "severity": "error",
                        "message": f"Revenue stream '{stream_name}' not found",
                        "value": stream_name
                    })

            # Validate category if provided
            if category_name:
                category = self.db.query(RevenueCategory).filter(
                    RevenueCategory.name == category_name,
                    RevenueCategory.department_id == department_id
                ).first()

                if not category:
                    messages.append({
                        "row": row_num,
                        "column": "revenue_category_name",
                        "severity": "error",
                        "message": f"Revenue category '{category_name}' not found",
                        "value": category_name
                    })

        return messages

    def _import_entities(
        self,
        entity_type: str,
        config: ImportConfig,
        mapped_data: List[Dict[str, Any]],
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Import entities to database"""

        model_class = self.ENTITY_MODELS.get(config.entity)
        if not model_class:
            return {
                "success": False,
                "error": f"No model found for entity: {config.entity}"
            }

        created_count = 0
        updated_count = 0
        skipped_count = 0
        errors = []

        # Use provided department_id or fall back to current user's department
        target_department_id = department_id if department_id is not None else self.current_user.department_id

        for row in mapped_data:
            row_num = row.pop("_row_number")

            try:
                # Add department_id
                row["department_id"] = target_department_id

                # Handle lookups (find related entities)
                for lookup_field in config.get_lookup_fields():
                    field_name = lookup_field["name"]
                    lookup_value = row.get(field_name)

                    if lookup_value:
                        related_entity = self._lookup_related_entity(
                            lookup_field, lookup_value, target_department_id
                        )

                        if related_entity:
                            # Store resolved ID but keep original name for validation/logging
                            id_field = field_name.replace("_name", "_id")
                            row[id_field] = related_entity.id
                        elif lookup_field.get("auto_create"):
                            # Auto-create related entity
                            related_entity = self._create_related_entity(
                                lookup_field, lookup_value, target_department_id
                            )
                            if related_entity:
                                id_field = field_name.replace("_name", "_id")
                                row[id_field] = related_entity.id
                        else:
                            errors.append({
                                "row": row_num,
                                "error": f"Related entity not found: {lookup_value}"
                            })
                            skipped_count += 1
                            continue

                # Calculate derived fields
                calculated_fields = config.get_calculated_fields()
                if calculated_fields:
                    for field_name, expression in calculated_fields.items():
                        # Simple evaluation for sum expressions
                        if "+" in expression:
                            field_names = [f.strip() for f in expression.split("+")]
                            total = sum(row.get(f, 0) or 0 for f in field_names)
                            row[field_name] = total

                # Entity-specific transformations
                self._apply_entity_transformations(entity_type, row)

                # Apply default values for missing fields
                for field in config.fields:
                    field_name = field["name"]
                    if field_name not in row or row[field_name] is None:
                        if "default" in field:
                            row[field_name] = field["default"]

                # Filter out fields not present on the model before persistence
                persist_data = self._filter_model_fields(model_class, row)

                # Check for updates
                existing_entity = None
                if config.allows_update():
                    existing_entity = self._find_existing_entity(
                        model_class, config, row, target_department_id
                    )

                if existing_entity:
                    # Update
                    for key, value in persist_data.items():
                        setattr(existing_entity, key, value)
                    updated_count += 1
                else:
                    # Create new
                    entity = model_class(**persist_data)
                    self.db.add(entity)
                    created_count += 1

            except Exception as e:
                logger.error(f"Failed to import row {row_num}: {str(e)}")
                errors.append({
                    "row": row_num,
                    "error": str(e)
                })
                skipped_count += 1

        return {
            "success": True,
            "statistics": {
                "total_processed": len(mapped_data),
                "created": created_count,
                "updated": updated_count,
                "skipped": skipped_count,
                "errors": len(errors)
            },
            "errors": errors[:50]  # First 50 errors
        }

    @staticmethod
    def _filter_model_fields(model_class: Any, row_data: Dict[str, Any]) -> Dict[str, Any]:
        """Keep only attributes that correspond to actual model columns"""
        if not hasattr(model_class, "__table__"):
            return row_data

        model_columns = {column.key for column in model_class.__table__.columns}
        return {key: value for key, value in row_data.items() if key in model_columns}

    @staticmethod
    def _apply_entity_transformations(entity_type: str, row: Dict[str, Any]) -> None:
        """Apply entity-specific adjustments before persistence"""
        if entity_type != "payroll_plans":
            return

        base_salary = row.get("base_salary") or 0

        bonus_amount = row.get("bonus_amount") or 0
        social_contributions = row.get("social_contributions") or 0

        # Map generic bonus field to monthly_bonus by default
        row.setdefault("monthly_bonus", bonus_amount)
        row.setdefault("quarterly_bonus", 0)
        row.setdefault("annual_bonus", 0)
        row.setdefault("other_payments", social_contributions)

        # Total planned includes base salary, bonuses and other payments
        row["total_planned"] = (
            base_salary
            + (row.get("monthly_bonus") or 0)
            + (row.get("quarterly_bonus") or 0)
            + (row.get("annual_bonus") or 0)
            + (row.get("other_payments") or 0)
        )

    def _normalize_field_types(self, config: ImportConfig, mapped_data: List[Dict[str, Any]]) -> None:
        """Normalize mapped data values according to config field types."""
        type_map = {field["name"]: field.get("type") for field in config.fields}

        for row in mapped_data:
            for field_name, field_type in type_map.items():
                if field_type != "integer":
                    continue

                value = row.get(field_name)
                if value is None:
                    continue

                if isinstance(value, bool):
                    row[field_name] = 1 if value else 0
                elif isinstance(value, float):
                    if value.is_integer():
                        row[field_name] = int(value)
                elif isinstance(value, str):
                    stripped = value.strip()
                    if stripped.isdigit():
                        row[field_name] = int(stripped)
                    else:
                        try:
                            normalized = int(float(stripped.replace(",", ".")))
                            row[field_name] = normalized
                        except ValueError:
                            continue

    def _lookup_related_entity(
        self,
        lookup_field: Dict[str, Any],
        lookup_value: str,
        department_id: int
    ) -> Optional[Any]:
        """Find related entity by lookup value"""
        entity_name = lookup_field["lookup_entity"]
        field_name = lookup_field["lookup_field"]

        model_class = self.ENTITY_MODELS.get(entity_name)
        if not model_class:
            return None

        return self.db.query(model_class).filter(
            getattr(model_class, field_name) == lookup_value,
            model_class.department_id == department_id
        ).first()

    def _create_related_entity(
        self,
        lookup_field: Dict[str, Any],
        name: str,
        department_id: int
    ) -> Optional[Any]:
        """Auto-create related entity"""
        entity_name = lookup_field["lookup_entity"]
        model_class = self.ENTITY_MODELS.get(entity_name)

        if not model_class:
            return None

        # Create with minimal data
        entity_data = {
            "name": name,
            "department_id": department_id
        }

        # Add type for categories
        if entity_name == "budget_categories":
            # Detect OPEX/CAPEX from name
            name_lower = name.lower()
            if any(kw in name_lower for kw in ["оборудование", "техника", "hardware", "equipment"]):
                entity_data["type"] = ExpenseTypeEnum.CAPEX
            else:
                entity_data["type"] = ExpenseTypeEnum.OPEX

        entity = model_class(**entity_data)
        self.db.add(entity)
        self.db.flush()  # Get ID immediately

        return entity

    def _find_existing_entity(
        self,
        model_class: Any,
        config: ImportConfig,
        row_data: Dict[str, Any],
        department_id: int
    ) -> Optional[Any]:
        """Find existing entity by update key"""
        update_key = config.get_update_key()
        if not update_key:
            return None

        query = self.db.query(model_class).filter(
            model_class.department_id == department_id
        )

        # Build filter
        key_fields = [update_key] if isinstance(update_key, str) else update_key

        for key in key_fields:
            attr_name, value = self._resolve_update_key(model_class, row_data, key)
            if value is None:
                return None

            column_attr = getattr(model_class, attr_name, None)
            if column_attr is None:
                raise AttributeError(f"type object '{model_class.__name__}' has no attribute '{attr_name}'")

            query = query.filter(column_attr == value)

        return query.first()

    @staticmethod
    def _resolve_update_key(
        model_class: Any,
        row_data: Dict[str, Any],
        key: str
    ) -> Tuple[str, Any]:
        """Map logical update key names (like *_name) to actual model columns"""
        if hasattr(model_class, key):
            return key, row_data.get(key)

        if key.endswith("_name"):
            alt_key = key.replace("_name", "_id")
            if hasattr(model_class, alt_key):
                # Prefer already-resolved ID value if present
                value = row_data.get(alt_key)
                if value is not None:
                    return alt_key, value

        return key, row_data.get(key)
