"""
Import Configuration Manager

Manages import configurations for different entities.
Loads and validates JSON config files.
"""

import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path


class ImportConfig:
    """Import configuration for an entity"""

    def __init__(self, config_data: Dict[str, Any]):
        self.entity = config_data.get("entity")
        self.display_name = config_data.get("display_name", {})
        self.description = config_data.get("description", {})
        self.fields = config_data.get("fields", [])
        self.validation_rules = config_data.get("validation_rules", {})
        self.import_options = config_data.get("import_options", {})

        # Build quick lookup dicts
        self._field_by_name = {f["name"]: f for f in self.fields}
        self._alias_map = self._build_alias_map()

    def _build_alias_map(self) -> Dict[str, str]:
        """Build map of alias -> field_name"""
        alias_map = {}
        for field in self.fields:
            field_name = field["name"]
            # Add field name itself
            alias_map[field_name.lower()] = field_name

            # Add all aliases
            for alias in field.get("aliases", []):
                alias_map[alias.lower()] = field_name

        return alias_map

    def get_field(self, field_name: str) -> Optional[Dict[str, Any]]:
        """Get field config by name"""
        return self._field_by_name.get(field_name)

    def get_field_by_alias(self, alias: str) -> Optional[Dict[str, Any]]:
        """Get field config by alias"""
        field_name = self._alias_map.get(alias.lower())
        if field_name:
            return self._field_by_name.get(field_name)
        return None

    def get_required_fields(self) -> List[str]:
        """Get list of required field names"""
        return [f["name"] for f in self.fields if f.get("required", False)]

    def get_lookup_fields(self) -> List[Dict[str, Any]]:
        """Get fields that reference other entities"""
        return [f for f in self.fields if "lookup_entity" in f]

    def get_target_field_names(self) -> List[str]:
        """Get list of all field names"""
        return [f["name"] for f in self.fields]

    def should_auto_create_related(self) -> bool:
        """Check if related entities should be auto-created"""
        return self.import_options.get("auto_create_related", False)

    def allows_update(self) -> bool:
        """Check if updates are allowed"""
        return self.import_options.get("allow_update", False)

    def get_update_key(self) -> Optional[str | List[str]]:
        """Get the field(s) used to identify existing records"""
        return self.import_options.get("update_key")

    def get_batch_size(self) -> int:
        """Get batch size for imports"""
        return self.import_options.get("batch_size", 100)

    def get_calculated_fields(self) -> Dict[str, str]:
        """Get calculated fields and their expressions"""
        return self.import_options.get("calculated_fields", {})

    def get_alias_map(self) -> Dict[str, str]:
        """Get alias map (alias_lowercase -> field_name)"""
        return self._alias_map


class ImportConfigManager:
    """Manager for import configurations"""

    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            # Default to import_configs directory
            base_dir = Path(__file__).parent.parent
            config_dir = os.path.join(base_dir, "import_configs")

        self.config_dir = config_dir
        self._configs: Dict[str, ImportConfig] = {}
        self._load_configs()

    def _load_configs(self):
        """Load all configuration files from directory"""
        if not os.path.exists(self.config_dir):
            return

        for filename in os.listdir(self.config_dir):
            if filename.endswith(".json"):
                entity_type = filename[:-5]  # Remove .json
                config_path = os.path.join(self.config_dir, filename)

                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        config_data = json.load(f)
                        self._configs[entity_type] = ImportConfig(config_data)
                except Exception as e:
                    print(f"Failed to load config {filename}: {e}")

    def get_config(self, entity_type: str) -> Optional[ImportConfig]:
        """Get configuration for entity type"""
        return self._configs.get(entity_type)

    def get_available_entities(self) -> List[str]:
        """Get list of available entity types"""
        return list(self._configs.keys())

    def get_entity_info(self, entity_type: str, language: str = "ru") -> Optional[Dict[str, Any]]:
        """Get display info for entity"""
        config = self.get_config(entity_type)
        if not config:
            return None

        return {
            "entity": config.entity,
            "display_name": config.display_name.get(language, config.entity),
            "description": config.description.get(language, ""),
            "fields_count": len(config.fields),
            "required_fields": config.get_required_fields(),
            "allows_update": config.allows_update(),
            "auto_create_related": config.should_auto_create_related()
        }

    def get_all_entities_info(self, language: str = "ru") -> List[Dict[str, Any]]:
        """Get info for all available entities"""
        return [
            self.get_entity_info(entity_type, language)
            for entity_type in self.get_available_entities()
        ]

    def reload_configs(self):
        """Reload all configurations"""
        self._configs.clear()
        self._load_configs()


# Global instance
_config_manager: Optional[ImportConfigManager] = None


def get_import_config_manager() -> ImportConfigManager:
    """Get global config manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ImportConfigManager()
    return _config_manager
