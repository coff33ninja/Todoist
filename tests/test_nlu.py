import sqlite3
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai.nlu_processor import NLUProcessor

def get_db():
    """Mock database connection function"""
    conn = sqlite3.connect('db/inventory.db')
    conn.row_factory = sqlite3.Row
    return conn

def test_queries():
    nlu = NLUProcessor()

    test_cases = [
        "show me all items in the kitchen",
        "how many products do I have",
        "what is the total value of my inventory",
        "list items that cost more than 100 dollars",
        "count all things in storage",
        "what items are in the living room",
        "how much are my things worth",
        "show me products that cost less than 50"
    ]

    for query in test_cases:
        print(f"\nQuery: {query}")
        result = nlu.process_natural_language_query(query, get_db)
        print("Result:", result)

if __name__ == "__main__":
    test_queries()
