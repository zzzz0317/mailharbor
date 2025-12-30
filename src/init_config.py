#!/usr/bin/env python3

import sys
import logging
from pathlib import Path

from .config_manager import ConfigManager
from .fetchmail_generator import FetchmailGenerator
from .dovecot_generator import DovecotGenerator
from .utils import setup_logger, ensure_directory


def init_configs(config_dir: str = "/config") -> int:
    logger = setup_logger(
        "init_config",
        log_file="/data/logs/init_config.log",
        level="INFO"
    )
    
    logger.info("=" * 60)
    logger.info("Starting MailHarbor configuration initialization")
    logger.info("=" * 60)
    
    try:
        logger.info("Ensuring required directories exist...")
        ensure_directory("/data/mail")
        ensure_directory("/data/fts")
        ensure_directory("/data/logs")
        ensure_directory("/etc/dovecot")
        ensure_directory("/etc/fetchmail")
        
        logger.info(f"Loading configurations from {config_dir}...")
        config_manager = ConfigManager(config_dir)
        config_manager.load_all()
        
        global_config = config_manager.global_config
        account_configs = config_manager.get_enabled_accounts()
        
        if not account_configs:
            logger.error("No enabled accounts found in configuration.")
            return 1
        
        logger.info(f"Loaded global config and {len(account_configs)} enabled account configs")
        
        fetchmail_generator = FetchmailGenerator()
        dovecot_generator = DovecotGenerator()
        
        logger.info("Generating Dovecot configuration...")
        dovecot_generator.generate_config(
            global_config,
            account_configs
        )
        logger.info("Dovecot configuration generated successfully")
        
        logger.info("Generating Fetchmail configuration...")
        fetchmail_generator.generate_config(
            global_config,
            account_configs
        )
        logger.info("Fetchmail configuration generated successfully")
            
        logger.info("=" * 60)
        logger.info("Configuration initialization completed successfully")
        logger.info("=" * 60)
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        logger.error("Ensure the config directory is mounted and global.yaml exists")
        return 1
        
    except Exception as e:
        logger.error(f"Configuration initialization failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(init_configs())
