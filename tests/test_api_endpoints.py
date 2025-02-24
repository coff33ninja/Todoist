import json
import pytest

def test_query_endpoint_items(client, sample_data):
    """Test the /api/query endpoint with an items query"""
    response = client.post('/api/query', 
                         json={'query': 'Show me all items'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "response" in data
    assert "items in inventory" in data["response"]

def test_query_endpoint_repairs(client, sample_data):
    """Test the /api/query endpoint with a repairs query"""
    response = client.post('/api/query', 
                         json={'query': 'Show repair history'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "response" in data
    assert "repair records" in data["response"]

def test_query_endpoint_no_query(client):
    """Test the /api/query endpoint with missing query"""
    response = client.post('/api/query', json={})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data

def test_query_endpoint_empty_query(client):
    """Test the /api/query endpoint with empty query string"""
    response = client.post('/api/query', 
                         json={'query': ''})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data