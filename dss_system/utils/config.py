"""Configuration management for DSS system"""

import os
from pathlib import Path
from typing import Dict, Any
import yaml


class Config:
    """Configuration manager"""

    # Default configuration
    DEFAULT_CONFIG = {
        'data': {
            'data_dir': 'D:/KLTN/data/lite_furniture_data',
            'output_dir': 'D:/KLTN/outputs'
        },
        'paths': {
            'reports': 'D:/KLTN/outputs/reports',
            'visualizations': 'D:/KLTN/outputs/visualizations',
            'results': 'D:/KLTN/outputs/results'
        },
        'optimization': {
            'solver': 'PULP_CBC_CMD',
            'time_limit': 300,  # seconds
            'mip_gap': 0.01
        },
        'costs': {
            'stockout_penalty': 100,  # per unit
            'emergency_order_multiplier': 1.5
        },
        'policies': {
            'safety_stock_service_level': 0.95,
            'review_period_days': 7,
            'max_transshipment_distance': 5000  # km
        }
    }

    def __init__(self, config_file: str = None):
        self.config = self.DEFAULT_CONFIG.copy()

        # Load from file if provided
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)

    def load_from_file(self, file_path: str):
        """Load configuration from YAML file"""
        with open(file_path, 'r') as f:
            custom_config = yaml.safe_load(f)
            self._update_config(self.config, custom_config)

    def _update_config(self, base: Dict, update: Dict):
        """Recursively update configuration"""
        for key, value in update.items():
            if isinstance(value, dict) and key in base:
                self._update_config(base[key], value)
            else:
                base[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'data.data_dir')"""
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def get_data_dir(self) -> Path:
        """Get data directory path"""
        return Path(self.get('data.data_dir'))

    def get_output_dir(self) -> Path:
        """Get output directory path"""
        return Path(self.get('data.output_dir'))

    def ensure_directories(self):
        """Create output directories if they don't exist"""
        for key in ['reports', 'visualizations', 'results']:
            path = Path(self.get(f'paths.{key}'))
            path.mkdir(parents=True, exist_ok=True)

    def save_to_file(self, file_path: str):
        """Save configuration to YAML file"""
        with open(file_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)

    def __repr__(self):
        return f"Config({self.config})"


# Global configuration instance
config = Config()
