import sqlite3
from datetime import datetime

class TaskManager:
    def __init__(self, db_path='inventory.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        # Table for repair tasks
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS repairs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                description TEXT NOT NULL,
                repair_date TEXT,
                cost REAL,
                next_due_date TEXT,
                status TEXT CHECK(status IN ('scheduled', 'in_progress', 'completed', 'cancelled')),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(item_id) REFERENCES items(id)
            )
        ''')
        
        # Table for components needed for repairs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repair_id INTEGER,
                name TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                estimated_cost REAL,
                priority TEXT CHECK(priority IN ('low', 'medium', 'high')),
                status TEXT CHECK(status IN ('needed', 'ordered', 'received')),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(repair_id) REFERENCES repairs(id)
            )
        ''')
        self.conn.commit()

    def add_repair(self, item_id, description, repair_date=None, cost=None, 
                  next_due_date=None, status='scheduled'):
        """Add a new repair task"""
        cursor = self.conn.cursor()
        current_time = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO repairs (item_id, description, repair_date, cost,
                               next_due_date, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (item_id, description, repair_date, cost, next_due_date, 
              status, current_time))
        self.conn.commit()
        return cursor.lastrowid

    def add_component(self, repair_id, name, quantity=1, estimated_cost=None,
                     priority='medium', status='needed'):
        """Add a component needed for a repair"""
        cursor = self.conn.cursor()
        current_time = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO components (repair_id, name, quantity, estimated_cost,
                                  priority, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (repair_id, name, quantity, estimated_cost, priority, 
              status, current_time))
        self.conn.commit()
        return cursor.lastrowid

    def get_repairs(self, status=None, item_id=None):
        """Get repair tasks, optionally filtered by status or item"""
        cursor = self.conn.cursor()
        query = '''
            SELECT r.*, i.name as item_name 
            FROM repairs r
            JOIN items i ON r.item_id = i.id
        '''
        params = []
        
        if status and item_id:
            query += ' WHERE r.status = ? AND r.item_id = ?'
            params = [status, item_id]
        elif status:
            query += ' WHERE r.status = ?'
            params = [status]
        elif item_id:
            query += ' WHERE r.item_id = ?'
            params = [item_id]
        
        query += ' ORDER BY r.created_at DESC'
        
        cursor.execute(query, params)
        return cursor.fetchall()

    def get_components(self, repair_id=None, status=None):
        """Get components, optionally filtered by repair or status"""
        cursor = self.conn.cursor()
        query = '''
            SELECT c.*, r.description as repair_description
            FROM components c
            JOIN repairs r ON c.repair_id = r.id
        '''
        params = []
        
        if repair_id and status:
            query += ' WHERE c.repair_id = ? AND c.status = ?'
            params = [repair_id, status]
        elif repair_id:
            query += ' WHERE c.repair_id = ?'
            params = [repair_id]
        elif status:
            query += ' WHERE c.status = ?'
            params = [status]
        
        query += ' ORDER BY c.priority DESC, c.created_at DESC'
        
        cursor.execute(query, params)
        return cursor.fetchall()

    def update_repair_status(self, repair_id, status):
        """Update the status of a repair task"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE repairs 
            SET status = ?
            WHERE id = ?
        ''', (status, repair_id))
        self.conn.commit()

    def update_component_status(self, component_id, status):
        """Update the status of a component"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE components 
            SET status = ?
            WHERE id = ?
        ''', (status, component_id))
        self.conn.commit()

    def calculate_repair_costs(self, include_components=True):
        """Calculate total cost of repairs and optionally their components"""
        cursor = self.conn.cursor()
        total_cost = 0
        
        # Get repair costs
        cursor.execute('SELECT SUM(cost) FROM repairs')
        repair_cost = cursor.fetchone()[0]
        total_cost += repair_cost if repair_cost else 0
        
        if include_components:
            cursor.execute('SELECT SUM(estimated_cost) FROM components')
            component_cost = cursor.fetchone()[0]
            total_cost += component_cost if component_cost else 0
        
        return total_cost

    def close(self):
        """Close the database connection"""
        self.conn.close()