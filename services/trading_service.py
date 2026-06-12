from db.database import get_db_connection
from datetime import datetime, date, timedelta
from services.alert_service import AlertService
from services.vehicle_service import VehicleService

class TradingService:
    INVENTORY_DAYS_NORMAL = 15
    INVENTORY_DAYS_OVERSTOCK = 30
    OVERSTOCK_PRICE_REDUCTION_RATE = 0.05
    
    @staticmethod
    def calculate_suggested_price(vehicle_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        vehicle = VehicleService.get_vehicle(vehicle_id)
        if not vehicle:
            raise ValueError("车辆不存在")
        
        cursor.execute('''
            SELECT avg_price FROM market_price_data
            WHERE brand = ? AND model = ? AND year = ?
            ORDER BY data_date DESC LIMIT 1
        ''', (vehicle['brand'], vehicle['model'], vehicle['year']))
        
        market_row = cursor.fetchone()
        base_price = market_row['avg_price'] if market_row else vehicle['intended_price']
        
        cursor.execute('''
            SELECT * FROM inspection_records
            WHERE vehicle_id = ? AND status = 'completed'
            ORDER BY created_at DESC LIMIT 1
        ''', (vehicle_id,))
        
        inspection_row = cursor.fetchone()
        
        inspection_adjustment = 0
        if inspection_row:
            if inspection_row['water_damage_score'] > 30:
                inspection_adjustment -= inspection_row['water_damage_score'] * 100
            if inspection_row['fire_damage_score'] > 30:
                inspection_adjustment -= inspection_row['fire_damage_score'] * 150
            if inspection_row['major_accident_score'] > 30:
                inspection_adjustment -= inspection_row['major_accident_score'] * 200
        
        stock_days = (date.today() - date.fromisoformat(vehicle['entry_date'].split(' ')[0])).days
        inventory_adjustment = 0
        if stock_days > TradingService.INVENTORY_DAYS_NORMAL:
            extra_days = stock_days - TradingService.INVENTORY_DAYS_NORMAL
            inventory_adjustment = -base_price * 0.005 * min(extra_days / 5, 10)
        
        mileage_adjustment = 0
        if vehicle['mileage']:
            avg_yearly_mileage = vehicle['mileage'] / max(date.today().year - vehicle['year'], 1)
            if avg_yearly_mileage > 25000:
                mileage_adjustment = -base_price * 0.05
            elif avg_yearly_mileage < 10000:
                mileage_adjustment = base_price * 0.03
        
        suggested_price = base_price + inspection_adjustment + inventory_adjustment + mileage_adjustment
        suggested_price = max(suggested_price, base_price * 0.5)
        
        calculation_basis = f'''基础市场价: {base_price:.0f}元
车况调整: {inspection_adjustment:.0f}元
库存调整: {inventory_adjustment:.0f}元
里程调整: {mileage_adjustment:.0f}元
建议售价: {suggested_price:.0f}元'''
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO price_suggestions 
                (vehicle_id, base_price, market_adjustment, inventory_adjustment, 
                 suggested_price, calculation_basis)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                vehicle_id,
                base_price,
                inspection_adjustment + mileage_adjustment,
                inventory_adjustment,
                suggested_price,
                calculation_basis
            ))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
        
        return {
            'base_price': base_price,
            'suggested_price': suggested_price,
            'calculation_basis': calculation_basis
        }
    
    @staticmethod
    def get_price_suggestion(vehicle_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM price_suggestions WHERE vehicle_id = ?", (vehicle_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    @staticmethod
    def create_buyer_offer(vehicle_id, buyer_name, buyer_phone, offer_price):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO buyer_offers (vehicle_id, buyer_name, buyer_phone, offer_price, status)
                VALUES (?, ?, ?, ?, 'pending_approval')
            ''', (vehicle_id, buyer_name, buyer_phone, offer_price))
            
            offer_id = cursor.lastrowid
            
            AlertService.create_alert(
                vehicle_id=vehicle_id,
                alert_type='new_offer',
                title='新买家出价待审批',
                content=f'{buyer_name} 出价 {offer_price:.0f} 元，请审批',
                severity='info',
                recipient_role='sales_manager'
            )
            
            conn.commit()
            return offer_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def approve_buyer_offer(offer_id, manager_id, approval_notes=''):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM buyer_offers WHERE id = ?", (offer_id,))
            offer = cursor.fetchone()
            
            if not offer:
                raise ValueError("出价记录不存在")
            
            vehicle_id = offer['vehicle_id']
            
            cursor.execute('''
                UPDATE buyer_offers 
                SET status = 'approved', sales_manager_id = ?, approved_at = ?, approval_notes = ?
                WHERE id = ?
            ''', (manager_id, datetime.now(), approval_notes, offer_id))
            
            contract_no = f"HT{datetime.now().strftime('%Y%m%d')}{offer_id:06d}"
            
            cursor.execute('''
                INSERT INTO contracts (contract_no, vehicle_id, offer_id, buyer_name, buyer_phone, final_price, status)
                VALUES (?, ?, ?, ?, ?, ?, 'active')
            ''', (
                contract_no, vehicle_id, offer_id,
                offer['buyer_name'], offer['buyer_phone'], offer['offer_price']
            ))
            
            VehicleService.update_status(vehicle_id, 'sold')
            
            cursor.execute("UPDATE parking_spots SET status = 'empty', vehicle_id = NULL WHERE vehicle_id = ?", (vehicle_id,))
            
            conn.commit()
            return contract_no
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def reject_buyer_offer(offer_id, manager_id, rejection_reason=''):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE buyer_offers 
                SET status = 'rejected', sales_manager_id = ?, approved_at = ?, approval_notes = ?
                WHERE id = ?
            ''', (manager_id, datetime.now(), rejection_reason, offer_id))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def get_pending_approval_offers():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT o.*, v.vin, v.brand, v.model, v.intended_price
            FROM buyer_offers o
            JOIN vehicles v ON o.vehicle_id = v.id
            WHERE o.status = 'pending_approval'
            ORDER BY o.offer_time DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    @staticmethod
    def check_overstock_vehicles():
        conn = get_db_connection()
        cursor = conn.cursor()
        
        overstock_vehicles = VehicleService.get_overstock_vehicles(TradingService.INVENTORY_DAYS_OVERSTOCK)
        
        results = []
        for vehicle in overstock_vehicles:
            cursor.execute('''
                SELECT id FROM alerts 
                WHERE vehicle_id = ? AND alert_type = 'overstock_reminder' 
                AND DATE(created_at) = DATE('now')
            ''', (vehicle['id'],))
            
            if not cursor.fetchone():
                AlertService.create_alert(
                    vehicle_id=vehicle['id'],
                    alert_type='overstock_reminder',
                    title='库存超期降价提醒',
                    content=f"车辆已库存{int(vehicle['stock_days'])}天，建议降价促销",
                    severity='warning',
                    recipient_role='marketing'
                )
                results.append(vehicle)
        
        conn.close()
        return results
    
    @staticmethod
    def apply_price_reduction(vehicle_id, new_price, reason, operator_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            vehicle = VehicleService.get_vehicle(vehicle_id)
            if not vehicle:
                raise ValueError("车辆不存在")
            
            original_price = vehicle['intended_price']
            
            cursor.execute('''
                INSERT INTO price_reduction_logs (vehicle_id, original_price, new_price, reduction_reason, operator_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (vehicle_id, original_price, new_price, reason, operator_id))
            
            VehicleService.update_vehicle(vehicle_id, intended_price=new_price)
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def get_contract(contract_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.*, v.vin, v.brand, v.model, v.year
            FROM contracts c
            JOIN vehicles v ON c.vehicle_id = v.id
            WHERE c.id = ?
        ''', (contract_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    @staticmethod
    def list_contracts(status=None, page=1, page_size=20):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT c.*, v.vin, v.brand, v.model
            FROM contracts c
            JOIN vehicles v ON c.vehicle_id = v.id
            WHERE 1=1
        '''
        params = []
        
        if status:
            query += " AND c.status = ?"
            params.append(status)
        
        query += " ORDER BY c.sign_date DESC LIMIT ? OFFSET ?"
        params.extend([page_size, (page - 1) * page_size])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
