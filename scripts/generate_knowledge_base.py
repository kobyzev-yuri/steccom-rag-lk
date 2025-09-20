#!/usr/bin/env python3
"""
Скрипт для формирования базы знаний из MediaWiki
Экспортирует страницы MediaWiki в структурированный формат для системы СТЭККОМ
"""

import argparse
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Добавляем корень проекта в путь
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.integrations.mediawiki_client import MediaWikiClient


class KnowledgeBaseGenerator:
    """Генератор базы знаний из MediaWiki"""
    
    def __init__(self, wiki_url: str, username: str = None, password: str = None):
        self.client = MediaWikiClient(wiki_url, username, password)
        self.knowledge_base = []
    
    def extract_page_content(self, page_title: str) -> Optional[Dict]:
        """Извлечение содержимого страницы в структурированном формате"""
        try:
            content = self.client.get_page_content(page_title)
            if not content:
                return None
            
            # Парсинг MediaWiki разметки
            parsed_content = self._parse_wiki_content(content, page_title)
            return parsed_content
            
        except Exception as e:
            print(f"Ошибка при извлечении страницы '{page_title}': {e}")
            return None
    
    def _parse_wiki_content(self, content: str, page_title: str) -> Dict:
        """Парсинг содержимого MediaWiki в структурированный формат"""
        
        # Определяем метаданные из заголовка
        audience = self._extract_audience(content)
        scope = self._extract_scope(content)
        status = self._extract_status(content)
        
        # Извлекаем секции
        sections = self._extract_sections(content)
        
        return {
            "title": page_title,
            "audience": audience,
            "scope": scope,
            "status": status,
            "content": sections,
            "source": {
                "type": "mediawiki",
                "url": f"http://localhost:8080/index.php/{page_title.replace(' ', '_')}",
                "last_updated": datetime.now().isoformat()
            }
        }
    
    def _extract_audience(self, content: str) -> List[str]:
        """Извлечение аудитории из метаданных"""
        audience = []
        if "'''Аудитория:'''" in content:
            # Простое извлечение аудитории
            lines = content.split('\n')
            for line in lines:
                if "'''Аудитория:'''" in line:
                    audience_text = line.split("'''Аудитория:'''")[1].strip()
                    audience = [a.strip() for a in audience_text.split(',')]
                    break
        return audience if audience else ["user", "admin"]
    
    def _extract_scope(self, content: str) -> List[str]:
        """Извлечение области применения"""
        scope = []
        if "'''Область:'''" in content:
            lines = content.split('\n')
            for line in lines:
                if "'''Область:'''" in line:
                    scope_text = line.split("'''Область:'''")[1].strip()
                    scope = [s.strip() for s in scope_text.split(',')]
                    break
        return scope if scope else ["general"]
    
    def _extract_status(self, content: str) -> str:
        """Извлечение статуса"""
        if "'''Статус:'''" in content:
            lines = content.split('\n')
            for line in lines:
                if "'''Статус:'''" in line:
                    return line.split("'''Статус:'''")[1].strip()
        return "reference"
    
    def _extract_sections(self, content: str) -> List[Dict]:
        """Извлечение секций из содержимого"""
        sections = []
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # Пропускаем метаданные
            if any(keyword in line for keyword in ["'''Аудитория:'''", "'''Область:'''", "'''Статус:'''", "== Источник ==", "----"]):
                continue
            
            # Заголовки секций
            if line.startswith('== ') and not line.startswith('=== '):
                if current_section:
                    sections.append(current_section)
                
                title = line.replace('== ', '').replace(' ==', '').strip()
                current_section = {
                    "title": title,
                    "text": "",
                    "subsections": []
                }
            
            # Подзаголовки
            elif line.startswith('=== ') and current_section:
                title = line.replace('=== ', '').replace(' ===', '').strip()
                current_section["subsections"].append({
                    "title": title,
                    "text": ""
                })
            
            # Содержимое
            elif current_section and line:
                if current_section["subsections"]:
                    # Добавляем к последнему подразделу
                    current_section["subsections"][-1]["text"] += line + "\n"
                else:
                    # Добавляем к основной секции
                    current_section["text"] += line + "\n"
        
        # Добавляем последнюю секцию
        if current_section:
            sections.append(current_section)
        
        return sections
    
    def generate_from_namespace(self, namespace: str = "СТЭККОМ") -> List[Dict]:
        """Генерация базы знаний из пространства имен"""
        try:
            # Получаем список страниц в пространстве имен
            pages = self.client.search_pages(f"{namespace}:", limit=100)
            
            knowledge_base = []
            for page in pages:
                page_title = page['title']
                print(f"Обрабатываем страницу: {page_title}")
                
                content = self.extract_page_content(page_title)
                if content:
                    knowledge_base.append(content)
            
            return knowledge_base
            
        except Exception as e:
            print(f"Ошибка при генерации базы знаний: {e}")
            return []
    
    def generate_from_page_list(self, page_titles: List[str]) -> List[Dict]:
        """Генерация базы знаний из списка страниц"""
        knowledge_base = []
        
        for page_title in page_titles:
            print(f"Обрабатываем страницу: {page_title}")
            content = self.extract_page_content(page_title)
            if content:
                knowledge_base.append(content)
        
        return knowledge_base
    
    def save_knowledge_base(self, knowledge_base: List[Dict], output_file: str):
        """Сохранение базы знаний в файл"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(knowledge_base, f, ensure_ascii=False, indent=2)
        
        print(f"База знаний сохранена в: {output_path}")
        print(f"Обработано страниц: {len(knowledge_base)}")


def main():
    parser = argparse.ArgumentParser(description="Генерация базы знаний из MediaWiki")
    parser.add_argument("--wiki-url", required=True, help="URL MediaWiki API")
    parser.add_argument("--username", help="Имя пользователя MediaWiki")
    parser.add_argument("--password", help="Пароль MediaWiki")
    parser.add_argument("--namespace", default="СТЭККОМ", help="Пространство имен (по умолчанию: СТЭККОМ)")
    parser.add_argument("--pages", nargs="+", help="Список конкретных страниц для обработки")
    parser.add_argument("--output", default="docs/kb/mediawiki_knowledge_base.json", help="Выходной файл")
    parser.add_argument("--list-pages", action="store_true", help="Показать список страниц в пространстве имен")
    
    args = parser.parse_args()
    
    try:
        generator = KnowledgeBaseGenerator(args.wiki_url, args.username, args.password)
        
        if args.list_pages:
            # Показать список страниц
            pages = generator.client.search_pages(f"{args.namespace}:", limit=100)
            print(f"Страницы в пространстве имен '{args.namespace}':")
            for page in pages:
                print(f"  • {page['title']}")
            return
        
        if args.pages:
            # Обработать конкретные страницы
            knowledge_base = generator.generate_from_page_list(args.pages)
        else:
            # Обработать все страницы в пространстве имен
            knowledge_base = generator.generate_from_namespace(args.namespace)
        
        if knowledge_base:
            generator.save_knowledge_base(knowledge_base, args.output)
        else:
            print("База знаний пуста")
            
    except Exception as e:
        print(f"Ошибка: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
