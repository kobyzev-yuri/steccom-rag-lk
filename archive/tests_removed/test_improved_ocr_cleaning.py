#!/usr/bin/env python3
"""
Тест улучшенной очистки OCR текста
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'kb_admin'))

from kb_admin.modules.core.smart_document_agent import SmartLibrarian
from kb_admin.modules.knowledge_base.kb_manager import KnowledgeBaseManager

def test_improved_ocr_cleaning():
    """Тест улучшенной очистки OCR"""
    
    print("🧪 Тестирование улучшенной очистки OCR текста")
    print("=" * 60)
    
    # Инициализируем SmartLibrarian
    kb_manager = KnowledgeBaseManager()
    smart_librarian = SmartLibrarian(kb_manager)
    
    # Тестовый текст с кракозябрами (тот же, что показал пользователь)
    test_ocr_text = """СИСТЕМА СЕРТИФИКАЦИИ ОБЛАСТИ СВЯЗИ СЕРТИФИКАТ СООТВЕТСТВИЯ Регистрационный номер: ОС-3-СТ-0274 Срок действия: с 27 января 2010г. до 27 января 2011г. А Scorer НАСТОЯЩИМ СЕРТИФИКАТОМ ОРГАН СЕРТИФИКАЦИИ Te tT AHO «II KC», 111024, г. Москва, ул. Авиамоторная, д. 8A {сокрашенное наименование органа по сертификации, алрес места нахождения УДОСТОВЕРЯЕТ, ЧТО — система расчетов «Билл-Мастер» наименование epee na связи. pepe ия (Шри наличии технические условия 2 и) (Версия ПО 7) в составе согласно Приложению, технические условия № TY 4251-010-47397453- 2009. нех у же =: : SSS Sa ПРОИЗВОДИМЫЕ ООО «Инлайн Телеком Солюшис», 127521, г. Москва, > (Ваюменовяние иоготовителя средства связи алрес места нахождения) ул. Октябрьская, д. 72 ПРЕДПРИЯТИИ (ЗАВОДЕ) OOO «Инлайн Телеком Солюшис», 127521, г. Москва, (наименование предприятия ( средства святи. адрес места нахождения) СООТВЕТСТВУЮТ УСТАНОВЛЕННЫМ ТРЕБОВАНИЯМ «Правила применения систем расчетов» (утв. Приказом Мининформсвязи России от 02.07.2007 г. №7..."""
    
    print(f"Исходный текст ({len(test_ocr_text)} символов):")
    print("-" * 40)
    print(test_ocr_text[:200] + "..." if len(test_ocr_text) > 200 else test_ocr_text)
    print("-" * 40)
    
    # Проверяем наличие кракозябр
    krakozyabry = [
        "epee na связи. pepe ия",
        "О бр ООН es 5 ЕЕ ЕЕЕВЕЕЕРЫЕЕРЕЕЕ", 
        "ee ae oe ae oe eo se ee Se SSS Sa",
        "Ваюменовяние иоготовителя",
        "завола] - изготовителя",
        "еее СООТВЕТСТВУЮТ",
        "нех у же =: :",
        "SSS Sa"
    ]
    
    print("\n🔍 Проверяем наличие кракозябр в исходном тексте:")
    found_krakozyabry = []
    for krakozyabry_text in krakozyabry:
        if krakozyabry_text in test_ocr_text:
            found_krakozyabry.append(krakozyabry_text)
            print(f"  ❌ Найдено: '{krakozyabry_text}'")
        else:
            print(f"  ✅ Не найдено: '{krakozyabry_text}'")
    
    print(f"\n📊 Найдено кракозябр: {len(found_krakozyabry)} из {len(krakozyabry)}")
    
    # Тестируем очистку
    print("\n🧹 Запускаем улучшенную очистку OCR...")
    try:
        cleaned_text = smart_librarian._clean_ocr_text(test_ocr_text)
        
        print(f"\n📄 Результат очистки ({len(cleaned_text)} символов):")
        print("=" * 50)
        print(cleaned_text)
        print("=" * 50)
        
        # Проверяем, удалились ли кракозябры
        print("\n🔍 Проверяем результат очистки:")
        removed_krakozyabry = []
        remaining_krakozyabry = []
        
        for krakozyabry_text in found_krakozyabry:
            if krakozyabry_text in cleaned_text:
                remaining_krakozyabry.append(krakozyabry_text)
                print(f"  ❌ Осталось: '{krakozyabry_text}'")
            else:
                removed_krakozyabry.append(krakozyabry_text)
                print(f"  ✅ Удалено: '{krakozyabry_text}'")
        
        print(f"\n📊 Результаты очистки:")
        print(f"  Удалено кракозябр: {len(removed_krakozyabry)}")
        print(f"  Осталось кракозябр: {len(remaining_krakozyabry)}")
        print(f"  Эффективность: {len(removed_krakozyabry)/len(found_krakozyabry)*100:.1f}%")
        
        # Статистика
        print(f"\n📈 Статистика:")
        print(f"  Исходная длина: {len(test_ocr_text)}")
        print(f"  Очищенная длина: {len(cleaned_text)}")
        print(f"  Сокращение: {len(test_ocr_text) - len(cleaned_text)} символов")
        print(f"  Процент сокращения: {(len(test_ocr_text) - len(cleaned_text))/len(test_ocr_text)*100:.1f}%")
        
        # Проверяем качество очищенного текста
        print(f"\n📋 Анализ качества:")
        if "СЕРТИФИКАТ СООТВЕТСТВИЯ" in cleaned_text:
            print("  ✅ Основная информация сохранена")
        else:
            print("  ❌ Основная информация потеряна")
            
        if "ОС-3-СТ-0274" in cleaned_text:
            print("  ✅ Номер сертификата сохранен")
        else:
            print("  ❌ Номер сертификата потерян")
            
        if "Билл-Мастер" in cleaned_text:
            print("  ✅ Название системы сохранено")
        else:
            print("  ❌ Название системы потеряно")
        
        return len(remaining_krakozyabry) == 0
        
    except Exception as e:
        print(f"❌ Ошибка при очистке: {e}")
        return False

if __name__ == "__main__":
    success = test_improved_ocr_cleaning()
    
    print(f"\n{'='*60}")
    if success:
        print("🎉 ТЕСТ ПРОЙДЕН: Все кракозябры успешно удалены!")
    else:
        print("⚠️ ТЕСТ ЧАСТИЧНО ПРОЙДЕН: Некоторые кракозябры остались")
    print(f"{'='*60}")

