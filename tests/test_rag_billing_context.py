#!/usr/bin/env python3
"""
Unit tests for RAG billing context accuracy.
Tests both gpt-4o (ProxyAPI) and qwen (Ollama) models.
"""

import os
import sys
import time
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.rag.multi_kb_rag import MultiKBRAG


class TestRAGBillingContext:
    """Test RAG system with billing-specific questions."""
    
    @pytest.fixture(autouse=True)
    def setup_rag(self):
        """Initialize RAG system for each test."""
        self.rag = MultiKBRAG()
        # Ensure we have knowledge bases loaded
        assert len(self.rag.vectorstores) > 0, "No knowledge bases loaded"
    
    def test_proportional_traffic_calculation_gpt4o(self):
        """Test gpt-4o understanding of proportional traffic calculation."""
        question = "Как рассчитывается включенный трафик при подключении в середине месяца?"
        
        # Set gpt-4o via ProxyAPI
        self.rag.chat_provider = "proxyapi"
        self.rag.chat_model_name = "gpt-4o"
        self.rag.temperature = 0.0
        
        start_time = time.time()
        result = self.rag.ask_question(question)
        response_time = time.time() - start_time
        
        answer = result.get("answer", "")
        sources = result.get("sources", [])
        
        print(f"\n=== GPT-4o Response (ProxyAPI) ===")
        print(f"Question: {question}")
        print(f"Response time: {response_time:.2f}s")
        print(f"Answer: {answer}")
        print(f"Sources: {len(sources)} found")
        
        # Verify response contains key billing concepts
        assert "пропорционально" in answer.lower(), "Response should mention proportional calculation"
        assert "активных дней" in answer.lower(), "Response should mention active days"
        assert "финансовый период" in answer.lower(), "Response should mention financial period"
        assert response_time < 30, "Response should be fast (< 30s)"
        
        return answer
    
    def test_proportional_traffic_calculation_qwen(self):
        """Test qwen understanding of proportional traffic calculation."""
        question = "Как рассчитывается включенный трафик при подключении в середине месяца?"
        
        # Set qwen via Ollama
        self.rag.chat_provider = "ollama"
        self.rag.chat_model_name = "qwen2.5:1.5b"
        self.rag.temperature = 0.0
        
        start_time = time.time()
        result = self.rag.ask_question(question)
        response_time = time.time() - start_time
        
        answer = result.get("answer", "")
        sources = result.get("sources", [])
        
        print(f"\n=== Qwen Response (Ollama) ===")
        print(f"Question: {question}")
        print(f"Response time: {response_time:.2f}s")
        print(f"Answer: {answer}")
        print(f"Sources: {len(sources)} found")
        
        # Verify response contains key billing concepts
        assert "пропорционально" in answer.lower(), "Response should mention proportional calculation"
        assert "активных дней" in answer.lower(), "Response should mention active days"
        assert response_time < 15, "Response should be fast (< 15s)"
        
        return answer
    
    def test_deactivation_fee_structure_gpt4o(self):
        """Test gpt-4o understanding of deactivation fee structure."""
        question = "Какие правила действуют при деактивации терминала в течение месяца?"
        
        # Set gpt-4o via ProxyAPI
        self.rag.chat_provider = "proxyapi"
        self.rag.chat_model_name = "gpt-4o"
        self.rag.temperature = 0.0
        
        start_time = time.time()
        result = self.rag.ask_question(question)
        response_time = time.time() - start_time
        
        answer = result.get("answer", "")
        sources = result.get("sources", [])
        
        print(f"\n=== GPT-4o Response (ProxyAPI) ===")
        print(f"Question: {question}")
        print(f"Response time: {response_time:.2f}s")
        print(f"Answer: {answer}")
        print(f"Sources: {len(sources)} found")
        
        # Verify response contains deactivation rules
        assert "деактивац" in answer.lower(), "Response should mention deactivation"
        assert "месяц" in answer.lower(), "Response should mention monthly limits"
        assert "плата" in answer.lower(), "Response should mention fees"
        assert response_time < 30, "Response should be fast (< 30s)"
        
        return answer
    
    def test_traffic_tarification_rules_qwen(self):
        """Test qwen understanding of traffic tarification rules."""
        question = "Как тарифицируется трафик электронных сообщений и когда он попадает в счет?"
        
        # Set qwen via Ollama
        self.rag.chat_provider = "ollama"
        self.rag.chat_model_name = "qwen2.5:1.5b"
        self.rag.temperature = 0.0
        
        start_time = time.time()
        result = self.rag.ask_question(question)
        response_time = time.time() - start_time
        
        answer = result.get("answer", "")
        sources = result.get("sources", [])
        
        print(f"\n=== Qwen Response (Ollama) ===")
        print(f"Question: {question}")
        print(f"Response time: {response_time:.2f}s")
        print(f"Answer: {answer}")
        print(f"Sources: {len(sources)} found")
        
        # Verify response contains tarification rules
        assert "тарифицир" in answer.lower(), "Response should mention tarification"
        assert "следующий день" in answer.lower(), "Response should mention next-day processing"
        assert "финансовый период" in answer.lower(), "Response should mention financial period"
        assert response_time < 15, "Response should be fast (< 15s)"
        
        return answer
    
    def test_kilobyte_definition_gpt4o(self):
        """Test gpt-4o understanding of kilobyte definition."""
        question = "Сколько байт в одном килобайте согласно тарифам?"
        
        # Set gpt-4o via ProxyAPI
        self.rag.chat_provider = "proxyapi"
        self.rag.chat_model_name = "gpt-4o"
        self.rag.temperature = 0.0
        
        start_time = time.time()
        result = self.rag.ask_question(question)
        response_time = time.time() - start_time
        
        answer = result.get("answer", "")
        sources = result.get("sources", [])
        
        print(f"\n=== GPT-4o Response (ProxyAPI) ===")
        print(f"Question: {question}")
        print(f"Response time: {response_time:.2f}s")
        print(f"Answer: {answer}")
        print(f"Sources: {len(sources)} found")
        
        # Verify response contains exact kilobyte definition
        assert "1000" in answer, "Response should mention 1000 bytes"
        assert "байт" in answer.lower(), "Response should mention bytes"
        assert response_time < 30, "Response should be fast (< 30s)"
        
        return answer


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
