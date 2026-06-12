from db.database import get_db_connection
import hashlib
from datetime import datetime

class AuthService:
    _current_user = None
    
    @staticmethod
    def hash_password(password):
        return hashlib.md5(password.encode()).hexdigest()
    
    @staticmethod
    def login(username, password):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        hashed_pwd = AuthService.hash_password(password)
        cursor.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, hashed_pwd)
        )
        user = cursor.fetchone()
        conn.close()
        
        if user:
            user_dict = dict(user)
            user_dict.pop('password', None)
            AuthService._current_user = user_dict
            return user_dict
        return None
    
    @staticmethod
    def get_current_user():
        return AuthService._current_user
    
    @staticmethod
    def logout():
        AuthService._current_user = None
    
    @staticmethod
    def get_user_by_id(user_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    
    @staticmethod
    def get_inspector_by_user_id(user_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM inspectors WHERE user_id = ?", (user_id,))
        inspector = cursor.fetchone()
        conn.close()
        return dict(inspector) if inspector else None
    
    @staticmethod
    def list_users(role=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT id, username, real_name, role, phone, created_at FROM users WHERE 1=1"
        params = []
        
        if role:
            query += " AND role = ?"
            params.append(role)
        
        query += " ORDER BY id"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    @staticmethod
    def has_role(role_name):
        user = AuthService.get_current_user()
        if not user:
            return False
        return user['role'] == role_name or user['role'] == 'admin'
