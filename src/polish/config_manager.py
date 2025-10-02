#!/usr/bin/env python3
"""
Configuration Manager - Flexible system configuration
Generic configuration management system with validation, hot-reloading, and environment support
"""

import json
import yaml
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum

from src.core import FileFormat, ProcessingConfig


class ConfigFormat(str, Enum):
    """Configuration file formats"""
    JSON = "json"
    YAML = "yaml"
    ENV = "env"
    INI = "ini"


@dataclass
class ConfigSection:
    """Configuration section"""
    name: str
    data: Dict[str, Any]
    required: bool = True
    description: str = ""


@dataclass
class ConfigValidationRule:
    """Configuration validation rule"""
    key: str
    required: bool = True
    data_type: type = str
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    allowed_values: Optional[List[Any]] = None
    custom_validator: Optional[Callable[[Any], bool]] = None


class ConfigurationManager:
    """
    Generic configuration management system with comprehensive features
    
    Features:
    - Multiple configuration sources
    - Environment variable support
    - Configuration validation
    - Hot-reloading
    - Default values
    - Configuration merging
    - Type conversion
    - Security features
    """
    
    def __init__(self, config_path: Optional[str] = None, 
                 config_format: ConfigFormat = ConfigFormat.JSON):
        """Initialize configuration manager"""
        self.config_path = config_path
        self.config_format = config_format
        self.config_data: Dict[str, Any] = {}
        self.default_config: Dict[str, Any] = {}
        self.validation_rules: List[ConfigValidationRule] = []
        self.config_sections: Dict[str, ConfigSection] = {}
        
        # Configuration change callbacks
        self.change_callbacks: List[Callable[[str, Any, Any], Any]] = []
        
        # Initialize default configuration
        self._initialize_default_config()
        
        # Load configuration
        if config_path:
            self.load_configuration()
    
    def _initialize_default_config(self):
        """Initialize default configuration"""
        self.default_config = {
            'file_scanner': {
                'supported_formats': ['.pdf', '.docx', '.doc'],
                'max_file_size': 50 * 1024 * 1024,  # 50MB
                'min_file_size': 1024,  # 1KB
                'scan_depth': 10,
                'exclude_patterns': ['.git', '__pycache__', 'node_modules']
            },
            'validation_engine': {
                'min_quality_score': 0.8,
                'max_processing_time': 300.0,
                'require_manual_review': False,
                'auto_approve_threshold': 0.95,
                'escalation_threshold': 0.3
            },
            'queue_manager': {
                'max_concurrent_items': 5,
                'max_queue_size': 1000,
                'retry_delay_base': 60,
                'max_retry_delay': 3600
            },
            'review_system': {
                'reviewers': [],
                'escalation_rules': {},
                'review_timeout_hours': 24
            },
            'output_manager': {
                'base_output_dir': 'output',
                'organize_by_date': True,
                'organize_by_person': True,
                'create_backups': True,
                'backup_retention_days': 30,
                'archive_old_files': True,
                'archive_after_days': 90,
                'file_naming_pattern': '{person_name}_{date}_{type}',
                'create_metadata_files': True
            },
            'monitoring_system': {
                'collection_interval': 5,
                'retention_hours': 24,
                'alert_thresholds': {
                    'system.cpu.usage': {'warning': 80.0, 'error': 90.0, 'critical': 95.0},
                    'system.memory.usage': {'warning': 80.0, 'error': 90.0, 'critical': 95.0},
                    'system.disk.usage': {'warning': 85.0, 'error': 90.0, 'critical': 95.0}
                }
            },
            'error_recovery': {
                'retry_config': {
                    'max_attempts': 3,
                    'base_delay': 1.0,
                    'max_delay': 60.0,
                    'strategy': 'exponential',
                    'jitter': True
                },
                'circuit_config': {
                    'failure_threshold': 5,
                    'recovery_timeout': 60.0,
                    'success_threshold': 3,
                    'timeout': 30.0
                }
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
                'file_enabled': True,
                'console_enabled': True,
                'max_file_size': 10 * 1024 * 1024,  # 10MB
                'backup_count': 5
            },
            'security': {
                'encrypt_sensitive_data': False,
                'mask_passwords': True,
                'allowed_file_extensions': ['.pdf', '.docx', '.doc'],
                'max_file_size_mb': 50
            }
        }
        
        # Set default config as current config
        self.config_data = self.default_config.copy()
    
    def load_configuration(self, config_path: Optional[str] = None):
        """Load configuration from file"""
        path = config_path or self.config_path
        if not path:
            raise ValueError("No configuration path provided")
        
        config_file = Path(path)
        if not config_file.exists():
            self._log(f"Configuration file not found: {path}, using defaults", "WARNING")
            return
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                if self.config_format == ConfigFormat.JSON:
                    file_config = json.load(f)
                elif self.config_format == ConfigFormat.YAML:
                    file_config = yaml.safe_load(f)
                else:
                    raise ValueError(f"Unsupported config format: {self.config_format}")
            
            # Merge with defaults
            self.config_data = self._merge_configs(self.default_config, file_config)
            
            # Load environment variables
            self._load_environment_variables()
            
            # Validate configuration
            self._validate_configuration()
            
            self._log(f"Configuration loaded from {path}")
            
        except Exception as e:
            self._log(f"Failed to load configuration: {str(e)}", "ERROR")
            raise
    
    def save_configuration(self, config_path: Optional[str] = None):
        """Save current configuration to file"""
        path = config_path or self.config_path
        if not path:
            raise ValueError("No configuration path provided")
        
        config_file = Path(path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                if self.config_format == ConfigFormat.JSON:
                    json.dump(self.config_data, f, indent=2, ensure_ascii=False)
                elif self.config_format == ConfigFormat.YAML:
                    yaml.dump(self.config_data, f, default_flow_style=False, allow_unicode=True)
                else:
                    raise ValueError(f"Unsupported config format: {self.config_format}")
            
            self._log(f"Configuration saved to {path}")
            
        except Exception as e:
            self._log(f"Failed to save configuration: {str(e)}", "ERROR")
            raise
    
    def _merge_configs(self, default: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge configuration dictionaries"""
        result = default.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _load_environment_variables(self):
        """Load configuration from environment variables"""
        env_mappings = {
            'CV_AUTOMATION_LOG_LEVEL': 'logging.level',
            'CV_AUTOMATION_OUTPUT_DIR': 'output_manager.base_output_dir',
            'CV_AUTOMATION_MAX_FILE_SIZE': 'file_scanner.max_file_size',
            'CV_AUTOMATION_MAX_CONCURRENT': 'queue_manager.max_concurrent_items',
            'CV_AUTOMATION_MONITORING_INTERVAL': 'monitoring_system.collection_interval'
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                self._set_nested_value(config_path, env_value)
    
    def _set_nested_value(self, path: str, value: Any):
        """Set nested configuration value using dot notation"""
        keys = path.split('.')
        current = self.config_data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Convert value type if needed
        converted_value = self._convert_value_type(value)
        current[keys[-1]] = converted_value
    
    def _convert_value_type(self, value: str) -> Any:
        """Convert string value to appropriate type"""
        # Try to convert to number
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # Try to convert to boolean
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Try to parse as JSON
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Return as string
        return value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        keys = key.split('.')
        current = self.config_data
        
        try:
            for key_part in keys:
                current = current[key_part]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """Set configuration value using dot notation"""
        old_value = self.get(key)
        self._set_nested_value(key, value)
        
        # Call change callbacks
        for callback in self.change_callbacks:
            try:
                callback(key, old_value, value)
            except Exception as e:
                self._log(f"Configuration change callback error: {str(e)}", "ERROR")
    
    def get_section(self, section_name: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        return self.get(section_name, {})
    
    def set_section(self, section_name: str, section_data: Dict[str, Any]):
        """Set entire configuration section"""
        self.set(section_name, section_data)
    
    def add_validation_rule(self, rule: ConfigValidationRule):
        """Add configuration validation rule"""
        self.validation_rules.append(rule)
    
    def _validate_configuration(self):
        """Validate current configuration"""
        for rule in self.validation_rules:
            value = self.get(rule.key)
            
            # Check if required
            if rule.required and value is None:
                raise ValueError(f"Required configuration key missing: {rule.key}")
            
            if value is None:
                continue
            
            # Check data type
            if not isinstance(value, rule.data_type):
                raise ValueError(f"Configuration key {rule.key} has wrong type: expected {rule.data_type}, got {type(value)}")
            
            # Check min/max values
            if rule.min_value is not None and value < rule.min_value:
                raise ValueError(f"Configuration key {rule.key} value {value} is below minimum {rule.min_value}")
            
            if rule.max_value is not None and value > rule.max_value:
                raise ValueError(f"Configuration key {rule.key} value {value} is above maximum {rule.max_value}")
            
            # Check allowed values
            if rule.allowed_values is not None and value not in rule.allowed_values:
                raise ValueError(f"Configuration key {rule.key} value {value} not in allowed values: {rule.allowed_values}")
            
            # Custom validation
            if rule.custom_validator and not rule.custom_validator(value):
                raise ValueError(f"Configuration key {rule.key} failed custom validation")
    
    def add_change_callback(self, callback: Callable[[str, Any, Any], Any]):
        """Add configuration change callback"""
        self.change_callbacks.append(callback)
    
    def reload_configuration(self):
        """Reload configuration from file"""
        if self.config_path:
            self.load_configuration()
            self._log("Configuration reloaded")
    
    def export_configuration(self, format_type: ConfigFormat = None) -> str:
        """Export current configuration as string"""
        format_type = format_type or self.config_format
        
        if format_type == ConfigFormat.JSON:
            return json.dumps(self.config_data, indent=2, ensure_ascii=False)
        elif format_type == ConfigFormat.YAML:
            return yaml.dump(self.config_data, default_flow_style=False, allow_unicode=True)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get configuration summary"""
        return {
            'config_path': self.config_path,
            'config_format': self.config_format.value,
            'sections': list(self.config_data.keys()),
            'validation_rules': len(self.validation_rules),
            'change_callbacks': len(self.change_callbacks),
            'environment_variables_loaded': len([k for k in os.environ.keys() if k.startswith('CV_AUTOMATION_')])
        }
    
    def create_configuration_template(self, output_path: str):
        """Create configuration template file"""
        template_data = self.default_config.copy()
        
        # Add comments/descriptions
        template_data['_comments'] = {
            'file_scanner': 'Configuration for file discovery and validation',
            'validation_engine': 'Configuration for data validation and quality checks',
            'queue_manager': 'Configuration for processing queue management',
            'review_system': 'Configuration for manual review workflows',
            'output_manager': 'Configuration for file output and organization',
            'monitoring_system': 'Configuration for system monitoring and alerting',
            'error_recovery': 'Configuration for error handling and retry logic',
            'logging': 'Configuration for logging system',
            'security': 'Configuration for security settings'
        }
        
        template_file = Path(output_path)
        template_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(template_file, 'w', encoding='utf-8') as f:
            if self.config_format == ConfigFormat.JSON:
                json.dump(template_data, f, indent=2, ensure_ascii=False)
            elif self.config_format == ConfigFormat.YAML:
                yaml.dump(template_data, f, default_flow_style=False, allow_unicode=True)
        
        self._log(f"Configuration template created: {output_path}")
    
    def _log(self, message: str, level: str = "INFO") -> None:
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] [ConfigurationManager] {message}")
