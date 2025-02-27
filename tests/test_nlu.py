import sqlite3
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai.nlu_processor import NLUProcessor


def setup_database():
    """Set up an in-memory SQLite database with the 'items' table and sample data."""
    conn = sqlite3.connect(":memory:")  # In-memory database for testing
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Create the 'items' table
    cursor.execute(
        """
        CREATE TABLE items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL,
            quantity INTEGER,
            location TEXT,
            category TEXT,
            tags TEXT,
            purchase_date TEXT,
            needs_repair INTEGER
        )
    """
    )

    # Insert sample data
    sample_items = [
        ("toaster", 30.0, 1, "kitchen", "appliances", "small", "2023-03-10", 0),
        ("sofa", 500.0, 1, "living room", "furniture", "large", "2022-11-05", 0),
        ("lamp", 25.0, 2, "storage", "decor", "lighting", "2021-08-15", 1),
    ]
    cursor.executemany(
        """
        INSERT INTO items (name, price, quantity, location, category, tags, purchase_date, needs_repair)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        sample_items,
    )

    conn.commit()
    return conn


def test_queries(conn):
    """Run test queries against the NLUProcessor with the provided database connection."""
    nlu = NLUProcessor()

    test_cases = [
        "show me all items in the kitchen",  # Search by location
        "how many products do I have",  # Count total items
        "what is the total value of my inventory",  # Total value
        "list items that cost more than 100 dollars",  # Price range (high)
        "count all things in storage",  # Count by location
        "what items are in the living room",  # Search by location
        "how much are my things worth",  # Total value (alternate phrasing)
        "show me products that cost less than 50",  # Price range (low)
        "what items need repair",  # Repair intent
        "what did I buy last year",  # Purchase history
    ]

    for query in test_cases:
        print(f"\nQuery: {query}")
        try:
            result = nlu.process_natural_language_query(query, lambda: conn)
            print("Result:", result)
        except Exception as e:
            print(f"Error processing query: {e}")


if __name__ == "__main__":
    # Set up the database
    conn = setup_database()

    # Run test queries
    test_queries(conn)

    # Clean up by closing the connection
    conn.close()
