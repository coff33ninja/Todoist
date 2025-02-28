import sqlite3
import os
from datetime import datetime

def init_db():
    db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db')
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, 'inventory.db')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create categories table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    ''')

    # Create conditions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS conditions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    ''')

    # Create acquisition_types table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS acquisition_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    ''')

    # Create items table with extended fields
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        location TEXT NOT NULL,
        description TEXT,
        category TEXT,
        tags TEXT,
        purchase_date TEXT,
        is_gift BOOLEAN DEFAULT 0,
        storage_location TEXT,
        usage_location TEXT,
        condition TEXT,
        warranty_info TEXT,
        maintenance_schedule TEXT,
        last_maintained_date TEXT,
        acquisition_type TEXT,
        acquisition_date TEXT DEFAULT CURRENT_TIMESTAMP,
        disposal_date TEXT,
        disposal_method TEXT,
        original_owner TEXT,
        current_owner TEXT,
        shared_with TEXT,
        notes TEXT,
        FOREIGN KEY (category) REFERENCES categories (name),
        FOREIGN KEY (condition) REFERENCES conditions (name),
        FOREIGN KEY (acquisition_type) REFERENCES acquisition_types (name)
    )
    ''')

    # Create item_history table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS item_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER,
        action_type TEXT NOT NULL,
        action_date TEXT DEFAULT CURRENT_TIMESTAMP,
        from_whom TEXT,
        to_whom TEXT,
        previous_location TEXT,
        new_location TEXT,
        condition_change TEXT,
        price_change REAL,
        notes TEXT,
        FOREIGN KEY (item_id) REFERENCES items (id)
    )
    ''')

    # Create maintenance_records table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS maintenance_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER,
        maintenance_date TEXT,
        maintenance_type TEXT,
        cost REAL,
        performed_by TEXT,
        notes TEXT,
        next_maintenance_date TEXT,
        FOREIGN KEY (item_id) REFERENCES items (id)
    )
    ''')

    # Insert default categories
    default_categories = [
        'Electronics', 'Books', 'Clothing', 'Food', 'Gifts', 'Office Supplies',
        'Kitchen', 'Furniture', 'Tools', 'Appliances', 'Sports Equipment',
        'Decorations', 'Personal Care', 'Entertainment', 'Other'
    ]
    for category in default_categories:
        cursor.execute('INSERT OR IGNORE INTO categories (name) VALUES (?)', (category,))

    # Insert default conditions
    default_conditions = [
        'New', 'Like New', 'Very Good', 'Good', 'Fair', 'Poor', 'Broken',
        'Needs Repair', 'Under Maintenance', 'Unknown'
    ]
    for condition in default_conditions:
        cursor.execute('INSERT OR IGNORE INTO conditions (name) VALUES (?)', (condition,))

    # Insert default acquisition types
    default_acquisition_types = [
        'Purchased', 'Gift', 'Found', 'Borrowed', 'Rented', 'Inherited',
        'Traded', 'Made', 'Won', 'Other'
    ]
    for acq_type in default_acquisition_types:
        cursor.execute('INSERT OR IGNORE INTO acquisition_types (name) VALUES (?)', (acq_type,))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()