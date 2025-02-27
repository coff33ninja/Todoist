#!/usr/bin/env python
"""
Database initialization script for Todoist.
Creates the items table (with extra columns) and populates it with sample data.
"""
import sqlite3
import os


def init_db():
    """Initialize the database with required tables."""
    # Ensure the db directory exists
    base_dir = os.path.dirname(os.path.dirname(__file__))
    db_dir = os.path.join(base_dir, "db")
    os.makedirs(db_dir, exist_ok=True)

    db_path = os.path.join(db_dir, "inventory.db")

    # Connect to the database (creates it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Create the categories table
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

    # Create the items table with additional fields
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

    # Create the purchases table
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

    # Create the purchase_items table
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

    # Create the repairs table
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

    # Insert sample item data if the table is empty
    cursor.execute("SELECT COUNT(*) FROM items")
    if cursor.fetchone()[0] == 0:
        sample_items = [
            # Original sample items
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
            # New types of items
            (
                "Smartphone",
                "Latest flagship smartphone",
                1,
                "2023-09-10",
                799.99,
                "2025-09-10",
                "purchase",
                "Pocket",
                "new",
                "Sleek design with high performance",
                "Electronics",
                "mobile,smartphone",
                0,
                "Drawer",
                "Everyday",
                0,
            ),
            (
                "Tablet",
                "10-inch tablet for work and play",
                1,
                "2023-08-20",
                399.99,
                "2025-08-20",
                "purchase",
                "Office",
                "new",
                "Great for reading and drawing",
                "Electronics",
                "tablet,portable",
                0,
                "Office Drawer",
                "Office",
                0,
            ),
            (
                "Headphones",
                "Wireless noise-cancelling headphones",
                1,
                "2023-07-15",
                299.99,
                "2024-07-15",
                "purchase",
                "Living Room",
                "new",
                "Immersive sound experience",
                "Electronics",
                "audio,wireless",
                0,
                "Entertainment Center",
                "Living Room",
                0,
            ),
            (
                "Gaming Console",
                "Next-gen gaming console",
                1,
                "2023-10-01",
                499.99,
                "2025-10-01",
                "purchase",
                "Living Room",
                "new",
                "For gaming marathons",
                "Electronics",
                "gaming,console",
                0,
                "Entertainment Center",
                "Living Room",
                0,
            ),
            (
                "Novel",
                "Bestselling mystery novel",
                1,
                "2023-05-01",
                12.99,
                "",
                "purchase",
                "Bookshelf",
                "new",
                "Page-turner",
                "Books",
                "book,fiction",
                0,
                "Bookshelf",
                "Reading Nook",
                0,
            ),
            (
                "T-shirt",
                "100% cotton T-shirt",
                3,
                "2023-06-01",
                9.99,
                "",
                "purchase",
                "Closet",
                "new",
                "Comfortable everyday wear",
                "Clothing",
                "apparel,casual",
                0,
                "Wardrobe",
                "Daily",
                0,
            ),
            (
                "Bicycle",
                "Mountain bike",
                1,
                "2023-04-15",
                349.99,
                "2024-04-15",
                "purchase",
                "Garage",
                "new",
                "Ready for off-road trails",
                "Sports",
                "outdoor,cycling",
                0,
                "Garage",
                "Outdoor",
                0,
            ),
            (
                "Office Desk",
                "Ergonomic office desk with drawers",
                1,
                "2023-03-20",
                249.99,
                "2025-03-20",
                "purchase",
                "Office",
                "new",
                "Spacious work area",
                "Furniture",
                "office,desk",
                0,
                "Office",
                "Office",
                0,
            ),
        ]
        cursor.executemany(
            """
        INSERT INTO items (
            name, description, quantity, purchase_date, price, 
            warranty_expiry, acquisition_type, location, condition, notes,
            category, tags, is_gift, storage_location, usage_location, needs_repair
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            sample_items,
        )
        print("[✅] Sample item data inserted successfully")
    else:
        print("[ℹ️] Items table already contains data")

    # Insert sample repair data if the table is empty
    cursor.execute("SELECT COUNT(*) FROM repairs")
    if cursor.fetchone()[0] == 0:
        # Helper function to fetch an item ID by name
        def get_item_id(item_name):
            cursor.execute("SELECT id FROM items WHERE name = ?", (item_name,))
            row = cursor.fetchone()
            return row[0] if row else None

        broken_lamp_id = get_item_id("Broken Lamp")
        laptop_id = get_item_id("Laptop")
        coffee_maker_id = get_item_id("Coffee Maker")

        sample_repairs = []
        if broken_lamp_id is not None:
            sample_repairs.append(
                (
                    broken_lamp_id,
                    "2023-03-15",
                    "Fix broken switch",
                    25.00,
                    None,
                    "in_progress",
                )
            )
        if laptop_id is not None:
            sample_repairs.append(
                (laptop_id, "2023-09-01", "Replace battery", 75.00, None, "completed")
            )
        if coffee_maker_id is not None:
            sample_repairs.append(
                (
                    coffee_maker_id,
                    "2023-08-15",
                    "Clean internal components",
                    0.00,
                    "2024-02-15",
                    "completed",
                )
            )

        if sample_repairs:
            cursor.executemany(
                """
            INSERT INTO repairs (
                item_id, repair_date, description, cost, next_due_date, status
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
                sample_repairs,
            )
            print("[✅] Sample repair data inserted successfully")
        else:
            print("[⚠️] No valid items found for repairs sample data.")
    else:
        print("[ℹ️] Repair data already exists")

    # Insert sample purchase data if the table is empty
    cursor.execute("SELECT COUNT(*) FROM purchases")
    if cursor.fetchone()[0] == 0:
        sample_purchases = [
            ("ElectroMart", "2023-08-10", 999.99),
            ("Home Goods", "2023-07-01", 79.99),
        ]
        cursor.executemany(
            """
            INSERT INTO purchases (
                store_name, purchase_date, total
            ) VALUES (?, ?, ?)
        """,
            sample_purchases,
        )
        print("[✅] Sample purchase data inserted successfully")
    else:
        print("[ℹ️] Purchase data already exists")

    conn.commit()
    conn.close()
    print(f"[✅] Database initialized at {db_path}")


if __name__ == "__main__":
    init_db()
