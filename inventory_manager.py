import sqlite3
from datetime import datetime

class InventoryManager:
    def __init__(self, db_path='inventory.db'):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        # Table for inventory items
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT,
                quantity INTEGER DEFAULT 1,
                source TEXT,  # bought, traded, free
                source_details TEXT,  # who gave it, what traded for
                purchase_price REAL,
                purchase_date TEXT,
                warranty_expiry TEXT,
                location TEXT,
                notes TEXT
            )
        ''')
        
        # Table for repair tasks
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS repairs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                description TEXT,
                status TEXT DEFAULT 'pending',
                required_components TEXT,
                estimated_cost REAL,
                FOREIGN KEY(item_id) REFERENCES items(id)
            )
        ''')
        
        self.conn.commit()

    def add_item(self, name, category=None, quantity=1, source='bought', 
                 source_details=None, purchase_price=None, purchase_date=None,
                 warranty_expiry=None, location=None, notes=None):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO items (name, category, quantity, source, source_details,
                             purchase_price, purchase_date, warranty_expiry,
                             location, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, category, quantity, source, source_details, purchase_price,
              purchase_date, warranty_expiry, location, notes))
        self.conn.commit()
        return cursor.lastrowid

    def add_repair_task(self, item_id, description, required_components=None,
                       estimated_cost=None):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO repairs (item_id, description, required_components,
                               estimated_cost)
            VALUES (?, ?, ?, ?)
        ''', (item_id, description, required_components, estimated_cost))
        self.conn.commit()
        return cursor.lastrowid

    def get_item(self, item_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM items WHERE id = ?', (item_id,))
        return cursor.fetchone()

    def get_repair_tasks(self, item_id=None):
        cursor = self.conn.cursor()
        if item_id:
            cursor.execute('SELECT * FROM repairs WHERE item_id = ?', (item_id,))
        else:
            cursor.execute('SELECT * FROM repairs')
        return cursor.fetchall()

    def close(self):
        self.conn.close()
