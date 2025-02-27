#!/usr/bin/env python
"""
Database initialization script for Todoist tests.
Creates the necessary tables for testing.
"""
import sqlite3
import os


def init_test_db(db_conn):
    """Initialize the test database with required tables."""
    cursor = db_conn.cursor()

    # Create items table with additional fields
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
        category TEXT,
        tags TEXT,
        is_gift BOOLEAN DEFAULT 0,
        storage_location TEXT,
        usage_location TEXT,
        needs_repair BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    )

    # Create repairs table
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

    db_conn.commit()
    print("[✓] Test database initialized")


if __name__ == "__main__":
    # Create an in-memory database for testing
    conn = sqlite3.connect(':memory:')
    init_test_db(conn)
    conn.close()