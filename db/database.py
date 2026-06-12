import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'used_car_system.db')

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        real_name TEXT NOT NULL,
        role TEXT NOT NULL,
        phone TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inspectors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        employee_no TEXT UNIQUE NOT NULL,
        skill_tags TEXT,
        status TEXT DEFAULT 'available',
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS workstations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        station_type TEXT NOT NULL,
        status TEXT DEFAULT 'idle',
        location TEXT,
        tools TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vehicles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vin TEXT UNIQUE NOT NULL,
        brand TEXT NOT NULL,
        model TEXT,
        year INTEGER,
        mileage REAL,
        color TEXT,
        accident_record TEXT,
        intended_price REAL,
        entry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'pending_inspection',
        urgent_level INTEGER DEFAULT 1,
        parking_spot TEXT,
        notes TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inspection_schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id INTEGER NOT NULL,
        inspector_id INTEGER,
        workstation_id INTEGER,
        schedule_date DATE NOT NULL,
        start_time TEXT,
        end_time TEXT,
        inspection_type TEXT,
        status TEXT DEFAULT 'pending_approval',
        priority INTEGER DEFAULT 0,
        approver_id INTEGER,
        approved_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
        FOREIGN KEY (inspector_id) REFERENCES inspectors(id),
        FOREIGN KEY (workstation_id) REFERENCES workstations(id),
        FOREIGN KEY (approver_id) REFERENCES users(id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inspection_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id INTEGER NOT NULL,
        schedule_id INTEGER,
        inspector_id INTEGER,
        workstation_id INTEGER,
        inspection_stage TEXT,
        start_time TIMESTAMP,
        end_time TIMESTAMP,
        status TEXT,
        water_damage_score INTEGER DEFAULT 0,
        fire_damage_score INTEGER DEFAULT 0,
        major_accident_score INTEGER DEFAULT 0,
        appearance_score INTEGER,
        chassis_score INTEGER,
        engine_score INTEGER,
        is_reinspection INTEGER DEFAULT 0,
        reinspection_reason TEXT,
        result TEXT,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
        FOREIGN KEY (schedule_id) REFERENCES inspection_schedules(id),
        FOREIGN KEY (inspector_id) REFERENCES inspectors(id),
        FOREIGN KEY (workstation_id) REFERENCES workstations(id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inspection_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_id INTEGER NOT NULL,
        item_name TEXT NOT NULL,
        item_category TEXT NOT NULL,
        result TEXT,
        score INTEGER,
        notes TEXT,
        FOREIGN KEY (record_id) REFERENCES inspection_records(id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id INTEGER,
        alert_type TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT,
        severity TEXT DEFAULT 'warning',
        status TEXT DEFAULT 'unread',
        recipient_role TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS price_suggestions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id INTEGER UNIQUE NOT NULL,
        base_price REAL,
        market_adjustment REAL,
        inventory_adjustment REAL,
        suggested_price REAL,
        calculation_basis TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS buyer_offers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id INTEGER NOT NULL,
        buyer_name TEXT NOT NULL,
        buyer_phone TEXT,
        offer_price REAL NOT NULL,
        offer_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'pending_approval',
        sales_manager_id INTEGER,
        approved_at TIMESTAMP,
        approval_notes TEXT,
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
        FOREIGN KEY (sales_manager_id) REFERENCES users(id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS contracts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contract_no TEXT UNIQUE NOT NULL,
        vehicle_id INTEGER NOT NULL,
        offer_id INTEGER UNIQUE,
        buyer_name TEXT,
        buyer_phone TEXT,
        final_price REAL,
        sign_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'active',
        contract_content TEXT,
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
        FOREIGN KEY (offer_id) REFERENCES buyer_offers(id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS price_reduction_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id INTEGER NOT NULL,
        original_price REAL,
        new_price REAL,
        reduction_reason TEXT,
        operator_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
        FOREIGN KEY (operator_id) REFERENCES users(id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS approval_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_type TEXT NOT NULL,
        related_id INTEGER,
        applicant_id INTEGER,
        approver_role TEXT,
        approver_id INTEGER,
        status TEXT DEFAULT 'pending',
        title TEXT,
        reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        approved_at TIMESTAMP,
        approval_notes TEXT,
        FOREIGN KEY (applicant_id) REFERENCES users(id),
        FOREIGN KEY (approver_id) REFERENCES users(id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS market_price_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand TEXT NOT NULL,
        model TEXT,
        year INTEGER,
        avg_price REAL,
        sample_count INTEGER DEFAULT 0,
        data_date DATE
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS parking_spots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        spot_code TEXT UNIQUE NOT NULL,
        zone TEXT,
        row_num INTEGER,
        col_num INTEGER,
        status TEXT DEFAULT 'empty',
        vehicle_id INTEGER UNIQUE,
        x_coord REAL,
        y_coord REAL,
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
    )
    ''')
    
    conn.commit()
    conn.close()
