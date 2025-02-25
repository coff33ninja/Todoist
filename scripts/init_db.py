#!/usr/bin/env python
"""
Database initialization script for Todoist.
Creates the items table (with extra columns) and populates it with sample data.
"""
import sqlite3
import os


def init_db():
    """Initialize the database with required tables."""
    # Ensure db directory exists
    db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db")
    os.makedirs(db_dir, exist_ok=True)

    db_path = os.path.join(db_dir, "inventory.db")

    # Connect to database (creates it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Create categories table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    """
    )

    # Insert predefined categories
    categories = [
        ("Electronics",),
        ("Furniture",),
        ("Appliances",),
        ("Clothing",),
        ("Books",),
        ("Kitchen",),
        ("Tools",),
        ("Sports",),
        ("Toys",),
        ("Decorations",),
        ("Office Supplies",),
        ("Personal Care",),
        ("Other",),
    ]
    cursor.executemany("INSERT OR IGNORE INTO categories (name) VALUES (?)", categories)

    # Create items table with additional fields
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        quantity INTEGER DEFAULT 1,
        price REAL,
        location TEXT,
        description TEXT,
        category TEXT,
        tags TEXT,
        purchase_date TEXT,
        is_gift BOOLEAN DEFAULT 0,
        storage_location TEXT,
        usage_location TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category) REFERENCES categories(name)
    )
    """
    )

    # Add sample data
    sample_items = [
        (
            "Laptop",
            1,
            999.99,
            "Office",
            "Dell XPS 13",
            "Electronics",
            "work,portable",
            "2023-08-10",
            0,
            "Office Drawer",
            "Work Desk",
        ),
        (
            "Coffee Maker",
            1,
            79.99,
            "Kitchen",
            "Drip coffee maker",
            "Appliances",
            "kitchen",
            "2023-07-01",
            0,
            "Kitchen Counter",
            "Kitchen Counter",
        ),
        (
            "Desk Chair",
            2,
            199.99,
            "Office",
            "Ergonomic mesh chair",
            "Furniture",
            "",
            "2023-06-15",
            0,
            "Office",
            "Office",
        ),
        (
            "Bookshelf",
            1,
            149.99,
            "Living Room",
            "Wooden 5-shelf bookcase",
            "Furniture",
            "",
            "2023-05-20",
            0,
            "Living Room",
            "Living Room",
        ),
        (
            "Blender",
            1,
            59.99,
            "Kitchen",
            "High-speed blender",
            "Appliances",
            "kitchen,small",
            "2023-07-22",
            0,
            "Kitchen Cabinet",
            "Kitchen Counter",
        ),
        (
            "Photo Frame",
            1,
            0,
            "Living Room",
            "Birthday gift from Mom",
            "Decorations",
            "gift,memories",
            "2023-08-15",
            1,
            "Living Room Wall",
            "Living Room Wall",
        ),
    ]

    # Only insert sample data if table is empty
    cursor.execute("SELECT COUNT(*) FROM items")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            """
        INSERT INTO items (
            name, quantity, price, location, description, 
            category, tags, purchase_date, is_gift, 
            storage_location, usage_location
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            sample_items,
        )
        print("[✅] Sample data inserted successfully")
    else:
        print("[ℹ️] Database already contains data")

    conn.commit()
    conn.close()
    print(f"[✅] Database initialized at {db_path}")


if __name__ == "__main__":
    init_db()
