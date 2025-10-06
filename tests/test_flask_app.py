# tests/test_flask_app.py
import pytest
import json
from app import app

@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    """Test health endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'status' in data
    assert data['status'] == 'healthy'

def test_index_page(client):
    """Test index page loads."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'RAG Document Q&A System' in response.data

def test_ask_page(client):
    """Test ask page loads."""
    response = client.get('/ask')
    assert response.status_code == 200
    assert b'Ask a Question' in response.data

def test_upload_page(client):
    """Test upload page loads."""
    response = client.get('/upload')
    assert response.status_code == 200
    assert b'Upload Documents' in response.data

def test_api_ask_missing_question(client):
    """Test API ask endpoint with missing question."""
    response = client.post('/api/ask', json={})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_api_ask_invalid_question(client):
    """Test API ask endpoint with invalid question."""
    response = client.post('/api/ask', json={'question': 'hi'})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

if __name__ == '__main__':
    pytest.main([__file__])
