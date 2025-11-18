"""
Universal Dynamic Import Service

Provides flexible Excel parsing with:
- Auto-detection of data types
- Flexible column mapping (Russian/English)
- Preview with validation
- Support for multiple date/number formats
- Entity-agnostic design
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
from decimal import Decimal
import re
from enum import Enum
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


class DataType(str, Enum):
    """Detected data types"""
    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    ENUM = "enum"


class ValidationSeverity(str, Enum):
    """Validation message severity"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationMessage:
    """Validation message with context"""
    def __init__(
        self,
        row: int,
        column: str,
        severity: ValidationSeverity,
        message: str,
        value: Any = None
    ):
        self.row = row
        self.column = column
        self.severity = severity
        self.message = message
        self.value = value

    def to_dict(self):
        return {
            "row": self.row,
            "column": self.column,
            "severity": self.severity,
            "message": self.message,
            "value": str(self.value) if self.value is not None else None
        }


class ColumnInfo:
    """Column metadata"""
    def __init__(
        self,
        index: int,
        name: str,
        detected_type: DataType,
        sample_values: List[Any],
        null_count: int,
        unique_count: int,
        total_count: int
    ):
        self.index = index
        self.name = name
        self.detected_type = detected_type
        self.sample_values = sample_values
        self.null_count = null_count
        self.unique_count = unique_count
        self.total_count = total_count

    def to_dict(self):
        return {
            "index": self.index,
            "name": self.name,
            "detected_type": self.detected_type,
            "sample_values": [str(v) for v in self.sample_values if pd.notna(v)],
            "null_count": self.null_count,
            "unique_count": self.unique_count,
            "total_count": self.total_count,
            "completeness": round((self.total_count - self.null_count) / self.total_count * 100, 2) if self.total_count > 0 else 0
        }


class DynamicImportService:
    """Universal service for dynamic data import"""

    # Common date formats
    DATE_FORMATS = [
        "%d.%m.%Y",      # 31.12.2024
        "%d/%m/%Y",      # 31/12/2024
        "%Y-%m-%d",      # 2024-12-31
        "%d-%m-%Y",      # 31-12-2024
        "%d.%m.%y",      # 31.12.24
        "%d/%m/%y",      # 31/12/24
        "%Y/%m/%d",      # 2024/12/31
        "%d %b %Y",      # 31 Dec 2024
        "%d %B %Y",      # 31 December 2024
    ]

    # Common boolean values
    TRUE_VALUES = {
        "да", "yes", "true", "1", "y", "т", "истина", "+",
        "активен", "активна", "активно", "active", "enabled"
    }
    FALSE_VALUES = {
        "нет", "no", "false", "0", "n", "ф", "ложь", "-",
        "неактивен", "неактивна", "неактивно", "inactive", "disabled"
    }

    # Common column name aliases (Russian/English)
    COLUMN_ALIASES = {
        # Common fields
        "название": ["название", "name", "наименование", "title"],
        "описание": ["описание", "description", "desc"],
        "комментарий": ["комментарий", "comment", "примечание", "notes", "note"],
        "активен": ["активен", "активна", "active", "is_active", "enabled"],
        "тип": ["тип", "type", "вид", "категория"],

        # Financial
        "сумма": ["сумма", "amount", "sum", "total"],
        "оклад": ["оклад", "salary", "base_salary", "базовый_оклад"],
        "премия": ["премия", "bonus"],
        "год": ["год", "year"],
        "месяц": ["месяц", "month"],

        # Organizations
        "инн": ["инн", "inn", "tax_id"],
        "краткое_название": ["краткое_название", "short_name", "краткое название"],
        "контакт": ["контакт", "контактная_информация", "contact", "contact_info"],

        # Employees
        "фио": ["фио", "full_name", "имя", "name", "employee", "сотрудник"],
        "должность": ["должность", "position", "роль", "role"],

        # Dates
        "дата": ["дата", "date"],
        "дата_оплаты": ["дата_оплаты", "payment_date", "дата оплаты"],
        "дата_заявки": ["дата_заявки", "request_date", "дата заявки"],

        # Status
        "статус": ["статус", "status", "состояние", "state"],
    }

    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.columns_info: List[ColumnInfo] = []
        self.validation_messages: List[ValidationMessage] = []

    def read_excel(
        self,
        file_content: bytes,
        sheet_name: Union[str, int] = 0,
        header_row: int = 0,
        max_rows: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Read Excel file and analyze structure

        Args:
            file_content: File bytes
            sheet_name: Sheet name or index
            header_row: Row index for headers (0-based)
            max_rows: Maximum rows to read (None = all)

        Returns:
            Dictionary with file info and column analysis
        """
        try:
            # Read Excel
            excel_file = pd.ExcelFile(BytesIO(file_content))

            # Get sheet names
            sheet_names = excel_file.sheet_names

            # Read specified sheet
            if isinstance(sheet_name, str) and sheet_name not in sheet_names:
                return {
                    "success": False,
                    "error": f"Sheet '{sheet_name}' not found. Available: {sheet_names}"
                }

            self.df = pd.read_excel(
                BytesIO(file_content),
                sheet_name=sheet_name,
                header=header_row,
                skiprows=[1] if header_row == 0 else None,  # Skip type hints row (row 2 in Excel)
                nrows=max_rows
            )

            # DEBUG: Log what was read
            logger.info(f"=== EXCEL READ DEBUG ===")
            logger.info(f"header_row: {header_row}")
            logger.info(f"skiprows: {[1] if header_row == 0 else None}")
            logger.info(f"DataFrame shape: {self.df.shape}")
            logger.info(f"Columns: {list(self.df.columns)}")
            logger.info(f"First row data:\n{self.df.head(1).to_dict('records')}")
            logger.info(f"======================")

            # Analyze columns
            self.columns_info = self._analyze_columns()

            return {
                "success": True,
                "sheet_names": sheet_names,
                "selected_sheet": sheet_names[sheet_name] if isinstance(sheet_name, int) else sheet_name,
                "total_rows": len(self.df),
                "total_columns": len(self.df.columns),
                "columns": [col.to_dict() for col in self.columns_info],
                "preview_rows": self._get_preview_rows(10)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to read Excel file: {str(e)}"
            }

    def _analyze_columns(self) -> List[ColumnInfo]:
        """Analyze each column and detect data type"""
        columns_info = []

        for idx, col_name in enumerate(self.df.columns):
            series = self.df[col_name]

            # Get statistics
            null_count = series.isna().sum()
            unique_count = series.nunique()
            total_count = len(series)

            # Get sample values (non-null)
            sample_values = series.dropna().head(5).tolist()

            # Detect data type
            detected_type = self._detect_data_type(series)

            columns_info.append(ColumnInfo(
                index=idx,
                name=str(col_name),
                detected_type=detected_type,
                sample_values=sample_values,
                null_count=null_count,
                unique_count=unique_count,
                total_count=total_count
            ))

        return columns_info

    def _detect_data_type(self, series: pd.Series) -> DataType:
        """Detect the most likely data type for a series"""
        # Skip null values
        series_clean = series.dropna()

        if len(series_clean) == 0:
            return DataType.STRING

        # Check if boolean
        if self._is_boolean_column(series_clean):
            return DataType.BOOLEAN

        # Check if date/datetime
        if self._is_date_column(series_clean):
            return DataType.DATE

        # Check if numeric
        if pd.api.types.is_numeric_dtype(series_clean):
            # Check if all values are integers
            if all(float(x).is_integer() for x in series_clean if pd.notna(x)):
                return DataType.INTEGER
            return DataType.DECIMAL

        # Try to convert to numeric
        try:
            numeric_series = pd.to_numeric(series_clean, errors='coerce')
            if numeric_series.notna().sum() / len(series_clean) > 0.8:  # 80% convertible
                if all(float(x).is_integer() for x in numeric_series.dropna()):
                    return DataType.INTEGER
                return DataType.DECIMAL
        except:
            pass

        # Check if enum (low unique count)
        unique_ratio = series_clean.nunique() / len(series_clean)
        if unique_ratio < 0.1 and series_clean.nunique() < 20:
            return DataType.ENUM

        return DataType.STRING

    def _is_boolean_column(self, series: pd.Series) -> bool:
        """Check if column contains boolean values"""
        unique_values = set(str(v).lower().strip() for v in series.unique())
        all_boolean_values = self.TRUE_VALUES | self.FALSE_VALUES
        return unique_values.issubset(all_boolean_values)

    def _is_date_column(self, series: pd.Series) -> bool:
        """Check if column contains date values"""
        # If already datetime
        if pd.api.types.is_datetime64_any_dtype(series):
            return True

        # Try parsing dates
        sample = series.head(10)
        parsed_count = 0

        for value in sample:
            if self._parse_date(str(value)) is not None:
                parsed_count += 1

        return parsed_count / len(sample) > 0.8  # 80% parseable

    def _get_preview_rows(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get preview rows as list of dictionaries"""
        preview_df = self.df.head(limit)

        # Convert to records, handling NaN
        records = []
        for idx, row in preview_df.iterrows():
            record = {"_row_number": idx + 1}
            for col in preview_df.columns:
                value = row[col]
                if pd.isna(value):
                    record[col] = None
                elif isinstance(value, (pd.Timestamp, datetime)):
                    record[col] = value.isoformat()
                elif isinstance(value, (np.integer, np.floating)):
                    record[col] = float(value)
                else:
                    record[col] = str(value)
            records.append(record)

        return records

    def map_columns(
        self,
        column_mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Map Excel columns to entity fields

        Args:
            column_mapping: Dict of {excel_column: entity_field}

        Returns:
            Mapped data with validation messages
        """
        if self.df is None:
            return {"success": False, "error": "No data loaded. Call read_excel first."}

        # DEBUG: Log mapping
        logger.info(f"=== MAP COLUMNS DEBUG ===")
        logger.info(f"Column mapping received: {column_mapping}")
        logger.info(f"DataFrame columns: {list(self.df.columns)}")
        logger.info(f"DataFrame has {len(self.df)} rows")
        logger.info(f"========================")

        self.validation_messages = []
        mapped_data = []

        for idx, row in self.df.iterrows():
            row_data = {}
            row_number = idx + 1

            for excel_col, entity_field in column_mapping.items():
                if excel_col not in self.df.columns:
                    self.validation_messages.append(ValidationMessage(
                        row=row_number,
                        column=excel_col,
                        severity=ValidationSeverity.ERROR,
                        message=f"Column '{excel_col}' not found in Excel file"
                    ))
                    continue

                value = row[excel_col]

                # Skip empty values
                if pd.isna(value):
                    row_data[entity_field] = None
                    continue

                # Get column info
                col_info = next((c for c in self.columns_info if c.name == excel_col), None)
                if col_info is None:
                    row_data[entity_field] = value
                    continue

                # Convert based on detected type
                try:
                    converted_value = self._convert_value(value, col_info.detected_type)
                    row_data[entity_field] = converted_value
                except Exception as e:
                    self.validation_messages.append(ValidationMessage(
                        row=row_number,
                        column=excel_col,
                        severity=ValidationSeverity.WARNING,
                        message=f"Failed to convert value: {str(e)}",
                        value=value
                    ))
                    row_data[entity_field] = str(value)

            mapped_data.append({"_row_number": row_number, **row_data})

        return {
            "success": True,
            "total_rows": len(mapped_data),
            "mapped_data": mapped_data,
            "validation_messages": [msg.to_dict() for msg in self.validation_messages]
        }

    def _convert_value(self, value: Any, target_type: DataType) -> Any:
        """Convert value to target type"""
        if pd.isna(value):
            return None

        if target_type == DataType.STRING:
            return str(value).strip()

        elif target_type == DataType.INTEGER:
            return int(float(value))

        elif target_type == DataType.DECIMAL:
            return float(value)

        elif target_type == DataType.BOOLEAN:
            return self._parse_boolean(str(value))

        elif target_type == DataType.DATE:
            return self._parse_date(str(value))

        elif target_type == DataType.DATETIME:
            return self._parse_date(str(value))

        else:
            return str(value)

    def _parse_boolean(self, value: str) -> bool:
        """Parse boolean value from string"""
        value_lower = value.lower().strip()

        if value_lower in self.TRUE_VALUES:
            return True
        elif value_lower in self.FALSE_VALUES:
            return False
        else:
            raise ValueError(f"Cannot parse boolean from '{value}'")

    def _parse_date(self, value: str) -> Optional[datetime]:
        """Parse date from string using multiple formats"""
        if isinstance(value, (datetime, pd.Timestamp)):
            return value

        value_str = str(value).strip()

        for date_format in self.DATE_FORMATS:
            try:
                return datetime.strptime(value_str, date_format)
            except ValueError:
                continue

        return None

    def suggest_mapping(
        self,
        target_fields: List[str],
        alias_map: Optional[Dict[str, str]] = None
    ) -> Dict[str, Optional[str]]:
        """
        Suggest column mapping based on field names and aliases

        Args:
            target_fields: List of entity field names to map to
            alias_map: Dictionary of {alias_lowercase: field_name} from config

        Returns:
            Dictionary of {entity_field: suggested_excel_column}
        """
        if self.df is None:
            return {}

        suggestions = {}
        # Remove asterisks and normalize column names
        excel_columns_lower = [str(col).lower().strip().replace('*', '').strip() for col in self.df.columns]

        for target_field in target_fields:
            # Try matching using alias_map if provided (from config)
            if alias_map:
                for excel_col_idx, excel_col_lower in enumerate(excel_columns_lower):
                    # Check exact match first
                    if alias_map.get(excel_col_lower) == target_field:
                        original_col = self.df.columns[excel_col_idx]
                        suggestions[target_field] = str(original_col)
                        break

                    # Check if any alias is contained in Excel column name
                    # e.g., "оклад" in "базовый оклад"
                    for alias_lower, field_name in alias_map.items():
                        if field_name == target_field and alias_lower in excel_col_lower:
                            original_col = self.df.columns[excel_col_idx]
                            suggestions[target_field] = str(original_col)
                            break

                    if target_field in suggestions:
                        break

            # Fallback to old behavior for backwards compatibility
            if target_field not in suggestions:
                target_lower = target_field.lower().strip()

                # Check static aliases (backwards compatibility)
                if target_lower in self.COLUMN_ALIASES:
                    aliases = self.COLUMN_ALIASES[target_lower]

                    for alias in aliases:
                        if alias in excel_columns_lower:
                            # Get original column name
                            original_col = self.df.columns[excel_columns_lower.index(alias)]
                            suggestions[target_field] = str(original_col)
                            break

                # Direct match
                if target_field not in suggestions and target_lower in excel_columns_lower:
                    original_col = self.df.columns[excel_columns_lower.index(target_lower)]
                    suggestions[target_field] = str(original_col)

                # Fuzzy match (contains)
                if target_field not in suggestions:
                    for idx, excel_col in enumerate(excel_columns_lower):
                        if target_lower in excel_col or excel_col in target_lower:
                            suggestions[target_field] = str(self.df.columns[idx])
                            break

        # Fill unmapped fields with None
        for field in target_fields:
            if field not in suggestions:
                suggestions[field] = None

        return suggestions

    def validate_data(
        self,
        data: List[Dict[str, Any]],
        validation_rules: Dict[str, Any]
    ) -> List[ValidationMessage]:
        """
        Validate mapped data against rules

        Args:
            data: List of mapped records
            validation_rules: Dictionary of field_name: validation_config

        Returns:
            List of validation messages
        """
        messages = []

        for record in data:
            row_number = record.get("_row_number", 0)

            for field, rules in validation_rules.items():
                value = record.get(field)

                # Required check
                if rules.get("required", False) and value is None:
                    messages.append(ValidationMessage(
                        row=row_number,
                        column=field,
                        severity=ValidationSeverity.ERROR,
                        message=f"Field '{field}' is required",
                        value=value
                    ))
                    continue

                # Skip further validation if value is None and not required
                if value is None:
                    continue

                # Type check
                expected_type = rules.get("type")
                if expected_type and not isinstance(value, expected_type):
                    messages.append(ValidationMessage(
                        row=row_number,
                        column=field,
                        severity=ValidationSeverity.ERROR,
                        message=f"Field '{field}' must be {expected_type.__name__}",
                        value=value
                    ))

                # Min/Max check for numbers
                if isinstance(value, (int, float, Decimal)):
                    min_value = rules.get("min")
                    max_value = rules.get("max")

                    if min_value is not None and value < min_value:
                        messages.append(ValidationMessage(
                            row=row_number,
                            column=field,
                            severity=ValidationSeverity.ERROR,
                            message=f"Field '{field}' must be >= {min_value}",
                            value=value
                        ))

                    if max_value is not None and value > max_value:
                        messages.append(ValidationMessage(
                            row=row_number,
                            column=field,
                            severity=ValidationSeverity.ERROR,
                            message=f"Field '{field}' must be <= {max_value}",
                            value=value
                        ))

                # Length check for strings
                if isinstance(value, str):
                    min_length = rules.get("min_length")
                    max_length = rules.get("max_length")

                    if min_length is not None and len(value) < min_length:
                        messages.append(ValidationMessage(
                            row=row_number,
                            column=field,
                            severity=ValidationSeverity.ERROR,
                            message=f"Field '{field}' must be at least {min_length} characters",
                            value=value
                        ))

                    if max_length is not None and len(value) > max_length:
                        messages.append(ValidationMessage(
                            row=row_number,
                            column=field,
                            severity=ValidationSeverity.WARNING,
                            message=f"Field '{field}' exceeds {max_length} characters (will be truncated)",
                            value=value
                        ))

                # Enum check
                allowed_values = rules.get("enum")
                if allowed_values and value not in allowed_values:
                    messages.append(ValidationMessage(
                        row=row_number,
                        column=field,
                        severity=ValidationSeverity.ERROR,
                        message=f"Field '{field}' must be one of: {allowed_values}",
                        value=value
                    ))

                # Pattern check (regex)
                pattern = rules.get("pattern")
                if pattern and isinstance(value, str):
                    if not re.match(pattern, value):
                        messages.append(ValidationMessage(
                            row=row_number,
                            column=field,
                            severity=ValidationSeverity.ERROR,
                            message=f"Field '{field}' does not match required pattern",
                            value=value
                        ))

        return messages
