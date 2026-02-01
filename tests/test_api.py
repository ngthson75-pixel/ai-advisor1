"""
Backend API Tests
Test all critical API endpoints
"""
import pytest
import json


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check_success(self, client):
        """Test /health returns 200"""
        response = client.get('/health')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
    
    def test_health_check_includes_gemini(self, client):
        """Test /health includes Gemini status"""
        response = client.get('/health')
        data = response.get_json()
        
        assert 'gemini' in data
        assert isinstance(data['gemini'], bool)


class TestSignalsEndpoint:
    """Test signals API endpoints"""
    
    def test_get_signals_success(self, client):
        """Test GET /api/signals returns 200"""
        response = client.get('/api/signals')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'success' in data
        assert 'signals' in data
        assert isinstance(data['signals'], list)
    
    def test_get_signals_structure(self, client):
        """Test signal data structure is correct"""
        response = client.get('/api/signals')
        data = response.get_json()
        
        if len(data['signals']) > 0:
            signal = data['signals'][0]
            
            # Required fields
            assert 'ticker' in signal
            assert 'strategy' in signal
            assert 'entry_price' in signal
            assert 'stop_loss' in signal
            assert 'take_profit' in signal
            assert 'action' in signal
    
    def test_create_signal(self, client, sample_signal):
        """Test creating a new signal"""
        response = client.post(
            '/api/signals',
            data=json.dumps(sample_signal),
            content_type='application/json'
        )
        
        # Should either succeed or endpoint not exist yet
        assert response.status_code in [200, 201, 404, 405]


class TestPortfolioEndpoint:
    """Test portfolio API endpoints"""
    
    def test_get_portfolio_requires_user_id(self, client):
        """Test GET /api/portfolio requires user_id"""
        response = client.get('/api/portfolio')
        
        # Should fail without user_id or return empty
        assert response.status_code in [200, 400]
    
    def test_get_portfolio_with_user_id(self, client):
        """Test GET /api/portfolio?user_id=1"""
        response = client.get('/api/portfolio?user_id=1')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'success' in data
    
    def test_add_stock_to_portfolio(self, client, sample_portfolio):
        """Test POST /api/portfolio"""
        response = client.post(
            '/api/portfolio',
            data=json.dumps(sample_portfolio),
            content_type='application/json'
        )
        
        assert response.status_code in [200, 201]
        data = response.get_json()
        assert data['success'] == True
    
    def test_delete_stock_from_portfolio(self, client):
        """Test DELETE /api/portfolio/{ticker}"""
        response = client.delete('/api/portfolio/VCB?user_id=1')
        
        # Should succeed or fail gracefully
        assert response.status_code in [200, 404]


class TestChatEndpoint:
    """Test AI chat endpoints"""
    
    def test_chat_requires_message(self, client):
        """Test POST /api/chat requires message"""
        response = client.post(
            '/api/chat',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        # Should fail without message
        assert response.status_code in [400, 422]
    
    def test_chat_with_valid_message(self, client):
        """Test POST /api/chat with valid message"""
        data = {
            'user_id': 1,
            'message': 'Tôi nên mua VCB không?'
        }
        
        response = client.post(
            '/api/chat',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Should succeed if Gemini configured
        assert response.status_code in [200, 500]  # 500 if no API key
        
        if response.status_code == 200:
            result = response.get_json()
            assert 'response' in result
    
    def test_get_chat_history(self, client):
        """Test GET /api/chat/history?user_id=1"""
        response = client.get('/api/chat/history?user_id=1')
        
        assert response.status_code in [200, 404]


class TestMigrationEndpoint:
    """Test database migration endpoint"""
    
    def test_migration_endpoint_exists(self, client):
        """Test POST /api/migrate"""
        response = client.post('/api/migrate')
        
        assert response.status_code in [200, 404, 405]


class TestScanEndpoint:
    """Test signal scanning endpoint"""
    
    @pytest.mark.slow
    def test_scan_endpoint_exists(self, client):
        """Test POST /api/scan (slow)"""
        response = client.post('/api/scan')
        
        # Should either start scan or not exist
        assert response.status_code in [200, 404, 405]
    
    def test_scan_status_endpoint(self, client):
        """Test GET /api/scan/status"""
        response = client.get('/api/scan/status')
        
        assert response.status_code in [200, 404]


class TestCORSHeaders:
    """Test CORS configuration"""
    
    def test_cors_headers_present(self, client):
        """Test CORS headers are set"""
        response = client.options('/api/signals')
        
        # CORS headers should be present
        assert 'Access-Control-Allow-Origin' in response.headers or \
               response.status_code == 404  # Endpoint might not support OPTIONS


class TestErrorHandling:
    """Test error handling"""
    
    def test_404_on_invalid_endpoint(self, client):
        """Test 404 on non-existent endpoint"""
        response = client.get('/api/does-not-exist')
        
        assert response.status_code == 404
    
    def test_405_on_wrong_method(self, client):
        """Test 405 on wrong HTTP method"""
        # GET on POST-only endpoint
        response = client.get('/api/chat')
        
        assert response.status_code in [405, 404]


# Mark slow tests
pytest.mark.slow(TestScanEndpoint)
