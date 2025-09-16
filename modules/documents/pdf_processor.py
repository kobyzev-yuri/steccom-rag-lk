"""
PDF Document Processing Module
Обработка PDF документов для базы знаний
"""

import streamlit as st
import PyPDF2
import fitz  # PyMuPDF
from typing import List, Dict, Optional
import os
from pathlib import Path
import hashlib
import json

class PDFProcessor:
    def __init__(self, upload_dir: str = "data/uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_text_pypdf2(self, pdf_path: str) -> str:
        """Extract text using PyPDF2"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            st.error(f"Ошибка PyPDF2: {e}")
            return ""
    
    def extract_text_pymupdf(self, pdf_path: str) -> str:
        """Extract text using PyMuPDF (faster and more accurate)"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text() + "\n"
            doc.close()
            return text
        except Exception as e:
            st.error(f"Ошибка PyMuPDF: {e}")
            return ""
    
    def extract_text(self, pdf_path: str, method: str = "pymupdf") -> str:
        """Extract text from PDF using specified method"""
        if method == "pymupdf":
            return self.extract_text_pymupdf(pdf_path)
        elif method == "pypdf2":
            return self.extract_text_pypdf2(pdf_path)
        else:
            # Try PyMuPDF first, fallback to PyPDF2
            text = self.extract_text_pymupdf(pdf_path)
            if not text.strip():
                text = self.extract_text_pypdf2(pdf_path)
            return text
    
    def get_pdf_metadata(self, pdf_path: str) -> Dict:
        """Extract PDF metadata"""
        try:
            doc = fitz.open(pdf_path)
            metadata = doc.metadata
            doc.close()
            
            return {
                'title': metadata.get('title', ''),
                'author': metadata.get('author', ''),
                'subject': metadata.get('subject', ''),
                'creator': metadata.get('creator', ''),
                'producer': metadata.get('producer', ''),
                'creation_date': metadata.get('creationDate', ''),
                'modification_date': metadata.get('modDate', ''),
                'pages': len(doc)
            }
        except Exception as e:
            st.warning(f"Не удалось извлечь метаданные: {e}")
            return {}
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def process_pdf(self, uploaded_file, kb_id: int, title: str = None) -> Dict:
        """Process uploaded PDF file"""
        try:
            # Generate filename
            file_hash = hashlib.md5(uploaded_file.getvalue()).hexdigest()
            file_extension = Path(uploaded_file.name).suffix
            filename = f"{file_hash}{file_extension}"
            file_path = self.upload_dir / filename
            
            # Save file
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            # Extract text
            text_content = self.extract_text(str(file_path))
            
            # Get metadata
            metadata = self.get_pdf_metadata(str(file_path))
            metadata.update({
                'original_filename': uploaded_file.name,
                'file_hash': file_hash,
                'kb_id': kb_id,
                'extraction_method': 'pymupdf'
            })
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            return {
                'success': True,
                'file_path': str(file_path),
                'text_content': text_content,
                'metadata': metadata,
                'file_size': file_size,
                'title': title or uploaded_file.name,
                'content_type': 'application/pdf'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def split_text_into_chunks(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        if not text.strip():
            return []
        
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk.strip())
        
        return chunks
    
    def extract_tables_from_pdf(self, pdf_path: str) -> List[Dict]:
        """Extract tables from PDF (basic implementation)"""
        try:
            doc = fitz.open(pdf_path)
            tables = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # This is a simplified table extraction
                # In production, you might want to use more sophisticated methods
                text = page.get_text()
                
                # Look for table-like patterns (lines with multiple columns)
                lines = text.split('\n')
                for line in lines:
                    if '\t' in line or '  ' in line:
                        # Potential table row
                        cells = [cell.strip() for cell in line.split('\t') if cell.strip()]
                        if len(cells) > 1:
                            tables.append({
                                'page': page_num + 1,
                                'row': cells
                            })
            
            doc.close()
            return tables
            
        except Exception as e:
            st.warning(f"Ошибка извлечения таблиц: {e}")
            return []
    
    def validate_pdf(self, file_path: str) -> Dict:
        """Validate PDF file"""
        try:
            doc = fitz.open(file_path)
            page_count = len(doc)
            doc.close()
            
            return {
                'valid': True,
                'pages': page_count,
                'readable': True
            }
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'readable': False
            }
