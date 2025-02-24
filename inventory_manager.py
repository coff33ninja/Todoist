import sqlite3
from datetime import datetime
import threading
import os

class InventoryManager:
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self, db_path='inventory.db'):
        self.db_path = db_path
        self._local = threading.local()
        
    def get_connection(self):
        """Get a thread-local database connection"""
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(self.db_path)
            self._local.conn.row_factory = sqlite3.Row
            self.create_tables()
        return self._local.conn

    def close_connection(self):
        """Close the thread-local database connection"""
        if hasattr(self._local, 'conn'):
            try:
                self._local.conn.close()
            except Exception:
                pass
            finally:
                if hasattr(self._local, 'conn'):
                    del self._local.conn

    def create_tables(self):
        """Create database tables if they don't exist"""
        cursor = self.get_connection().cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                quantity INTEGER DEFAULT 1,
                acquisition_type TEXT CHECK(acquisition_type IN ('purchase', 'trade', 'gift')),
                source_details TEXT,
                price REAL,
                purchase_date TEXT,
                warranty_expiry TEXT,
                location TEXT,
                condition TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                traded_item TEXT NOT NULL,
                traded_item_value REAL,
                trade_date TEXT,
                trade_partner TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(item_id) REFERENCES items(id)
            )
        ''')
        self.get_connection().commit()

    def add_item(self, name, description=None, quantity=1, acquisition_type='purchase',
                source_details=None, price=None, purchase_date=None,
                warranty_expiry=None, location=None, condition='new', notes=None):
        """Add a new item to inventory"""
        cursor = self.get_connection().cursor()
        current_time = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO items (name, description, quantity, acquisition_type,
                             source_details, price, purchase_date, warranty_expiry,
                             location, condition, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, description, quantity, acquisition_type, source_details,
              price, purchase_date, warranty_expiry, location, condition,
              notes, current_time))
        self.get_connection().commit()
        return cursor.lastrowid

    def add_trade(self, item_id, traded_item, traded_item_value=None,
                 trade_date=None, trade_partner=None, notes=None):
        """Record a trade transaction"""
        cursor = self.get_connection().cursor()
        current_time = datetime.now().isoformat()
        if not trade_date:
            trade_date = current_time
        
        cursor.execute('''
            INSERT INTO trades (item_id, traded_item, traded_item_value,
                              trade_date, trade_partner, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (item_id, traded_item, traded_item_value, trade_date,
              trade_partner, notes, current_time))
        self.get_connection().commit()
        return cursor.lastrowid

    def get_items(self, acquisition_type=None):
        """Get all items, optionally filtered by acquisition type"""
        cursor = self.get_connection().cursor()
        query = 'SELECT * FROM items'
        params = []
        
        if acquisition_type:
            query += ' WHERE acquisition_type = ?'
            params = [acquisition_type]
        
        query += ' ORDER BY created_at DESC'
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_item(self, item_id):
        """Get a specific item by ID"""
        cursor = self.get_connection().cursor()
        cursor.execute('''
            SELECT i.*, t.traded_item, t.traded_item_value, t.trade_partner
            FROM items i
            LEFT JOIN trades t ON i.id = t.item_id
            WHERE i.id = ?
        ''', (item_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_item(self, item_id, **kwargs):
        """Update item details"""
        cursor = self.get_connection().cursor()
        updates = []
        values = []
        
        for key, value in kwargs.items():
            if key in ['name', 'description', 'quantity', 'acquisition_type',
                      'source_details', 'price', 'purchase_date', 'warranty_expiry',
                      'location', 'condition', 'notes']:
                updates.append(f'{key} = ?')
                values.append(value)
        
        if updates:
            query = f'''
                UPDATE items 
                SET {', '.join(updates)}
                WHERE id = ?
            '''
            values.append(item_id)
            cursor.execute(query, values)
            self.get_connection().commit()
            return True
        return False

    def get_trades(self):
        """Get all trade records"""
        cursor = self.get_connection().cursor()
        cursor.execute('''
            SELECT t.*, i.name as item_name
            FROM trades t
            JOIN items i ON t.item_id = i.id
            ORDER BY t.trade_date DESC
        ''')
        return [dict(row) for row in cursor.fetchall()]

    def search_items(self, query):
        """Search items by name, description, or notes"""
        cursor = self.get_connection().cursor()
        search = f'%{query}%'
        cursor.execute('''
            SELECT * FROM items
            WHERE name LIKE ? 
               OR description LIKE ?
               OR notes LIKE ?
            ORDER BY created_at DESC
        ''', (search, search, search))
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        """Close the database connection"""
        self.close_connection()

    def __del__(self):
        """Ensure connection is closed when object is destroyed"""
        self.close()