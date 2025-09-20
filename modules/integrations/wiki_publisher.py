"""
Wiki Publisher module for MediaWiki integration
Handles publishing KB files to MediaWiki with update/delete capabilities
"""

import json
import os
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


class WikiPublisher:
    """Publisher for KB files to MediaWiki"""
    
    def __init__(self, wiki_url: str, username: str = None, password: str = None):
        """
        Initialize WikiPublisher
        
        Args:
            wiki_url: MediaWiki API URL (e.g., http://localhost:8080/w/api.php)
            username: MediaWiki username for authentication
            password: MediaWiki password for authentication
        """
        self.wiki_url = wiki_url.rstrip('/')
        if not self.wiki_url.endswith('/api.php'):
            self.wiki_url += '/api.php'
        
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.csrf_token = None
        
        if username and password:
            self._authenticate()
    
    def _authenticate(self) -> bool:
        """Authenticate with MediaWiki"""
        try:
            # Get login token
            login_token_params = {
                'action': 'query',
                'meta': 'tokens',
                'type': 'login',
                'format': 'json'
            }
            response = self.session.get(self.wiki_url, params=login_token_params)
            result = response.json()
            login_token = result['query']['tokens']['logintoken']
            
            # Login
            login_params = {
                'action': 'login',
                'lgname': self.username,
                'lgpassword': self.password,
                'lgtoken': login_token,
                'format': 'json'
            }
            response = self.session.post(self.wiki_url, data=login_params)
            result = response.json()
            
            if result['login']['result'] == 'Success':
                logger.info(f"Successfully authenticated as {self.username}")
                return True
            else:
                logger.error(f"Authentication failed: {result['login']['result']}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def _get_csrf_token(self) -> Optional[str]:
        """Get CSRF token for editing"""
        try:
            params = {
                'action': 'query',
                'meta': 'tokens',
                'format': 'json'
            }
            response = self.session.get(self.wiki_url, params=params)
            result = response.json()
            return result['query']['tokens']['csrftoken']
        except Exception as e:
            logger.error(f"Failed to get CSRF token: {e}")
            return None
    
    def _kb_to_wiki_content(self, kb_data: List[Dict], kb_filename: str) -> str:
        """Convert KB JSON to MediaWiki markup"""
        content = f"<noinclude>{{{{KB_Document|{kb_filename}}}}}\n"
        content += f"''Последнее обновление: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}''\n</noinclude>\n\n"
        
        for item in kb_data:
            if isinstance(item, dict):
                title = item.get('title', 'Без названия')
                audience = item.get('audience', [])
                scope = item.get('scope', [])
                status = item.get('status', 'unknown')
                
                content += f"== {title} ==\n"
                
                # Metadata
                if audience or scope or status:
                    content += "'''Метаданные:'''\n"
                    if audience:
                        content += f"* Аудитория: {', '.join(audience)}\n"
                    if scope:
                        content += f"* Область: {', '.join(scope)}\n"
                    if status:
                        content += f"* Статус: {status}\n"
                    content += "\n"
                
                # Content sections
                if 'content' in item and isinstance(item['content'], list):
                    for section in item['content']:
                        if isinstance(section, dict):
                            section_title = section.get('title', '')
                            section_text = section.get('text', '')
                            
                            if section_title:
                                content += f"=== {section_title} ===\n"
                            if section_text:
                                content += f"{section_text}\n\n"
                
                content += "----\n\n"
        
        return content
    
    def publish_kb_to_wiki(self, kb_file_path: str, wiki_namespace: str = "KB") -> Tuple[bool, str]:
        """
        Publish KB file to MediaWiki
        
        Args:
            kb_file_path: Path to KB JSON file
            wiki_namespace: MediaWiki namespace (default: "KB")
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Load KB file
            with open(kb_file_path, 'r', encoding='utf-8') as f:
                kb_data = json.load(f)
            
            # Generate page title
            kb_filename = Path(kb_file_path).stem
            page_title = f"{wiki_namespace}:{kb_filename.replace('_', ' ').title()}"
            
            # Convert to wiki content
            wiki_content = self._kb_to_wiki_content(kb_data, kb_filename)
            
            # Get CSRF token
            csrf_token = self._get_csrf_token()
            if not csrf_token:
                return False, "Failed to get CSRF token"
            
            # Edit page
            edit_params = {
                'action': 'edit',
                'title': page_title,
                'text': wiki_content,
                'token': csrf_token,
                'format': 'json',
                'summary': f'Updated from KB file: {kb_filename}'
            }
            
            response = self.session.post(self.wiki_url, data=edit_params)
            result = response.json()
            
            if 'edit' in result and result['edit']['result'] == 'Success':
                logger.info(f"Successfully published {kb_filename} to {page_title}")
                return True, f"Successfully published to {page_title}"
            else:
                error_msg = result.get('error', {}).get('info', 'Unknown error')
                logger.error(f"Failed to publish {kb_filename}: {error_msg}")
                return False, f"Failed to publish: {error_msg}"
                
        except Exception as e:
            logger.error(f"Error publishing KB file {kb_file_path}: {e}")
            return False, f"Error: {str(e)}"
    
    def update_wiki_page(self, page_title: str, content: str, summary: str = "Updated") -> Tuple[bool, str]:
        """Update existing wiki page"""
        try:
            csrf_token = self._get_csrf_token()
            if not csrf_token:
                return False, "Failed to get CSRF token"
            
            edit_params = {
                'action': 'edit',
                'title': page_title,
                'text': content,
                'token': csrf_token,
                'format': 'json',
                'summary': summary
            }
            
            response = self.session.post(self.wiki_url, data=edit_params)
            result = response.json()
            
            if 'edit' in result and result['edit']['result'] == 'Success':
                return True, f"Successfully updated {page_title}"
            else:
                error_msg = result.get('error', {}).get('info', 'Unknown error')
                return False, f"Failed to update: {error_msg}"
                
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def delete_wiki_page(self, page_title: str, reason: str = "KB file deleted") -> Tuple[bool, str]:
        """Delete wiki page"""
        try:
            csrf_token = self._get_csrf_token()
            if not csrf_token:
                return False, "Failed to get CSRF token"
            
            delete_params = {
                'action': 'delete',
                'title': page_title,
                'token': csrf_token,
                'format': 'json',
                'reason': reason
            }
            
            response = self.session.post(self.wiki_url, data=delete_params)
            result = response.json()
            
            if 'delete' in result:
                return True, f"Successfully deleted {page_title}"
            else:
                error_msg = result.get('error', {}).get('info', 'Unknown error')
                return False, f"Failed to delete: {error_msg}"
                
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def list_published_pages(self, namespace: str = "KB") -> List[str]:
        """List pages in namespace"""
        try:
            params = {
                'action': 'query',
                'list': 'allpages',
                'apnamespace': self._get_namespace_id(namespace),
                'aplimit': 'max',
                'format': 'json'
            }
            
            response = self.session.get(self.wiki_url, params=params)
            result = response.json()
            
            pages = []
            if 'query' in result and 'allpages' in result['query']:
                pages = [page['title'] for page in result['query']['allpages']]
            
            return pages
            
        except Exception as e:
            logger.error(f"Error listing pages: {e}")
            return []
    
    def _get_namespace_id(self, namespace: str) -> int:
        """Get namespace ID (simplified - assumes custom namespace)"""
        # For custom namespaces, MediaWiki typically uses 100+
        # This is a simplified mapping
        namespace_map = {
            "KB": 100,
            "Main": 0,
            "User": 2,
            "Project": 4,
            "File": 6,
            "MediaWiki": 8,
            "Template": 10,
            "Help": 12,
            "Category": 14
        }
        return namespace_map.get(namespace, 100)
    
    def get_page_content(self, page_title: str) -> Optional[str]:
        """Get current content of a wiki page"""
        try:
            params = {
                'action': 'query',
                'prop': 'revisions',
                'titles': page_title,
                'rvprop': 'content',
                'format': 'json'
            }
            
            response = self.session.get(self.wiki_url, params=params)
            result = response.json()
            
            pages = result.get('query', {}).get('pages', {})
            for page_id, page_data in pages.items():
                if 'revisions' in page_data:
                    return page_data['revisions'][0]['*']
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting page content: {e}")
            return None
