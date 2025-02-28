import sqlite3
import os

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

    # Create items table
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
        FOREIGN KEY (category) REFERENCES categories (name)
    )
    ''')

    # Create received_items_conversations table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS received_items_conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL,
        from_whom TEXT,
        action_taken TEXT,
        location TEXT,
        additional_notes TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        item_id INTEGER,
        FOREIGN KEY (item_id) REFERENCES items (id)
    )
    ''')

    # Insert default categories if they don't exist
    default_categories = [
        'Electronics',
        'Books',
        'Clothing',
        'Food',
        'Gifts',
        'Office Supplies',
        'Kitchen',
        'Furniture',
        'Tools',
        'Other'
    ]

    for category in default_categories:
        cursor.execute('INSERT OR IGNORE INTO categories (name) VALUES (?)', (category,))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()