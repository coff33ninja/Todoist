import pytest
from nlu_processor import process_natural_language_query

def test_inventory_query(sample_data):
    """Test querying about inventory items"""
    query = "Show me all items in inventory"
    result = process_natural_language_query(query, lambda: sample_data)
    assert "There are 2 items in inventory" in result
    assert "Test Item 1" in result
    assert "Test Item 2" in result

def test_repairs_query(sample_data):
    """Test querying about repairs"""
    query = "What repairs have been done?"
    result = process_natural_language_query(query, lambda: sample_data)
    assert "There are 2 repair records" in result
    assert "Test Item 1 on 2023-01-01" in result
    assert "Test Item 2 on 2023-02-01" in result

def test_budget_query(sample_data):
    """Test querying about budget"""
    query = "What's our current budget?"
    result = process_natural_language_query(query, lambda: sample_data)
    assert "current budget is set at $1000.00" in result
    assert "monthly" in result

def test_components_query(sample_data):
    """Test querying about components"""
    query = "List all components needed"
    result = process_natural_language_query(query, lambda: sample_data)
    assert "There are 2 components required" in result
    assert "Component 1 for Test Item 1" in result
    assert "Component 2 for Test Item 2" in result

def test_unknown_query(sample_data):
    """Test handling of unknown query types"""
    query = "What's the weather like today?"
    result = process_natural_language_query(query, lambda: sample_data)
    assert "I'm sorry, I didn't understand your query" in result
    assert "items, repairs, budget, or components" in result

def test_error_handling(sample_data):
    """Test handling of database errors"""
    def failing_db():
        raise Exception("Database connection failed")
    
    query = "Show me all items"
    result = process_natural_language_query(query, failing_db)
    assert "An error occurred" in result
    assert "Database connection failed" in result

@pytest.mark.parametrize("query,expected_keyword", [
    ("show inventory", "inventory"),
    ("list all items", "item"),
    ("repair history", "repair"),
    ("maintenance records", "repair"),
    ("current budget", "budget"),
    ("total costs", "cost"),
    ("needed components", "component"),
    ("required parts", "component"),
])
def test_keyword_detection(sample_data, query, expected_keyword):
    """Test various phrasings for each query type"""
    result = process_natural_language_query(query, lambda: sample_data)
    assert result != "I'm sorry, I didn't understand your query"