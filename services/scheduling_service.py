from db.database import get_db_connection
from datetime import datetime, date, timedelta
from services.vehicle_service import VehicleService
from services.alert_service import AlertService

class SchedulingService:
    INSPECTION_STAGES = ['appearance', 'chassis', 'engine']
    STAGE_NAMES = {
        'appearance': '外观检测',
        'chassis': '底盘检测',
        'engine': '发动机检测'
    }
    STAGE_TOOL_SWITCH_TIME = {
        ('appearance', 'chassis'): 15,
        ('chassis', 'engine'): 20,
        ('appearance', 'engine'): 25
    }
    
    @staticmethod
    def generate_daily_schedule(schedule_date=None):
        if schedule_date is None:
            schedule_date = date.today()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        pending_vehicles = VehicleService.get_pending_inspection_vehicles()
        
        cursor.execute("SELECT * FROM inspectors WHERE status = 'available'")
        inspectors = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("SELECT * FROM workstations WHERE status != 'maintenance'")
        workstations = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("SELECT * FROM inspection_records WHERE end_time IS NOT NULL")
        history_records = [dict(row) for row in cursor.fetchall()]
        
        schedules = []
        
        for vehicle in pending_vehicles:
            vehicle_schedules = SchedulingService._schedule_vehicle(
                vehicle, inspectors, workstations, history_records, schedule_date
            )
            schedules.extend(vehicle_schedules)
        
        for sched in schedules:
            cursor.execute('''
                INSERT INTO inspection_schedules 
                (vehicle_id, inspector_id, workstation_id, schedule_date, 
                 start_time, end_time, inspection_type, status, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'pending_approval', ?)
            ''', (
                sched['vehicle_id'],
                sched['inspector_id'],
                sched['workstation_id'],
                schedule_date,
                sched['start_time'],
                sched['end_time'],
                sched['inspection_type'],
                sched['priority']
            ))
        
        conn.commit()
        conn.close()
        
        return schedules
    
    @staticmethod
    def _schedule_vehicle(vehicle, inspectors, workstations, history_records, schedule_date):
        schedules = []
        priority = vehicle['urgent_level']
        
        avg_durations = SchedulingService._calculate_avg_durations(vehicle, history_records)
        
        current_time = datetime.combine(schedule_date, datetime.strptime('08:00', '%H:%M').time())
        
        for stage in SchedulingService.INSPECTION_STAGES:
            stage_name = SchedulingService.STAGE_NAMES[stage]
            stage_cn = SchedulingService.STAGE_NAMES[stage].replace('检测', '')
            
            suitable_inspectors = [
                insp for insp in inspectors
                if stage_cn in (insp['skill_tags'] or '').split(',')
            ]
            
            suitable_stations = [
                ws for ws in workstations
                if stage_cn in ws['station_type'] or '综合' in ws['station_type']
            ]
            
            if not suitable_inspectors or not suitable_stations:
                continue
            
            duration = avg_durations.get(stage, 60)
            
            best_pair = SchedulingService._find_best_slot(
                suitable_inspectors, suitable_stations, 
                current_time, duration, schedule_date
            )
            
            if best_pair:
                start_time = best_pair['start_time']
                end_time = start_time + timedelta(minutes=duration)
                
                schedules.append({
                    'vehicle_id': vehicle['id'],
                    'inspector_id': best_pair['inspector_id'],
                    'workstation_id': best_pair['workstation_id'],
                    'start_time': start_time.strftime('%H:%M'),
                    'end_time': end_time.strftime('%H:%M'),
                    'inspection_type': stage_name,
                    'priority': priority
                })
                
                current_time = end_time
                
                if stage != SchedulingService.INSPECTION_STAGES[-1]:
                    next_stage = SchedulingService.INSPECTION_STAGES[
                        SchedulingService.INSPECTION_STAGES.index(stage) + 1
                    ]
                    switch_time = SchedulingService.STAGE_TOOL_SWITCH_TIME.get(
                        (stage, next_stage), 10
                    )
                    current_time += timedelta(minutes=switch_time)
        
        return schedules
    
    @staticmethod
    def _calculate_avg_durations(vehicle, history_records):
        durations = {}
        
        for stage in SchedulingService.INSPECTION_STAGES:
            stage_records = [
                r for r in history_records
                if r['inspection_stage'] == stage and r['end_time'] and r['start_time']
            ]
            
            if stage_records:
                total = 0
                count = 0
                for r in stage_records:
                    try:
                        start = datetime.strptime(r['start_time'], '%Y-%m-%d %H:%M:%S')
                        end = datetime.strptime(r['end_time'], '%Y-%m-%d %H:%M:%S')
                        total += (end - start).total_seconds() / 60
                        count += 1
                    except:
                        pass
                if count > 0:
                    durations[stage] = int(total / count)
        
        if not durations:
            durations = {
                'appearance': 45,
                'chassis': 60,
                'engine': 75
            }
        
        return durations
    
    @staticmethod
    def _find_best_slot(inspectors, workstations, earliest_time, duration, schedule_date):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        best_slot = None
        earliest_end = None
        
        for inspector in inspectors:
            for workstation in workstations:
                cursor.execute('''
                    SELECT start_time, end_time FROM inspection_schedules
                    WHERE inspector_id = ? AND workstation_id = ? 
                    AND schedule_date = ? AND status != 'cancelled'
                    ORDER BY start_time
                ''', (inspector['id'], workstation['id'], schedule_date))
                
                existing_slots = cursor.fetchall()
                
                slot_start = earliest_time
                
                for slot in existing_slots:
                    slot_end = datetime.combine(
                        schedule_date,
                        datetime.strptime(slot['end_time'], '%H:%M').time()
                    )
                    slot_start_actual = datetime.combine(
                        schedule_date,
                        datetime.strptime(slot['start_time'], '%H:%M').time()
                    )
                    
                    if slot_start + timedelta(minutes=duration) <= slot_start_actual:
                        break
                    else:
                        slot_start = max(slot_start, slot_end)
                
                slot_end = slot_start + timedelta(minutes=duration)
                
                work_end = datetime.combine(schedule_date, datetime.strptime('18:00', '%H:%M').time())
                if slot_end > work_end:
                    continue
                
                if earliest_end is None or slot_end < earliest_end:
                    earliest_end = slot_end
                    best_slot = {
                        'inspector_id': inspector['id'],
                        'workstation_id': workstation['id'],
                        'start_time': slot_start
                    }
        
        conn.close()
        return best_slot
    
    @staticmethod
    def get_pending_approval_schedules():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.*, v.vin, v.brand, v.model, i.employee_no, u.real_name as inspector_name,
                   ws.name as workstation_name
            FROM inspection_schedules s
            JOIN vehicles v ON s.vehicle_id = v.id
            LEFT JOIN inspectors i ON s.inspector_id = i.id
            LEFT JOIN users u ON i.user_id = u.id
            LEFT JOIN workstations ws ON s.workstation_id = ws.id
            WHERE s.status = 'pending_approval'
            ORDER BY s.priority DESC, s.schedule_date, s.start_time
        ''')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    @staticmethod
    def approve_schedule(schedule_id, approver_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE inspection_schedules 
                SET status = 'approved', approver_id = ?, approved_at = ?
                WHERE id = ?
            ''', (approver_id, datetime.now(), schedule_id))
            conn.commit()
            
            AlertService.create_alert(
                alert_type='schedule_approved',
                title='检测排程已审批',
                content=f'您的检测排程已通过审批',
                severity='info',
                recipient_role='inspector'
            )
            
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def reject_schedule(schedule_id, approver_id, reason=''):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE inspection_schedules 
                SET status = 'rejected', approver_id = ?, approved_at = ?
                WHERE id = ?
            ''', (approver_id, datetime.now(), schedule_id))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def get_schedules_by_date(schedule_date):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.*, v.vin, v.brand, v.model, i.employee_no, u.real_name as inspector_name,
                   ws.name as workstation_name
            FROM inspection_schedules s
            JOIN vehicles v ON s.vehicle_id = v.id
            LEFT JOIN inspectors i ON s.inspector_id = i.id
            LEFT JOIN users u ON i.user_id = u.id
            LEFT JOIN workstations ws ON s.workstation_id = ws.id
            WHERE s.schedule_date = ?
            ORDER BY s.start_time
        ''', (schedule_date,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    @staticmethod
    def request_schedule_adjustment(schedule_id, applicant_id, reason):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO approval_requests 
                (request_type, related_id, applicant_id, approver_role, title, reason)
                VALUES ('schedule_adjustment', ?, ?, 'chief_inspector', '检测排程调整申请', ?)
            ''', (schedule_id, applicant_id, reason))
            
            cursor.execute('''
                UPDATE inspection_schedules SET status = 'adjustment_pending' WHERE id = ?
            ''', (schedule_id,))
            
            conn.commit()
            
            AlertService.create_alert(
                alert_type='schedule_adjustment',
                title='检测排程调整申请',
                content=f'检测师申请调整排程，请及时处理',
                severity='warning',
                recipient_role='chief_inspector'
            )
            
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def get_today_schedules_by_inspector(inspector_id):
        today = date.today()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.*, v.vin, v.brand, v.model, ws.name as workstation_name
            FROM inspection_schedules s
            JOIN vehicles v ON s.vehicle_id = v.id
            JOIN workstations ws ON s.workstation_id = ws.id
            WHERE s.inspector_id = ? AND s.schedule_date = ? AND s.status = 'approved'
            ORDER BY s.start_time
        ''', (inspector_id, today))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
