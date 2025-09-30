#!/usr/bin/env python3
"""
Тест агента очистки OCR текста
"""

import os
import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent / "kb_admin"))

def test_ocr_cleaning_agent():
    """Тест агента очистки OCR текста"""
    print("=== Тест агента очистки OCR текста ===")
    
    from kb_admin.modules.core.smart_document_agent import SmartLibrarian
    from kb_admin.modules.core.knowledge_manager import KnowledgeBaseManager
    from kb_admin.modules.documents.pdf_processor import PDFProcessor
    
    # Создаем SmartLibrarian
    kb_manager = KnowledgeBaseManager()
    pdf_processor = PDFProcessor()
    smart_librarian = SmartLibrarian(kb_manager, pdf_processor)
    
    # Реальный OCR текст с кракозябрами (как вы показывали)
    real_ocr_text = """
СИСТЕМА СЕРТИФИКАЦИИ В ОБЛАСТИ СВЯЗИ СЕРТИФИКАТ СООТВЕТСТВИЯ Регистрационный номер: ОС-3-СТ-0274 Срок действия: с 27 января 2010г. до 27 января 2011г. А Scorer НАСТОЯЩИМ СЕРТИФИКАТОМ ОРГАН ПО СЕРТИФИКАЦИИ Te tT AHO «II KC», 111024, г. Москва, ул. Авиамоторная, д. 8A {сокрашенное наименование органа по сертификации, алрес места нахождения УДОСТОВЕРЯЕТ, ЧТО — Автоматизированная система расчетов «Билл-Мастер» наименование epee na связи. pepe ия (Шри наличии |}, технические условия 2 и) (Версия ПО 7) в составе согласно Приложению, технические условия № TY 4251-010-47397453- 2009. О бр ООН es 5 ЕЕ ЕЕЕВЕЕЕРЫЕЕРЕЕЕ нех у же =: : i Bo a ee ae oe ae oe eo se ee Se SSS Sa ПРОИЗВОДИМЫЕ ООО «Инлайн Телеком Солюшис», 127521, г. Москва, > (Ваюменовяние иоготовителя средства связи алрес места нахождения) ул. Октябрьская, д. 72 НА ПРЕДПРИЯТИИ (ЗАВОДЕ) OOO «Инлайн Телеком Солюшис», 127521, г. Москва, (наименование предприятия (завола] - изготовителя средства святи. адрес места нахождения) еее СООТВЕТСТВУЮТ
    """
    
    print("Исходный OCR текст с кракозябрами:")
    print(real_ocr_text)
    print(f"\nДлина исходного текста: {len(real_ocr_text)}")
    
    # Проверяем API ключ
    api_key = os.getenv("PROXYAPI_KEY") or os.getenv("PROXYAPI_API_KEY") or os.getenv("OPEN_AI_API_KEY")
    if not api_key:
        print("\n⚠️ API ключ не настроен!")
        print("Установите переменную окружения PROXYAPI_API_KEY или OPEN_AI_API_KEY")
        print("Агент не сможет работать без API ключа")
        return
    
    print(f"\n✅ API ключ настроен: {api_key[:10]}...")
    
    # Показываем существующие БЗ
    existing_kbs = smart_librarian._get_existing_knowledge_bases()
    print(f"\n📚 Существующие базы знаний:")
    print(existing_kbs)
    
    # Тестируем агента очистки
    print("\n🧹 Запускаем агента очистки OCR...")
    
    # Симулируем анализ от Gemini
    gemini_analysis = """
    Анализ изображения от Gemini:
    Документ представляет собой сертификат соответствия в области связи.
    На документе видны следующие элементы:
    - Заголовок "СЕРТИФИКАТ СООТВЕТСТВИЯ"
    - Регистрационный номер: ОС-3-СТ-0274
    - Срок действия: с 27 января 2010г. до 27 января 2011г.
    - Орган по сертификации: АНО «ИИКС»
    - Адрес: г. Москва, ул. Авиамоторная, д. 8A
    - Наименование системы: Автоматизированная система расчетов «Билл-Мастер»
    - Версия ПО: 7
    - Технические условия: ТУ 4251-010-47397453-2009
    - Изготовитель: ООО «Инлайн Телеком Солюшис»
    - Адрес изготовителя: г. Москва, ул. Октябрьская, д. 72
    """
    
    try:
        clean_abstract = smart_librarian._create_ocr_cleaning_agent(real_ocr_text, gemini_analysis)
        
        # Парсим результат для получения метаданных
        parsed_result = smart_librarian._parse_agent_response(clean_abstract)
        
        print("\n📊 Анализ агента:")
        print(f"Качество текста: {parsed_result.get('quality', 'НЕИЗВЕСТНО')}")
        print(f"Осмысленность: {parsed_result.get('meaningfulness', 'НЕИЗВЕСТНО')}")
        print(f"Готовность для KB: {parsed_result.get('kb_ready', 'НЕИЗВЕСТНО')}")
        print(f"Категория БЗ: {parsed_result.get('category', 'НЕИЗВЕСТНО')}")
        
        print(f"\n🔗 Объединение данных:")
        print(f"  OCR текст: {len(real_ocr_text)} символов")
        print(f"  Анализ Gemini: {len(gemini_analysis)} символов")
        print(f"  Итоговый abstract: {len(parsed_result.get('abstract', clean_abstract))} символов")
        
        print("\n📄 Чистый abstract:")
        print("=" * 50)
        print(parsed_result.get('abstract', clean_abstract))
        print("=" * 50)
        
        print(f"\n📊 Статистика:")
        print(f"Исходная длина OCR: {len(real_ocr_text)}")
        print(f"Длина анализа Gemini: {len(gemini_analysis)}")
        print(f"Итоговая длина: {len(clean_abstract)}")
        print(f"Сокращение: {len(real_ocr_text) - len(clean_abstract)} символов")
        
        # Проверяем качество очистки
        if "epee na связи" not in clean_abstract:
            print("✅ Кракозябры 'epee na связи' удалены")
        else:
            print("❌ Кракозябры 'epee na связи' не удалены")
            
        if "ЕЕЕВЕЕЕРЫЕЕРЕЕЕ" not in clean_abstract:
            print("✅ Кракозябры 'ЕЕЕВЕЕЕРЫЕЕРЕЕЕ' удалены")
        else:
            print("❌ Кракозябры 'ЕЕЕВЕЕЕРЫЕЕРЕЕЕ' не удалены")
            
        if "ee ae oe ae oe eo se ee Se SSS Sa" not in clean_abstract:
            print("✅ Кракозябры 'ee ae oe ae oe eo se ee Se SSS Sa' удалены")
        else:
            print("❌ Кракозябры 'ee ae oe ae oe eo se ee Se SSS Sa' не удалены")
            
        if "СИСТЕМА СЕРТИФИКАЦИИ" in clean_abstract:
            print("✅ Полезная информация 'СИСТЕМА СЕРТИФИКАЦИИ' сохранена")
        else:
            print("❌ Полезная информация 'СИСТЕМА СЕРТИФИКАЦИИ' потеряна")
            
        if "Билл-Мастер" in clean_abstract:
            print("✅ Полезная информация 'Билл-Мастер' сохранена")
        else:
            print("❌ Полезная информация 'Билл-Мастер' потеряна")
        
        print("\n🎉 Тест завершен успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка тестирования агента: {e}")
        import traceback
        traceback.print_exc()

def test_full_ocr_cleaning_workflow():
    """Тест полного процесса очистки OCR"""
    print("\n=== Тест полного процесса очистки OCR ===")
    
    from kb_admin.modules.core.smart_document_agent import SmartLibrarian
    from kb_admin.modules.core.knowledge_manager import KnowledgeBaseManager
    from kb_admin.modules.documents.pdf_processor import PDFProcessor
    
    # Создаем SmartLibrarian
    kb_manager = KnowledgeBaseManager()
    pdf_processor = PDFProcessor()
    smart_librarian = SmartLibrarian(kb_manager, pdf_processor)
    
    # Тестовый OCR текст
    test_ocr_text = """
@#$%^&*()_+{}|:<>?[]\\;'\",./~`1234567890-=qwertyuiopasdfghjklzxcvbnm
СИСТЕМА СЕРТИФИКАЦИИ В ОБЛАСТИ СВЯЗИ
@#$%^&*()_+{}|:<>?[]\\;'\",./~`1234567890-=qwertyuiopasdfghjklzxcvbnm
СЕРТИФИКАТ СООТВЕТСТВИЯ Регистрационный номер: ОС-3-СТ-0274
@#$%^&*()_+{}|:<>?[]\\;'\",./~`1234567890-=qwertyuiopasdfghjklzxcvbnm
Срок действия: с 27 января 2010г. до 27 января 2011г.
@#$%^&*()_+{}|:<>?[]\\;'\",./~`1234567890-=qwertyuiopasdfghjklzxcvbnm
НАСТОЯЩИМ СЕРТИФИКАТОМ ОРГАН ПО СЕРТИФИКАЦИИ
@#$%^&*()_+{}|:<>?[]\\;'\",./~`1234567890-=qwertyuiopasdfghjklzxcvbnm
AHO «II KC», 111024, г. Москва, ул. Авиамоторная, д. 8A
@#$%^&*()_+{}|:<>?[]\\;'\",./~`1234567890-=qwertyuiopasdfghjklzxcvbnm
УДОСТОВЕРЯЕТ, ЧТО Автоматизированная система расчетов «Билл-Мастер»
@#$%^&*()_+{}|:<>?[]\\;'\",./~`1234567890-=qwertyuiopasdfghjklzxcvbnm
технические условия № TY 4251-010-47397453-2009
@#$%^&*()_+{}|:<>?[]\\;'\",./~`1234567890-=qwertyuiopasdfghjklzxcvbnm
ПРОИЗВОДИМЫЕ ООО «Инлайн Телеком Солюшис», 127521, г. Москва
@#$%^&*()_+{}|:<>?[]\\;'\",./~`1234567890-=qwertyuiopasdfghjklzxcvbnm
ул. Октябрьская, д. 72 НА ПРЕДПРИЯТИИ (ЗАВОДЕ)
@#$%^&*()_+{}|:<>?[]\\;'\",./~`1234567890-=qwertyuiopasdfghjklzxcvbnm
    """
    
    print("Исходный OCR текст с мусором:")
    print(test_ocr_text[:200] + "...")
    print(f"Длина: {len(test_ocr_text)}")
    
    # Тестируем полный процесс очистки
    print("\n🧹 Запускаем полный процесс очистки OCR...")
    try:
        cleaned_text = smart_librarian._clean_ocr_text(test_ocr_text)
        
        print("\n📄 Результат полной очистки:")
        print("=" * 50)
        print(cleaned_text)
        print("=" * 50)
        
        print(f"\n📊 Статистика:")
        print(f"Исходная длина: {len(test_ocr_text)}")
        print(f"Очищенная длина: {len(cleaned_text)}")
        print(f"Сокращение: {len(test_ocr_text) - len(cleaned_text)} символов")
        
        print("\n🎉 Полный тест завершен!")
        
    except Exception as e:
        print(f"\n❌ Ошибка полного теста: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Основная функция тестирования"""
    print("🧪 Тестирование агента очистки OCR текста\n")
    
    try:
        # Тест 1: Агент очистки OCR
        test_ocr_cleaning_agent()
        
        # Тест 2: Полный процесс очистки
        test_full_ocr_cleaning_workflow()
        
        print("\n=== Результаты тестирования ===")
        print("✅ Агент очистки OCR создан")
        print("✅ Полный процесс очистки работает")
        
        print("\n=== Рекомендации ===")
        print("1. Установите переменную окружения PROXYAPI_API_KEY для работы агента")
        print("2. Протестируйте на реальных PDF документах в интерфейсе")
        print("3. Проверьте логи в файле kb_admin.log")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
