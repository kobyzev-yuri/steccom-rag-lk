"""
Tests for СТЭККОМ Billing API
"""

import pytest
import httpx
import json
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from api.main import app

client = TestClient(app)

# Test data
TEST_USER = {
    "username": "staff1",
    "password": "staff123"
}

TEST_USER_REGULAR = {
    "username": "user1", 
    "password": "user123"
}

class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_login_success(self):
        """Test successful login"""
        response = client.post("/auth/login", json=TEST_USER)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user_info" in data
        assert data["user_info"]["username"] == "staff1"
        assert data["user_info"]["role"] == "staff"
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = client.post("/auth/login", json={
            "username": "invalid",
            "password": "invalid"
        })
        assert response.status_code == 401
    
    def test_get_current_user(self):
        """Test getting current user info"""
        # First login
        login_response = client.post("/auth/login", json=TEST_USER)
        token = login_response.json()["access_token"]
        
        # Get user info
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["username"] == "staff1"
        assert data["role"] == "staff"
    
    def test_unauthorized_access(self):
        """Test accessing protected endpoint without token"""
        response = client.get("/auth/me")
        assert response.status_code == 401

class TestAgreements:
    """Test agreements endpoints"""
    
    def test_get_current_agreements(self):
        """Test getting current agreements"""
        # Login
        login_response = client.post("/auth/login", json=TEST_USER)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get agreements
        response = client.get("/agreements/current", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_agreements_history(self):
        """Test getting agreements history"""
        # Login
        login_response = client.post("/auth/login", json=TEST_USER)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get history
        response = client.get("/agreements/history", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

class TestDevices:
    """Test devices endpoints"""
    
    def test_get_devices(self):
        """Test getting devices"""
        # Login
        login_response = client.post("/auth/login", json=TEST_USER)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get devices
        response = client.get("/devices", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

class TestReports:
    """Test reports endpoints"""
    
    def test_get_available_reports(self):
        """Test getting available reports list"""
        response = client.get("/reports/available")
        assert response.status_code == 200
        
        data = response.json()
        assert "reports" in data
        assert isinstance(data["reports"], list)
        assert len(data["reports"]) > 0
    
    def test_get_standard_report(self):
        """Test getting standard report"""
        # Login
        login_response = client.post("/auth/login", json=TEST_USER)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get report
        report_data = {"report_type": "current_agreement"}
        response = client.post("/reports/standard", json=report_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "report_type" in data
        assert "data" in data
        assert "total_records" in data
    
    def test_get_invalid_report(self):
        """Test getting invalid report type"""
        # Login
        login_response = client.post("/auth/login", json=TEST_USER)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get invalid report
        report_data = {"report_type": "invalid_report"}
        response = client.post("/reports/standard", json=report_data, headers=headers)
        assert response.status_code == 400

class TestWikiIntegration:
    """Test wiki integration endpoints"""
    
    def test_test_wiki_connection_unauthorized(self):
        """Test wiki connection without staff role"""
        # Login as regular user
        login_response = client.post("/auth/login", json=TEST_USER_REGULAR)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to test wiki connection
        response = client.get(
            "/wiki/test-connection",
            params={
                "wiki_url": "http://localhost:8080/w/api.php",
                "username": "test",
                "password": "test"
            },
            headers=headers
        )
        assert response.status_code == 403  # Forbidden for non-staff
    
    def test_publish_to_wiki_unauthorized(self):
        """Test wiki publishing without staff role"""
        # Login as regular user
        login_response = client.post("/auth/login", json=TEST_USER_REGULAR)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to publish to wiki
        wiki_data = {
            "wiki_url": "http://localhost:8080/w/api.php",
            "username": "test",
            "password": "test"
        }
        response = client.post("/wiki/publish", json=wiki_data, headers=headers)
        assert response.status_code == 403  # Forbidden for non-staff

class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "unhealthy"]

class TestRoot:
    """Test root endpoint"""
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert data["message"] == "СТЭККОМ Billing API"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
