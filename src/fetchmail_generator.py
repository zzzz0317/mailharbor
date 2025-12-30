import os
import logging
from pathlib import Path
from typing import Dict, Any, List
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)


class FetchmailGenerator:
    
    def __init__(self, template_dir: str = "/app/templates"):
        self.template_dir = Path(template_dir)
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))
        
    def generate_config(
        self, 
        global_config: Dict[str, Any],
        account_configs: List[Dict[str, Any]],
        output_path: str = "/etc/fetchmailrc"
    ) -> None:
        logger.info("Generating Fetchmail configuration...")
        
        enabled_accounts = [
            acc for acc in account_configs 
            if acc.get('enabled', True)
        ]
        
        if not enabled_accounts:
            logger.warning("No enabled accounts. Skipping configuration generation.")
            return
            
        template_data = self._prepare_template_data(global_config, enabled_accounts)
        
        template = self.env.get_template('fetchmailrc.j2')
        content = template.render(**template_data)
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        os.chmod(output_file, 0o600)
        
        logger.info(f"Fetchmail configuration generated: {output_path} ({len(enabled_accounts)} accounts)")
        
    def _prepare_template_data(
        self, 
        global_config: Dict[str, Any],
        account_configs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        fetchmail_config = global_config.get('fetchmail', {})
        accounts_data = []
        
        for account in account_configs:
            account_name = account.get('_account_name', 'unknown')
            account_info = account.get('account', {})
            source_info = account.get('source', {})
            fetch_info = account.get('fetch', {})
            
            account_data = {
                'name': account_name,
                'username': account_info.get('username'),
                'source': {
                    'protocol': source_info.get('protocol', 'pop3'),
                    'host': source_info.get('host'),
                    'port': source_info.get('port'),
                    'ssl': source_info.get('ssl', True),
                    'username': source_info.get('username'),
                    'password': source_info.get('password'),
                    'keep_mail': fetch_info.get('keep_mail', fetchmail_config.get('keep_mail', True)),
                    'batch_limit': fetch_info.get('batch_limit', 100),
                    'folders': fetch_info.get('folders', ['INBOX']),
                },
            }
            
            accounts_data.append(account_data)
            
        return {
            'poll_interval': fetchmail_config.get('poll_interval', 300),
            'syslog': fetchmail_config.get('syslog', False),
            'accounts': accounts_data,
        }