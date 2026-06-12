from db.database import get_db_connection
from datetime import datetime
from services.alert_service import AlertService

class ApprovalService:
    @staticmethod
    def get_pending_approvals(approver_role=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT a.*, u.real_name as applicant_name
            FROM approval_requests a
            LEFT JOIN users u ON a.applicant_id = u.id
            WHERE a.status = 'pending'
        '''
        params = []
        
        if approver_role:
            query += " AND a.approver_role = ?"
            params.append(approver_role)
        
        query += " ORDER BY a.created_at DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    @staticmethod
    def approve_request(request_id, approver_id, notes=''):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE approval_requests 
                SET status = 'approved', approver_id = ?, approved_at = ?, approval_notes = ?
                WHERE id = ?
            ''', (approver_id, datetime.now(), notes, request_id))
            
            cursor.execute("SELECT * FROM approval_requests WHERE id = ?", (request_id,))
            request = dict(cursor.fetchone())
            
            if request['request_type'] == 'schedule_adjustment':
                cursor.execute('''
                    UPDATE inspection_schedules SET status = 'approved' WHERE id = ?
                ''', (request['related_id'],))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def reject_request(request_id, approver_id, reason=''):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE approval_requests 
                SET status = 'rejected', approver_id = ?, approved_at = ?, approval_notes = ?
                WHERE id = ?
            ''', (approver_id, datetime.now(), reason, request_id))
            
            cursor.execute("SELECT * FROM approval_requests WHERE id = ?", (request_id,))
            request = dict(cursor.fetchone())
            
            if request['request_type'] == 'schedule_adjustment':
                cursor.execute('''
                    UPDATE inspection_schedules SET status = 'approved' WHERE id = ?
                ''', (request['related_id'],))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def create_request(request_type, related_id, applicant_id, approver_role, title, reason):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO approval_requests 
                (request_type, related_id, applicant_id, approver_role, title, reason)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (request_type, related_id, applicant_id, approver_role, title, reason))
            conn.commit()
            
            AlertService.create_alert(
                alert_type=f'{request_type}_request',
                title=f'新的审批申请：{title}',
                content=reason,
                severity='warning',
                recipient_role=approver_role
            )
            
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
