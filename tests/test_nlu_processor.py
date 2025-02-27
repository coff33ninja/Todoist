import os
import sys
import time
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai.nlu_processor import NLUProcessor

def test_intent_classification():
    """Test the transformer model's intent classification"""
    processor = NLUProcessor()

    test_cases = [
        ("show me all items in the kitchen", "search"),
        ("how many products do I have", "count"),
        ("what is the total value of my inventory", "value"),
        ("list items that cost more than 100 dollars", "price_range"),
        ("unknown query that should fail", "unknown")
    ]

    # Use mock_db for all queries
    class MockCursor:
        def __init__(self):
            self.query = ""
            self.description = [("name", None, None, None, None, None, None), 
                               ("price", None, None, None, None, None, None)]
            
        def execute(self, query, params=None):
            self.query = query
            return self
            
        def fetchall(self):
            return [{"name": "Test Item", "price": 10.0}]
            
        def fetchone(self):
            if "COUNT" in self.query:
                return {"count": 1}
            return {"total": 100.0}
    
    mock_cursor = MockCursor()

    for query, expected_intent in test_cases:
        result = processor.process_natural_language_query(query, mock_cursor)
        assert result.get("intent") == expected_intent, \
            f"Expected {expected_intent} for query: {query}"

def test_response_format():
    """Test the response format for different intents"""
    processor = NLUProcessor()

    # Mock database cursor directly
    class MockCursor:
        def __init__(self):
            self.query = ""
            self.description = [("name", None, None, None, None, None, None), 
                               ("price", None, None, None, None, None, None)]
            
        def execute(self, query, params=None):
            self.query = query
            return self

        def fetchall(self):
            return [{"name": "Test Item", "price": 10.0}]

        def fetchone(self):
            if "COUNT" in self.query:
                return {"count": 1}
            return {"total": 100.0}

    # Pass the cursor directly
    mock_cursor = MockCursor()

    test_cases = [
        ("show me all items", "search", {"items": [{"name": "Test Item", "price": 10.0}]}),
        ("how many items", "count", {"count": 1}),
        ("what is the total value", "value", {"total": 100.0}),
        ("show items over $50", "price_range", {"items": [{"name": "Test Item", "price": 10.0}]})
    ]

    for query, intent, expected_data in test_cases:
        # Create a fresh cursor for each test
        fresh_cursor = MockCursor()
        result = processor.process_natural_language_query(query, fresh_cursor)
        assert result.get("intent") == intent, f"Expected intent {intent} for query: {query}"
        for key, value in expected_data.items():
            assert key in result, f"Key {key} not found in result for query: {query}"
            if key == "items":
                assert len(result[key]) == len(value), f"Expected {len(value)} items, got {len(result[key])}"
            else:
                assert result[key] == value, f"Expected {value}, got {result[key]}"

def test_performance():
    """Test the performance of the NLU processor"""
    processor = NLUProcessor()

    # Mock cursor for testing
    class MockCursor:
        def __init__(self):
            self.description = [("name", None, None, None, None, None, None), 
                               ("price", None, None, None, None, None, None)]
            
        def execute(self, query, params=None):
            return self
        def fetchall(self):
            return [{"name": "Test Item", "price": 10.0}]
        def fetchone(self):
            return {"count": 1}
    
    mock_cursor = MockCursor()

    # Warm up
    for _ in range(5):
        processor.process_natural_language_query("test query", mock_cursor)

    # Measure performance
    start_time = time.time()
    for _ in range(100):
        processor.process_natural_language_query("show me all items", mock_cursor)
    elapsed_time = time.time() - start_time

    assert elapsed_time < 5.0, "NLU processing is too slow"

def test_error_handling():
    """Test error handling in the NLU processor"""
    processor = NLUProcessor()

    # Test database error
    def failing_db():
        raise Exception("Database connection failed")

    result = processor.process_natural_language_query("show me all items", failing_db)
    assert result.get("error") == "Database connection failed"

    # Mock cursor for testing
    class MockCursor:
        def __init__(self):
            self.description = [("name", None, None, None, None, None, None), 
                               ("price", None, None, None, None, None, None)]
            
        def execute(self, query, params=None):
            return self
        def fetchall(self):
            return [{"name": "Test Item", "price": 10.0}]
        def fetchone(self):
            return {"count": 1}
    
    mock_cursor = MockCursor()

    # Test invalid query
    result = processor.process_natural_language_query("invalid query", mock_cursor)
    assert result.get("intent") == "unknown"

@pytest.mark.parametrize("query,expected_intent", [
    ("display all products", "search"),
    ("count my items", "count"),
    ("what's my inventory worth", "value"),
    ("show expensive items", "price_range"),
    ("unknown query", "unknown")
])
def test_various_phrasings(query, expected_intent):
    """Test various phrasings for each intent"""
    processor = NLUProcessor()
    
    # Mock cursor for testing
    class MockCursor:
        def __init__(self):
            self.description = [("name", None, None, None, None, None, None), 
                               ("price", None, None, None, None, None, None)]
            
        def execute(self, query, params=None):
            return self
        def fetchall(self):
            return [{"name": "Test Item", "price": 10.0}]
        def fetchone(self):
            return {"count": 1}
    
    mock_cursor = MockCursor()
    
    result = processor.process_natural_language_query(query, mock_cursor)
    assert result.get("intent") == expected_intent, \
        f"Expected {expected_intent} for query: {query}"
