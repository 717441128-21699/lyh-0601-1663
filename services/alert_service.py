from db.database import get_db_connection
from datetime import datetime

class AlertService:
    @staticmethod
    def create_alert(vehicle_id=None, alert_type='', title='', content='', severity='warning', recipient_role=''):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO alerts (vehicle_id, alert_type, title, content, severity, recipient_role)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (vehicle_id, alert_type, title, content, severity, recipient_role))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def get_unread_alerts(recipient_role=None, limit=20):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM alerts WHERE status = 'unread'"
        params = []
        
        if recipient_role:
            query += " AND recipient_role = ?"
            params.append(recipient_role)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    @staticmethod
    def mark_as_read(alert_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE alerts SET status = 'read' WHERE id = ?", (alert_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def get_all_alerts(recipient_role=None, status=None, page=1, page_size=20):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM alerts WHERE 1=1"
        params = []
        
        if recipient_role:
            query += " AND recipient_role = ?"
            params.append(recipient_role)
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([page_size, (page - 1) * page_size])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
