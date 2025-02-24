import pytest
import sqlite3
import os
from flask import Flask
from flask.testing import FlaskClient
import sys

# Add the parent directory to the Python path so we can import our app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, init_db

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
    
    # Initialize the database schema
    init_db()
    
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