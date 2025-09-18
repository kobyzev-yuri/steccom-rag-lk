"""
MediaWiki Integration Module
Интеграция с корпоративной MediaWiki для публикации базы знаний
"""

import requests
import json
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import hashlib


class MediaWikiClient:
    def __init__(self, wiki_url: str, username: str = None, password: str = None):
        """
        Инициализация клиента MediaWiki
        
        Args:
            wiki_url: URL MediaWiki (например, http://wiki.company.com/w/api.php)
            username: Имя пользователя для аутентификации
            password: Пароль для аутентификации
        """
        self.wiki_url = wiki_url.rstrip('/')
        if not self.wiki_url.endswith('/w/api.php'):
            self.wiki_url += '/w/api.php'
        
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.csrf_token = None
        
        if username and password:
            self._authenticate()
    
    def _authenticate(self) -> bool:
        """Аутентификация в MediaWiki"""
        try:
            # Получение токена для входа
            login_token_params = {
                'action': 'query',
                'meta': 'tokens',
                'type': 'login',
                'format': 'json'
            }
            
            response = self.session.get(self.wiki_url, params=login_token_params)
            login_token = response.json()['query']['tokens']['logintoken']
            
            # Вход в систему
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
                # Получение CSRF токена для редактирования
                csrf_params = {
                    'action': 'query',
                    'meta': 'tokens',
                    'type': 'csrf',
                    'format': 'json'
                }
                
                response = self.session.get(self.wiki_url, params=csrf_params)
                self.csrf_token = response.json()['query']['tokens']['csrftoken']
                return True
            else:
                print(f"Ошибка аутентификации: {result['login']['result']}")
                return False
                
        except Exception as e:
            print(f"Ошибка аутентификации MediaWiki: {e}")
            return False
    
    def _get_csrf_token(self) -> str:
        """Получение CSRF токена"""
        if not self.csrf_token:
            params = {
                'action': 'query',
                'meta': 'tokens',
                'type': 'csrf',
                'format': 'json'
            }
            response = self.session.get(self.wiki_url, params=params)
            self.csrf_token = response.json()['query']['tokens']['csrftoken']
        return self.csrf_token
    
    def page_exists(self, title: str) -> bool:
        """Проверка существования страницы"""
        params = {
            'action': 'query',
            'titles': title,
            'format': 'json'
        }
        
        response = self.session.get(self.wiki_url, params=params)
        result = response.json()
        
        pages = result['query']['pages']
        page_id = list(pages.keys())[0]
        return page_id != '-1'  # -1 означает, что страница не существует
    
    def get_page_content(self, title: str) -> Optional[str]:
        """Получение содержимого страницы"""
        params = {
            'action': 'query',
            'titles': title,
            'prop': 'revisions',
            'rvprop': 'content',
            'format': 'json'
        }
        
        response = self.session.get(self.wiki_url, params=params)
        result = response.json()
        
        pages = result['query']['pages']
        page_id = list(pages.keys())[0]
        
        if page_id == '-1':
            return None
        
        revisions = pages[page_id]['revisions']
        if revisions:
            return revisions[0]['*']
        return None
    
    def create_or_update_page(self, title: str, content: str, summary: str = None) -> Tuple[bool, str]:
        """
        Создание или обновление страницы
        
        Args:
            title: Заголовок страницы
            content: Содержимое страницы (в формате MediaWiki)
            summary: Описание изменений
            
        Returns:
            Tuple[bool, str]: (успех, сообщение)
        """
        try:
            csrf_token = self._get_csrf_token()
            
            # Проверяем, существует ли страница
            exists = self.page_exists(title)
            
            if exists:
                # Получаем текущее содержимое для проверки изменений
                current_content = self.get_page_content(title)
                if current_content == content:
                    return True, "Страница не изменилась"
            
            # Создаем или обновляем страницу
            edit_params = {
                'action': 'edit',
                'title': title,
                'text': content,
                'token': csrf_token,
                'format': 'json'
            }
            
            if summary:
                edit_params['summary'] = summary
            
            response = self.session.post(self.wiki_url, data=edit_params)
            result = response.json()
            
            if 'edit' in result and result['edit']['result'] == 'Success':
                action = "обновлена" if exists else "создана"
                return True, f"Страница '{title}' {action}"
            else:
                error_msg = result.get('error', {}).get('info', 'Неизвестная ошибка')
                return False, f"Ошибка редактирования: {error_msg}"
                
        except Exception as e:
            return False, f"Ошибка при работе с MediaWiki: {e}"
    
    def delete_page(self, title: str, reason: str = None) -> Tuple[bool, str]:
        """Удаление страницы"""
        try:
            csrf_token = self._get_csrf_token()
            
            delete_params = {
                'action': 'delete',
                'title': title,
                'token': csrf_token,
                'format': 'json'
            }
            
            if reason:
                delete_params['reason'] = reason
            
            response = self.session.post(self.wiki_url, data=delete_params)
            result = response.json()
            
            if 'delete' in result:
                return True, f"Страница '{title}' удалена"
            else:
                error_msg = result.get('error', {}).get('info', 'Неизвестная ошибка')
                return False, f"Ошибка удаления: {error_msg}"
                
        except Exception as e:
            return False, f"Ошибка при удалении: {e}"
    
    def search_pages(self, query: str, namespace: int = 0, limit: int = 10) -> List[Dict]:
        """Поиск страниц"""
        params = {
            'action': 'query',
            'list': 'search',
            'srsearch': query,
            'srnamespace': namespace,
            'srlimit': limit,
            'format': 'json'
        }
        
        response = self.session.get(self.wiki_url, params=params)
        result = response.json()
        
        if 'query' in result and 'search' in result['query']:
            return result['query']['search']
        return []


class KBToWikiPublisher:
    """Публикация базы знаний в MediaWiki"""
    
    def __init__(self, mediawiki_client: MediaWikiClient):
        self.client = mediawiki_client
    
    def _convert_kb_to_wiki_format(self, kb_data: Dict) -> str:
        """Конвертация данных KB в формат MediaWiki"""
        title = kb_data.get('title', 'Без названия')
        content = kb_data.get('content', [])
        audience = kb_data.get('audience', [])
        scope = kb_data.get('scope', [])
        status = kb_data.get('status', '')
        source = kb_data.get('source', {})
        
        # Заголовок страницы
        wiki_content = f"= {title} =\n\n"
        
        # Метаданные
        if audience or scope or status:
            wiki_content += "== Метаданные ==\n"
            if audience:
                wiki_content += f"* '''Аудитория:''' {', '.join(audience)}\n"
            if scope:
                wiki_content += f"* '''Область:''' {', '.join(scope)}\n"
            if status:
                wiki_content += f"* '''Статус:''' {status}\n"
            wiki_content += "\n"
        
        # Источник
        if source:
            wiki_content += "== Источник ==\n"
            if source.get('file'):
                wiki_content += f"* '''Файл:''' {source['file']}\n"
            if source.get('pointer'):
                wiki_content += f"* '''Указатель:''' {source['pointer']}\n"
            wiki_content += "\n"
        
        # Содержимое
        if content:
            wiki_content += "== Содержимое ==\n\n"
            for item in content:
                if isinstance(item, dict):
                    item_title = item.get('title', '')
                    item_text = item.get('text', '')
                    
                    if item_title:
                        wiki_content += f"=== {item_title} ===\n\n"
                    
                    if item_text:
                        # Простая конвертация текста в MediaWiki формат
                        wiki_text = self._format_text_for_wiki(item_text)
                        wiki_content += f"{wiki_text}\n\n"
                    
                    # Подразделы
                    subsections = item.get('subsections', [])
                    for subsection in subsections:
                        if isinstance(subsection, dict):
                            sub_title = subsection.get('title', '')
                            sub_text = subsection.get('text', '')
                            
                            if sub_title:
                                wiki_content += f"==== {sub_title} ====\n\n"
                            
                            if sub_text:
                                wiki_text = self._format_text_for_wiki(sub_text)
                                wiki_content += f"{wiki_text}\n\n"
        
        # Подвал с информацией о публикации
        wiki_content += "----\n"
        wiki_content += f"''Опубликовано из системы СТЭККОМ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}''\n"
        
        return wiki_content
    
    def _format_text_for_wiki(self, text: str) -> str:
        """Форматирование текста для MediaWiki"""
        # Замена переносов строк
        text = text.replace('\n', '\n\n')
        
        # Выделение важных фраз
        text = re.sub(r'\*\*(.*?)\*\*', r"'''\1'''", text)  # Жирный текст
        text = re.sub(r'\*(.*?)\*', r"''\1''", text)        # Курсив
        
        # Ссылки на файлы
        text = re.sub(r'data/uploads/([^)]+)', r'[[File:\1]]', text)
        
        return text
    
    def publish_kb_item(self, kb_data: Dict, namespace_prefix: str = "СТЭККОМ") -> Tuple[bool, str]:
        """
        Публикация одного элемента KB в MediaWiki
        
        Args:
            kb_data: Данные KB (из JSON)
            namespace_prefix: Префикс для пространства имен
            
        Returns:
            Tuple[bool, str]: (успех, сообщение)
        """
        try:
            title = kb_data.get('title', 'Без названия')
            wiki_title = f"{namespace_prefix}:{title}"
            
            # Конвертируем в формат MediaWiki
            wiki_content = self._convert_kb_to_wiki_format(kb_data)
            
            # Создаем или обновляем страницу
            summary = f"Обновление из системы СТЭККОМ: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            success, message = self.client.create_or_update_page(wiki_title, wiki_content, summary)
            
            return success, message
            
        except Exception as e:
            return False, f"Ошибка публикации: {e}"
    
    def publish_kb_file(self, kb_file_path: str, namespace_prefix: str = "СТЭККОМ") -> List[Tuple[bool, str]]:
        """
        Публикация всего файла KB в MediaWiki
        
        Args:
            kb_file_path: Путь к JSON файлу KB
            namespace_prefix: Префикс для пространства имен
            
        Returns:
            List[Tuple[bool, str]]: Список результатов публикации
        """
        results = []
        
        try:
            with open(kb_file_path, 'r', encoding='utf-8') as f:
                kb_data = json.load(f)
            
            if isinstance(kb_data, list):
                for item in kb_data:
                    success, message = self.publish_kb_item(item, namespace_prefix)
                    results.append((success, message))
            elif isinstance(kb_data, dict):
                success, message = self.publish_kb_item(kb_data, namespace_prefix)
                results.append((success, message))
            
        except Exception as e:
            results.append((False, f"Ошибка чтения файла {kb_file_path}: {e}"))
        
        return results
    
    def publish_all_kb_files(self, kb_directory: str = "docs/kb", namespace_prefix: str = "СТЭККОМ") -> Dict[str, List[Tuple[bool, str]]]:
        """
        Публикация всех KB файлов в MediaWiki
        
        Args:
            kb_directory: Директория с KB файлами
            namespace_prefix: Префикс для пространства имен
            
        Returns:
            Dict[str, List[Tuple[bool, str]]]: Результаты по файлам
        """
        import glob
        
        results = {}
        kb_files = glob.glob(f"{kb_directory}/*.json")
        
        for kb_file in kb_files:
            file_results = self.publish_kb_file(kb_file, namespace_prefix)
            results[kb_file] = file_results
        
        return results
