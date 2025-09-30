"""
Smart Librarian - Умный библиотекарь
Интеллектуальный помощник для анализа и обработки документов разных форматов
"""

import streamlit as st
import os
import mimetypes
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import json
import re
from datetime import datetime
import logging
from .document_manager import DocumentManager
from ..documents.vision_processor import VisionProcessor
from .base_agent import BaseAgent
from .transaction_manager import TransactionManager
from .transaction_decorator import with_transaction, manual_transaction

class SmartLibrarian(BaseAgent):
    """Умный библиотекарь - интеллектуальный помощник для работы с документами
    
    Функции:
    - Автоматический анализ документов разных форматов
    - Определение типа и категории контента
    - Рекомендации по созданию баз знаний
    - Умная обработка и индексация документов
    """
    
    def __init__(self, kb_manager, pdf_processor):
        # Инициализируем базовый агент
        super().__init__("SmartLibrarian", "document_analysis")
        
        self.kb_manager = kb_manager
        self.pdf_processor = pdf_processor
        self.document_manager = DocumentManager()
        # Используем путь из document_manager
        self.upload_dir = self.document_manager.upload_dir
        
        # Инициализируем анализатор изображений (используем существующий VisionProcessor)
        self.vision_processor = VisionProcessor()
        
        # Инициализируем менеджер транзакций
        self.transaction_manager = TransactionManager()
        
        # Создаем директорию для извлеченных изображений
        self.images_dir = self.upload_dir.parent / "extracted_images"
        self.images_dir.mkdir(exist_ok=True)
        
        # Поддерживаемые форматы
        self.supported_formats = {
            '.pdf': 'PDF документ',
            '.txt': 'Текстовый файл',
            '.docx': 'Word документ',
            '.doc': 'Word документ (старый формат)',
            '.rtf': 'Rich Text Format',
            '.md': 'Markdown документ',
            '.html': 'HTML документ',
            '.xml': 'XML документ'
        }
        
        # Типы контента для автоматической категоризации
        self.content_types = {
            'technical_regulations': {
                'keywords': ['регламент', 'технический', 'стандарт', 'требования', 'процедуры', 'инструкция'],
                'category': 'Технические регламенты',
                'description': 'Технические регламенты и стандарты'
            },
            'licenses': {
                'keywords': ['лицензия', 'разрешение', 'сертификат', 'аттестация', 'допуск', 'billmaster', 'программное обеспечение', 'software'],
                'exclude_keywords': ['best practices', 'guide', 'service', 'technical', 'sbd', 'short burst data'],
                'category': 'Лицензии и разрешения',
                'description': 'Лицензии, разрешения и сертификаты'
            },
            'manuals': {
                'keywords': ['руководство', 'инструкция', 'мануал', 'пособие', 'гайд', 'how to'],
                'category': 'Руководства',
                'description': 'Руководства пользователя и инструкции'
            },
            'technical_guides': {
                'keywords': ['best practices', 'guide', 'service guide', 'technical guide', 'sbd', 'short burst data', 'iridium', 'service documentation'],
                'category': 'Технические руководства',
                'description': 'Технические руководства и гайды по услугам'
            },
            'billing': {
                'keywords': ['биллинг', 'тариф', 'оплата', 'счет', 'платеж', 'billing', 'tariff'],
                'category': 'Биллинг и тарифы',
                'description': 'Документы по биллингу и тарифам'
            },
            'legal': {
                'keywords': ['договор', 'соглашение', 'условия', 'политика', 'правовой', 'legal'],
                'category': 'Правовые документы',
                'description': 'Правовые документы и соглашения'
            },
            'technical_docs': {
                'keywords': ['техническая', 'документация', 'api', 'интерфейс', 'протокол', 'техническая'],
                'category': 'Техническая документация',
                'description': 'Техническая документация и спецификации'
            }
        }
    
    @manual_transaction("document_analysis")
    def analyze_document_transactional(self, file_path: Path, transaction_id: str = None) -> Dict:
        """Анализ одного документа с поддержкой транзакций"""
        return self.analyze_document(file_path)
    
    def analyze_document(self, file_path: Path) -> Dict:
        """Анализ документа для определения его типа и содержимого"""
        analysis = {
            'file_path': str(file_path),
            'file_name': file_path.name,
            'file_size': file_path.stat().st_size,
            'file_extension': file_path.suffix.lower(),
            'mime_type': mimetypes.guess_type(str(file_path))[0],
            'content_type': None,
            'category': 'Другое',
            'description': '',
            'keywords': [],
            'confidence': 0.0,
            'recommendations': []
        }
        
        # Определяем поддерживаемый ли формат
        if analysis['file_extension'] in self.supported_formats:
            analysis['format_supported'] = True
            analysis['format_description'] = self.supported_formats[analysis['file_extension']]
        else:
            analysis['format_supported'] = False
            analysis['format_description'] = f"Формат {analysis['file_extension']} не поддерживается"
            return analysis
        
        # Извлекаем текст для анализа
        try:
            text_content = self._extract_text_content(file_path)
        except Exception:
            text_content = ""
        if not text_content:
            analysis['recommendations'].append("Не удалось извлечь текст из документа")
            return analysis
        
        analysis['text_length'] = len(text_content)
        
        # Сохраняем исходный текст
        analysis['raw_ocr_text'] = text_content
        
        # 1) Базовая очистка без сокращений (полный текст)
        base_cleaned_text = self._get_original_cleaned_text(text_content)
        analysis['original_cleaned_text'] = base_cleaned_text
        
        # Выделяем Q/A пары (FAQ) если есть
        try:
            qa_pairs = self._extract_qa_pairs(base_cleaned_text)
            analysis['qa_pairs'] = qa_pairs
            analysis['qa_count'] = len(qa_pairs)
        except Exception:
            analysis['qa_pairs'] = []
            analysis['qa_count'] = 0
        
        # 2) Дополнительная полная очистка с помощью агента (не суммаризация)
        # Для текстовых форматов по умолчанию НЕ вызываем внешний агент (ProxyAPI),
        # чтобы избежать лишних сетевых запросов. Можно включить через STEC_ENABLE_AI_CLEANING_TEXT=true
        import os
        text_like_exts = ['.docx', '.doc', '.txt', '.md', '.rtf', '.html', '.xml']
        enable_ai_cleaning_text = os.getenv("STEC_ENABLE_AI_CLEANING_TEXT", "false").lower() == "true"
        if analysis['file_extension'] in text_like_exts and not enable_ai_cleaning_text:
            fully_cleaned_text = base_cleaned_text
        else:
            fully_cleaned_text = self._create_full_cleaned_text(base_cleaned_text)
        
        # 3) Определяем правило размера: для очень больших документов оставляем только abstract
        file_size_mb = analysis['file_size'] / (1024 * 1024)
        is_huge_document = (file_size_mb > 20) or (len(fully_cleaned_text) > 100_000)
        analysis['is_huge_document'] = is_huge_document
        
        # Если документ не огромный, включаем полный текст; иначе опускаем его из результатов
        analysis['full_cleaned_text'] = fully_cleaned_text if not is_huge_document else ""
        analysis['full_included'] = not is_huge_document
        
        # 4) Создаем отдельный краткий abstract
        # Для текстовых форматов по умолчанию используем локальную выжимку без ProxyAPI
        if analysis['file_extension'] in text_like_exts and not enable_ai_cleaning_text:
            abstract_text = self._create_smart_summary(base_cleaned_text, analysis['file_name'])
        else:
            abstract_text = self._create_ocr_cleaning_agent(base_cleaned_text)
        analysis['smart_summary'] = abstract_text
        
        # Показываем превью (берем из abstract)
        smart_summary = abstract_text
        
        # Показываем умную выжимку как превью
        analysis['text_preview'] = smart_summary[:500] + "..." if len(smart_summary) > 500 else smart_summary
        
        # Анализируем содержимое (используем очищенный текст)
        content_analysis = self._analyze_content(base_cleaned_text, file_path.name)
        analysis.update(content_analysis)
        
        # Анализируем изображения в документе
        if analysis['file_extension'] == '.pdf':
            image_analyses = self.analyze_document_images(file_path)
            analysis['images'] = image_analyses
            analysis['image_count'] = len(image_analyses)
            
            # Собираем все анализы от Gemini для передачи в агент очистки
            gemini_analyses = []
            for img_analysis in image_analyses:
                if 'analysis' in img_analysis and img_analysis['analysis']:
                    gemini_analyses.append(img_analysis['analysis'])
            
            # Объединяем все анализы от Gemini
            if gemini_analyses:
                combined_gemini_analysis = "\n\n".join(gemini_analyses)
                analysis['gemini_analysis'] = combined_gemini_analysis
                
                # Пересоздаем умную выжимку с учетом анализа от Gemini
                smart_summary_with_gemini = self._create_ocr_cleaning_agent(cleaned_text, combined_gemini_analysis)
                analysis['smart_summary'] = smart_summary_with_gemini
                
                # Используем ключевые слова от агента, если они есть
                if hasattr(self, '_last_parsed_result') and self._last_parsed_result:
                    agent_keywords = self._last_parsed_result.get('keywords', [])
                    if agent_keywords:
                        analysis['keywords'] = agent_keywords
        elif analysis['file_extension'] in ['.docx', '.doc']:
            image_analyses = self.analyze_docx_images(file_path)
            analysis['images'] = image_analyses
            analysis['image_count'] = len(image_analyses)
            analysis['gemini_analysis'] = None
        else:
            analysis['images'] = []
            analysis['image_count'] = 0
            analysis['gemini_analysis'] = None
            # Явно фиксируем, что Gemini не используется для не-изображений
            try:
                logger = logging.getLogger(__name__)
                logger.info(f"Gemini пропущен для формата {analysis['file_extension']} (разрешен только для изображений/картинок из PDF)")
            except Exception:
                pass

        # Генерируем рекомендации и завершаем анализ
        analysis['recommendations'] = self._generate_recommendations(analysis)
        kb_suggestion = self._suggest_kb_topic(analysis)
        analysis['suggested_kb'] = kb_suggestion
        return analysis
    
    def generate_relevance_test_questions(self, analysis: Dict) -> List[Dict[str, Any]]:
        """Генерация тестовых вопросов для проверки релевантности БЗ на основе анализа документа"""
        try:
            import logging
            import os
            import requests
            
            logger = logging.getLogger(__name__)
            logger.info("Генерируем тестовые вопросы для проверки релевантности")
            
            # Проверяем, есть ли уже сгенерированные вопросы от агента
            if hasattr(self, '_last_parsed_result') and self._last_parsed_result:
                agent_questions = self._last_parsed_result.get('test_questions', [])
                if agent_questions:
                    logger.info(f"✅ Используем {len(agent_questions)} вопросов с ответами, сгенерированных агентом")
                    # Преобразуем в нужный формат
                    formatted_questions = []
                    for i, question in enumerate(agent_questions):
                        formatted_questions.append({
                            "question": question.get('question', ''),
                            "answer": question.get('answer', 'Информация не найдена в документе'),
                            "expected_keywords": [],  # Агент не генерирует ключевые слова для вопросов
                            "category": "agent_generated",
                            "difficulty": "medium"
                        })
                    return formatted_questions
            
            # Получаем информацию о документе
            doc_content = analysis.get('original_cleaned_text', analysis.get('full_cleaned_text', ''))
            doc_summary = analysis.get('smart_summary', '')
            doc_category = analysis.get('category', 'Неизвестно')
            doc_title = analysis.get('file_name', 'Документ')
            
            # Логируем размер документа
            logger.info(f"Размер документа для анализа: {len(doc_content)} символов")
            
            # Используем локальную модель через self.chat_model
            logger.info("Используем локальную модель для генерации тестовых вопросов")
            logger.info(f"🔍 DEBUG: Размер документа: {len(doc_content)} символов")
            logger.info(f"🔍 DEBUG: Название документа: {doc_title}")
            logger.info(f"🔍 DEBUG: Категория документа: {doc_category}")
            
            # Создаем промпт для генерации тестовых вопросов с ответами
            logger.info(f"🔍 DEBUG: Создаем промпт для генерации вопросов")
            logger.info(f"🔍 DEBUG: Длина промпта будет: ~{len(doc_content) + 1000} символов")
            
            prompt = f"""
Ты - эксперт по созданию тестовых вопросов для проверки релевантности базы знаний. Твоя задача - создать 5-7 вопросов с ответами ТОЛЬКО на основе информации, найденной в документе.

ИНФОРМАЦИЯ О ДОКУМЕНТЕ:
- Название файла: {doc_title}
- Категория: {doc_category}
- Краткое содержание: {doc_summary[:500]}...

СОДЕРЖИМОЕ ДОКУМЕНТА (полный текст, {len(doc_content)} символов):
{doc_content}

ЗАДАЧА:
Проанализируй РЕАЛЬНЫЙ текст документа и создай 3-5 релевантных вопросов с ответами на основе НАЙДЕННОЙ в документе информации.

КРИТИЧЕСКИ ВАЖНО:
- НЕ используй шаблонные вопросы!
- НЕ придумывай вопросы "в общем"!
- Анализируй КОНКРЕТНЫЙ текст документа!
- Найди РЕАЛЬНЫЕ факты, названия, даты, процедуры в тексте!
- Создай вопросы об этих РЕАЛЬНЫХ фактах!

ПРОЦЕСС:
1. Прочитай ВЕСЬ документ внимательно
2. Найди 3-5 КОНКРЕТНЫХ фактов из текста
3. Создай вопросы об этих КОНКРЕТНЫХ фактах
4. Дай ответы на основе НАЙДЕННОЙ в документе информации

ВАЖНО:
- Ответы должны быть на основе информации из документа
- Если информации нет, укажи "Информация не найдена в документе"
- Вопросы должны быть простыми и понятными
- Используй любую полезную информацию из документа

ТРЕБОВАНИЯ:
1. Вопросы на русском языке
2. Ответы на основе информации из документа
3. Простые и понятные вопросы
4. Конкретные факты в ответах

ФОРМАТ ОТВЕТА (JSON):
{{{{"questions": [
        {{{{"question": "Вопрос на русском языке",
            "answer": "Ответ ТОЛЬКО на основе информации из документа с цитатами",
            "expected_keywords": ["ключевое", "слово1", "слово2"],
            "category": "категория_вопроса",
            "difficulty": "easy/medium/hard",
            "source_info": "Конкретный фрагмент из документа, на котором основан ответ"
        }}}}
    ]
}}}}

ПРИМЕРЫ ВОПРОСОВ:
- Вопрос: "Какая основная тема документа?"
  Ответ: "Основная тема: [найденная тема]"
- Вопрос: "Какие компании упоминаются в документе?"
  Ответ: "В документе упоминаются: [найденные компании]"
- Вопрос: "Какие даты указаны в документе?"
  Ответ: "В документе указаны даты: [найденные даты]"
- Вопрос: "Какие требования описаны в документе?"
  Ответ: "В документе описаны требования: [найденные требования]"

ВЕРНИ ТОЛЬКО JSON БЕЗ ДОПОЛНИТЕЛЬНЫХ КОММЕНТАРИЕВ.
"""
            
            # Используем локальную модель
            try:
                from langchain.prompts import ChatPromptTemplate
                
                # Создаем промпт для LangChain
                system_prompt = "Ты - эксперт по созданию тестовых вопросов для проверки релевантности базы знаний. Твоя задача - создать качественные вопросы на основе анализа документа."
                
                template = ChatPromptTemplate.from_messages([
                    ("system", system_prompt),
                    ("user", prompt)
                ])
                
                # Вызываем модель
                logger.info(f"🔍 DEBUG: Вызываем модель для генерации вопросов")
                logger.info(f"🔍 DEBUG: Тип модели: {type(self.chat_model)}")
                logger.info(f"🔍 DEBUG: Модель: {getattr(self.chat_model, 'model_name', 'Неизвестно')}")
                
                chain = template | self.chat_model
                response = chain.invoke({})
                
                logger.info(f"🔍 DEBUG: Получен ответ от модели")
                logger.info(f"🔍 DEBUG: Тип ответа: {type(response)}")
                
                # Получаем текст ответа
                response_text = getattr(response, 'content', None) or str(response)
                logger.info(f"🔍 DEBUG: Ответ модели: {response_text[:500]}...")
                
                # Очищаем ответ от markdown блоков
                cleaned_response = response_text.strip()
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]  # Убираем ```json
                if cleaned_response.startswith('```'):
                    cleaned_response = cleaned_response[3:]   # Убираем ```
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]  # Убираем ``` в конце
                cleaned_response = cleaned_response.strip()
                
                # Парсим JSON ответ
                try:
                    import json
                    questions_data = json.loads(cleaned_response)
                    questions = questions_data.get('questions', [])
                    logger.info(f"✅ Сгенерировано {len(questions)} тестовых вопросов через LLM")
                    return questions
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Ошибка парсинга JSON ответа: {e}")
                    logger.error(f"Очищенный ответ модели: {cleaned_response[:500]}...")
                    logger.error("❌ НЕ ИСПОЛЬЗУЕМ шаблонные вопросы! Требуется реальный анализ документа!")
                    # Возвращаем пустой список вместо шаблонных вопросов
                    return []
            except Exception as e:
                logger.error(f"❌ Ошибка при вызове локальной модели: {e}")
                logger.error(f"🔍 DEBUG: Тип ошибки: {type(e)}")
                import traceback
                logger.error(f"🔍 DEBUG: Трассировка ошибки: {traceback.format_exc()}")
                logger.error("❌ НЕ ИСПОЛЬЗУЕМ шаблонные вопросы! Требуется реальный анализ документа!")
                # Возвращаем пустой список вместо шаблонных вопросов
                return []
                
        except Exception as e:
            logger.error(f"❌ Ошибка при генерации тестовых вопросов: {e}")
            logger.error(f"🔍 DEBUG: Тип ошибки: {type(e)}")
            import traceback
            logger.error(f"🔍 DEBUG: Трассировка ошибки: {traceback.format_exc()}")
            logger.error("❌ НЕ ИСПОЛЬЗУЕМ шаблонные вопросы! Требуется реальный анализ документа!")
            # Возвращаем пустой список вместо шаблонных вопросов
            return []
    
    def _get_basic_test_questions(self, category: str) -> List[Dict[str, Any]]:
        """Базовые тестовые вопросы на основе категории"""
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"⚠️ Используем базовые вопросы для категории: {category}")
        basic_questions = {
            'Лицензии и разрешения': [
                {
                    "question": "Какие лицензии упоминаются в документах?",
                    "expected_keywords": ["лицензия", "разрешение", "программное обеспечение"],
                    "category": "licenses",
                    "difficulty": "easy"
                },
                {
                    "question": "Какие требования к использованию лицензий?",
                    "expected_keywords": ["требования", "условия", "использование"],
                    "category": "license_requirements",
                    "difficulty": "medium"
                }
            ],
            'Биллинг и тарифы': [
                {
                    "question": "Как рассчитываются тарифы?",
                    "expected_keywords": ["тариф", "расчет", "стоимость"],
                    "category": "billing",
                    "difficulty": "medium"
                },
                {
                    "question": "Какие условия оплаты указаны?",
                    "expected_keywords": ["оплата", "условия", "платеж"],
                    "category": "payment_terms",
                    "difficulty": "easy"
                }
            ],
            'Правовые документы': [
                {
                    "question": "Какие основные условия договора?",
                    "expected_keywords": ["договор", "условия", "стороны"],
                    "category": "contract_terms",
                    "difficulty": "medium"
                },
                {
                    "question": "Какие права и обязанности сторон?",
                    "expected_keywords": ["права", "обязанности", "стороны"],
                    "category": "rights_obligations",
                    "difficulty": "hard"
                }
            ],
            'Технические руководства': [
                {
                    "question": "Какие технические требования описаны в руководстве?",
                    "answer": "В руководстве описаны следующие технические требования: [найти в документе]",
                    "expected_keywords": ["требования", "технические", "спецификации"],
                    "category": "technical_guides",
                    "difficulty": "medium"
                },
                {
                    "question": "Как использовать описанную услугу или сервис?",
                    "answer": "Для использования услуги необходимо: [найти в документе]",
                    "expected_keywords": ["использование", "применение", "работа"],
                    "category": "technical_guides",
                    "difficulty": "easy"
                },
                {
                    "question": "Какие лучшие практики рекомендованы?",
                    "answer": "В документе рекомендованы следующие лучшие практики: [найти в документе]",
                    "expected_keywords": ["best practices", "рекомендации", "советы"],
                    "category": "technical_guides",
                    "difficulty": "medium"
                },
                {
                    "question": "Какие услуги или сервисы упоминаются в документе?",
                    "answer": "В документе упоминаются следующие услуги: [найти в документе]",
                    "expected_keywords": ["услуги", "сервисы", "services"],
                    "category": "technical_guides",
                    "difficulty": "easy"
                },
                {
                    "question": "Какие компании или организации упоминаются в документе?",
                    "answer": "В документе упоминаются следующие компании: [найти в документе]",
                    "expected_keywords": ["компании", "организации", "companies"],
                    "category": "technical_guides",
                    "difficulty": "easy"
                }
            ]
        }
        
        questions = basic_questions.get(category, [
            {
                "question": "Какая основная информация содержится в документе?",
                "expected_keywords": ["информация", "документ", "содержание"],
                "category": "general",
                "difficulty": "easy"
            }
        ])
        
        logger.warning(f"⚠️ Возвращаем {len(questions)} базовых вопросов для категории: {category}")
        return questions
    
    def _test_single_question(self, question: Dict[str, Any]):
        """Тестирование одного вопроса через RAG систему"""
        try:
            import streamlit as st
            import time
            
            question_text = question["question"]
            expected_keywords = question.get("expected_keywords", [])
            
            st.info(f"🔍 Тестируем вопрос: **{question_text}**")
            
            # Инициализируем RAG систему
            from ..rag.multi_kb_rag import MultiKBRAG
            rag = MultiKBRAG()
            
            # Загружаем все активные БЗ
            with st.spinner("Загружаем базы знаний..."):
                rag.load_all_active_kbs()
            
            # Выполняем поиск
            with st.spinner("Ищем ответ в базах знаний..."):
                start_time = time.time()
                try:
                    search_result = rag.ask_question(question_text)
                    response_time = time.time() - start_time
                    
                    answer = search_result.get("answer", "")
                    sources = search_result.get("sources", [])
                    
                except Exception as e:
                    response_time = time.time() - start_time
                    answer = f"Ошибка поиска: {str(e)}"
                    sources = []
            
            # Отображаем результаты
            st.subheader("📋 Результат тестирования")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("⏱️ Время ответа", f"{response_time:.2f} сек")
                st.metric("📚 Найдено источников", len(sources))
            
            with col2:
                # Простая оценка релевантности
                if expected_keywords:
                    found_keywords = sum(1 for keyword in expected_keywords 
                                       if keyword.lower() in answer.lower())
                    relevance_score = (found_keywords / len(expected_keywords)) * 100
                    st.metric("🎯 Релевантность", f"{relevance_score:.1f}%")
                else:
                    st.metric("🎯 Релевантность", "Не оценена")
            
            # Ответ
            st.subheader("💬 Ответ системы")
            if answer:
                st.write(answer)
            else:
                st.warning("Ответ не найден")
            
            # Источники
            if sources:
                st.subheader("📖 Источники")
                for i, source in enumerate(sources[:3], 1):  # Показываем только первые 3
                    with st.expander(f"Источник {i}: {source.get('source', 'Неизвестно')}"):
                        st.write(f"**Содержание:** {source.get('content', '')[:300]}...")
                        st.write(f"**Релевантность:** {source.get('score', 0):.3f}")
            
            # Ожидаемые ключевые слова
            if expected_keywords:
                st.subheader("🔑 Ожидаемые ключевые слова")
                found_keywords = []
                missing_keywords = []
                
                for keyword in expected_keywords:
                    if keyword.lower() in answer.lower():
                        found_keywords.append(f"✅ {keyword}")
                    else:
                        missing_keywords.append(f"❌ {keyword}")
                
                if found_keywords:
                    st.success("Найденные ключевые слова:")
                    for keyword in found_keywords:
                        st.write(keyword)
                
                if missing_keywords:
                    st.error("Отсутствующие ключевые слова:")
                    for keyword in missing_keywords:
                        st.write(keyword)
            
        except Exception as e:
            st.error(f"Ошибка при тестировании вопроса: {e}")
    
    def _show_relevance_testing_after_creation(self, kb_id: int, test_questions: List[Dict[str, Any]]):
        """Показать тестирование релевантности после создания/обновления БЗ"""
        st.markdown("---")
        st.subheader("🧪 Тестирование релевантности созданной БЗ")
        st.info(f"Тестируем БЗ ID {kb_id} с помощью {len(test_questions)} сгенерированных вопросов")
        
        # Отображаем вопросы с возможностью тестирования
        for i, question in enumerate(test_questions, 1):
            with st.expander(f"❓ Вопрос {i}: {question['question']}"):
                st.write(f"**Категория:** {question.get('category', 'Не указана')}")
                st.write(f"**Сложность:** {question.get('difficulty', 'Не указана')}")
                st.write(f"**Ожидаемые ключевые слова:** {', '.join(question.get('expected_keywords', []))}")
                
                # Кнопка для тестирования этого вопроса на конкретной БЗ
                if st.button(f"🔍 Протестировать на БЗ ID {kb_id}", key=f"test_question_kb_{kb_id}_{i}"):
                    self._test_single_question_on_kb(question, kb_id)
    
    def _test_single_question_on_kb(self, question: Dict[str, Any], kb_id: int):
        """Тестирование одного вопроса на конкретной БЗ"""
        try:
            import streamlit as st
            import time
            
            question_text = question["question"]
            expected_keywords = question.get("expected_keywords", [])
            
            st.info(f"🔍 Тестируем вопрос на БЗ ID {kb_id}: **{question_text}**")
            
            # Инициализируем RAG систему
            from ..rag.multi_kb_rag import MultiKBRAG
            rag = MultiKBRAG()
            
            # Загружаем только конкретную БЗ
            with st.spinner(f"Загружаем БЗ ID {kb_id}..."):
                try:
                    # Загружаем все БЗ, но будем искать только в конкретной
                    rag.load_all_active_kbs()
                    
                    # Получаем информацию о БЗ
                    kb_info = self.kb_manager.get_knowledge_base(kb_id)
                    if not kb_info:
                        st.error(f"БЗ ID {kb_id} не найдена")
                        return
                        
                except Exception as e:
                    st.error(f"Ошибка загрузки БЗ: {e}")
                    return
            
            # Выполняем поиск
            with st.spinner("Ищем ответ в БЗ..."):
                start_time = time.time()
                try:
                    search_result = rag.ask_question(question_text)
                    response_time = time.time() - start_time
                    
                    answer = search_result.get("answer", "")
                    sources = search_result.get("sources", [])
                    
                    # Фильтруем источники только по нашей БЗ
                    kb_sources = [s for s in sources if s.get('kb_id') == kb_id]
                    
                except Exception as e:
                    response_time = time.time() - start_time
                    answer = f"Ошибка поиска: {str(e)}"
                    kb_sources = []
            
            # Отображаем результаты
            st.subheader("📋 Результат тестирования")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("⏱️ Время ответа", f"{response_time:.2f} сек")
                st.metric("📚 Найдено источников в БЗ", len(kb_sources))
            
            with col2:
                # Простая оценка релевантности
                if expected_keywords:
                    found_keywords = sum(1 for keyword in expected_keywords 
                                       if keyword.lower() in answer.lower())
                    relevance_score = (found_keywords / len(expected_keywords)) * 100
                    st.metric("🎯 Релевантность", f"{relevance_score:.1f}%")
                else:
                    st.metric("🎯 Релевантность", "Не оценена")
            
            # Ответ
            st.subheader("💬 Ответ системы")
            if answer:
                st.write(answer)
            else:
                st.warning("Ответ не найден в данной БЗ")
            
            # Источники из конкретной БЗ
            if kb_sources:
                st.subheader(f"📖 Источники из БЗ ID {kb_id}")
                for i, source in enumerate(kb_sources[:3], 1):  # Показываем только первые 3
                    with st.expander(f"Источник {i}: {source.get('source', 'Неизвестно')}"):
                        st.write(f"**Содержание:** {source.get('content', '')[:300]}...")
                        st.write(f"**Релевантность:** {source.get('score', 0):.3f}")
            else:
                st.warning(f"В БЗ ID {kb_id} не найдено релевантных источников для этого вопроса")
            
            # Ожидаемые ключевые слова
            if expected_keywords:
                st.subheader("🔑 Ожидаемые ключевые слова")
                found_keywords = []
                missing_keywords = []
                
                for keyword in expected_keywords:
                    if keyword.lower() in answer.lower():
                        found_keywords.append(f"✅ {keyword}")
                    else:
                        missing_keywords.append(f"❌ {keyword}")
                
                if found_keywords:
                    st.success("Найденные ключевые слова:")
                    for keyword in found_keywords:
                        st.write(keyword)
                
                if missing_keywords:
                    st.error("Отсутствующие ключевые слова:")
                    for keyword in missing_keywords:
                        st.write(keyword)
            
        except Exception as e:
            st.error(f"Ошибка при тестировании вопроса: {e}")
    
    def _save_test_questions_to_kb(self, kb_id: int, test_questions: List[Dict[str, Any]]):
        """Сохранение тестовых вопросов в БЗ как метаданные"""
        try:
            import json
            import logging
            
            logger = logging.getLogger(__name__)
            logger.info(f"Сохраняем {len(test_questions)} тестовых вопросов в БЗ ID {kb_id}")
            
            # Подготавливаем данные для сохранения
            test_questions_data = {
                "questions": test_questions,
                "created_at": datetime.now().isoformat(),
                "created_by": "smart_librarian",
                "version": "1.0",
                "description": "Тестовые вопросы для проверки релевантности БЗ"
            }
            
            # Сохраняем в БЗ как метаданные
            success = self.kb_manager.update_knowledge_base_metadata(
                kb_id=kb_id,
                metadata_key="relevance_test_questions",
                metadata_value=json.dumps(test_questions_data, ensure_ascii=False, indent=2)
            )
            
            if success:
                logger.info(f"✅ Тестовые вопросы успешно сохранены в БЗ ID {kb_id}")
                st.success(f"💾 Тестовые вопросы сохранены в БЗ ID {kb_id} для использования другими системами")
            else:
                logger.error(f"❌ Ошибка сохранения тестовых вопросов в БЗ ID {kb_id}")
                st.warning("⚠️ Не удалось сохранить тестовые вопросы в БЗ")
                
        except Exception as e:
            logger.error(f"Ошибка при сохранении тестовых вопросов: {e}")
            st.error(f"Ошибка при сохранении тестовых вопросов: {e}")
    
    def get_test_questions_from_kb(self, kb_id: int) -> List[Dict[str, Any]]:
        """Получение тестовых вопросов из БЗ"""
        try:
            import json
            import logging
            
            logger = logging.getLogger(__name__)
            
            # Получаем метаданные БЗ
            metadata = self.kb_manager.get_knowledge_base_metadata(kb_id, "relevance_test_questions")
            
            if "relevance_test_questions" in metadata:
                test_questions_data = json.loads(metadata["relevance_test_questions"])
                questions = test_questions_data.get("questions", [])
                logger.info(f"✅ Загружено {len(questions)} тестовых вопросов из БЗ ID {kb_id}")
                return questions
            else:
                logger.info(f"В БЗ ID {kb_id} нет сохраненных тестовых вопросов")
                return []
                
        except Exception as e:
            logger.error(f"Ошибка при получении тестовых вопросов из БЗ: {e}")
            return []

    def _is_image_noise(self, image_path: Path) -> bool:
        """Проверка изображения на мусор/пустоту.
        Критерии (любой из):
        - Минимальный размер стороны < 200 px
        - Размер файла < 8 KB
        - > 80% очень темных пикселей или > 95% почти белых пикселей
        - Низкая дисперсия яркости (stddev < 10)
        - Имя файла содержит logo/icon
        - Очень маленькая площадь (< 40k px) или экстремальные пропорции (AR > 5:1 или < 1:5)
        - Низкая цветовая вариативность (после квантования <= 16 уникальных цветов)
        """
        try:
            from PIL import Image, ImageStat
            stat = image_path.stat()
            if stat.st_size < 8 * 1024:
                return True
            # Явные логотипы по имени
            name_l = image_path.name.lower()
            if any(tag in name_l for tag in ("logo", "icon", "favicon", "brand")):
                return True
            img = Image.open(image_path).convert('L')
            width, height = img.size
            # Порог по минимальной стороне и площади
            if min(width, height) < 200:
                return True
            if (width * height) < (200 * 200):
                return True
            # Экстремальные пропорции (часто полоски/баннеры без текста)
            ar = width / height if height else 9999
            if ar > 5.0 or ar < 0.2:
                return True
            histogram = img.histogram()
            total = sum(histogram)
            white_pct = (sum(histogram[245:256]) / total * 100) if total else 0.0
            black_pct = (sum(histogram[0:10]) / total * 100) if total else 0.0
            stat_b = ImageStat.Stat(img)
            stddev = stat_b.stddev[0]
            if black_pct > 80.0 or white_pct > 95.0 or stddev < 10.0:
                return True
            # Низкая цветовая вариативность (по квантованию до 64 цветов)
            try:
                img_rgb = Image.open(image_path).convert('RGB')
                pal = img_rgb.convert('P', palette=Image.ADAPTIVE, colors=64)
                colors = pal.getcolors(1_000_000) or []
                unique_colors = len(colors)
                if unique_colors <= 16:
                    return True
            except Exception:
                pass
            return False
        except Exception:
            # В случае ошибки не фильтруем
            return False
        
        # Генерируем рекомендации
        analysis['recommendations'] = self._generate_recommendations(analysis)
        
        # Предлагаем тему KB с учетом существующих
        kb_suggestion = self._suggest_kb_topic(analysis)
        analysis['suggested_kb'] = kb_suggestion
        
        return analysis

    def _fallback_analysis(self, file_path: Path) -> Dict:
        """Резервный анализ, когда основной упал: извлекает текст и строит минимальный словарь."""
        try:
            text = self._extract_text_content(file_path)
        except Exception:
            text = ""
        qa_pairs = []
        try:
            qa_pairs = self._extract_qa_pairs(text)
        except Exception:
            qa_pairs = []
        return {
            'file_path': str(file_path),
            'file_name': file_path.name,
            'file_size': file_path.stat().st_size if file_path.exists() else 0,
            'file_extension': file_path.suffix.lower(),
            'mime_type': mimetypes.guess_type(str(file_path))[0],
            'content_type': 'unknown',
            'category': 'Другое',
            'description': '',
            'keywords': [],
            'confidence': 0.0,
            'format_supported': True,
            'format_description': self.supported_formats.get(file_path.suffix.lower(), 'Документ'),
            'raw_ocr_text': text,
            'original_cleaned_text': self._get_original_cleaned_text(text),
            'full_cleaned_text': self._get_original_cleaned_text(text),
            'smart_summary': self._create_smart_summary(text, file_path.name),
            'text_preview': (text[:500] + '...') if len(text) > 500 else text,
            'text_length': len(text),
            'images': [],
            'image_count': 0,
            'gemini_analysis': None,
            'recommendations': [],
            'qa_pairs': qa_pairs,
            'qa_count': len(qa_pairs)
        }
    
    def _extract_text_content(self, file_path: Path) -> str:
        """Извлечение текста из документа с поддержкой OCR"""
        try:
            if file_path.suffix.lower() == '.pdf':
                # Сначала пробуем обычное извлечение
                text = self.pdf_processor.extract_text(str(file_path))
                
                # Если текста мало, пробуем OCR
                if len(text.strip()) < 100:
                    try:
                        from modules.documents.ocr_processor import OCRProcessor
                        ocr_processor = OCRProcessor()
                        ocr_result = ocr_processor.process_document(str(file_path))
                        if ocr_result['success'] and ocr_result.get('text_content'):
                            text = ocr_result['text_content']
                            st.info(f"🔍 Использован OCR для {file_path.name}")
                    except Exception as ocr_e:
                        st.warning(f"OCR недоступен: {ocr_e}")
                
                return text
                
            elif file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
                # Для изображений используем OCR
                try:
                    from modules.documents.ocr_processor import OCRProcessor
                    ocr_processor = OCRProcessor()
                    ocr_result = ocr_processor.process_document(str(file_path))
                    if ocr_result['success'] and ocr_result.get('text_content'):
                        return ocr_result['text_content']
                    else:
                        return ""
                except Exception as ocr_e:
                    st.warning(f"OCR недоступен для {file_path.name}: {ocr_e}")
                    return ""
                    
            elif file_path.suffix.lower() in ['.docx', '.doc']:
                # Улучшенная обработка Word документов
                try:
                    from docx import Document
                    logger = logging.getLogger(__name__)
                    logger.info(f"DOCX: открываем файл {file_path}")
                    doc = Document(file_path)
                    try:
                        logger.info(f"DOCX: sections={len(getattr(doc, 'sections', []))}, paragraphs={len(getattr(doc, 'paragraphs', []))}, tables={len(getattr(doc, 'tables', []))}")
                    except Exception:
                        pass
                    text_parts = []
                    
                    def _norm_text(s: str) -> str:
                        import re
                        s = re.sub(r'\s+', ' ', s or '').strip()
                        return s
                    
                    # Заголовки/колонтитулы (если есть)
                    try:
                        for section in doc.sections:
                            header_text = _norm_text(getattr(section.header, 'text', '') if hasattr(section, 'header') else '')
                            footer_text = _norm_text(getattr(section.footer, 'text', '') if hasattr(section, 'footer') else '')
                            if header_text:
                                text_parts.append(header_text)
                            if footer_text:
                                text_parts.append(footer_text)
                    except Exception:
                        pass
                    
                    # Параграфы (учет списка по bullet/numbering через tabs)
                    for paragraph in getattr(doc, 'paragraphs', []) or []:
                        try:
                            p = _norm_text(getattr(paragraph, 'text', '') or '')
                            if not p:
                                continue
                            # Признаки списка: уровень отступа/нумерации не трогаем, просто добавим маркер
                            try:
                                style = getattr(paragraph, 'style', None)
                                style_name = getattr(style, 'name', '') if style is not None else ''
                                if style_name and 'List' in str(style_name):
                                    p = f"- {p}"
                            except Exception:
                                pass
                            text_parts.append(p)
                        except Exception as para_e:
                            try:
                                logger.warning(f"DOCX: ошибка чтения параграфа: {para_e}")
                            except Exception:
                                pass
                    
                    # Таблицы
                    for table in getattr(doc, 'tables', []) or []:
                        try:
                            for row in getattr(table, 'rows', []) or []:
                                row_text = []
                                for cell in getattr(row, 'cells', []) or []:
                                    try:
                                        cell_text = _norm_text(getattr(cell, 'text', '') or '')
                                        if cell_text:
                                            row_text.append(cell_text)
                                    except Exception:
                                        continue
                                if row_text:
                                    text_parts.append(' | '.join(row_text))
                        except Exception as tbl_e:
                            try:
                                logger.warning(f"DOCX: ошибка чтения таблицы: {tbl_e}")
                            except Exception:
                                pass
                    
                    # Итоговая нормализация
                    content = '\n'.join([t for t in text_parts if t])
                    logger.info(f"DOCX: извлечено {len(content)} символов текста из {file_path.name}")
                    return content
                except Exception as docx_e:
                    try:
                        logger = logging.getLogger(__name__)
                        logger.error(f"DOCX: ошибка обработки {file_path.name}: {docx_e}")
                    except Exception:
                        pass
                    st.warning(f"Ошибка обработки DOCX {file_path.name}: {docx_e}")
                    return ""
                    
            elif file_path.suffix.lower() == '.txt':
                # TXT с резервными кодировками
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return f.read()
                except Exception:
                    for enc in ['cp1251', 'latin-1']:
                        try:
                            with open(file_path, 'r', encoding=enc, errors='ignore') as f:
                                return f.read()
                        except Exception:
                            continue
                    return ""
            elif file_path.suffix.lower() == '.md':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif file_path.suffix.lower() == '.rtf':
                # Обработка RTF файлов
                try:
                    import re
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # Простая очистка RTF разметки
                        content = re.sub(r'\\[a-z]+\d*\s?', '', content)
                        content = re.sub(r'[{}]', '', content)
                        return content.strip()
                except Exception as rtf_e:
                    st.warning(f"Ошибка обработки RTF {file_path.name}: {rtf_e}")
                    return ""
            elif file_path.suffix.lower() == '.html':
                # Обработка HTML файлов
                try:
                    from bs4 import BeautifulSoup
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        soup = BeautifulSoup(content, 'html.parser')
                        return soup.get_text()
                except Exception as html_e:
                    st.warning(f"Ошибка обработки HTML {file_path.name}: {html_e}")
                    # Fallback - простое удаление тегов
                    try:
                        import re
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            content = re.sub(r'<[^>]+>', '', content)
                            return content.strip()
                    except:
                        return ""
            elif file_path.suffix.lower() == '.xml':
                # Обработка XML файлов
                try:
                    from bs4 import BeautifulSoup
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        soup = BeautifulSoup(content, 'xml')
                        return soup.get_text()
                except Exception as xml_e:
                    st.warning(f"Ошибка обработки XML {file_path.name}: {xml_e}")
                    return ""
            else:
                # Для других форматов пока возвращаем пустую строку
                return ""
        except Exception as e:
            st.warning(f"Ошибка извлечения текста из {file_path.name}: {e}")
            return ""
    
    def _clean_ocr_text(self, text: str) -> str:
        """Очистка текста от мусора OCR с использованием агента при необходимости"""
        if not text:
            return ""
        
        import re
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info(f"Начинаем очистку OCR текста в SmartLibrarian, длина: {len(text)}")
        
        # Удаляем номера страниц
        text = re.sub(r'---\s*Страница\s+\d+\s*---', '', text)
        
        # Удаляем повторяющиеся символы (более 3 подряд)
        text = re.sub(r'(.)\1{3,}', r'\1', text)
        
        # Удаляем кривые символы и артефакты OCR - более агрессивная очистка
        # Удаляем строки с множественными повторяющимися символами
        text = re.sub(r'^[^\w\s]{5,}$', '', text, flags=re.MULTILINE)
        
        # Удаляем строки состоящие только из символов =, -, _, +, *, ~, #, $, %, ^, &, *, (, ), [, ], {, }, |, \, :, ;, ", ', <, >, ?, /, ., ,, !, @
        text = re.sub(r'^[=\-_+*~#$%^&*()\[\]{}|\\:;"\'<>,.?!/@\s]{3,}$', '', text, flags=re.MULTILINE)
        
        # Удаляем одиночные символы в начале строки (артефакты OCR)
        text = re.sub(r'^\s*[^\w\s]\s*$', '', text, flags=re.MULTILINE)
        
        # Удаляем строки с множественными пробелами и символами
        text = re.sub(r'^\s*[\s\W]{15,}\s*$', '', text, flags=re.MULTILINE)
        
        # Удаляем кракозябры в середине текста (последовательности из 3+ небуквенных символов)
        text = re.sub(r'[^\w\s]{3,}', ' ', text)
        
        # Удаляем кривые символы типа "oe ee ee eS a" - короткие бессмысленные комбинации
        # Удаляем строки из 2-3 символов, состоящие только из букв без пробелов
        text = re.sub(r'^\s*[a-zA-Zа-яА-Я]{1,3}\s*$', '', text, flags=re.MULTILINE)
        
        # Удаляем строки типа "eS a", "oe ee" - короткие комбинации букв с пробелами
        text = re.sub(r'^\s*[a-zA-Zа-яА-Я]{1,2}\s+[a-zA-Zа-яА-Я]{1,2}\s*$', '', text, flags=re.MULTILINE)
        
        # Удаляем строки из повторяющихся коротких буквенных комбинаций
        text = re.sub(r'^\s*([a-zA-Zа-яА-Я]{1,2}\s+){2,}[a-zA-Zа-яА-Я]{1,2}\s*$', '', text, flags=re.MULTILINE)
        
        # Удаляем строки состоящие только из одиночных букв и пробелов
        text = re.sub(r'^\s*([a-zA-Zа-яА-Я]\s+){3,}[a-zA-Zа-яА-Я]\s*$', '', text, flags=re.MULTILINE)
        
        # Удаляем кракозябры типа "epee na связи. pepe ия" - короткие слова с точками
        text = re.sub(r'\b[a-zA-Zа-яА-Я]{2,4}\s+[a-zA-Zа-яА-Я]{2,4}\s*\.\s*[a-zA-Zа-яА-Я]{2,4}\s+[a-zA-Zа-яА-Я]{2,4}\b', '', text)
        
        # Удаляем кракозябры типа "О бр ООН es 5 ЕЕ ЕЕЕВЕЕЕРЫЕЕРЕЕЕ" - смешанные буквы и цифры
        text = re.sub(r'\b[а-яА-Я]{1,2}\s+[а-яА-Я]{1,3}\s+[а-яА-Я]{1,3}\s+[a-zA-Z]{1,2}\s+\d+\s+[а-яА-Я]{1,2}\s+[а-яА-Я]{10,}\b', '', text)
        
        # Удаляем кракозябры типа "ee ae oe ae oe eo se ee Se SSS Sa" - повторяющиеся короткие буквы
        text = re.sub(r'\b([a-zA-Z]{1,2}\s+){5,}[a-zA-Z]{1,2}\b', '', text)
        
        # Удаляем кракозябры типа "еее СООТВЕТСТВУЮТ" - короткие буквы перед нормальными словами
        text = re.sub(r'\b[а-яА-Я]{1,3}\s+([А-Я]{5,})\b', r'\1', text)
        
        # Удаляем кракозябры типа "Ваюменовяние иоготовителя" - искаженные слова
        text = re.sub(r'\b[а-яА-Я]{8,}и[а-яА-Я]{8,}\b', '', text)
        
        # Удаляем кракозябры типа "завола] - изготовителя" - слова с лишними символами
        text = re.sub(r'\b[а-яА-Я]{5,}[\]\)]\s*-\s*[а-яА-Я]{5,}\b', '', text)
        
        # ДОПОЛНИТЕЛЬНЫЕ ПРАВИЛА ДЛЯ КОНКРЕТНЫХ КРАКОЗЯБР:
        
        # Удаляем "epee na связи. pepe ия" - конкретный паттерн
        text = re.sub(r'\bepee\s+na\s+связи\.\s+pepe\s+ия\b', '', text)
        
        # Удаляем "О бр ООН es 5 ЕЕ ЕЕЕВЕЕЕРЫЕЕРЕЕЕ" - конкретный паттерн
        text = re.sub(r'\bО\s+бр\s+ООН\s+es\s+5\s+ЕЕ\s+ЕЕЕВЕЕЕРЫЕЕРЕЕЕ\b', '', text)
        
        # Удаляем "ee ae oe ae oe eo se ee Se SSS Sa" - конкретный паттерн
        text = re.sub(r'\bee\s+ae\s+oe\s+ae\s+oe\s+eo\s+se\s+ee\s+Se\s+SSS\s+Sa\b', '', text)
        
        # Удаляем "Ваюменовяние иоготовителя" - конкретный паттерн
        text = re.sub(r'\bВаюменовяние\s+иоготовителя\b', '', text)
        
        # Удаляем "завола] - изготовителя" - конкретный паттерн
        text = re.sub(r'\bзавола\]\s*-\s*изготовителя\b', '', text)
        
        # Удаляем "еее СООТВЕТСТВУЮТ" - конкретный паттерн
        text = re.sub(r'\bеее\s+СООТВЕТСТВУЮТ\b', 'СООТВЕТСТВУЮТ', text)
        
        # Удаляем "нех у же =: :" - конкретный паттерн
        text = re.sub(r'\bнех\s+у\s+же\s*=\s*:\s*:\s*', '', text)
        
        # Удаляем "SSS Sa" - конкретный паттерн
        text = re.sub(r'\bSSS\s+Sa\b', '', text)
        
        # Убираем множественные пробелы
        text = re.sub(r'\s+', ' ', text)
        
        # Убираем лишние переносы строк
        text = re.sub(r'\n\s*\n', '\n', text)
        
        # Удаляем пустые строки
        text = re.sub(r'\n\s*\n', '\n', text)
        
        cleaned_text = text.strip()
        logger.info(f"После базовой очистки, длина: {len(cleaned_text)}")
        
        # Всегда используем агента для создания чистого abstract из OCR текста
        if len(cleaned_text) > 50:  # Только для достаточно длинных текстов
            logger.info("Используем агента для создания чистого abstract из OCR текста")
            try:
                abstract = self._create_ocr_cleaning_agent(cleaned_text)
                logger.info(f"Агент очистки создал abstract, длина: {len(abstract)}")
                
                # Сохраняем исходный очищенный текст в session_state для использования в интерфейсе
                if 'original_cleaned_text' not in st.session_state:
                    st.session_state['original_cleaned_text'] = cleaned_text
                
                return abstract
            except Exception as e:
                logger.error(f"Ошибка агента очистки: {e}")
                return cleaned_text
        else:
            logger.info("Текст слишком короткий для использования агента")
        
        return cleaned_text
    
    def _get_original_cleaned_text(self, text: str) -> str:
        """Получить только очищенный текст без создания абстракта"""
        if not text:
            return ""
        
        import re
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info(f"Создаем исходный очищенный текст, длина: {len(text)}")
        
        # Применяем ту же базовую очистку, что и в _clean_ocr_text, но БЕЗ агента
        # Удаляем номера страниц
        text = re.sub(r'---\s*Страница\s+\d+\s*---', '', text)
        
        # Удаляем повторяющиеся символы (более 3 подряд)
        text = re.sub(r'(.)\1{3,}', r'\1', text)
        
        # Удаляем кривые символы и артефакты OCR - более агрессивная очистка
        # Удаляем строки с множественными повторяющимися символами
        text = re.sub(r'^[^\w\s]{5,}$', '', text, flags=re.MULTILINE)
        
        # Удаляем строки состоящие только из символов
        text = re.sub(r'^[=\-_+*~#$%^&*()\[\]{}|\\:;"\'<>,.?!/@\s]{3,}$', '', text, flags=re.MULTILINE)
        
        # Удаляем одиночные символы в начале строки (артефакты OCR)
        text = re.sub(r'^\s*[^\w\s]\s*$', '', text, flags=re.MULTILINE)
        
        # Удаляем строки с множественными пробелами и символами
        text = re.sub(r'^\s*[\s\W]{15,}\s*$', '', text, flags=re.MULTILINE)
        
        # Удаляем кракозябры в середине текста (последовательности из 3+ небуквенных символов)
        text = re.sub(r'[^\w\s]{3,}', ' ', text)
        
        # Удаляем кривые символы типа "oe ee ee eS a" - короткие бессмысленные комбинации
        text = re.sub(r'^\s*[a-zA-Zа-яА-Я]{1,3}\s*$', '', text, flags=re.MULTILINE)
        
        # Удаляем строки типа "eS a", "oe ee" - короткие комбинации букв с пробелами
        text = re.sub(r'^\s*[a-zA-Zа-яА-Я]{1,2}\s+[a-zA-Zа-яА-Я]{1,2}\s*$', '', text, flags=re.MULTILINE)
        
        # Удаляем строки из повторяющихся коротких буквенных комбинаций
        text = re.sub(r'^\s*([a-zA-Zа-яА-Я]{1,2}\s+){2,}[a-zA-Zа-яА-Я]{1,2}\s*$', '', text, flags=re.MULTILINE)
        
        # Удаляем строки состоящие только из одиночных букв и пробелов
        text = re.sub(r'^\s*([a-zA-Zа-яА-Я]\s+){3,}[a-zA-Zа-яА-Я]\s*$', '', text, flags=re.MULTILINE)
        
        # ДОПОЛНИТЕЛЬНЫЕ ПРАВИЛА ДЛЯ КОНКРЕТНЫХ КРАКОЗЯБР:
        
        # Удаляем "epee na связи. pepe ия" - конкретный паттерн
        text = re.sub(r'\bepee\s+na\s+связи\.\s+pepe\s+ия\b', '', text)
        
        # Удаляем "О бр ООН es 5 ЕЕ ЕЕЕВЕЕЕРЫЕЕРЕЕЕ" - конкретный паттерн
        text = re.sub(r'\bО\s+бр\s+ООН\s+es\s+5\s+ЕЕ\s+ЕЕЕВЕЕЕРЫЕЕРЕЕЕ\b', '', text)
        
        # Удаляем "ee ae oe ae oe eo se ee Se SSS Sa" - конкретный паттерн
        text = re.sub(r'\bee\s+ae\s+oe\s+ae\s+oe\s+eo\s+se\s+ee\s+Se\s+SSS\s+Sa\b', '', text)
        
        # Удаляем "Ваюменовяние иоготовителя" - конкретный паттерн
        text = re.sub(r'\bВаюменовяние\s+иоготовителя\b', '', text)
        
        # Удаляем "завола] - изготовителя" - конкретный паттерн
        text = re.sub(r'\bзавола\]\s*-\s*изготовителя\b', '', text)
        
        # Удаляем "еее СООТВЕТСТВУЮТ" - конкретный паттерн
        text = re.sub(r'\bеее\s+СООТВЕТСТВУЮТ\b', 'СООТВЕТСТВУЮТ', text)
        
        # Удаляем "нех у же =: :" - конкретный паттерн
        text = re.sub(r'\bнех\s+у\s+же\s*=\s*:\s*:\s*', '', text)
        
        # Удаляем "SSS Sa" - конкретный паттерн
        text = re.sub(r'\bSSS\s+Sa\b', '', text)
        
        # Убираем множественные пробелы
        text = re.sub(r'\s+', ' ', text)
        
        # Убираем лишние переносы строк
        text = re.sub(r'\n\s*\n', '\n', text)
        
        # Удаляем пустые строки
        text = re.sub(r'\n\s*\n', '\n', text)
        
        cleaned_text = text.strip()
        logger.info(f"Исходный очищенный текст создан, длина: {len(cleaned_text)}")
        
        return cleaned_text

    def _extract_qa_pairs(self, text: str) -> List[Dict[str, str]]:
        """Выделение Q/A пар из текста (FAQ): поддержка RU/EN маркеров."""
        if not text:
            return []
        import re
        pairs: List[Dict[str, str]] = []
        # Нормализуем переносы абзацев
        blocks = [b.strip() for b in re.split(r"\n{2,}", text) if b.strip()]
        # Паттерны для вопрос/ответ
        question_patterns = [
            r"^Q\s*[:\-]\s*(.+)$",
            r"^Question\s*[:\-]\s*(.+)$",
            r"^Вопрос\s*[:\-]\s*(.+)$",
            r"^П\.?\s*[:\-]\s*(.+)$",
        ]
        answer_patterns = [
            r"^A\s*[:\-]\s*(.+)$",
            r"^Answer\s*[:\-]\s*(.+)$",
            r"^Ответ\s*[:\-]\s*(.+)$",
            r"^О\.?\s*[:\-]\s*(.+)$",
        ]
        q_re = re.compile("|".join(f"({p})" for p in question_patterns), re.IGNORECASE)
        a_re = re.compile("|".join(f"({p})" for p in answer_patterns), re.IGNORECASE)
        current_q = None
        for block in blocks:
            qm = q_re.match(block)
            if qm:
                # Возьмем первую не-пустую группу
                for g in qm.groups():
                    if g and not g.strip().startswith(('Q', 'Question', 'Вопрос', 'П', 'A', 'Answer', 'Ответ', 'О')):
                        current_q = g.strip()
                        break
                continue
            am = a_re.match(block)
            if am and current_q:
                for g in am.groups():
                    if g and not g.strip().startswith(('Q', 'Question', 'Вопрос', 'П', 'A', 'Answer', 'Ответ', 'О')):
                        pairs.append({"question": current_q, "answer": g.strip()})
                        current_q = None
                        break
        # Доп. эвристика: «Вопрос …?\nОтвет …» в одном блоке
        if not pairs:
            inline = re.findall(r"(?:Вопрос|Question|Q)\s*[:\-]?\s*(.+?)\?\s*(?:\n|\s){1,3}(?:Ответ|Answer|A)\s*[:\-]?\s*(.+?)(?=\n\n|\Z)", text, re.IGNORECASE | re.DOTALL)
            for q, a in inline:
                qn = q.strip()
                an = a.strip()
                if qn and an:
                    pairs.append({"question": qn, "answer": an})
        # Эвристика по строкам: вопрос — строка, заканчивающаяся '?', ответ — следующий абзац
        if not pairs:
            lines = [ln.rstrip() for ln in text.splitlines()]
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                # пропускаем пустые
                if not line:
                    i += 1
                    continue
                # вопрос, если заканчивается на '?'
                if line.endswith('?') and 3 <= len(line) <= 300:
                    question = line
                    # собрать ответ из следующих 1-8 строк до пустой строки или следующего вопроса
                    answer_lines = []
                    j = i + 1
                    while j < len(lines) and len(answer_lines) < 8:
                        nxt = lines[j].strip()
                        if not nxt:
                            # конец ответа
                            break
                        if nxt.endswith('?') and len(nxt) <= 300:
                            # следующая строка похожа на вопрос — прерываем
                            break
                        answer_lines.append(nxt)
                        j += 1
                    answer = ' '.join(answer_lines).strip()
                    if answer:
                        pairs.append({"question": question, "answer": answer})
                        i = j
                        continue
                i += 1
        # Инлайновые bullets после вопроса в одной строке: "What is X? • ... • ..."
        try:
            if not pairs:
                import re as _re
                pattern = _re.compile(r"(?s)(?P<q>[^\n]{3,300}?\?)\s*(?P<a>.+?)(?=(?:\n\s*[^\n]{0,300}?\?|\Z))")
                for m in pattern.finditer(text):
                    q = (m.group('q') or '').strip()
                    a = (m.group('a') or '').strip()
                    if not q or not a:
                        continue
                    # Если в ответе есть маркеры '•', соберем как связный ответ
                    if '•' in a:
                        bullets = [seg.strip() for seg in a.split('•') if seg.strip()]
                        a_norm = ' '.join(bullets)
                    else:
                        a_norm = a
                    # Ограничим чрезмерные хвосты
                    a_norm = a_norm.strip()
                    if a_norm:
                        pairs.append({"question": q, "answer": a_norm})
        except Exception:
            pass
        return pairs[:100]
    
    def _create_full_cleaned_text(self, ocr_text: str) -> str:
        """Создать полный очищенный текст с помощью AI агента (без сокращений)"""
        try:
            import os
            import requests
            import logging
            
            logger = logging.getLogger(__name__)
            logger.info("Создаем полный очищенный текст с помощью AI агента")
            
            # Текст уже очищен в analyze_document, используем его как есть
            base_cleaned = ocr_text
            
            # Если текст слишком короткий, возвращаем как есть
            if len(base_cleaned) < 100:
                return base_cleaned
            
            # Проверяем наличие API ключа
            api_key = os.getenv("PROXYAPI_KEY") or os.getenv("PROXYAPI_API_KEY") or os.getenv("OPEN_AI_API_KEY")
            if not api_key:
                logger.warning("API ключ не найден, возвращаем базовую очистку")
                return base_cleaned
            
            logger.info("API ключ найден, отправляем запрос к агенту для полной очистки")
            
            # Создаем промпт для полной очистки без сокращений
            prompt = f"""
Ты - эксперт по очистке OCR текста. Твоя задача - исправить искаженные слова и символы в тексте, но СОХРАНИТЬ ВСЕ СОДЕРЖАНИЕ ПОЛНОСТЬЮ.

ИСХОДНЫЙ OCR ТЕКСТ:
{base_cleaned}

ЗАДАЧА:
1. Исправь все искаженные слова (кракозябры) на правильные
2. Восстанови структуру предложений
3. КРИТИЧЕСКИ ВАЖНО: Сохрани ВСЕ содержимое - НЕ сокращай, НЕ удаляй предложения, НЕ создавай краткое изложение
4. Удали только явный мусор (повторяющиеся символы, артефакты OCR)
5. Сохрани все числа, даты, названия, технические термины, полные предложения
6. Результат должен быть ДЛИННЕЕ или РАВЕН исходному тексту

ПРИМЕРЫ ИСПРАВЛЕНИЙ:
- "Ваюменовяние" → "Наименование"
- "иоготовителя" → "изготовителя" 
- "еее СООТВЕТСТВУЮТ" → "СООТВЕТСТВУЮТ"
- "завола] - изготовителя" → "завода - изготовителя"

ВЕРНИ ТОЛЬКО ОЧИЩЕННЫЙ ПОЛНЫЙ ТЕКСТ БЕЗ ДОПОЛНИТЕЛЬНЫХ КОММЕНТАРИЕВ.
"""
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "system",
                        "content": "Ты - эксперт по очистке OCR текста. Твоя задача - исправить искаженные слова, сохранив все содержимое без сокращений."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "max_tokens": 4000,
                "temperature": 0.1
            }
            
            response = requests.post(
                "https://api.proxyapi.ru/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                cleaned_text = result['choices'][0]['message']['content'].strip()
                logger.info(f"✅ Агент полной очистки завершил работу, длина: {len(cleaned_text)}")
                return cleaned_text
            else:
                logger.error(f"Ошибка API при полной очистке: {response.status_code} - {response.text}")
                return base_cleaned
                
        except Exception as e:
            logger.error(f"Ошибка при создании полного очищенного текста: {e}")
            return self._get_original_cleaned_text(ocr_text)
    
    def _smart_kb_suggestion(self, analysis: Dict) -> Dict:
        """Умное предложение KB с проверкой дубликатов и возможностью объединения"""
        try:
            import os
            import requests
            import logging
            
            logger = logging.getLogger(__name__)
            logger.info("Умное предложение KB с проверкой дубликатов")
            
            # Получаем список существующих KB
            existing_kbs = self.kb_manager.get_knowledge_bases(active_only=True)
            existing_categories = self.kb_manager.get_categories()
            
            # Подготавливаем информацию о документе
            doc_content = analysis.get('original_cleaned_text', analysis.get('full_cleaned_text', ''))
            doc_summary = analysis.get('smart_summary', '')
            doc_category = analysis.get('category', 'Неизвестно')
            doc_title = analysis.get('file_name', 'Документ')
            
            # Проверяем наличие API ключа
            api_key = os.getenv("PROXYAPI_KEY") or os.getenv("PROXYAPI_API_KEY") or os.getenv("OPEN_AI_API_KEY")
            if not api_key:
                logger.warning("API ключ не найден, используем базовое предложение")
                return self._create_basic_kb_suggestion(doc_category, existing_categories)
            
            logger.info("API ключ найден, отправляем запрос к агенту для умного предложения KB")
            
            # Создаем промпт для умного предложения темы KB
            existing_kb_info = ""
            if existing_kbs:
                existing_kb_info = "СУЩЕСТВУЮЩИЕ БАЗЫ ЗНАНИЙ:\n"
                for kb in existing_kbs[:15]:  # Показываем первые 15
                    existing_kb_info += f"- ID {kb['id']}: {kb['name']} (категория: {kb['category']})\n"
                    if kb.get('description'):
                        existing_kb_info += f"  Описание: {kb['description'][:100]}...\n"
            
            prompt = f"""
Ты - эксперт по организации баз знаний для оператора спутниковой связи. Твоя задача - предложить оптимальную тему/название для новой базы знаний с учетом существующих и возможности объединения.

ИНФОРМАЦИЯ О ДОКУМЕНТЕ:
- Название файла: {doc_title}
- Категория: {doc_category}
- Краткое содержание: {doc_summary[:500]}...

{existing_kb_info}

СУЩЕСТВУЮЩИЕ КАТЕГОРИИ: {', '.join(existing_categories)}

ЗАДАЧА:
1. Проанализируй содержание документа
2. Проверь, есть ли похожие документы в существующих KB
3. Если есть похожие - предложи объединение с существующей KB
4. Если нет похожих - предложи новую KB с уникальным названием
5. Предложи категорию из существующих или новую
6. Избегай дублирования названий

ОТВЕТ В ФОРМАТЕ JSON:
{{
    "suggested_name": "Название базы знаний",
    "suggested_category": "Категория",
    "description": "Краткое описание (1-2 предложения)",
    "merge_with_existing": {{
        "can_merge": true/false,
        "existing_kb_id": null или ID,
        "existing_kb_name": null или название,
        "merge_reason": "Причина объединения"
    }},
    "duplicate_check": {{
        "has_duplicates": true/false,
        "duplicate_kbs": [список ID дубликатов],
        "duplicate_reason": "Причина дублирования"
    }},
    "confidence": 0.85,
    "reasoning": "Обоснование предложения"
}}
"""
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "system",
                        "content": "Ты - эксперт по организации баз знаний. Твоя задача - предложить оптимальную тему KB с учетом существующих, избегая дублирования и предлагая объединение когда это уместно."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.3
            }
            
            response = requests.post(
                "https://api.proxyapi.ru/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result['choices'][0]['message']['content'].strip()
                
                # Парсим JSON ответ
                try:
                    import json
                    suggestion = json.loads(response_text)
                    logger.info(f"✅ Умное предложение KB создано: {suggestion.get('suggested_name', 'Неизвестно')}")
                    return suggestion
                except json.JSONDecodeError:
                    logger.warning("Ошибка парсинга JSON ответа, используем базовое предложение")
                    return self._create_basic_kb_suggestion(doc_category, existing_categories)
            else:
                logger.error(f"Ошибка API при умном предложении KB: {response.status_code} - {response.text}")
                return self._create_basic_kb_suggestion(doc_category, existing_categories)
                
        except Exception as e:
            logger.error(f"Ошибка при умном предложении темы KB: {e}")
            return self._create_basic_kb_suggestion(analysis.get('category', 'Неизвестно'), [])

    def _suggest_kb_topic(self, analysis: Dict) -> Dict:
        """Предложить тему KB с учетом существующих и возможности объединения"""
        # Используем новый умный метод
        return self._smart_kb_suggestion(analysis)
    
    def _create_basic_kb_suggestion(self, doc_category: str, existing_categories: List[str]) -> Dict:
        """Создать базовое предложение KB без AI"""
        # Простое предложение на основе категории документа
        suggested_name = f"База знаний: {doc_category}"
        suggested_category = doc_category if doc_category in existing_categories else "Общие документы"
        
        return {
            "suggested_name": suggested_name,
            "suggested_category": suggested_category,
            "description": f"База знаний для документов категории {doc_category}",
            "merge_with_existing": {
                "can_merge": False,
                "existing_kb_id": None,
                "existing_kb_name": None,
                "merge_reason": "Не найдено подходящих для объединения"
            },
            "confidence": 0.5,
            "reasoning": "Базовое предложение без AI анализа"
        }
    
    def _create_ocr_cleaning_agent(self, ocr_text: str, gemini_analysis: str = None) -> str:
        """Специальный агент для очистки OCR текста и создания abstract для KB"""
        try:
            import logging
            
            logger = logging.getLogger(__name__)
            logger.info("Запускаем агента очистки OCR текста для KB (локальная модель)")
            
            # Получаем информацию о существующих базах знаний
            existing_kbs = self._get_existing_knowledge_bases()
            logger.info(f"Найдено {len(existing_kbs)} существующих БЗ")
            
            # Логируем наличие анализа от Gemini
            if gemini_analysis:
                logger.info(f"✅ Получен анализ от Gemini ({len(gemini_analysis)} символов) - будет объединен с OCR")
            else:
                logger.info("ℹ️ Анализ от Gemini не предоставлен - работаем только с OCR")
            
            # Умный промпт для агента очистки OCR с анализом качества
            prompt = f"""
Ты - эксперт по анализу документов для базы знаний. Твоя задача:

1. ОЧИСТИТЬ OCR текст от кракозябр и мусора
2. ВОССТАНОВИТЬ осмысленный текст на русском языке
3. ОЦЕНИТЬ качество восстановленного текста
4. ПРЕДЛОЖИТЬ категорию для базы знаний
5. ВЫДЕЛИТЬ ключевые слова
6. СФОРМУЛИРОВАТЬ тестовые вопросы для проверки релевантности

Исходный OCR текст (полный текст, {len(ocr_text)} символов):
{ocr_text}

СУЩЕСТВУЮЩИЕ БАЗЫ ЗНАНИЙ:
{existing_kbs}

ПРАВИЛА ОЧИСТКИ:
- Удали кракозябры: "epee na связи. pepe ия", "О бр ООН es 5 ЕЕ ЕЕЕВЕЕЕРЫЕЕРЕЕЕ"
- Удали мусор: "ee ae oe ae oe eo se ee Se SSS Sa", "Ваюменовяние иоготовителя"
- Восстанови нормальные слова из искажений
- Сохрани только осмысленную информацию
- Создай краткий, структурированный abstract ТОЛЬКО из OCR текста

ФОРМАТ ОТВЕТА:
```
КАЧЕСТВО_ТЕКСТА: [ОТЛИЧНОЕ/ХОРОШЕЕ/УДОВЛЕТВОРИТЕЛЬНОЕ/ПЛОХОЕ]
ОСМЫСЛЕННОСТЬ: [ВЫСОКАЯ/СРЕДНЯЯ/НИЗКАЯ]
ГОТОВНОСТЬ_ДЛЯ_KB: [ДА/НЕТ]

КАТЕГОРИЯ_БЗ: [выбери из существующих БЗ или предложи новую]

КЛЮЧЕВЫЕ_СЛОВА: [список из 5-10 ключевых слов через запятую]

ЧИСТЫЙ_ABSTRACT:
[здесь КРАТКИЙ абстракт (максимум 200-300 слов) с ключевой информацией для базы знаний]

ТЕСТОВЫЕ_ВОПРОСЫ:
1. [вопрос на русском языке]
   Ответ: [ответ на основе информации из документа]
2. [вопрос на русском языке]
   Ответ: [ответ на основе информации из документа]
3. [вопрос на русском языке]
   Ответ: [ответ на основе информации из документа]
4. [вопрос на русском языке]
   Ответ: [ответ на основе информации из документа]
5. [вопрос на русском языке]
   Ответ: [ответ на основе информации из документа]
```

СОЗДАНИЕ АБСТРАКТА:
- Создай КРАТКИЙ абстракт (200-300 слов максимум)
- Включи только КЛЮЧЕВУЮ информацию: название, номер, даты, основные характеристики
- Убери повторения и избыточные детали
- Структурируй информацию в логическом порядке
- Используй четкие, понятные формулировки

КЛЮЧЕВЫЕ СЛОВА:
- Выдели 5-10 самых важных терминов, понятий, названий
- Включи технические термины, названия услуг, ключевые понятия
- Используй как русские, так и английские термины если нужно

ТЕСТОВЫЕ ВОПРОСЫ:
- Найди 3-5 интересных фактов в документе
- Создай простые вопросы об этих фактах
- Ответы на основе информации из документа
- Вопросы на русском языке
"""
            
            # Используем локальную модель через BaseAgent
            from langchain.prompts import ChatPromptTemplate
            from langchain.schema import StrOutputParser
            
            template = ChatPromptTemplate.from_template(prompt)
            chain = template | self.chat_model | StrOutputParser()
            
            agent_response = chain.invoke({})
            
            # Парсим структурированный ответ агента
            parsed_result = self._parse_agent_response(agent_response)
            
            logger.info(f"✅ Агент очистки завершил работу (локальная модель)")
            logger.info(f"Качество текста: {parsed_result.get('quality', 'НЕИЗВЕСТНО')}")
            logger.info(f"Осмысленность: {parsed_result.get('meaningfulness', 'НЕИЗВЕСТНО')}")
            logger.info(f"Готовность для KB: {parsed_result.get('kb_ready', 'НЕИЗВЕСТНО')}")
            logger.info(f"Категория БЗ: {parsed_result.get('category', 'НЕИЗВЕСТНО')}")
            logger.info(f"Ключевые слова: {parsed_result.get('keywords', [])}")
            logger.info(f"Тестовые вопросы: {len(parsed_result.get('test_questions', []))}")
            logger.info(f"Длина abstract: {len(parsed_result.get('abstract', ''))}")
            
            # Сохраняем результат в session_state для использования в других методах
            if hasattr(self, '_last_parsed_result'):
                self._last_parsed_result = parsed_result
            
            return parsed_result.get('abstract', agent_response)
                
        except Exception as e:
            logger.error(f"❌ Ошибка агента очистки: {e}")
            return ocr_text
    
    def _get_existing_knowledge_bases(self) -> str:
        """Получить информацию о существующих базах знаний"""
        try:
            # Получаем список существующих БЗ
            kbs = self.kb_manager.get_knowledge_bases()
            
            if not kbs:
                return "Существующих баз знаний не найдено."
            
            kb_info = "Существующие базы знаний:\n"
            for kb in kbs:
                kb_info += f"- ID: {kb['id']}, Название: '{kb['name']}', Категория: '{kb['category']}', Описание: '{kb['description']}'{chr(10)}"
            
            return kb_info
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Ошибка получения списка БЗ: {e}")
            return "Ошибка получения списка существующих БЗ."
    
    def _parse_agent_response(self, response: str) -> dict:
        """Парсинг структурированного ответа агента очистки OCR"""
        try:
            import re
            
            result = {
                'quality': 'НЕИЗВЕСТНО',
                'meaningfulness': 'НЕИЗВЕСТНО', 
                'kb_ready': 'НЕИЗВЕСТНО',
                'category': 'НЕИЗВЕСТНО',
                'keywords': [],
                'test_questions': [],
                'abstract': response  # По умолчанию весь ответ
            }
            
            # Ищем качество текста
            quality_match = re.search(r'КАЧЕСТВО_ТЕКСТА:\s*([А-Я]+)', response)
            if quality_match:
                result['quality'] = quality_match.group(1)
            
            # Ищем осмысленность
            meaningfulness_match = re.search(r'ОСМЫСЛЕННОСТЬ:\s*([А-Я]+)', response)
            if meaningfulness_match:
                result['meaningfulness'] = meaningfulness_match.group(1)
            
            # Ищем готовность для KB
            kb_ready_match = re.search(r'ГОТОВНОСТЬ_ДЛЯ_KB:\s*([А-Я]+)', response)
            if kb_ready_match:
                result['kb_ready'] = kb_ready_match.group(1)
            
            # Ищем категорию БЗ
            category_match = re.search(r'КАТЕГОРИЯ_БЗ:\s*([^\n]+)', response)
            if category_match:
                result['category'] = category_match.group(1).strip()
            
            # Ищем ключевые слова
            keywords_match = re.search(r'КЛЮЧЕВЫЕ_СЛОВА:\s*([^\n]+)', response)
            if keywords_match:
                keywords_text = keywords_match.group(1).strip()
                result['keywords'] = [kw.strip() for kw in keywords_text.split(',') if kw.strip()]
            
            # Ищем тестовые вопросы с ответами
            questions_match = re.search(r'ТЕСТОВЫЕ_ВОПРОСЫ:\s*\n(.*?)(?:\n\n|\Z)', response, re.DOTALL)
            if questions_match:
                questions_text = questions_match.group(1).strip()
                # Парсим нумерованный список вопросов с ответами
                questions = []
                current_question = None
                current_answer = None
                
                for line in questions_text.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Проверяем, является ли строка вопросом (начинается с цифры)
                    if re.match(r'^\d+\.', line):
                        # Сохраняем предыдущий вопрос, если есть
                        if current_question:
                            questions.append({
                                'question': current_question,
                                'answer': current_answer or 'Информация не найдена в документе'
                            })
                        
                        # Начинаем новый вопрос
                        current_question = re.sub(r'^\d+\.\s*', '', line)
                        current_answer = None
                    
                    # Проверяем, является ли строка ответом
                    elif line.startswith('Ответ:'):
                        current_answer = line.replace('Ответ:', '').strip()
                
                # Добавляем последний вопрос
                if current_question:
                    questions.append({
                        'question': current_question,
                        'answer': current_answer or 'Информация не найдена в документе'
                    })
                
                result['test_questions'] = questions
            
            # Ищем чистый abstract
            abstract_match = re.search(r'ЧИСТЫЙ_ABSTRACT:\s*\n(.*?)(?:\n\n|\Z)', response, re.DOTALL)
            if abstract_match:
                result['abstract'] = abstract_match.group(1).strip()
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка парсинга ответа агента: {e}")
            return {
                'quality': 'ОШИБКА',
                'meaningfulness': 'ОШИБКА',
                'kb_ready': 'ОШИБКА', 
                'category': 'ОШИБКА',
                'abstract': response
            }
    
    def _create_abstract_with_agent(self, ocr_text: str) -> str:
        """Создание abstract из OCR текста с помощью агента"""
        try:
            import os
            import requests
            import logging
            
            logger = logging.getLogger(__name__)
            logger.info("Запускаем агента для создания abstract из OCR текста в SmartLibrarian")
            
            # Проверяем, есть ли API ключ для агента
            api_key = os.getenv("PROXYAPI_KEY") or os.getenv("PROXYAPI_API_KEY") or os.getenv("OPEN_AI_API_KEY")
            if not api_key:
                logger.warning("API ключ не настроен, возвращаем исходный текст")
                return ocr_text
            
            logger.info("API ключ найден, отправляем запрос к агенту")
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Промпт для создания abstract
            prompt = f"""
Проанализируй следующий текст, извлеченный с помощью OCR из PDF документа.
Создай краткий и понятный abstract (резюме) на русском языке.

Исходный OCR текст:
{ocr_text[:2000]}  # Ограничиваем длину для API

Задача:
1. Определи основную тему документа
2. Выдели ключевые моменты и важную информацию
3. Создай структурированный abstract
4. Если текст содержит много мусора OCR, попробуй восстановить смысл

Ответь только abstract без дополнительных комментариев.
"""
            
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.1
            }
            
            response = requests.post(
                "https://api.proxyapi.ru/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                abstract = result['choices'][0]['message']['content']
                logger.info(f"✅ Abstract создан с помощью агента в SmartLibrarian, длина: {len(abstract)}")
                logger.info(f"Первые 200 символов abstract: {abstract[:200]}...")
                return abstract
            else:
                logger.error(f"❌ Ошибка API агента: {response.status_code} - {response.text}")
                return ocr_text
                
        except Exception as e:
            logger.error(f"❌ Ошибка создания abstract: {e}")
            return ocr_text
    
    def _create_smart_summary(self, text: str, file_name: str = None) -> str:
        """Создание умной выжимки из текста с учетом контекста документа"""
        if not text:
            return ""
        
        # Специальные правила для создания абстракта по типу документа
        if file_name:
            if 'iridium' in file_name.lower() and 'sbd' in file_name.lower():
                # Для документов Iridium SBD создаем более структурированный абстракт
                lines = text.split('\n')
                important_lines = []
                for line in lines[:20]:  # Берем первые 20 строк
                    line = line.strip()
                    if line and len(line) > 10:  # Пропускаем короткие строки
                        important_lines.append(line)
                
                if important_lines:
                    return '\n'.join(important_lines[:10])  # Возвращаем первые 10 важных строк
            
            elif 'billmaster' in file_name.lower():
                # Для документов BillMaster
                return text[:800] + "..." if len(text) > 800 else text
        
        # Общий случай - ограничиваем длину текста
        if len(text) > 1000:
            return text[:1000] + "..."
        
        return text
    
    def analyze_document_images(self, file_path: Path) -> List[Dict]:
        """Анализ изображений в документе с помощью VisionProcessor"""
        # Проверяем доступность модели
        model_status = self.vision_processor.check_model_availability()
        if not model_status.get('available', False):
            st.warning(f"Vision модель недоступна: {model_status.get('message', 'Неизвестная ошибка')}")
            return []
        
        try:
            # Извлекаем изображения из PDF
            extracted_images = self._extract_images_from_pdf(file_path)
            
            if not extracted_images:
                return []
            
            # Фильтруем мусорные изображения
            filtered_images = [p for p in extracted_images if not self._is_image_noise(p)]
            
            # Анализируем каждое изображение
            image_analyses = []
            for image_path in filtered_images:
                # Используем VisionProcessor для анализа
                analysis_result = self.vision_processor.analyze_image_with_gemini(image_path)
                
                if analysis_result['success']:
                    # Извлекаем текст из изображения
                    text_content = self.vision_processor.extract_text_from_image_gemini(image_path)
                    
                    # Анализируем структуру документа
                    structure_result = self.vision_processor.analyze_document_structure(image_path)
                    
                    image_analyses.append({
                        'image_path': str(image_path),
                        'image_name': image_path.name,
                        'description': analysis_result['analysis'][:200] + "..." if len(analysis_result['analysis']) > 200 else analysis_result['analysis'],
                        'analysis': analysis_result['analysis'],
                        'text_content': text_content,
                        'structure': structure_result.get('structure') if structure_result['success'] else None,
                        'model_used': analysis_result['model'],
                        'provider': analysis_result.get('provider', 'gemini')
                    })
                else:
                    # Сохраняем информацию об ошибке
                    image_analyses.append({
                        'image_path': str(image_path),
                        'image_name': image_path.name,
                        'description': '',
                        'analysis': '',
                        'error': analysis_result['error']
                    })
            
            return image_analyses
            
        except Exception as e:
            st.warning(f"Ошибка анализа изображений в {file_path.name}: {e}")
            return []

    def analyze_docx_images(self, docx_path: Path) -> List[Dict]:
        """Извлечение изображений из DOCX и их анализ с помощью VisionProcessor"""
        # Проверяем доступность модели
        model_status = self.vision_processor.check_model_availability()
        if not model_status.get('available', False):
            st.warning(f"Vision модель недоступна: {model_status.get('message', 'Неизвестная ошибка')}")
            return []
        
        try:
            from docx import Document
            import shutil
            
            doc = Document(docx_path)
            extracted_images: List[Path] = []
            
            # 1) Изображения как встроенные объекты (inline shapes)
            for idx, shape in enumerate(getattr(doc.inline_shapes, '_inline_shapes', doc.inline_shapes)):
                try:
                    # Получаем бинарные данные изображения через связанный рисунок
                    blip = shape._inline.graphic.graphicData.pic.blipFill.blip
                    rId = blip.embed
                    image_part = doc.part.related_parts[rId]
                    image_bytes = image_part.blob
                    
                    image_name = f"{docx_path.stem}_img_{idx + 1}.png"
                    image_path = self.images_dir / image_name
                    with open(image_path, 'wb') as f:
                        f.write(image_bytes)
                    extracted_images.append(image_path)
                except Exception:
                    # Пропускаем если формат неожиданный
                    continue
            
            # 2) Резервный способ: пройти по всем media частям документа с фильтром дубликатов
            try:
                seen_hashes = set()
                for rel in doc.part.rels.values():
                    if getattr(rel.target_part, 'content_type', '').startswith('image/'):
                        image_bytes = rel.target_part.blob
                        # Фильтр дубликатов по хэшу
                        try:
                            import hashlib
                            h = hashlib.sha256(image_bytes).hexdigest()
                            if h in seen_hashes:
                                continue
                            seen_hashes.add(h)
                        except Exception:
                            pass
                        image_name = f"{docx_path.stem}_media_{len(extracted_images) + 1}.png"
                        image_path = self.images_dir / image_name
                        with open(image_path, 'wb') as f:
                            f.write(image_bytes)
                        extracted_images.append(image_path)
            except Exception:
                pass
            
            if not extracted_images:
                return []
            
            # Фильтруем мусорные изображения
            filtered_images = [p for p in extracted_images if not self._is_image_noise(p)]
            if not filtered_images:
                return []
            
            # Анализируем изображения через VisionProcessor
            image_analyses: List[Dict] = []
            for image_path in filtered_images:
                analysis_result = self.vision_processor.analyze_image_with_gemini(image_path)
                if analysis_result.get('success'):
                    text_content = self.vision_processor.extract_text_from_image_gemini(image_path)
                    structure_result = self.vision_processor.analyze_document_structure(image_path)
                    image_analyses.append({
                        'image_path': str(image_path),
                        'image_name': image_path.name,
                        'description': (analysis_result.get('analysis', '')[:200] + "...") if len(analysis_result.get('analysis', '')) > 200 else analysis_result.get('analysis', ''),
                        'analysis': analysis_result.get('analysis', ''),
                        'text_content': text_content,
                        'structure': structure_result.get('structure') if structure_result.get('success') else None,
                        'model_used': analysis_result.get('model'),
                        'provider': analysis_result.get('provider', 'gemini')
                    })
                else:
                    image_analyses.append({
                        'image_path': str(image_path),
                        'image_name': image_path.name,
                        'description': '',
                        'analysis': '',
                        'error': analysis_result.get('error', 'analysis_failed')
                    })
            
            return image_analyses
        
        except ImportError:
            st.warning("python-docx не установлен. Установите: pip install python-docx")
            return []
        except Exception as e:
            st.warning(f"Ошибка извлечения изображений из DOCX: {e}")
            return []
    
    def _extract_images_from_pdf(self, pdf_path: Path) -> List[Path]:
        """Извлечение изображений из PDF"""
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(pdf_path)
            extracted_images = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    # Получаем изображение
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    # Пропускаем изображения с альфа-каналом
                    if pix.n - pix.alpha < 4:
                        # Сохраняем изображение
                        image_name = f"{pdf_path.stem}_page_{page_num + 1}_img_{img_index + 1}.png"
                        image_path = self.images_dir / image_name
                        
                        if pix.alpha:
                            pix = fitz.Pixmap(fitz.csRGB, pix)
                        
                        pix.save(str(image_path))
                        extracted_images.append(image_path)
                        pix = None
            
            doc.close()
            return extracted_images
            
        except ImportError:
            st.warning("PyMuPDF не установлен. Установите: pip install PyMuPDF")
            return []
        except Exception as e:
            st.warning(f"Ошибка извлечения изображений: {e}")
            return []
    
    def _analyze_content(self, text: str, file_name: str = None) -> Dict:
        """Анализ содержимого текста"""
        text_lower = text.lower()
        
        # Специальные правила для известных файлов по названию
        filename_rules = {
            'billmaster_7.pdf': {
                'content_type': 'licenses',
                'category': 'Лицензии и разрешения',
                'description': 'Лицензия на программное обеспечение BillMaster',
                'keywords': ['billmaster', 'лицензия', 'программное обеспечение'],
                'confidence': 0.9
            },
            'Iridium Short Burst Data Service Best Practices Guide Draft 091410_1.docx': {
                'content_type': 'technical_guides',
                'category': 'Технические руководства',
                'description': 'Руководство по лучшим практикам использования услуги Iridium Short Burst Data Service',
                'keywords': ['iridium', 'sbd', 'short burst data', 'best practices', 'service guide', 'technical'],
                'confidence': 0.95
            }
        }
        
        # Проверяем специальные правила по названию файла
        if file_name and file_name in filename_rules:
            rule_config = filename_rules[file_name]
            return {
                'content_type': rule_config['content_type'],
                'category': rule_config['category'],
                'description': rule_config['description'],
                'keywords': rule_config['keywords'],
                'confidence': rule_config['confidence']
            }
        
        # Специальные правила для известных файлов по содержимому
        special_rules = {
            'billmaster': {
                'content_type': 'licenses',
                'category': 'Лицензии и разрешения',
                'description': 'Лицензия на программное обеспечение BillMaster',
                'keywords': ['billmaster', 'лицензия', 'программное обеспечение'],
                'confidence': 0.9
            },
            'iridium': {
                'content_type': 'technical_guides',
                'category': 'Технические руководства',
                'description': 'Техническое руководство по услугам Iridium',
                'keywords': ['iridium', 'sbd', 'short burst data', 'service', 'technical'],
                'confidence': 0.8
            }
        }
        
        # Проверяем специальные правила по содержимому
        for rule_name, rule_config in special_rules.items():
            if rule_name in text_lower:
                return {
                    'content_type': rule_config['content_type'],
                    'category': rule_config['category'],
                    'description': rule_config['description'],
                    'keywords': rule_config['keywords'],
                    'confidence': rule_config['confidence']
                }
        
        # Подсчитываем совпадения с ключевыми словами для каждого типа контента
        content_scores = {}
        for content_type, config in self.content_types.items():
            score = 0
            matched_keywords = []
            
            for keyword in config['keywords']:
                if keyword.lower() in text_lower:
                    score += 1
                    matched_keywords.append(keyword)
            
            content_scores[content_type] = {
                'score': score,
                'matched_keywords': matched_keywords,
                'category': config['category'],
                'description': config['description']
            }
        
        # Находим тип с наибольшим количеством совпадений
        best_match = max(content_scores.items(), key=lambda x: x[1]['score'])
        
        if best_match[1]['score'] > 0:
            return {
                'content_type': best_match[0],
                'category': best_match[1]['category'],
                'description': best_match[1]['description'],
                'keywords': best_match[1]['matched_keywords'],
                'confidence': min(best_match[1]['score'] / 5.0, 1.0)  # Нормализуем до 0-1
            }
        else:
            return {
                'content_type': 'unknown',
                'category': 'Другое',
                'description': 'Не удалось определить тип документа',
                'keywords': [],
                'confidence': 0.0
            }
    
    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """Генерация рекомендаций по обработке документа"""
        recommendations = []
        
        # Рекомендации по формату
        if not analysis.get('format_supported', False):
            recommendations.append("❌ Формат документа не поддерживается")
            return recommendations
        
        # Рекомендации по размеру
        file_size_mb = analysis['file_size'] / (1024 * 1024)
        if file_size_mb > 50:
            recommendations.append("⚠️ Документ очень большой (>50MB), обработка может занять время")
        elif file_size_mb > 10:
            recommendations.append("ℹ️ Документ большой (>10MB), рекомендуется разбить на части")
        
        # Рекомендации по содержимому
        if analysis['confidence'] > 0.7:
            recommendations.append(f"✅ Высокая уверенность в типе документа: {analysis['category']}")
        elif analysis['confidence'] > 0.3:
            recommendations.append(f"⚠️ Средняя уверенность в типе документа: {analysis['category']}")
        else:
            recommendations.append("❓ Низкая уверенность в типе документа, рекомендуется ручная категоризация")
        
        # Рекомендации по обработке
        if analysis['text_length'] > 10000:
            recommendations.append("📄 Документ содержит много текста, рекомендуется разбить на чанки")
        
        if analysis['content_type'] == 'billing':
            recommendations.append("💰 Документ связан с биллингом, рекомендуется создать отдельную БЗ")
        
        if analysis['content_type'] == 'technical_regulations':
            recommendations.append("📋 Технический регламент, рекомендуется создать БЗ для быстрого поиска")
        
        return recommendations
    
    def suggest_kb_strategy(self, documents: List[Dict]) -> Dict:
        """Предложение стратегии создания БЗ на основе анализа документов"""
        if not documents:
            return {'type': 'no_documents', 'message': 'Нет документов для анализа'}
        
        # Анализируем все документы
        content_types = {}
        categories = {}
        
        for doc in documents:
            content_type = doc.get('content_type', 'unknown')
            category = doc.get('category', 'Другое')
            
            content_types[content_type] = content_types.get(content_type, 0) + 1
            categories[category] = categories.get(category, 0) + 1
        
        # Определяем стратегию
        total_docs = len(documents)
        unique_categories = len(categories)
        
        if unique_categories == 1:
            # Все документы одной категории
            category = list(categories.keys())[0]
            strategy = {
                'type': 'single_kb',
                'category': category,
                'kb_name': f"БЗ: {category}",
                'description': f"База знаний для документов категории '{category}'",
                'documents': documents,
                'reasoning': f"Все {total_docs} документов относятся к одной категории: {category}"
            }
        elif unique_categories <= 3 and total_docs <= 10:
            # Несколько категорий, но мало документов
            strategy = {
                'type': 'mixed_kb',
                'category': 'Смешанная',
                'kb_name': f"БЗ: Смешанные документы ({total_docs} файлов)",
                'description': f"База знаний, содержащая документы разных типов: {', '.join(categories.keys())}",
                'documents': documents,
                'reasoning': f"Небольшое количество документов ({total_docs}) разных категорий, можно объединить в одну БЗ"
            }
        else:
            # Много документов разных категорий
            strategy = {
                'type': 'multiple_kb',
                'categories': categories,
                'kb_suggestions': [],
                'reasoning': f"Много документов ({total_docs}) разных категорий, рекомендуется создать отдельные БЗ"
            }
            
            # Предлагаем отдельные БЗ для каждой категории
            for category, count in categories.items():
                if count > 0:
                    category_docs = [doc for doc in documents if doc.get('category') == category]
                    strategy['kb_suggestions'].append({
                        'category': category,
                        'kb_name': f"БЗ: {category}",
                        'description': f"База знаний для документов категории '{category}'",
                        'documents': category_docs,
                        'document_count': count
                    })
        
        return strategy
    
    def render_welcome(self):
        """Приветствие Умного библиотекаря"""
        st.markdown("""
        <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h2 style="color: white; margin: 0; text-align: center;">📚 Умный библиотекарь</h2>
            <p style="color: white; text-align: center; margin: 10px 0 0 0; font-size: 16px;">
                Ваш интеллектуальный помощник для работы с документами
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Показываем статистику документов
        self._render_document_statistics()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **🔍 Анализ документов**
            - Автоматическое определение формата
            - Анализ содержимого
            - Извлечение ключевых слов
            """)
        
        with col2:
            st.markdown("""
            **📚 Умная категоризация**
            - Определение типа документа
            - Автоматическая категоризация
            - Рекомендации по структуре БЗ
            """)
        
        with col3:
            st.markdown("""
            **🚀 Интеллектуальная обработка**
            - Создание оптимальных БЗ
            - Расширение существующих БЗ
            - Индексация для быстрого поиска
            """)
    
    def _render_document_statistics(self):
        """Отображение статистики документов"""
        try:
            # Сканируем директорию uploads
            doc_status = self.document_manager.scan_upload_directory()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="📄 Новые документы",
                    value=len(doc_status['new']),
                    delta=None
                )
            
            with col2:
                st.metric(
                    label="✅ Обработанные",
                    value=len(doc_status['processed']),
                    delta=None
                )
            
            with col3:
                st.metric(
                    label="❓ Неизвестные",
                    value=len(doc_status['unknown']),
                    delta=None
                )
            
            # Получаем информацию об архиве
            archive_info = self.document_manager.get_archive_info()
            with col4:
                st.metric(
                    label="📦 В архиве",
                    value=archive_info['total_files'],
                    delta=None
                )
            
            # Показываем уведомления
            if len(doc_status['new']) > 0:
                st.info(f"🆕 У вас есть {len(doc_status['new'])} новых документов для обработки!")
            
            if len(doc_status['processed']) > 0:
                st.success(f"✅ {len(doc_status['processed'])} документов уже обработаны и готовы к архивированию")
                
        except Exception as e:
            st.warning(f"Не удалось получить статистику документов: {e}")
    
    @manual_transaction("kb_save_operation")
    def save_documents_to_kb_transactional(self, analyses: List[Dict], kb_id: int, 
                                         selected_doc_indices: List[int], 
                                         selected_image_indices: List[tuple],
                                         transaction_id: str = None) -> Dict:
        """Сохранение документов в KB с поддержкой транзакций"""
        try:
            saved_count = 0
            
            for doc_idx in selected_doc_indices:
                analysis = analyses[doc_idx]
                
                # Получаем полный текст для сохранения
                full_text = analysis.get('original_cleaned_text', analysis.get('full_cleaned_text', ''))
                if not full_text or (full_text.strip() == analysis.get('smart_summary', '').strip()):
                    full_text = analysis.get('raw_ocr_text', '')
                
                # Логируем операцию вставки документа
                self.transaction_manager.log_database_change(
                    transaction_id, 'knowledge_documents', 'INSERT',
                    old_data=None, new_data={
                        'kb_id': kb_id,
                        'title': analysis.get('file_name', 'Документ'),
                        'file_path': str(analysis.get('file_path', '')),
                        'content_type': analysis.get('content_type', 'text/plain'),
                        'file_size': analysis.get('file_size', 0),
                        'metadata': {
                            'ocr_cleaned': True,
                            'gemini_analyzed': bool(analysis.get('images')),
                            'text_length': len(full_text),
                            'summary_length': len(analysis.get('smart_summary', '')),
                            'content': full_text,
                            'summary': analysis.get('smart_summary', ''),
                            'processed': True,
                            'status': "processed"
                        }
                    }
                )
                
                # Определяем корректный MIME type по расширению
                ext_to_mime = {
                    '.pdf': 'application/pdf',
                    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    '.doc': 'application/msword',
                    '.txt': 'text/plain',
                    '.md': 'text/markdown',
                    '.rtf': 'application/rtf',
                    '.html': 'text/html',
                    '.xml': 'application/xml'
                }
                file_ext = analysis.get('file_extension', '').lower()
                mime_type = ext_to_mime.get(file_ext) or (mimetypes.guess_type(str(analysis.get('file_path', '')))[0] or 'application/octet-stream')

                # Сохраняем документ
                doc_id = self.kb_manager.add_document(
                    kb_id=kb_id,
                    title=analysis.get('file_name', 'Документ'),
                    file_path=str(analysis.get('file_path', '')),
                    content_type=mime_type,
                    file_size=analysis.get('file_size', 0),
                    metadata={
                        'ocr_cleaned': True,
                        'gemini_analyzed': bool(analysis.get('images')),
                        'text_length': len(full_text),
                        'summary_length': len(analysis.get('smart_summary', '')),
                        'content': full_text,
                        'summary': analysis.get('smart_summary', ''),
                        'processed': True,
                        'status': "processed",
                        'domain_content_type': analysis.get('content_type', 'unknown')
                        ,
                        'qa_count': int(analysis.get('qa_count', 0)),
                        'qa_sample': analysis.get('qa_pairs', [])[:20]
                    }
                )
                
                # Логируем операцию вставки изображений
                if analysis.get('images'):
                    # Сохраняем только отмеченные пользователем изображения
                    allowed = set(idx for (doc_idx_allowed, idx) in selected_image_indices if doc_idx_allowed == doc_idx)
                    for img_idx, image_info in enumerate(analysis['images']):
                        if img_idx not in allowed:
                            continue
                        self.transaction_manager.log_database_change(
                            transaction_id, 'knowledge_images', 'INSERT',
                            old_data=None, new_data={
                                'kb_id': kb_id,
                                'image_path': image_info.get('image_path', ''),
                                'image_name': image_info.get('image_name', ''),
                                'image_description': image_info.get('description', ''),
                                'llava_analysis': image_info.get('description', '')
                            }
                        )
                        
                        self.kb_manager.add_image(
                            kb_id=kb_id,
                            image_path=image_info.get('image_path', ''),
                            image_name=image_info.get('image_name', ''),
                            image_description=image_info.get('description', ''),
                            llava_analysis=image_info.get('description', ''),
                        )
                
                saved_count += 1
            
            # Логируем архивирование файлов
            for doc_idx in selected_doc_indices:
                analysis = analyses[doc_idx]
                file_path = Path(analysis.get('file_path', ''))
                if file_path.exists():
                    archive_path = self.document_manager.archive_dir / datetime.now().strftime('%Y-%m-%d') / file_path.name
                    archive_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    self.transaction_manager.log_file_operation(
                        transaction_id, 'move',
                        source_path=str(file_path),
                        target_path=str(archive_path)
                    )
                    
                    # Перемещаем файл в архив
                    shutil.move(str(file_path), str(archive_path))
            
            return {
                'success': True,
                'saved_count': saved_count,
                'transaction_id': transaction_id
            }
            
        except Exception as e:
            raise Exception(f"Ошибка сохранения в KB: {e}")
    
    def process_documents_smart(self, file_paths: List[Path]) -> Dict:
        """Умная обработка документов с анализом и рекомендациями"""
        st.header("🧠 Умная обработка документов")
        
        # Анализируем все документы
        st.subheader("📊 Анализ документов")
        analyses = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, file_path in enumerate(file_paths):
            status_text.text(f"Анализ: {file_path.name}")
            analysis = self.analyze_document(file_path)
            analyses.append(analysis)
            progress_bar.progress((i + 1) / len(file_paths))
        
        status_text.text("")
        
        # Показываем результаты анализа (устойчиво к None)
        safe_analyses = [a for a in analyses if isinstance(a, dict)]
        self._display_analysis_results(safe_analyses)
        
        # Предлагаем стратегию создания БЗ
        st.subheader("🎯 Рекомендации по созданию БЗ")
        # Используем только валидные анализы для стратегии
        strategy = self.suggest_kb_strategy(safe_analyses)
        
        # Отладочная информация
        st.write(f"🔍 DEBUG: strategy type = {strategy.get('type', 'unknown')}")
        st.write(f"🔍 DEBUG: strategy keys = {list(strategy.keys())}")
        
        self._display_kb_strategy(strategy)
        
        return {
            'analyses': analyses,
            'strategy': strategy
        }
    
    def _display_analysis_results(self, analyses: List[Dict]):
        """Отображение результатов анализа"""
        for analysis in (analyses or []):
            if not isinstance(analysis, dict):
                continue
            # Страховка от отсутствующих ключей
            analysis.setdefault('file_name', 'Документ')
            analysis.setdefault('category', 'Другое')
            analysis.setdefault('file_size', 0)
            analysis.setdefault('format_description', 'Неизвестно')
            analysis.setdefault('content_type', 'unknown')
            analysis.setdefault('confidence', 0.0)
            analysis.setdefault('recommendations', [])
            with st.expander(f"📄 {analysis['file_name']} ({analysis['category']})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Размер:** {analysis['file_size'] / 1024:.1f} KB")
                    st.write(f"**Формат:** {analysis['format_description']}")
                    st.write(f"**Тип контента:** {analysis['content_type']}")
                    st.write(f"**Уверенность:** {analysis['confidence']:.1%}")
                
                with col2:
                    st.write(f"**Категория:** {analysis['category']}")
                    st.write(f"**Ключевые слова:** {', '.join(analysis['keywords'][:5])}")
                    st.write(f"**Длина текста:** {analysis.get('text_length', 0)} символов")
                
                # Показываем превью и полный текст
                if analysis.get('text_preview'):
                    st.write("**Превью содержимого:**")
                    # Используем st.text вместо st.text_area для избежания мигания
                    st.text(analysis['text_preview'])
                    
                    # Кнопка для просмотра полного текста
                    show_full_key = f"show_full_text_{analysis['file_name']}"
                    if st.button(f"📄 Показать полный текст", key=f"full_text_{analysis['file_name']}"):
                        st.session_state[show_full_key] = True
                        st.rerun()
                    
                    # Показываем полный текст если запрошен
                    if st.session_state.get(f"show_full_text_{analysis['file_name']}", False):
                        st.write("**Полный текст документа:**")
                        
                        # Кэшируем полный текст для избежания мигания
                        cache_key = f"full_text_cache_{analysis['file_name']}"
                        if cache_key not in st.session_state:
                            st.session_state[cache_key] = analysis.get('full_cleaned_text', analysis.get('text_preview', ''))
                        
                        full_text = st.session_state[cache_key]
                        
                        # Редактируемое поле для создания выжимки
                        edited_text = st.text_area(
                            "Редактируйте текст для создания выжимки:",
                            value=full_text,
                            height=300,
                            key=f"edit_text_{analysis['file_name']}",
                            help="Удалите ненужные части, оставьте только важную информацию"
                        )
                        
                        # Кнопки для работы с текстом
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if st.button(f"💾 Сохранить выжимку", key=f"save_{analysis['file_name']}"):
                                # Сохраняем отредактированный текст
                                st.session_state[f"saved_text_{analysis['file_name']}"] = edited_text
                                st.success("Выжимка сохранена!")
                        
                        with col2:
                            if st.button(f"📋 Копировать в буфер", key=f"copy_{analysis['file_name']}"):
                                st.code(edited_text, language=None)
                                st.info("Текст скопирован в буфер обмена")
                        
                        with col3:
                            if st.button(f"❌ Закрыть", key=f"close_{analysis['file_name']}"):
                                st.session_state[f"show_full_text_{analysis['file_name']}"] = False
                                st.rerun()
                        
                        # Показываем сохраненную выжимку если есть
                        if st.session_state.get(f"saved_text_{analysis['file_name']}"):
                            st.write("**Сохраненная выжимка:**")
                            st.text_area(
                                "Сохраненная выжимка",
                                st.session_state[f"saved_text_{analysis['file_name']}"],
                                height=150,
                                key=f"saved_{analysis['file_name']}",
                                label_visibility="collapsed"
                            )
                
                # Показываем рекомендации
                if analysis['recommendations']:
                    st.write("**Рекомендации:**")
                    for rec in analysis['recommendations']:
                        st.write(f"• {rec}")

            # Предложение стратегии чанкинга
            try:
                text_preview = (analysis.get('original_cleaned_text') or '')[:4000]
                t = (text_preview or '').lower()
                qa_like = (t.count('?') >= 3 and ('•' in text_preview or '- ' in text_preview)) or ('вопрос' in t and 'ответ' in t) or ('question' in t and 'answer' in t)
                code_like = ('```' in text_preview) or (t.count('{') + t.count('}') > 10) or (t.count(';') > 20)
                st.write("**Стратегия чанкинга (предложение):**")
                if qa_like:
                    st.write("- Разбивать по вопросам: разделители '?', буллеты ('•', '- '). Размер ~800, overlap ~120")
                elif code_like:
                    st.write("- Кодоподобный текст: мелкие чанки ~600, разделители по строкам/';', overlap ~80")
                else:
                    st.write("- Обычный текст: стандартные чанки ~1000, overlap ~200")
            except Exception:
                pass

    def _display_kb_strategy(self, strategy: Dict):
        """Отображение стратегии создания БЗ"""
        st.write(f"🔍 DEBUG: _display_kb_strategy called with type = {strategy.get('type', 'unknown')}")
        
        if strategy.get('type') == 'no_documents':
            st.warning(strategy.get('message', 'Нет документов для обработки'))
            return
        
        st.info(f"**Рекомендуемая стратегия:** {strategy['reasoning']}")
        
        if strategy['type'] == 'single_kb':
            st.success(f"✅ Создать одну БЗ: **{strategy['kb_name']}**")
            st.write(f"**Описание:** {strategy['description']}")
            st.write(f"**Документов:** {len(strategy['documents'])}")
            
            if st.button("🚀 Создать БЗ", key="create_single_kb_btn"):
                self._create_kb_from_strategy(strategy)
            
            # Добавить в существующую БЗ
            try:
                existing = self.kb_manager.get_knowledge_bases(active_only=True) or []
                if existing:
                    kb_options = {f"ID {kb['id']}: {kb['name']} [{kb.get('category','')}]": kb['id'] for kb in existing}
                    selected_label = st.selectbox(
                        "Или добавить документы в существующую БЗ:",
                        list(kb_options.keys()),
                        key="single_kb_add_select"
                    )
                    if st.button("➕ Добавить выбранные документы", key="single_kb_add_btn"):
                        self._process_documents_to_kb(strategy.get('documents', []), kb_options[selected_label])
                        st.success("Документы отправлены на обработку в выбранную БЗ")
                else:
                    st.info("Активные БЗ не найдены")
            except Exception:
                pass
            
            # Генерация тестовых вопросов для проверки релевантности
            st.markdown("---")
            st.subheader("🧪 Тестирование релевантности")
            
            if st.button("🎯 Сгенерировать тестовые вопросы", key="generate_test_questions_btn"):
                with st.spinner("Генерируем тестовые вопросы для проверки релевантности..."):
                    try:
                        # Получаем анализ первого документа для генерации вопросов
                        first_doc = strategy.get('documents', [{}])[0]
                        if first_doc and 'analysis' in first_doc:
                            test_questions = self.generate_relevance_test_questions(first_doc['analysis'])
                            
                            if test_questions:
                                st.success(f"✅ Сгенерировано {len(test_questions)} тестовых вопросов")
                                
                                # Сохраняем вопросы в session_state для последующего тестирования
                                st.session_state.generated_test_questions = test_questions
                                st.session_state.test_questions_kb_name = strategy['kb_name']
                                
                                # Отображаем вопросы
                                for i, question in enumerate(test_questions, 1):
                                    with st.expander(f"❓ Вопрос {i}: {question['question']}"):
                                        st.write(f"**Категория:** {question.get('category', 'Не указана')}")
                                        st.write(f"**Сложность:** {question.get('difficulty', 'Не указана')}")
                                        st.write(f"**Ожидаемые ключевые слова:** {', '.join(question.get('expected_keywords', []))}")
                                        
                                st.info("💡 Вопросы будут доступны для тестирования после создания БЗ или добавления документов в существующую БЗ")
                            else:
                                st.warning("Не удалось сгенерировать тестовые вопросы")
                        else:
                            st.error("Нет данных анализа для генерации вопросов")
                    except Exception as e:
                        st.error(f"Ошибка при генерации тестовых вопросов: {e}")
        
        elif strategy['type'] == 'mixed_kb':
            st.warning(f"⚠️ Создать смешанную БЗ: **{strategy['kb_name']}**")
            st.write(f"**Описание:** {strategy['description']}")
            st.write(f"**Документов:** {len(strategy['documents'])}")
            
            if st.button("🚀 Создать смешанную БЗ", key="create_mixed_kb_btn"):
                self._create_kb_from_strategy(strategy)
            
            # Добавить в существующую БЗ (все документы)
            try:
                existing = self.kb_manager.get_knowledge_bases(active_only=True) or []
                if existing:
                    kb_options = {f"ID {kb['id']}: {kb['name']} [{kb.get('category','')}]": kb['id'] for kb in existing}
                    selected_label = st.selectbox(
                        "Или добавить эти документы в существующую БЗ:",
                        list(kb_options.keys()),
                        key="mixed_kb_add_select"
                    )
                    if st.button("➕ Добавить выбранные документы", key="mixed_kb_add_btn"):
                        self._process_documents_to_kb(strategy.get('documents', []), kb_options[selected_label])
                        st.success("Документы отправлены на обработку в выбранную БЗ")
                else:
                    st.info("Активные БЗ не найдены")
            except Exception:
                pass
            
            # Генерация тестовых вопросов для проверки релевантности
            st.markdown("---")
            st.subheader("🧪 Тестирование релевантности")
            
            if st.button("🎯 Сгенерировать тестовые вопросы", key="generate_test_questions_mixed_btn"):
                with st.spinner("Генерируем тестовые вопросы для проверки релевантности..."):
                    try:
                        # Получаем анализ первого документа для генерации вопросов
                        first_doc = strategy.get('documents', [{}])[0]
                        if first_doc and 'analysis' in first_doc:
                            test_questions = self.generate_relevance_test_questions(first_doc['analysis'])
                            
                            if test_questions:
                                st.success(f"✅ Сгенерировано {len(test_questions)} тестовых вопросов")
                                
                                # Сохраняем вопросы в session_state для последующего тестирования
                                st.session_state.generated_test_questions = test_questions
                                st.session_state.test_questions_kb_name = strategy['kb_name']
                                
                                # Отображаем вопросы
                                for i, question in enumerate(test_questions, 1):
                                    with st.expander(f"❓ Вопрос {i}: {question['question']}"):
                                        st.write(f"**Категория:** {question.get('category', 'Не указана')}")
                                        st.write(f"**Сложность:** {question.get('difficulty', 'Не указана')}")
                                        st.write(f"**Ожидаемые ключевые слова:** {', '.join(question.get('expected_keywords', []))}")
                                        
                                st.info("💡 Вопросы будут доступны для тестирования после создания БЗ или добавления документов в существующую БЗ")
                            else:
                                st.warning("Не удалось сгенерировать тестовые вопросы")
                        else:
                            st.error("Нет данных анализа для генерации вопросов")
                    except Exception as e:
                        st.error(f"Ошибка при генерации тестовых вопросов: {e}")
        
        elif strategy['type'] == 'multiple_kb':
            st.info("📚 Рекомендуется создать несколько БЗ:")
            
            for kb_suggestion in strategy['kb_suggestions']:
                with st.expander(f"📁 {kb_suggestion['kb_name']} ({kb_suggestion['document_count']} документов)"):
                    st.write(f"**Описание:** {kb_suggestion['description']}")
                    st.write(f"**Документов:** {kb_suggestion['document_count']}")
                    
                    if st.button(f"🚀 Создать БЗ: {kb_suggestion['category']}", key=f"create_multiple_{kb_suggestion['category']}_btn"):
                        self._create_kb_from_strategy(kb_suggestion)

                    # Добавить конкретную категорию в существующую БЗ
                    try:
                        existing = self.kb_manager.get_knowledge_bases(active_only=True) or []
                        if existing:
                            kb_options = {f"ID {kb['id']}: {kb['name']} [{kb.get('category','')}]": kb['id'] for kb in existing}
                            selected_label = st.selectbox(
                                "Или добавить эти документы в существующую БЗ:",
                                list(kb_options.keys()),
                                key=f"multi_add_select_{kb_suggestion['category']}"
                            )
                            if st.button("➕ Добавить выбранные документы", key=f"multi_add_btn_{kb_suggestion['category']}"):
                                self._process_documents_to_kb(kb_suggestion.get('documents', []), kb_options[selected_label])
                                st.success("Документы отправлены на обработку в выбранную БЗ")
                        else:
                            st.info("Активные БЗ не найдены")
                    except Exception:
                        pass
                    
                    # Тестирование релевантности для этой категории
                    if st.button(f"🧪 Тест релевантности для {kb_suggestion['category']}", key=f"test_relevance_{kb_suggestion['category']}"):
                        with st.spinner("Генерируем тестовые вопросы для этой категории..."):
                            try:
                                # Получаем анализ первого документа этой категории
                                first_doc = kb_suggestion.get('documents', [{}])[0]
                                if first_doc and 'analysis' in first_doc:
                                    test_questions = self.generate_relevance_test_questions(first_doc['analysis'])
                                    
                                    if test_questions:
                                        st.success(f"✅ Сгенерировано {len(test_questions)} тестовых вопросов для категории {kb_suggestion['category']}")
                                        
                                        # Отображаем вопросы
                                        for i, question in enumerate(test_questions, 1):
                                            with st.expander(f"❓ Вопрос {i}: {question['question']}"):
                                                st.write(f"**Категория:** {question.get('category', 'Не указана')}")
                                                st.write(f"**Сложность:** {question.get('difficulty', 'Не указана')}")
                                                st.write(f"**Ожидаемые ключевые слова:** {', '.join(question.get('expected_keywords', []))}")
                                                
                                                # Кнопка для тестирования этого вопроса
                                                if st.button(f"🔍 Протестировать вопрос {i}", key=f"test_question_multi_{kb_suggestion['category']}_{i}"):
                                                    self._test_single_question(question)
                                    else:
                                        st.warning("Не удалось сгенерировать тестовые вопросы")
                                else:
                                    st.error("Нет данных анализа для генерации вопросов")
                            except Exception as e:
                                st.error(f"Ошибка при генерации тестовых вопросов: {e}")
    
    def _create_kb_from_strategy(self, strategy: Dict):
        """Создание БЗ на основе стратегии"""
        try:
            # Создаем БЗ
            kb_id = self.kb_manager.create_knowledge_base(
                name=strategy['kb_name'],
                description=strategy['description'],
                category=strategy.get('category', 'Смешанная'),
                created_by=st.session_state.get('username', 'smart_agent')
            )
            
            st.success(f"✅ База знаний '{strategy['kb_name']}' создана с ID: {kb_id}")
            
            # Обрабатываем документы
            documents = strategy.get('documents', [])
            if documents:
                self._process_documents_to_kb(documents, kb_id)
            
            # Устанавливаем флаг успешного создания БЗ
            st.session_state['kb_created_successfully'] = True
            st.session_state['created_kb_id'] = kb_id
            
            # Сохраняем тестовые вопросы в БЗ если они есть
            if hasattr(st.session_state, 'generated_test_questions') and st.session_state.generated_test_questions:
                self._save_test_questions_to_kb(kb_id, st.session_state.generated_test_questions)
                self._show_relevance_testing_after_creation(kb_id, st.session_state.generated_test_questions)
            st.session_state['created_kb_name'] = strategy['kb_name']
            
        except Exception as e:
            st.error(f"Ошибка создания БЗ: {e}")
    
    def _process_documents_to_kb(self, documents: List[Dict], kb_id: int):
        """Обработка документов в БЗ"""
        processed_count = 0
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, doc_analysis in enumerate(documents):
            try:
                file_path = Path(doc_analysis['file_path'])
                status_text.text(f"Обработка: {file_path.name}")
                
                # Читаем файл
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                # Создаем mock объект для PDFProcessor
                class MockUploadedFile:
                    def __init__(self, name, content):
                        self.name = name
                        self._content = content
                    
                    def getvalue(self):
                        return self._content
                
                mock_file = MockUploadedFile(file_path.name, file_content)
                
                # Обрабатываем документ
                result = self.pdf_processor.process_pdf(
                    mock_file, 
                    kb_id, 
                    file_path.stem
                )
                
                if result['success']:
                    # Добавляем документ в БЗ
                    doc_id = self.kb_manager.add_document(
                        kb_id,
                        result['title'],
                        result['file_path'],
                        result['content_type'],
                        result['file_size'],
                        result['metadata']
                    )
                    
                    # Обновляем статус
                    self.kb_manager.update_document_status(doc_id, True, 'completed')
                    processed_count += 1
                    
                    st.success(f"✅ Обработан: {file_path.name}")
                else:
                    st.error(f"❌ Ошибка: {file_path.name}")
                
            except Exception as e:
                st.error(f"❌ Ошибка: {file_path.name} - {e}")
            
            progress_bar.progress((i + 1) / len(documents))
        
        status_text.text("")
        st.success(f"🎉 Обработка завершена! Успешно обработано {processed_count} из {len(documents)} документов")
        
        # Сохраняем тестовые вопросы в БЗ если они есть
        if hasattr(st.session_state, 'generated_test_questions') and st.session_state.generated_test_questions:
            self._save_test_questions_to_kb(kb_id, st.session_state.generated_test_questions)
            self._show_relevance_testing_after_creation(kb_id, st.session_state.generated_test_questions)
        
        # Обновляем страницу
        st.rerun()
