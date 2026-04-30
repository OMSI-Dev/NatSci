"""
Configuration Management for SOS Control System

This module provides centralized configuration management with support for:
- JSON configuration files
- Environment variables
- Default values
- Configuration validation
"""

import os
import json
from pathlib import Path
from typing import Optional, Any


class Config:
    """
    Centralized configuration manager for SOS Control System.
    
    Loads configuration from:
    1. settings.json (if present)
    2. Environment variables (override file settings)
    3. Default values (fallback)
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_file: Path to JSON configuration file (optional)
        """
        self._config = {}
        self._load_defaults()
        
        # Load from file if provided
        if config_file and os.path.exists(config_file):
            self._load_from_file(config_file)
        else:
            # Try to find settings.json in standard locations
            self._load_from_standard_locations()
        
        # Override with environment variables
        self._load_from_environment()
    
    def _load_defaults(self):
        """Load default configuration values."""
        self._config = {
            # Network - SOS Server
            'sos': {
                'ip': '10.0.0.16',
                'port': 2468,
                'user': 'sos'
            },
            
            # Network - Raspberry Pi (Now Playing)
            'pi': {
                'ip': '10.10.51.111',
                'port': 4096,
                'enabled': False  # Set to True when Pi is connected
            },
            
            # Network - Local Servers
            'servers': {
                'query_port': 4097,
                'http_port': 5000
            },
            
            # Paths - Network Shares (Windows UNC paths)
            'paths': {
                'base_share': r'\\10.0.0.16\AuxShare',
                'cache_dir': r'\\10.0.0.16\AuxShare\cache',
                'audio_dir': r'\\10.0.0.16\AuxShare\audio',
                'documents_dir': r'\\10.0.0.16\AuxShare\documents',
                'data_dir': r'\\10.0.0.16\AuxShare\data',
                'assets_dir': r'\\10.0.0.16\AuxShare\assets'
            },
            
            'files': {
                'playlist_cache': 'playlist_cache.JSON',
                'metadata_cache': 'clip_metadata_cache.JSON',
                'audio_config': 'audio-config.JSON',
                'audio_list': 'audio-list.csv',
                'dataset_csv': 'SOS_datasets.csv',
                'presentation': 'noaa_presentation.odp'
            },
            
            # Audio
            'audio': {
                'remote_path': '/AuxShare/audio/mp3',
                'socket_path': '/tmp/mpv-audio-socket',
                'default_volume': 100,
                'fade_duration': 2.0
            },
            
            # LibreOffice
            'presentation': {
                'auto_start': True,
                'libreoffice_paths': [
                    r'C:\Program Files\LibreOffice\program\soffice.exe',
                    r'C:\Program Files (x86)\LibreOffice\program\soffice.exe'
                ]
            },
            
            # Overlay Display
            'overlay': {
                'progress_bar': {
                    'height': 12,
                    'margin_left': 210,
                    'margin_right': 210,
                    'y_offset': 87,
                    'color': '#ffffff'
                },
                'subtitles': {
                    'font_size': 28,
                    'y_offset': 80,
                    'opacity': 0.85
                }
            },
            
            # Features
            'features': {
                'nowplaying_enabled': False,
                'audio_enabled': True,
                'subtitles_enabled': True,
                'http_server_enabled': True
            },
            
            # Development
            'debug': {
                'show_borders': False,
                'verbose_ssh': False,
                'verbose_mpv': False
            }
        }
    
    def _load_from_file(self, config_file: str):
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                self._merge_config(file_config)
            print(f"[Config] Loaded configuration from: {config_file}")
        except Exception as e:
            print(f"[Config] Error loading config file: {e}")
    
    def _load_from_standard_locations(self):
        """Try to load settings.json from standard locations."""
        search_paths = [
            Path.cwd() / 'settings.json',
            Path.cwd() / 'config' / 'settings.json',
            Path(__file__).parent / 'settings.json',
            Path.home() / '.sos' / 'settings.json'
        ]
        
        for path in search_paths:
            if path.exists():
                self._load_from_file(str(path))
                break
    
    def _load_from_environment(self):
        """Load configuration overrides from environment variables."""
        # SOS Server
        if os.getenv('SOS_IP'):
            self._config['sos']['ip'] = os.getenv('SOS_IP')
        if os.getenv('SOS_PORT'):
            self._config['sos']['port'] = int(os.getenv('SOS_PORT'))
        
        # Raspberry Pi
        if os.getenv('PI_IP'):
            self._config['pi']['ip'] = os.getenv('PI_IP')
        if os.getenv('PI_PORT'):
            self._config['pi']['port'] = int(os.getenv('PI_PORT'))
        if os.getenv('PI_ENABLED'):
            self._config['pi']['enabled'] = os.getenv('PI_ENABLED').lower() == 'true'
        
        # Base share path
        if os.getenv('SOS_BASE_SHARE'):
            base = os.getenv('SOS_BASE_SHARE')
            self._config['paths']['base_share'] = base
            # Update derived paths
            self._config['paths']['cache_dir'] = os.path.join(base, 'cache')
            self._config['paths']['audio_dir'] = os.path.join(base, 'audio')
            self._config['paths']['documents_dir'] = os.path.join(base, 'documents')
            self._config['paths']['data_dir'] = os.path.join(base, 'data')
            self._config['paths']['assets_dir'] = os.path.join(base, 'assets')
    
    def _merge_config(self, new_config: dict):
        """Recursively merge new configuration into existing config."""
        def merge(d1, d2):
            for key, value in d2.items():
                if key in d1 and isinstance(d1[key], dict) and isinstance(value, dict):
                    merge(d1[key], value)
                else:
                    d1[key] = value
        merge(self._config, new_config)
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path (e.g., 'sos.ip' or 'paths.cache_dir')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
            
        Examples:
            >>> config.get('sos.ip')
            '10.0.0.16'
            >>> config.get('paths.cache_dir')
            '\\\\10.0.0.16\\AuxShare\\cache'
        """
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """
        Set configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path
            value: Value to set
        """
        keys = key_path.split('.')
        config = self._config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def get_full_path(self, file_key: str) -> str:
        """
        Get full path for a file by combining appropriate directory with filename.
        
        Args:
            file_key: Key from 'files' section
            
        Returns:
            Full path to file
            
        Examples:
            >>> config.get_full_path('playlist_cache')
            '\\\\10.0.0.16\\AuxShare\\cache\\playlist_cache.JSON'
        """
        filename = self._config['files'].get(file_key)
        if not filename:
            return None
        
        # Determine appropriate directory based on file type
        if file_key.endswith('_cache'):
            base_dir = self._config['paths']['cache_dir']
        elif file_key.startswith('audio'):
            base_dir = self._config['paths']['audio_dir']
        elif file_key == 'dataset_csv':
            base_dir = self._config['paths']['data_dir']
        elif file_key == 'presentation':
            base_dir = self._config['paths']['documents_dir']
        else:
            base_dir = self._config['paths']['base_share']
        
        return os.path.join(base_dir, filename)
    
    def validate(self) -> list[str]:
        """
        Validate configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required network settings
        if not self._config['sos']['ip']:
            errors.append("SOS IP address not configured")
        
        # Check if base share is accessible
        base_share = self._config['paths']['base_share']
        if not os.path.exists(base_share):
            errors.append(f"Base share not accessible: {base_share}")
        
        # Check if critical files exist
        critical_files = ['dataset_csv', 'presentation']
        for file_key in critical_files:
            path = self.get_full_path(file_key)
            if path and not os.path.exists(path):
                errors.append(f"Critical file not found: {path}")
        
        return errors
    
    def save(self, filepath: str):
        """Save current configuration to file."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4)
            print(f"[Config] Configuration saved to: {filepath}")
        except Exception as e:
            print(f"[Config] Error saving config: {e}")
    
    def print_summary(self):
        """Print configuration summary."""
        print("\n" + "="*60)
        print("SOS Control System Configuration")
        print("="*60)
        print(f"SOS Server:      {self._config['sos']['ip']}:{self._config['sos']['port']}")
        print(f"Now Playing:     {self._config['pi']['ip']}:{self._config['pi']['port']} "
              f"({'Enabled' if self._config['pi']['enabled'] else 'Disabled'})")
        print(f"Base Share:      {self._config['paths']['base_share']}")
        print(f"HTTP Server:     Port {self._config['servers']['http_port']}")
        print(f"Features:")
        for feature, enabled in self._config['features'].items():
            status = '✓' if enabled else '✗'
            print(f"  {status} {feature}")
        print("="*60 + "\n")


# Global configuration instance
_config_instance: Optional[Config] = None


def get_config(config_file: Optional[str] = None) -> Config:
    """
    Get global configuration instance (singleton pattern).
    
    Args:
        config_file: Path to configuration file (only used on first call)
        
    Returns:
        Global Config instance
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = Config(config_file)
    
    return _config_instance
