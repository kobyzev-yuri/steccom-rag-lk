#!/usr/bin/env python3
"""
Скрипт для загрузки базы знаний в MediaWiki
Загружает все KB файлы из docs/kb/ в MediaWiki
"""

import argparse
import json
import sys
import os
import glob
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Добавляем корень проекта в путь
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.integrations.mediawiki_client import MediaWikiClient, KBToWikiPublisher


class KBUploader:
    """Загрузчик базы знаний в MediaWiki"""
    
    def __init__(self, wiki_url: str, username: str, password: str):
        self.client = MediaWikiClient(wiki_url, username, password)
        self.publisher = KBToWikiPublisher(self.client)
        self.uploaded_pages = []
        self.failed_uploads = []
    
    def upload_kb_file(self, kb_file_path: str, namespace_prefix: str = "СТЭККОМ") -> bool:
        """Загрузка одного KB файла в MediaWiki"""
        try:
            print(f"Загружаем файл: {kb_file_path}")
            
            with open(kb_file_path, 'r', encoding='utf-8') as f:
                kb_data = json.load(f)
            
            if isinstance(kb_data, list):
                # Множественные элементы в файле
                for item in kb_data:
                    success, message = self.publisher.publish_kb_item(item, namespace_prefix)
                    if success:
                        self.uploaded_pages.append(item.get('title', 'Без названия'))
                        print(f"  ✅ {message}")
                    else:
                        self.failed_uploads.append(f"{item.get('title', 'Без названия')}: {message}")
                        print(f"  ❌ {message}")
            elif isinstance(kb_data, dict):
                # Один элемент в файле
                success, message = self.publisher.publish_kb_item(kb_data, namespace_prefix)
                if success:
                    self.uploaded_pages.append(kb_data.get('title', 'Без названия'))
                    print(f"  ✅ {message}")
                else:
                    self.failed_uploads.append(f"{kb_data.get('title', 'Без названия')}: {message}")
                    print(f"  ❌ {message}")
            
            return True
            
        except Exception as e:
            error_msg = f"Ошибка при загрузке {kb_file_path}: {e}"
            self.failed_uploads.append(error_msg)
            print(f"  ❌ {error_msg}")
            return False
    
    def upload_all_kb_files(self, kb_directory: str = "docs/kb", namespace_prefix: str = "СТЭККОМ") -> Dict:
        """Загрузка всех KB файлов в MediaWiki"""
        kb_files = glob.glob(f"{kb_directory}/*.json")
        
        if not kb_files:
            print(f"KB файлы не найдены в директории: {kb_directory}")
            return {"uploaded": 0, "failed": 0, "total": 0}
        
        print(f"Найдено KB файлов: {len(kb_files)}")
        print(f"Пространство имен: {namespace_prefix}")
        print("-" * 50)
        
        uploaded_count = 0
        failed_count = 0
        
        for kb_file in sorted(kb_files):
            if self.upload_kb_file(kb_file, namespace_prefix):
                uploaded_count += 1
            else:
                failed_count += 1
        
        return {
            "uploaded": uploaded_count,
            "failed": failed_count,
            "total": len(kb_files)
        }
    
    def create_index_page(self, namespace_prefix: str = "СТЭККОМ") -> bool:
        """Создание индексной страницы с навигацией по базе знаний"""
        try:
            index_content = f"""= База знаний СТЭККОМ =

== Обзор ==

Добро пожаловать в корпоративную базу знаний СТЭККОМ. Здесь собрана вся актуальная информация о системе спутниковой связи, процедурах, регламентах и руководствах.

== Разделы базы знаний ==

=== Пользовательский интерфейс ===
* [[{namespace_prefix}:Возможности интерфейса личного кабинета|Возможности интерфейса]]
* [[{namespace_prefix}:Руководство пользователя|Руководство пользователя]]
* [[{namespace_prefix}:Примеры использования|Примеры использования]]
* [[{namespace_prefix}:Техническая документация|Техническая документация]]
* [[{namespace_prefix}:Устранение неполадок|Устранение неполадок]]

=== Регламенты ===
* [[{namespace_prefix}:Регламент GPS-трекинга|Регламент GPS-трекинга]]
* [[{namespace_prefix}:Регламент мониторинга|Регламент мониторинга]]
* [[{namespace_prefix}:Регламент SBD (русский)|Регламент SBD (русский)]]
* [[{namespace_prefix}:Регламент SBD (английский)|Регламент SBD (английский)]]

== Быстрый доступ ==

=== Для пользователей ===
* [[{namespace_prefix}:Возможности интерфейса личного кабинета|Как пользоваться системой]]
* [[{namespace_prefix}:Устранение неполадок|Решение проблем]]

=== Для администраторов ===
* [[{namespace_prefix}:Техническая документация|Техническая документация]]
* [[{namespace_prefix}:Руководство пользователя|Руководство администратора]]

== Последние обновления ==

''Последнее обновление: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}''

----
''Автоматически сгенерировано системой СТЭККОМ''
"""
            
            index_title = f"{namespace_prefix}:База знаний"
            success, message = self.client.create_or_update_page(index_title, index_content, "Создание индексной страницы базы знаний")
            
            if success:
                print(f"✅ Создана индексная страница: {index_title}")
                return True
            else:
                print(f"❌ Ошибка создания индексной страницы: {message}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка при создании индексной страницы: {e}")
            return False
    
    def print_summary(self):
        """Вывод сводки по загрузке"""
        print("\n" + "=" * 50)
        print("СВОДКА ЗАГРУЗКИ")
        print("=" * 50)
        
        print(f"✅ Успешно загружено страниц: {len(self.uploaded_pages)}")
        if self.uploaded_pages:
            print("Загруженные страницы:")
            for page in self.uploaded_pages:
                print(f"  • {page}")
        
        print(f"\n❌ Ошибок загрузки: {len(self.failed_uploads)}")
        if self.failed_uploads:
            print("Ошибки:")
            for error in self.failed_uploads:
                print(f"  • {error}")


def main():
    parser = argparse.ArgumentParser(description="Загрузка базы знаний в MediaWiki")
    parser.add_argument("--wiki-url", required=True, help="URL MediaWiki API")
    parser.add_argument("--username", required=True, help="Имя пользователя MediaWiki")
    parser.add_argument("--password", required=True, help="Пароль MediaWiki")
    parser.add_argument("--namespace", default="СТЭККОМ", help="Пространство имен (по умолчанию: СТЭККОМ)")
    parser.add_argument("--kb-dir", default="docs/kb", help="Директория с KB файлами")
    parser.add_argument("--kb-file", help="Конкретный KB файл для загрузки")
    parser.add_argument("--create-index", action="store_true", help="Создать индексную страницу")
    parser.add_argument("--dry-run", action="store_true", help="Показать что будет загружено без фактической загрузки")
    
    args = parser.parse_args()
    
    try:
        uploader = KBUploader(args.wiki_url, args.username, args.password)
        
        if args.dry_run:
            # Показать что будет загружено
            kb_files = glob.glob(f"{args.kb_dir}/*.json")
            print(f"Найдено KB файлов для загрузки: {len(kb_files)}")
            for kb_file in sorted(kb_files):
                print(f"  • {kb_file}")
            return 0
        
        if args.kb_file:
            # Загрузить конкретный файл
            if not os.path.exists(args.kb_file):
                print(f"Файл не найден: {args.kb_file}")
                return 1
            
            uploader.upload_kb_file(args.kb_file, args.namespace)
        else:
            # Загрузить все файлы
            result = uploader.upload_all_kb_files(args.kb_dir, args.namespace)
            print(f"\nОбработано файлов: {result['total']}")
            print(f"Успешно: {result['uploaded']}")
            print(f"Ошибок: {result['failed']}")
        
        # Создать индексную страницу если запрошено
        if args.create_index:
            uploader.create_index_page(args.namespace)
        
        # Показать сводку
        uploader.print_summary()
        
    except Exception as e:
        print(f"Ошибка: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
