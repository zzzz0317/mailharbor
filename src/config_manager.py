import os
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

logger = logging.getLogger(__name__)


class ConfigManager:
    
    def __init__(self, config_dir: str = "/config"):
        self.config_dir = Path(config_dir)
        self.global_config_path = self.config_dir / "global.yaml"
        self.accounts_dir = self.config_dir / "accounts"
        
        self.global_config: Dict[str, Any] = {}
        self.account_configs: Dict[str, Dict[str, Any]] = {}
        
    def load_all(self) -> None:
        logger.info("Loading configuration files...")
        self.global_config = self.load_global_config()
        self.account_configs = self.load_account_configs()
        self.validate_all()
        self.check_security_warnings()
        logger.info(f"Configuration loaded: global config and {len(self.account_configs)} account configs.")

    def load_global_config(self) -> Dict[str, Any]:
        if not self.global_config_path.exists():
            # raise FileNotFoundError(f"Global config file not found: {self.global_config_path}")
            logger.warning(f"Global config file not found: {self.global_config_path}， using empty config instead.")
            return {}
            
        logger.info(f"Loading global config: {self.global_config_path}")
        with open(self.global_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
        
    def load_account_configs(self) -> Dict[str, Dict[str, Any]]:
        accounts = {}
        if not self.accounts_dir.exists():
            logger.warning(f"Accounts directory not found: {self.accounts_dir}")
            return accounts
            
        for config_file in self.accounts_dir.glob("*.yaml"):
            account_name = config_file.stem
            try:
                logger.info(f"Loading account config: {config_file}")
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                accounts[account_name] = config
            except Exception as e:
                logger.error(f"Failed to load account config {config_file}: {e}")
        return accounts
        
    def _deep_merge(self, default: Dict, override: Dict) -> Dict:
        result = default.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
        
    def validate_all(self) -> None:
        for account_name, config in self.account_configs.items():
            try:
                self._validate_account_config(account_name, config)
            except ValueError as e:
                logger.error(f"Account '{account_name}' validation failed: {e}")
                raise
                
    def _validate_account_config(self, account_name: str, config: Dict[str, Any]) -> None:
        if 'account' not in config or 'source' not in config:
            raise ValueError(f"Account '{account_name}' is missing required sections.")
        account = config['account']
        source = config['source']
        if 'username' not in account or 'password' not in account:
            raise ValueError(f"Account '{account_name}' is missing credentials.")
        if 'protocol' not in source or source['protocol'] not in ['imap', 'pop3']:
            raise ValueError(f"Account '{account_name}' has an invalid protocol.")
        if 'host' not in source or 'port' not in source:
            raise ValueError(f"Account '{account_name}' is missing server details.")
            
    def check_security_warnings(self) -> None:
        ssl_cert = self.global_config.get('dovecot', {}).get('ssl_cert')
        ssl_key = self.global_config.get('dovecot', {}).get('ssl_key')
        if not ssl_cert or not ssl_key:
            logger.warning("SSL certificates not configured. IMAPS (993) will be disabled.")
        else:
            if not os.path.exists(ssl_cert):
                logger.error(f"SSL certificate file not found: {ssl_cert}")
            if not os.path.exists(ssl_key):
                logger.error(f"SSL key file not found: {ssl_key}")
        for account_name, config in self.account_configs.items():
            if config.get('account', {}).get('password_scheme', 'PLAIN') == 'PLAIN':
                logger.warning(f"Account '{account_name}' uses plain text passwords. Consider using bcrypt.")
                
    def get_enabled_accounts(self) -> List[Dict[str, Any]]:
        enabled = []
        for account_name, config in self.account_configs.items():
            if config.get('enabled', True):
                config['_account_name'] = account_name
                enabled.append(config)
        return enabled


class ConfigChangeHandler(FileSystemEventHandler):
    
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.debounce_timer = None
        
    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith('.yaml'):
            return
        logger.info(f"Config file changed: {event.src_path}")
        if self.debounce_timer:
            self.debounce_timer.cancel()
        self.debounce_timer = threading.Timer(1.0, self.callback)
        self.debounce_timer.start()


def watch_config_changes(config_dir: str, callback) -> Observer:
    event_handler = ConfigChangeHandler(callback)
    observer = Observer()
    observer.schedule(event_handler, config_dir, recursive=True)
    observer.start()
    logger.info(f"Watching config directory: {config_dir}")
    return observer
