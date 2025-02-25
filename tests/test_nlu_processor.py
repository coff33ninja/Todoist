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
    def mock_db():
        class MockCursor:
            def execute(self, query, params=None):
                if "SELECT COUNT(*)" in query:
                    return 1  # Simulate a count of 1 item
                elif "SELECT * FROM items" in query:
                    return [{"name": "Test Item", "price": 10.0}]  # Simulate item data
                return None

            def fetchall(self):
                return [{"name": "Test Item", "price": 10.0}]

            def fetchone(self):
                return [100.0]

        class MockConn:
            def cursor(self):
                return MockCursor()

        return MockConn()

    for query, expected_intent in test_cases:
        result = processor.process_natural_language_query(query, mock_db)
        assert result.get("intent") == expected_intent, \
            f"Expected {expected_intent} for query: {query}"

def test_response_format():
    """Test the response format for different intents"""
    processor = NLUProcessor()

    # Mock database function
    def mock_db():
        class MockCursor:
            def execute(self, query, params):
                pass

            def fetchall(self):
                return [{"name": "Test Item", "price": 10.0}]

            def fetchone(self):
                return [100.0]

        class MockConn:
            def cursor(self):
                return MockCursor()

        return MockConn()

    test_cases = [
        ("show me all items", "search", {"items": [{"name": "Test Item", "price": 10.0}]}),
        ("how many items", "count", {"count": 1}),
        ("what is the total value", "value", {"total": 100.0}),
        ("show items over $50", "price_range", {"items": [{"name": "Test Item", "price": 10.0}]})
    ]

    for query, intent, expected_data in test_cases:
        result = processor.process_natural_language_query(query, mock_db)
        assert result.get("intent") == intent
        for key, value in expected_data.items():
            assert key in result
            assert result[key] == value

def test_performance():
    """Test the performance of the NLU processor"""
    processor = NLUProcessor()

    # Warm up
    for _ in range(5):
        processor.process_natural_language_query("test query", lambda: None)

    # Measure performance
    start_time = time.time()
    for _ in range(100):
        processor.process_natural_language_query("show me all items", lambda: None)
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

    # Test invalid query
    result = processor.process_natural_language_query("invalid query", lambda: None)
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
    result = processor.process_natural_language_query(query, lambda: None)
    assert result.get("intent") == expected_intent, \
        f"Expected {expected_intent} for query: {query}"
