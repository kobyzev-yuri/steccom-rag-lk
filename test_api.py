#!/usr/bin/env python3
"""
Test script for STECCOM API
"""

import requests
import json
import time
from typing import Dict, Any

API_BASE_URL = "http://localhost:8000"

def test_endpoint(endpoint: str, method: str = "GET", data: Dict[Any, Any] = None, headers: Dict[str, str] = None) -> Dict[Any, Any]:
    """Test an API endpoint"""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "status_code": getattr(e.response, 'status_code', None)}

def main():
    """Main test function"""
    print("🧪 Testing STECCOM API with Token Authentication")
    print("="*60)
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    result = test_endpoint("/health")
    print(f"   Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # Test 2: Root endpoint
    print("\n2. Testing root endpoint...")
    result = test_endpoint("/")
    print(f"   Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # Test 3: Login and get token
    print("\n3. Testing login and token generation...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    result = test_endpoint("/auth/login", "POST", login_data)
    print(f"   Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # Extract token for authenticated requests
    token = None
    if "error" not in result and result.get("success"):
        token = result.get("token")
        print(f"   ✅ Token received: {token[:20]}...")
        
        # Set up headers for authenticated requests
        auth_headers = {"Authorization": f"Bearer {token}"}
    else:
        print("   ❌ Login failed, skipping authenticated tests")
        auth_headers = None
    
    # Test 4: Token info
    if token:
        print("\n4. Testing token info...")
        result = test_endpoint("/auth/token-info", "GET", headers=auth_headers)
        print(f"   Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # Test 5: Current user info
    if token:
        print("\n5. Testing current user info...")
        result = test_endpoint("/users/me", "GET", headers=auth_headers)
        print(f"   Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # Test 6: Database schema (no auth required)
    print("\n6. Testing database schema...")
    result = test_endpoint("/database/schema")
    if "error" not in result:
        print(f"   Schema retrieved successfully (length: {len(result.get('schema', ''))})")
    else:
        print(f"   Error: {result['error']}")
    
    # Test 7: SQL generation (requires auth)
    if token:
        print("\n7. Testing SQL generation...")
        sql_data = {
            "question": "Покажи все устройства"
        }
        result = test_endpoint("/sql/generate", "POST", sql_data, auth_headers)
        print(f"   Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # Test 8: RAG query (requires auth)
    if token:
        print("\n8. Testing RAG query...")
        rag_data = {
            "question": "Как работает система биллинга?",
            "role": "user"
        }
        result = test_endpoint("/rag/query", "POST", rag_data, auth_headers)
        print(f"   Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # Test 9: Knowledge bases list (no auth required)
    print("\n9. Testing knowledge bases list...")
    result = test_endpoint("/rag/knowledge-bases")
    print(f"   Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # Test 10: Standard reports list (no auth required)
    print("\n10. Testing standard reports list...")
    result = test_endpoint("/reports/standard")
    print(f"   Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # Test 11: Execute standard report (requires auth)
    if token:
        print("\n11. Testing standard report execution...")
        result = test_endpoint("/reports/standard/My%20monthly%20traffic", "GET", headers=auth_headers)
        print(f"   Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # Test 12: Session state (requires auth)
    if token:
        print("\n12. Testing session state...")
        result = test_endpoint("/session/state", "GET", headers=auth_headers)
        print(f"   Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # Test 13: Logout (requires auth)
    if token:
        print("\n13. Testing logout...")
        result = test_endpoint("/auth/logout", "POST", headers=auth_headers)
        print(f"   Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    print("\n✅ API testing completed!")

if __name__ == "__main__":
    main()
