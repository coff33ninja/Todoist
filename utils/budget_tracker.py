import sqlite3
from datetime import datetime

class BudgetTracker:
    def __init__(self, db_path='inventory.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budget (
                id INTEGER PRIMARY KEY,
                amount REAL NOT NULL,
                period TEXT NOT NULL,
                last_updated TEXT NOT NULL,
                notes TEXT
            )
        ''')
        self.conn.commit()

    def get_budget(self):
        """Get the current budget settings"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM budget WHERE id = 1')
        budget = cursor.fetchone()
        
        if budget:
            return {
                'amount': budget[1],
                'period': budget[2],
                'last_updated': budget[3],
                'notes': budget[4]
            }
        return None

    def update_budget(self, amount, period='monthly', notes=None):
        """Update or create budget settings"""
        cursor = self.conn.cursor()
        current_time = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT OR REPLACE INTO budget (id, amount, period, last_updated, notes)
            VALUES (1, ?, ?, ?, ?)
        ''', (amount, period, current_time, notes))
        self.conn.commit()

    def calculate_total_spent(self, period_start=None, period_end=None):
        """Calculate total spent, optionally within a date range"""
        cursor = self.conn.cursor()
        
        if period_start and period_end:
            cursor.execute('''
                SELECT SUM(purchase_price) FROM items 
                WHERE purchase_date BETWEEN ? AND ?
            ''', (period_start, period_end))
        else:
            cursor.execute('SELECT SUM(purchase_price) FROM items')
        
        total = cursor.fetchone()[0]
        return total if total else 0.0

    def calculate_available_budget(self, period_start=None, period_end=None):
        """Calculate remaining budget for the period"""
        budget = self.get_budget()
        if not budget:
            return 0.0
        
        total_spent = self.calculate_total_spent(period_start, period_end)
        return budget['amount'] - total_spent

    def get_purchase_history(self, limit=None):
        """Get purchase history, optionally limited to a number of records"""
        cursor = self.conn.cursor()
        
        query = '''
            SELECT name, purchase_price, purchase_date, source, source_details
            FROM items 
            WHERE purchase_price IS NOT NULL
            ORDER BY purchase_date DESC
        '''
        
        if limit:
            query += f' LIMIT {limit}'
        
        cursor.execute(query)
        return cursor.fetchall()

    def close(self):
        """Close the database connection"""
        self.conn.close()