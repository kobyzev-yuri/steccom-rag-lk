#!/usr/bin/env python3
"""
Test script for STECCOM API
"""

import requests
import json
import time
from typing import Dict, Any

API_BASE_URL = "http://localhost:8000"

def test_endpoint(endpoint: str, method: str = "GET", data: Dict[Any, Any] = None) -> Dict[Any, Any]:
    """Test an API endpoint"""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "status_code": getattr(e.response, 'status_code', None)}

def main():
    """Main test function"""
    print("🧪 Testing STECCOM API")
    print("="*50)
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    result = test_endpoint("/health")
    print(f"   Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # Test 2: Root endpoint
    print("\n2. Testing root endpoint...")
    result = test_endpoint("/")
    print(f"   Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # Test 3: Database schema
    print("\n3. Testing database schema...")
    result = test_endpoint("/database/schema")
    if "error" not in result:
        print(f"   Schema retrieved successfully (length: {len(result.get('schema', ''))})")
    else:
        print(f"   Error: {result['error']}")
    
    # Test 4: Login
    print("\n4. Testing login...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    result = test_endpoint("/auth/login", "POST", login_data)
    print(f"   Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # Test 5: SQL generation
    print("\n5. Testing SQL generation...")
    sql_data = {
        "question": "Покажи все устройства",
        "username": "admin"
    }
    result = test_endpoint("/sql/generate", "POST", sql_data)
    print(f"   Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # Test 6: RAG query
    print("\n6. Testing RAG query...")
    rag_data = {
        "question": "Как работает система биллинга?",
        "role": "user"
    }
    result = test_endpoint("/rag/query", "POST", rag_data)
    print(f"   Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # Test 7: Knowledge bases list
    print("\n7. Testing knowledge bases list...")
    result = test_endpoint("/rag/knowledge-bases")
    print(f"   Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # Test 8: Standard reports list
    print("\n8. Testing standard reports list...")
    result = test_endpoint("/reports/standard")
    print(f"   Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # Test 9: Execute standard report
    print("\n9. Testing standard report execution...")
    result = test_endpoint("/reports/standard/My%20monthly%20traffic", "GET")
    print(f"   Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # Test 10: CSV export
    print("\n10. Testing CSV export...")
    result = test_endpoint("/export/csv?sql_query=SELECT%20*%20FROM%20users%20LIMIT%205&filename=test.csv", "GET")
    if "error" not in result:
        print(f"   CSV export successful (length: {len(str(result))})")
    else:
        print(f"   Error: {result['error']}")
    
    # Test 11: Chart creation
    print("\n11. Testing chart creation...")
    chart_data = [
        {"month": "2025-01", "usage": 100},
        {"month": "2025-02", "usage": 150},
        {"month": "2025-03", "usage": 200}
    ]
    result = test_endpoint("/charts/create", "POST", {
        "data": chart_data,
        "chart_type": "line",
        "title": "Test Chart"
    })
    print(f"   Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # Test 12: Session state
    print("\n12. Testing session state...")
    result = test_endpoint("/session/state", "GET")
    print(f"   Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    print("\n✅ API testing completed!")

if __name__ == "__main__":
    main()
