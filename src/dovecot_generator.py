import os
import logging
from pathlib import Path
from typing import Dict, Any, List
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)


class DovecotGenerator:
    
    def __init__(self, template_dir: str = "/app/templates"):
        self.template_dir = Path(template_dir)
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))
        
    def generate_config(
        self,
        global_config: Dict[str, Any],
        account_configs: List[Dict[str, Any]],
        dovecot_conf_path: str = "/etc/dovecot/dovecot.conf",
        users_file_path: str = "/etc/dovecot/users"
    ) -> None:
        logger.info("Generating Dovecot configuration...")
        self._generate_main_config(global_config, dovecot_conf_path)
        self._generate_users_file(account_configs, users_file_path)
        self._create_mailbox_directories(account_configs)
        logger.info("Dovecot configuration generated.")
        
    def _generate_main_config(
        self,
        global_config: Dict[str, Any],
        output_path: str
    ) -> None:
        dovecot_config = global_config.get('dovecot', {})
        ssl_cert = dovecot_config.get('ssl_cert')
        ssl_key = dovecot_config.get('ssl_key')
        ssl_enabled = False
        
        if ssl_cert and ssl_key:
            if os.path.exists(ssl_cert) and os.path.exists(ssl_key):
                ssl_enabled = True
                logger.info(f"SSL enabled: {ssl_cert}")
            else:
                logger.warning("SSL certificate files not found. IMAPS disabled.")
        else:
            logger.warning("SSL certificates not configured. IMAPS disabled.")
            
        template_data = {
            'imap_port': dovecot_config.get('imap_port', 143),
            'imaps_port': dovecot_config.get('imaps_port', 993),
            'ssl_enabled': ssl_enabled,
            'ssl_cert': ssl_cert,
            'ssl_key': ssl_key,
            'performance': dovecot_config.get('performance', {}),
            'fts': dovecot_config.get('fts', {}),
            'mail_location': '/data/mail/%u',
        }
        
        template = self.env.get_template('dovecot.conf.j2')
        content = template.render(**template_data)
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info(f"Main config generated: {output_path}")
        
    def _generate_users_file(
        self,
        account_configs: List[Dict[str, Any]],
        output_path: str
    ) -> None:
        users_data = []
        
        for account in account_configs:
            account_name = account.get('_account_name', 'unknown')
            account_info = account.get('account', {})
            
            username = account_info.get('username')
            password = account_info.get('password')
            password_scheme = account_info.get('password_scheme', 'PLAIN')
            
            users_data.append({
                'username': username,
                'password': password,
                'password_scheme': password_scheme,
            })
            
        template = self.env.get_template('dovecot-users.j2')
        content = template.render(users=users_data)
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        os.chmod(output_file, 0o640)
        os.chown(output_file, 0, 102)
        
        logger.info(f"User file generated: {output_path} ({len(users_data)} users)")
        
    def _create_mailbox_directories(self, account_configs: List[Dict[str, Any]]) -> None:
        mail_base_dir = Path("/data/mail")
        mail_base_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            os.chown(mail_base_dir, 5000, 5000)
        except Exception as e:
            logger.warning(f"Failed to set owner for {mail_base_dir}: {e}")
        
        for account in account_configs:
            account_info = account.get('account', {})
            username = account_info.get('username')
            
            if not username:
                continue
                
            user_mail_dir = mail_base_dir / username
            user_mail_dir.mkdir(parents=True, exist_ok=True)
            
            for subdir in ['cur', 'new', 'tmp']:
                subdir_path = user_mail_dir / subdir
                subdir_path.mkdir(parents=True, exist_ok=True)
                try:
                    os.chown(subdir_path, 5000, 5000)
                except Exception as e:
                    logger.warning(f"Failed to set owner for {subdir_path}: {e}")
            
            try:
                os.chown(user_mail_dir, 5000, 5000)
            except Exception as e:
                logger.warning(f"Failed to set owner for {user_mail_dir}: {e}")
                
            logger.info(f"Mailbox directory created: {user_mail_dir}")
            
        fts_base_dir = Path("/data/fts")
        fts_base_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            os.chown(fts_base_dir, 5000, 5000)
        except Exception as e:
            logger.warning(f"Failed to set owner for {fts_base_dir}: {e}")
        
        for account in account_configs:
            account_info = account.get('account', {})
            username = account_info.get('username')
            
            if not username:
                continue
                
            user_fts_dir = fts_base_dir / username
            user_fts_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                os.chown(user_fts_dir, 5000, 5000)
            except Exception as e:
                logger.warning(f"Failed to set owner for {user_fts_dir}: {e}")
            
    def test_config(self, config_path: str = "/etc/dovecot/dovecot.conf") -> bool:
        import subprocess
        
        try:
            result = subprocess.run(
                ['doveconf', '-n', '-c', config_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.info("Dovecot configuration is valid.")
                return True
            else:
                logger.error(f"Configuration validation failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Configuration validation timed out.")
            return False
        except Exception as e:
            logger.error(f"Configuration validation error: {e}")
            return False
