import pytest
import sqlite3
import os
import sys
from flask import Flask
from flask.testing import FlaskClient  # Import FlaskClient for type hinting

# Add the parent directory to the Python path so we can import our app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.main import app  # Removed init_db as it is unused


@pytest.fixture
def test_app():
    """Create a test Flask application"""
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(test_app) -> FlaskClient:
    """Create a test client"""
    return test_app.test_client()


@pytest.fixture
def test_db():
    """Create a test database connection"""
    # Use an in-memory database for testing
    conn = sqlite3.connect(':memory:')

    # Set up the row factory to return dictionaries
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    conn.row_factory = dict_factory

    # Initialize the database schema for the test database
    cursor = conn.cursor()
    # Create tables
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            quantity INTEGER DEFAULT 1,
            purchase_date TEXT,
            price REAL,
            warranty_expiry TEXT,
            acquisition_type TEXT CHECK(acquisition_type IN ('purchase', 'trade', 'gift')),
            location TEXT,
            condition TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            transaction_type TEXT CHECK(transaction_type IN ('purchase', 'trade', 'gift')),
            amount REAL,
            source TEXT,
            date TEXT,
            details TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(item_id) REFERENCES items(id)
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS repairs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            repair_date TEXT,
            description TEXT,
            cost REAL,
            next_due_date TEXT,
            status TEXT CHECK(status IN ('scheduled', 'in_progress', 'completed', 'cancelled')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(item_id) REFERENCES items(id)
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS budget (
            id INTEGER PRIMARY KEY,
            amount REAL,
            period TEXT,  -- 'monthly', 'yearly', etc.
            last_updated TEXT,
            notes TEXT
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS components (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            name TEXT NOT NULL,
            quantity_needed INTEGER,
            estimated_cost REAL,
            priority TEXT CHECK(priority IN ('low', 'medium', 'high')),
            status TEXT CHECK(status IN ('needed', 'ordered', 'received')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(item_id) REFERENCES items(id)
        )
    """
    )
    conn.commit()

    yield conn

    # Close the connection after the test
    conn.close()


@pytest.fixture
def sample_data(test_db):
    """Insert sample data into the test database"""
    cursor = test_db.cursor()

    # Insert sample items
    cursor.execute("""
        INSERT INTO items (name, description, quantity, price)
        VALUES
            ('Test Item 1', 'Description 1', 1, 100.00),
            ('Test Item 2', 'Description 2', 2, 200.00)
    """)

    # Insert sample repairs
    cursor.execute("""
        INSERT INTO repairs (item_id, repair_date, description, cost, status)
        VALUES
            (1, '2023-01-01', 'First repair', 50.00, 'scheduled'),
            (2, '2023-02-01', 'Second repair', 75.00, 'completed')
    """)
    cursor.execute("""
        INSERT INTO repairs (item_id, repair_date, description, cost)
        VALUES
            (1, '2023-01-01', 'Test Repair 1', 50.00),
            (2, '2023-02-01', 'Test Repair 2', 75.00)
    """)

    # Insert sample budget
    cursor.execute("""
        INSERT INTO budget (id, amount, period, notes)
        VALUES
            (1, 1000.00, 'monthly', 'Test Budget')
    """)

    # Insert sample components
    cursor.execute("""
        INSERT INTO components (item_id, name, quantity_needed, estimated_cost)
        VALUES
            (1, 'Component 1', 1, 25.00),
            (2, 'Component 2', 2, 35.00)
    """)

    test_db.commit()
    return test_db
