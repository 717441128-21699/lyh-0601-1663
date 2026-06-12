from db.database import get_db_connection
from datetime import datetime
from services.vehicle_service import VehicleService
from services.alert_service import AlertService

class InspectionService:
    WATER_DAMAGE_THRESHOLD = 60
    FIRE_DAMAGE_THRESHOLD = 50
    MAJOR_ACCIDENT_THRESHOLD = 70
    
    @staticmethod
    def start_inspection(schedule_id, inspector_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM inspection_schedules WHERE id = ?", (schedule_id,))
            schedule = cursor.fetchone()
            
            if not schedule:
                raise ValueError("排程不存在")
            
            vehicle_id = schedule['vehicle_id']
            workstation_id = schedule['workstation_id']
            
            cursor.execute('''
                INSERT INTO inspection_records 
                (vehicle_id, schedule_id, inspector_id, workstation_id, 
                 inspection_stage, start_time, status)
                VALUES (?, ?, ?, ?, ?, ?, 'in_progress')
            ''', (
                vehicle_id, schedule_id, inspector_id, workstation_id,
                schedule['inspection_type'], datetime.now()
            ))
            
            record_id = cursor.lastrowid
            
            cursor.execute("UPDATE vehicles SET status = 'inspecting' WHERE id = ?", (vehicle_id,))
            
            cursor.execute("UPDATE workstations SET status = 'occupied' WHERE id = ?", (workstation_id,))
            
            cursor.execute("UPDATE inspection_schedules SET status = 'in_progress' WHERE id = ?", (schedule_id,))
            
            conn.commit()
            return record_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def complete_inspection(record_id, scores, details=''):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM inspection_records WHERE id = ?", (record_id,))
            record = cursor.fetchone()
            
            if not record:
                raise ValueError("检测记录不存在")
            
            vehicle_id = record['vehicle_id']
            schedule_id = record['schedule_id']
            workstation_id = record['workstation_id']
            inspection_stage = record['inspection_stage']
            
            water_damage = scores.get('water_damage', 0)
            fire_damage = scores.get('fire_damage', 0)
            major_accident = scores.get('major_accident', 0)
            appearance = scores.get('appearance', 0)
            chassis = scores.get('chassis', 0)
            engine = scores.get('engine', 0)
            
            needs_reinspection = False
            reinspection_reasons = []
            
            if water_damage >= InspectionService.WATER_DAMAGE_THRESHOLD:
                needs_reinspection = True
                reinspection_reasons.append(f'泡水风险得分{water_damage}分，超过阈值')
            
            if fire_damage >= InspectionService.FIRE_DAMAGE_THRESHOLD:
                needs_reinspection = True
                reinspection_reasons.append(f'火烧风险得分{fire_damage}分，超过阈值')
            
            if major_accident >= InspectionService.MAJOR_ACCIDENT_THRESHOLD:
                needs_reinspection = True
                reinspection_reasons.append(f'重大事故风险得分{major_accident}分，超过阈值')
            
            if needs_reinspection:
                record_status = 'recheck'
                record_result = 'recheck'
            else:
                record_status = 'completed'
                avg_score = (appearance + chassis + engine) / 3
                if avg_score >= 60:
                    record_result = 'pass'
                else:
                    record_result = 'fail'
            
            update_fields = {
                'end_time': datetime.now(),
                'water_damage_score': water_damage,
                'fire_damage_score': fire_damage,
                'major_accident_score': major_accident,
                'appearance_score': appearance,
                'chassis_score': chassis,
                'engine_score': engine,
                'details': details,
                'status': record_status,
                'result': record_result
            }
            
            if needs_reinspection:
                update_fields['is_reinspection'] = 1
                update_fields['reinspection_reason'] = '; '.join(reinspection_reasons)
            
            set_clause = ', '.join([f"{k} = ?" for k in update_fields.keys()])
            values = list(update_fields.values()) + [record_id]
            
            cursor.execute(f"UPDATE inspection_records SET {set_clause} WHERE id = ?", values)
            
            new_vehicle_status = 'pending_inspection'
            
            if needs_reinspection:
                new_vehicle_status = 'reinspection'
            else:
                cursor.execute('''
                    SELECT COUNT(*) as cnt FROM inspection_schedules 
                    WHERE vehicle_id = ? AND status IN ('approved', 'in_progress', 'completed')
                ''', (vehicle_id,))
                total_stages = cursor.fetchone()['cnt']
                
                cursor.execute('''
                    SELECT COUNT(*) as cnt FROM inspection_records 
                    WHERE vehicle_id = ? AND status = 'completed'
                ''', (vehicle_id,))
                completed_stages = cursor.fetchone()['cnt']
                
                cursor.execute('''
                    SELECT result FROM inspection_records 
                    WHERE vehicle_id = ? AND status = 'completed'
                    ORDER BY created_at DESC
                ''', (vehicle_id,))
                all_results = [r['result'] for r in cursor.fetchall()]
                
                if completed_stages >= total_stages and total_stages > 0:
                    if 'fail' in all_results:
                        new_vehicle_status = 'inspection_failed'
                    else:
                        new_vehicle_status = 'inspection_passed'
                else:
                    new_vehicle_status = 'pending_inspection'
            
            cursor.execute("UPDATE vehicles SET status = ? WHERE id = ?", (new_vehicle_status, vehicle_id))
            
            cursor.execute("UPDATE workstations SET status = 'idle' WHERE id = ?", (workstation_id,))
            
            cursor.execute("UPDATE inspection_schedules SET status = 'completed' WHERE id = ?", (schedule_id,))
            
            conn.commit()
            
            if needs_reinspection:
                AlertService.create_alert(
                    vehicle_id=vehicle_id,
                    alert_type='reinspection_required',
                    title='复检预警',
                    content='; '.join(reinspection_reasons),
                    severity='critical',
                    recipient_role='chief_inspector'
                )
            
            return {
                'success': True,
                'needs_reinspection': needs_reinspection,
                'reasons': reinspection_reasons,
                'result': record_result
            }
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def get_current_inspection(inspector_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.*, v.vin, v.brand, v.model, ws.name as workstation_name
            FROM inspection_records r
            JOIN vehicles v ON r.vehicle_id = v.id
            JOIN workstations ws ON r.workstation_id = ws.id
            WHERE r.inspector_id = ? AND r.status = 'in_progress'
            ORDER BY r.start_time DESC
            LIMIT 1
        ''', (inspector_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    @staticmethod
    def get_inspection_history(vehicle_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.*, i.employee_no, u.real_name as inspector_name, ws.name as workstation_name
            FROM inspection_records r
            LEFT JOIN inspectors i ON r.inspector_id = i.id
            LEFT JOIN users u ON i.user_id = u.id
            LEFT JOIN workstations ws ON r.workstation_id = ws.id
            WHERE r.vehicle_id = ?
            ORDER BY r.created_at DESC
        ''', (vehicle_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    @staticmethod
    def get_inspection_items(record_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM inspection_items WHERE record_id = ? ORDER BY item_category, item_name
        ''', (record_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    @staticmethod
    def add_inspection_item(record_id, item_name, item_category, result, score, notes=''):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO inspection_items (record_id, item_name, item_category, result, score, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (record_id, item_name, item_category, result, score, notes))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def get_inspector_workload(inspector_id, start_date, end_date):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                COUNT(*) as total_inspections,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress
            FROM inspection_records
            WHERE inspector_id = ? 
            AND DATE(start_time) BETWEEN ? AND ?
        ''', (inspector_id, start_date, end_date))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
