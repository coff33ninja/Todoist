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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category) REFERENCES categories(name)
    )
    """
    )

    # Create purchases table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        store_name TEXT NOT NULL,
        purchase_date TEXT,
        total REAL
    )
    """
    )

    # Create purchase_items table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS purchase_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        purchase_id INTEGER,
        description TEXT NOT NULL,
        quantity INTEGER DEFAULT 1,
        price REAL,
        acquisition_type TEXT,
        FOREIGN KEY (purchase_id) REFERENCES purchases(id)
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

    # Add sample data
    sample_items = [
        (
            "Laptop",
            "Dell XPS 13",
            1,
            "2023-08-10",
            999.99,
            "2025-08-10",
            "purchase",
            "Office",
            "new",
            "High-end laptop for work",
            "Electronics",
            "work,portable",
            0,
            "Office Drawer",
            "Work Desk",
            0,
        ),
        (
            "Coffee Maker",
            "Drip coffee maker",
            1,
            "2023-07-01",
            79.99,
            "2024-07-01",
            "purchase",
            "Kitchen",
            "new",
            "Makes great coffee",
            "Appliances",
            "kitchen",
            0,
            "Kitchen Counter",
            "Kitchen Counter",
            0,
        ),
        (
            "Desk Chair",
            "Ergonomic mesh chair",
            2,
            "2023-06-15",
            199.99,
            "2025-06-15",
            "purchase",
            "Office",
            "new",
            "Comfortable office chair",
            "Furniture",
            "",
            0,
            "Office",
            "Office",
            0,
        ),
        (
            "Bookshelf",
            "Wooden 5-shelf bookcase",
            1,
            "2023-05-20",
            149.99,
            "2025-05-20",
            "purchase",
            "Living Room",
            "new",
            "For storing books",
            "Furniture",
            "",
            0,
            "Living Room",
            "Living Room",
            0,
        ),
        (
            "Blender",
            "High-speed blender",
            1,
            "2023-07-22",
            59.99,
            "2024-07-22",
            "purchase",
            "Kitchen",
            "new",
            "For making smoothies",
            "Appliances",
            "kitchen,small",
            0,
            "Kitchen Cabinet",
            "Kitchen Counter",
            0,
        ),
        (
            "Photo Frame",
            "Birthday gift from Mom",
            1,
            "2023-08-15",
            0,
            "",
            "gift",
            "Living Room",
            "new",
            "Special gift",
            "Decorations",
            "gift,memories",
            1,
            "Living Room Wall",
            "Living Room Wall",
            0,
        ),
        (
            "Broken Lamp",
            "Needs fixing",
            1,
            "2023-03-01",
            50.00,
            "2024-03-01",
            "purchase",
            "Living Room",
            "damaged",
            "Lamp with broken switch",
            "Lighting",
            "broken,repair",
            0,
            "Storage",
            "Living Room",
            1,
        ),
    ]

    # Only insert sample data if table is empty
    cursor.execute("SELECT COUNT(*) FROM items")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            """
        INSERT INTO items (
            name, description, quantity, purchase_date, price, 
            warranty_expiry, acquisition_type, location, condition, notes,
            category, tags, is_gift, storage_location, usage_location, needs_repair
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            sample_items,
        )
        print("[✅] Sample data inserted successfully")
    else:
        print("[ℹ️] Database already contains data")
        
    # Add sample repair data
    cursor.execute("SELECT COUNT(*) FROM repairs")
    if cursor.fetchone()[0] == 0:
        # Get item IDs for our sample items
        cursor.execute("SELECT id FROM items WHERE name = 'Broken Lamp'")
        broken_lamp_result = cursor.fetchone()
        if broken_lamp_result is not None:
            broken_lamp_id = broken_lamp_result[0]
        else:
            print("[⚠️] 'Broken Lamp' not found in items table.")
            broken_lamp_id = None
        
        cursor.execute("SELECT id FROM items WHERE name = 'Laptop'")
        laptop_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM items WHERE name = 'Coffee Maker'")
        coffee_maker_id = cursor.fetchone()[0]
        
        # Insert sample repairs
        sample_repairs = []
        if broken_lamp_id is not None:
            sample_repairs.append((broken_lamp_id, '2023-03-15', 'Fix broken switch', 25.00, None, 'in_progress'))


            (broken_lamp_id, '2023-03-15', 'Fix broken switch', 25.00, None, 'in_progress'),
            (laptop_id, '2023-09-01', 'Replace battery', 75.00, None, 'completed'),
            (coffee_maker_id, '2023-08-15', 'Clean internal components', 0.00, '2024-02-15', 'completed')
        ]
        
        cursor.executemany(
            """
        INSERT INTO repairs (
            item_id, repair_date, description, cost, next_due_date, status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
            sample_repairs,
        )
        print("[✅] Sample repair data inserted successfully")
    else:
        print("[ℹ️] Repair data already exists")

    conn.commit()
    conn.close()
    print(f"[✅] Database initialized at {db_path}")


if __name__ == "__main__":
    init_db()
