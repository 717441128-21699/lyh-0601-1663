from db.database import get_db_connection
from datetime import datetime

class VehicleService:
    @staticmethod
    def add_vehicle(vin, brand, model, year, mileage, color, accident_record, intended_price, urgent_level=1, parking_spot=None, notes=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO vehicles (vin, brand, model, year, mileage, color, accident_record, intended_price, urgent_level, parking_spot, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (vin, brand, model, year, mileage, color, accident_record, intended_price, urgent_level, parking_spot, notes))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def update_vehicle(vehicle_id, **kwargs):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            set_clause = ', '.join([f"{k} = ?" for k in kwargs.keys()])
            values = list(kwargs.values()) + [vehicle_id]
            cursor.execute(f"UPDATE vehicles SET {set_clause} WHERE id = ?", values)
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def get_vehicle(vehicle_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    @staticmethod
    def get_vehicle_by_vin(vin):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vehicles WHERE vin = ?", (vin,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    @staticmethod
    def list_vehicles(status=None, brand=None, page=1, page_size=20):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM vehicles WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        if brand:
            query += " AND brand LIKE ?"
            params.append(f"%{brand}%")
        
        query += " ORDER BY entry_date DESC LIMIT ? OFFSET ?"
        params.extend([page_size, (page - 1) * page_size])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    @staticmethod
    def count_vehicles(status=None, brand=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT COUNT(*) as cnt FROM vehicles WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        if brand:
            query += " AND brand LIKE ?"
            params.append(f"%{brand}%")
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.close()
        return result['cnt']
    
    @staticmethod
    def update_status(vehicle_id, status):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE vehicles SET status = ? WHERE id = ?", (status, vehicle_id))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def get_pending_inspection_vehicles():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vehicles WHERE status IN ('pending_inspection', 'reinspection') ORDER BY urgent_level DESC, entry_date ASC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    @staticmethod
    def get_for_sale_vehicles():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vehicles WHERE status = 'for_sale' ORDER BY entry_date DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    @staticmethod
    def get_overstock_vehicles(days=30):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT *, julianday('now') - julianday(entry_date) as stock_days
            FROM vehicles 
            WHERE status = 'for_sale' AND julianday('now') - julianday(entry_date) > ?
            ORDER BY stock_days DESC
        ''', (days,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
