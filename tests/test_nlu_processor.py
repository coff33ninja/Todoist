import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai.nlu_processor import NLUProcessor

def test_inventory_query(sample_data: dict):
    """Test querying about inventory items"""
    query = "Show me all items"
    processor = NLUProcessor()
    result: dict = processor.process_natural_language_query(query, lambda: sample_data)
    assert result.get("type") == "search"
    assert isinstance(result.get("count"), int) and result["count"] >= 2
    items = result.get("items", [])
    assert any("Test Item 1" in item.get("name", "") for item in items)
    assert any("Test Item 2" in item.get("name", "") for item in items)

def test_repairs_query(sample_data: dict):
    """Test querying about repairs"""
    query = "List all repairs"
    processor = NLUProcessor()
    result: dict = processor.process_natural_language_query(query, lambda: sample_data)
    assert result.get("type") == "repairs"
    assert isinstance(result.get("count"), int) and result["count"] >= 2
    repairs = result.get("repairs", [])
    assert any("First repair" in repair.get("description", "") for repair in repairs)
    assert any("Second repair" in repair.get("description", "") for repair in repairs)

def test_budget_query(sample_data: dict):
    """Test querying about budget"""
    query = "Show me the budget"
    processor = NLUProcessor()
    result: dict = processor.process_natural_language_query(query, lambda: sample_data)
    assert result.get("type") == "budget"
    budget = result.get("budget", {})
    assert isinstance(budget, dict)
    assert budget.get("amount") == 1000.0
    assert budget.get("period") == "monthly"

def test_components_query(sample_data: dict):
    """Test querying about components"""
    query = "Show me all components"
    processor = NLUProcessor()
    result: dict = processor.process_natural_language_query(query, lambda: sample_data)
    assert result.get("type") == "components"
    assert isinstance(result.get("count"), int) and result["count"] >= 2
    components = result.get("components", [])
    assert any("Component 1" in component.get("name", "") for component in components)
    assert any("Component 2" in component.get("name", "") for component in components)

def test_unknown_query(sample_data):
    """Test handling of unknown query types"""
    query = "How is the weather today?"
    processor = NLUProcessor()
    result = processor.process_natural_language_query(query, lambda: sample_data)
    assert result["type"] == "error"
    assert "not sure what you're asking about" in result["message"]

def test_error_handling(sample_data):
    """Test handling of database errors"""
    def failing_db():
        raise Exception("Database connection failed")

    query = "Show me all items"
    processor = NLUProcessor()
    result = processor.process_natural_language_query(query, failing_db)
    assert result["type"] == "error"
    assert "Database connection failed" in result["message"]

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
    processor = NLUProcessor()
    result = processor.process_natural_language_query(query, lambda: sample_data)
    assert result != "I'm sorry, I didn't understand your query"
