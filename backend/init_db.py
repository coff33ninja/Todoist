import sqlite3
import os

def init_db():
    # Get the path to the db directory
    db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db')
    os.makedirs(db_dir, exist_ok=True)
    
    db_path = os.path.join(db_dir, 'inventory.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create purchases table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        store_name TEXT,
        purchase_date TEXT,
        total REAL
    )
    ''')

    # Create purchase_items table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS purchase_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        purchase_id INTEGER,
        description TEXT,
        quantity INTEGER,
        price REAL,
        acquisition_type TEXT,
        FOREIGN KEY (purchase_id) REFERENCES purchases (id)
    )
    ''')

    # Create items table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL,
        location TEXT,
        description TEXT,
        category TEXT,
        tags TEXT,
        purchase_date TEXT,
        is_gift BOOLEAN,
        storage_location TEXT,
        usage_location TEXT
    )
    ''')

    # Create categories table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    ''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")