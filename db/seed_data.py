from db.database import get_db_connection
import hashlib

def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

def seed_test_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
    
    users = [
        ('admin', hash_password('123456'), '系统管理员', 'admin', '13800138000'),
        ('inspector_zhang', hash_password('123456'), '张工', 'inspector', '13800138001'),
        ('inspector_li', hash_password('123456'), '李工', 'inspector', '13800138002'),
        ('inspector_wang', hash_password('123456'), '王工', 'inspector', '13800138003'),
        ('chief_inspector', hash_password('123456'), '赵主管', 'chief_inspector', '13800138004'),
        ('sales_manager', hash_password('123456'), '孙经理', 'sales_manager', '13800138005'),
        ('sales_person', hash_password('123456'), '周销售', 'sales_person', '13800138006'),
        ('marketing', hash_password('123456'), '吴营销', 'marketing', '13800138007'),
    ]
    
    cursor.executemany(
        "INSERT INTO users (username, password, real_name, role, phone) VALUES (?, ?, ?, ?, ?)",
        users
    )
    
    inspectors = [
        (2, 'INS001', '外观,底盘,发动机', 'available'),
        (3, 'INS002', '外观,底盘', 'available'),
        (4, 'INS003', '发动机,电气', 'available'),
    ]
    
    cursor.executemany(
        "INSERT INTO inspectors (user_id, employee_no, skill_tags, status) VALUES (?, ?, ?, ?)",
        inspectors
    )
    
    workstations = [
        ('WS-01', '外观检测', 'idle', 'A区-1号工位', '漆面检测仪,漆膜仪'),
        ('WS-02', '底盘检测', 'idle', 'A区-2号工位', '举升机,底盘检测仪'),
        ('WS-03', '发动机检测', 'idle', 'B区-1号工位', '发动机诊断仪,尾气分析仪'),
        ('WS-04', '综合检测', 'idle', 'B区-2号工位', '全套检测设备'),
        ('WS-05', '外观检测', 'idle', 'C区-1号工位', '漆面检测仪,漆膜仪'),
    ]
    
    cursor.executemany(
        "INSERT INTO workstations (name, station_type, status, location, tools) VALUES (?, ?, ?, ?, ?)",
        workstations
    )
    
    vehicles = [
        ('LSV2A4185N2123456', '大众', '帕萨特', 2022, 35000, '黑色', '无重大事故', 165000, 'pending_inspection', 2, 'A-01'),
        ('LFV2A21K5D4098765', '奥迪', 'A4L', 2021, 52000, '白色', '轻微剐蹭', 220000, 'pending_inspection', 1, 'A-02'),
        ('LHGCR2656E8023456', '本田', '雅阁', 2023, 18000, '银色', '无事故', 158000, 'inspecting', 3, 'B-01'),
        ('LVSHFFAL7KF654321', '福特', '蒙迪欧', 2020, 78000, '红色', '前保险杠更换', 98000, 'inspection_completed', 1, 'C-01'),
        ('LGBF1DE068Y123456', '日产', '天籁', 2022, 42000, '黑色', '无事故', 145000, 'pending_inspection', 2, 'A-03'),
        ('LSGPC54U9AF987654', '别克', '君威', 2021, 61000, '白色', '后门钣金', 132000, 'pending_inspection', 1, 'B-02'),
        ('LGWEF4A58KF456789', '哈弗', 'H6', 2023, 25000, '蓝色', '无事故', 95000, 'for_sale', 1, 'D-01'),
        ('LFMAP22K8F0234567', '丰田', '凯美瑞', 2019, 95000, '黑色', '追尾事故', 110000, 'pending_inspection', 2, 'C-02'),
        ('LHGCM56573A345678', '本田', 'CR-V', 2022, 38000, '白色', '无事故', 168000, 'for_sale', 1, 'D-02'),
        ('LSVNF2186M2567890', '大众', '迈腾', 2021, 48000, '黑色', '轻微划痕', 175000, 'reinspection', 3, 'B-03'),
    ]
    
    cursor.executemany(
        "INSERT INTO vehicles (vin, brand, model, year, mileage, color, accident_record, intended_price, status, urgent_level, parking_spot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        vehicles
    )
    
    parking_spots = []
    zones = ['A', 'B', 'C', 'D']
    spot_id = 1
    for zone in zones:
        for row in range(1, 6):
            for col in range(1, 6):
                spot_code = f"{zone}-{row}{col}"
                x = (ord(zone) - ord('A')) * 200 + col * 35
                y = row * 35
                status = 'empty'
                vehicle_id = None
                
                if spot_id <= 10:
                    status = 'occupied'
                    vehicle_id = spot_id
                
                parking_spots.append((spot_code, zone, row, col, status, vehicle_id, x, y))
                spot_id += 1
    
    cursor.executemany(
        "INSERT INTO parking_spots (spot_code, zone, row_num, col_num, status, vehicle_id, x_coord, y_coord) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        parking_spots
    )
    
    market_prices = [
        ('大众', '帕萨特', 2022, 168000, 45, '2024-01-15'),
        ('奥迪', 'A4L', 2021, 225000, 32, '2024-01-15'),
        ('本田', '雅阁', 2023, 160000, 58, '2024-01-15'),
        ('福特', '蒙迪欧', 2020, 102000, 28, '2024-01-15'),
        ('日产', '天籁', 2022, 148000, 42, '2024-01-15'),
        ('别克', '君威', 2021, 135000, 35, '2024-01-15'),
        ('哈弗', 'H6', 2023, 98000, 62, '2024-01-15'),
        ('丰田', '凯美瑞', 2019, 115000, 38, '2024-01-15'),
        ('本田', 'CR-V', 2022, 172000, 48, '2024-01-15'),
        ('大众', '迈腾', 2021, 178000, 36, '2024-01-15'),
    ]
    
    cursor.executemany(
        "INSERT INTO market_price_data (brand, model, year, avg_price, sample_count, data_date) VALUES (?, ?, ?, ?, ?, ?)",
        market_prices
    )
    
    conn.commit()
    conn.close()
