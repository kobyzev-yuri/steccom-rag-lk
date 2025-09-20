#!/usr/bin/env python3
"""
Script to update existing legacy KB files with extracted PDF text
"""

import json
import os
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Use PyPDF2 directly instead of PDFProcessor to avoid fitz conflicts
import PyPDF2

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using PyPDF2"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
    except Exception as e:
        print(f"❌ Error reading PDF {pdf_path}: {e}")
        return ""

def update_legacy_kb_file(kb_path, pdf_path):
    """Update legacy KB file with extracted PDF text"""
    
    # Read existing KB file
    with open(kb_path, 'r', encoding='utf-8') as f:
        kb_data = json.load(f)
    
    if not kb_data or len(kb_data) == 0:
        print(f"❌ Empty KB file: {kb_path}")
        return False
    
    # Extract text from PDF
    extracted_text = extract_text_from_pdf(pdf_path)
    
    if extracted_text and len(extracted_text.strip()) > 50:
        # Create content with extracted text
        content = [
            {"title": "Содержимое документа", "text": extracted_text},
            {"title": "Исходный документ", "text": f"См. в {pdf_path}"}
        ]
        print(f"✅ Извлечено {len(extracted_text)} символов из {pdf_path}")
    else:
        # Keep existing content
        content = kb_data[0]["content"]
        print(f"⚠️ Не удалось извлечь текст из {pdf_path}, оставлен исходный контент")
    
    # Update content
    kb_data[0]["content"] = content
    
    # Write updated KB file
    with open(kb_path, 'w', encoding='utf-8') as f:
        json.dump(kb_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Обновлен KB файл: {kb_path}")
    return True

def main():
    # List of legacy KB files and their corresponding PDFs (only existing ones)
    mappings = [
        ("docs/kb/legacy_reglament_commonservices.json", "data/uploads/reg_07032015.pdf"),
    ]
    
    # Check which PDF files exist and create KB files for them
    pdf_files = [
        ("docs/kb/legacy_reglament_sbd.json", "data/uploads/reg_sbd.pdf"),
        ("docs/kb/legacy_reglament_sbd_en.json", "data/uploads/reg_sbd_en.pdf"),
        ("docs/kb/legacy_reglament_monitoring.json", "data/uploads/reg_monitor_16112013.pdf"),
        ("docs/kb/legacy_reglament_gpstrack.json", "data/uploads/reg_gpstrack_14042014.pdf"),
    ]
    
    # Add PDF files that exist but don't have KB files yet
    for kb_file, pdf_file in pdf_files:
        if os.path.exists(pdf_file) and not os.path.exists(kb_file):
            print(f"📄 Создание нового KB файла для {pdf_file}...")
            # Create basic KB structure
            kb_data = [{
                "title": f"Регламент {Path(pdf_file).stem}",
                "audience": ["user", "admin"],
                "scope": ["legacy_billing"],
                "status": "reference",
                "source": {"file": pdf_file, "pointer": ""},
                "content": [
                    {"title": f"Регламент {Path(pdf_file).stem}", "text": f"См. в {pdf_file}."}
                ]
            }]
            
            # Create directory if needed
            os.makedirs("docs/kb", exist_ok=True)
            
            # Write KB file
            with open(kb_file, 'w', encoding='utf-8') as f:
                json.dump(kb_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Создан KB файл: {kb_file}")
            mappings.append((kb_file, pdf_file))
    
    # Process all mappings
    for kb_file, pdf_file in mappings:
        if os.path.exists(kb_file) and os.path.exists(pdf_file):
            print(f"🔄 Обновление {kb_file} с текстом из {pdf_file}...")
            update_legacy_kb_file(kb_file, pdf_file)
            print()
        else:
            print(f"⚠️ Пропуск: {kb_file} или {pdf_file} не найден")

if __name__ == "__main__":
    main()
