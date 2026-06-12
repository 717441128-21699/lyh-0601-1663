from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QLabel, QMessageBox, QHeaderView, QGroupBox, QFormLayout, QLineEdit,
    QDoubleSpinBox, QDialog, QTextEdit, QComboBox, QTabWidget, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush
from services.trading_service import TradingService
from services.vehicle_service import VehicleService
from services.auth_service import AuthService

class TradingWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.refresh()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel('交易管理')
        title.setStyleSheet('font-size: 20px; font-weight: bold; color: #2c3e50;')
        layout.addWidget(title)
        
        self.tab_widget = QTabWidget()
        
        self.vehicle_tab = QWidget()
        self.setup_vehicle_tab()
        self.tab_widget.addTab(self.vehicle_tab, '在售车辆')
        
        self.offer_tab = QWidget()
        self.setup_offer_tab()
        self.tab_widget.addTab(self.offer_tab, '出价审批')
        
        self.contract_tab = QWidget()
        self.setup_contract_tab()
        self.tab_widget.addTab(self.contract_tab, '合同管理')
        
        self.overstock_tab = QWidget()
        self.setup_overstock_tab()
        self.tab_widget.addTab(self.overstock_tab, '库存预警')
        
        layout.addWidget(self.tab_widget)
    
    def setup_vehicle_tab(self):
        layout = QVBoxLayout(self.vehicle_tab)
        
        toolbar = QHBoxLayout()
        
        calc_price_btn = QPushButton('💰 计算建议售价')
        calc_price_btn.setStyleSheet('''
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover { background-color: #8e44ad; }
        ''')
        calc_price_btn.clicked.connect(self.calculate_suggested_price)
        toolbar.addWidget(calc_price_btn)
        
        create_offer_btn = QPushButton('🤝 新建出价')
        create_offer_btn.setStyleSheet('''
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover { background-color: #2980b9; }
        ''')
        create_offer_btn.clicked.connect(self.create_offer)
        toolbar.addWidget(create_offer_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        self.vehicle_table = QTableWidget()
        self.vehicle_table.setColumnCount(8)
        self.vehicle_table.setHorizontalHeaderLabels([
            'ID', 'VIN码', '品牌', '型号', '年份', '里程(km)',
            '意向售价(元)', '库存天数'
        ])
        self.vehicle_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.vehicle_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.vehicle_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.vehicle_table)
        
        detail_group = QGroupBox('建议售价详情')
        detail_layout = QVBoxLayout(detail_group)
        self.price_detail = QTextEdit()
        self.price_detail.setReadOnly(True)
        self.price_detail.setMaximumHeight(150)
        detail_layout.addWidget(self.price_detail)
        layout.addWidget(detail_group)
    
    def setup_offer_tab(self):
        layout = QVBoxLayout(self.offer_tab)
        
        self.offer_table = QTableWidget()
        self.offer_table.setColumnCount(7)
        self.offer_table.setHorizontalHeaderLabels([
            'ID', 'VIN码', '品牌', '买家姓名', '出价(元)', '出价时间', '状态'
        ])
        self.offer_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.offer_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.offer_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.offer_table)
        
        btn_layout = QHBoxLayout()
        
        approve_btn = QPushButton('✅ 批准出价')
        approve_btn.setStyleSheet('background-color: #27ae60; color: white; padding: 8px 16px; border-radius: 4px; border: none;')
        approve_btn.clicked.connect(lambda: self.handle_offer_approval('approve'))
        btn_layout.addWidget(approve_btn)
        
        reject_btn = QPushButton('❌ 拒绝出价')
        reject_btn.setStyleSheet('background-color: #e74c3c; color: white; padding: 8px 16px; border-radius: 4px; border: none;')
        reject_btn.clicked.connect(lambda: self.handle_offer_approval('reject'))
        btn_layout.addWidget(reject_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def setup_contract_tab(self):
        layout = QVBoxLayout(self.contract_tab)
        
        self.contract_table = QTableWidget()
        self.contract_table.setColumnCount(7)
        self.contract_table.setHorizontalHeaderLabels([
            '合同编号', 'VIN码', '品牌', '买家', '成交价(元)', '签订时间', '状态'
        ])
        self.contract_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.contract_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.contract_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.contract_table)
        
        detail_btn = QPushButton('查看合同详情')
        detail_btn.clicked.connect(self.show_contract_detail)
        layout.addWidget(detail_btn)
    
    def setup_overstock_tab(self):
        layout = QVBoxLayout(self.overstock_tab)
        
        info_label = QLabel('超期库存车辆（超过30天未售出）')
        info_label.setStyleSheet('font-weight: bold; color: #e74c3c;')
        layout.addWidget(info_label)
        
        refresh_btn = QPushButton('🔄 刷新预警')
        refresh_btn.clicked.connect(self.refresh_overstock)
        layout.addWidget(refresh_btn)
        
        self.overstock_table = QTableWidget()
        self.overstock_table.setColumnCount(8)
        self.overstock_table.setHorizontalHeaderLabels([
            'ID', 'VIN码', '品牌', '型号', '意向售价(元)', '库存天数', '建议降价', '操作'
        ])
        self.overstock_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.overstock_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.overstock_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.overstock_table)
        
        price_reduction_btn = QPushButton('📉 批量降价提醒')
        price_reduction_btn.setStyleSheet('background-color: #e67e22; color: white; padding: 8px 16px; border-radius: 4px; border: none;')
        price_reduction_btn.clicked.connect(self.notify_marketing)
        layout.addWidget(price_reduction_btn)
    
    def refresh(self):
        self.refresh_vehicles()
        self.refresh_offers()
        self.refresh_contracts()
        self.refresh_overstock()
    
    def refresh_vehicles(self):
        vehicles = VehicleService.get_for_sale_vehicles()
        
        self.vehicle_table.setRowCount(len(vehicles))
        
        for row, vehicle in enumerate(vehicles):
            self.vehicle_table.setItem(row, 0, QTableWidgetItem(str(vehicle['id'])))
            self.vehicle_table.setItem(row, 1, QTableWidgetItem(vehicle['vin']))
            self.vehicle_table.setItem(row, 2, QTableWidgetItem(vehicle['brand']))
            self.vehicle_table.setItem(row, 3, QTableWidgetItem(vehicle.get('model', '')))
            self.vehicle_table.setItem(row, 4, QTableWidgetItem(str(vehicle.get('year', ''))))
            self.vehicle_table.setItem(row, 5, QTableWidgetItem(f"{vehicle.get('mileage', 0):,.0f}"))
            self.vehicle_table.setItem(row, 6, QTableWidgetItem(f"{vehicle.get('intended_price', 0):,.0f}"))
            
            from datetime import date, datetime
            try:
                entry_date = datetime.strptime(vehicle['entry_date'].split(' ')[0], '%Y-%m-%d').date()
                stock_days = (date.today() - entry_date).days
                days_item = QTableWidgetItem(str(stock_days))
                if stock_days > 30:
                    days_item.setForeground(QBrush(QColor('#e74c3c')))
                self.vehicle_table.setItem(row, 7, days_item)
            except:
                self.vehicle_table.setItem(row, 7, QTableWidgetItem('-'))
    
    def refresh_offers(self):
        offers = TradingService.get_pending_approval_offers()
        
        self.offer_table.setRowCount(len(offers))
        
        for row, offer in enumerate(offers):
            self.offer_table.setItem(row, 0, QTableWidgetItem(str(offer['id'])))
            self.offer_table.setItem(row, 1, QTableWidgetItem(offer['vin']))
            self.offer_table.setItem(row, 2, QTableWidgetItem(offer['brand']))
            self.offer_table.setItem(row, 3, QTableWidgetItem(offer['buyer_name']))
            self.offer_table.setItem(row, 4, QTableWidgetItem(f"{offer['offer_price']:,.0f}"))
            self.offer_table.setItem(row, 5, QTableWidgetItem(offer.get('offer_time', '')[:16]))
            
            status_item = QTableWidgetItem(self.get_offer_status_text(offer['status']))
            status_item.setForeground(QBrush(self.get_offer_status_color(offer['status'])))
            self.offer_table.setItem(row, 6, status_item)
    
    def refresh_contracts(self):
        contracts = TradingService.list_contracts(page_size=50)
        
        self.contract_table.setRowCount(len(contracts))
        
        for row, contract in enumerate(contracts):
            self.contract_table.setItem(row, 0, QTableWidgetItem(contract['contract_no']))
            self.contract_table.setItem(row, 1, QTableWidgetItem(contract['vin']))
            self.contract_table.setItem(row, 2, QTableWidgetItem(contract['brand']))
            self.contract_table.setItem(row, 3, QTableWidgetItem(contract.get('buyer_name', '-')))
            self.contract_table.setItem(row, 4, QTableWidgetItem(f"{contract.get('final_price', 0):,.0f}"))
            self.contract_table.setItem(row, 5, QTableWidgetItem(contract.get('sign_date', '')[:10]))
            self.contract_table.setItem(row, 6, QTableWidgetItem(contract.get('status', '')))
    
    def refresh_overstock(self):
        overstock = TradingService.check_overstock_vehicles()
        
        vehicles = VehicleService.get_overstock_vehicles(30)
        
        self.overstock_table.setRowCount(len(vehicles))
        
        for row, vehicle in enumerate(vehicles):
            self.overstock_table.setItem(row, 0, QTableWidgetItem(str(vehicle['id'])))
            self.overstock_table.setItem(row, 1, QTableWidgetItem(vehicle['vin']))
            self.overstock_table.setItem(row, 2, QTableWidgetItem(vehicle['brand']))
            self.overstock_table.setItem(row, 3, QTableWidgetItem(vehicle.get('model', '')))
            self.overstock_table.setItem(row, 4, QTableWidgetItem(f"{vehicle.get('intended_price', 0):,.0f}"))
            
            days_item = QTableWidgetItem(str(int(vehicle.get('stock_days', 0))))
            days_item.setForeground(QBrush(QColor('#e74c3c')))
            self.overstock_table.setItem(row, 5, days_item)
            
            suggested_reduction = vehicle.get('intended_price', 0) * 0.05
            self.overstock_table.setItem(row, 6, QTableWidgetItem(f"-{suggested_reduction:,.0f}元"))
            
            action_btn = QPushButton('降价')
            action_btn.clicked.connect(lambda _, vid=vehicle['id']: self.apply_price_reduction(vid))
            self.overstock_table.setCellWidget(row, 7, action_btn)
    
    def get_offer_status_text(self, status):
        status_map = {
            'pending_approval': '待审批',
            'approved': '已批准',
            'rejected': '已拒绝',
            'expired': '已过期',
        }
        return status_map.get(status, status)
    
    def get_offer_status_color(self, status):
        color_map = {
            'pending_approval': QColor('#f39c12'),
            'approved': QColor('#27ae60'),
            'rejected': QColor('#e74c3c'),
            'expired': QColor('#7f8c8d'),
        }
        return color_map.get(status, QColor('#333'))
    
    def calculate_suggested_price(self):
        current_row = self.vehicle_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, '提示', '请先选择一辆车')
            return
        
        vehicle_id = int(self.vehicle_table.item(current_row, 0).text())
        
        try:
            result = TradingService.calculate_suggested_price(vehicle_id)
            self.price_detail.setText(result['calculation_basis'])
            QMessageBox.information(self, '成功', f"建议售价: {result['suggested_price']:,.0f} 元")
        except Exception as e:
            QMessageBox.critical(self, '错误', f'计算失败: {str(e)}')
    
    def create_offer(self):
        current_row = self.vehicle_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, '提示', '请先选择一辆车')
            return
        
        vehicle_id = int(self.vehicle_table.item(current_row, 0).text())
        
        dialog = OfferDialog(self, vehicle_id)
        if dialog.exec():
            self.refresh_offers()
            QMessageBox.information(self, '成功', '出价记录已创建')
    
    def handle_offer_approval(self, action):
        current_row = self.offer_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, '提示', '请先选择一条出价记录')
            return
        
        offer_id = int(self.offer_table.item(current_row, 0).text())
        user = AuthService.get_current_user()
        
        if action == 'approve':
            reply = QMessageBox.question(
                self, '确认批准',
                '确定要批准此出价吗？批准后将自动生成电子合同。',
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                try:
                    contract_no = TradingService.approve_buyer_offer(offer_id, user['id'])
                    QMessageBox.information(self, '成功', f'出价已批准，合同编号: {contract_no}')
                    self.refresh()
                except Exception as e:
                    QMessageBox.critical(self, '错误', f'批准失败: {str(e)}')
        else:
            reason, ok = self.get_reject_reason()
            if ok:
                try:
                    TradingService.reject_buyer_offer(offer_id, user['id'], reason)
                    QMessageBox.information(self, '成功', '出价已拒绝')
                    self.refresh_offers()
                except Exception as e:
                    QMessageBox.critical(self, '错误', f'拒绝失败: {str(e)}')
    
    def get_reject_reason(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('拒绝原因')
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel('请输入拒绝原因:'))
        
        reason_edit = QTextEdit()
        reason_edit.setMaximumHeight(150)
        layout.addWidget(reason_edit)
        
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton('确定')
        ok_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        if dialog.exec():
            return reason_edit.toPlainText(), True
        return '', False
    
    def show_contract_detail(self):
        current_row = self.contract_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, '提示', '请先选择一份合同')
            return
        
        contract_no = self.contract_table.item(current_row, 0).text()
        
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f'合同详情 - {contract_no}')
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        detail_text = QTextEdit()
        detail_text.setReadOnly(True)
        detail_text.setText(f'''合同编号: {contract_no}

【二手车买卖合同】

甲方（卖方）：二手车交易市场
乙方（买方）：[买家姓名]

经双方协商一致，就二手车买卖事宜达成如下协议：

1. 车辆信息
   车辆VIN码：[VIN码]
   品牌型号：[品牌型号]
   成交价：人民币 [价格] 元整

2. 付款方式
   乙方应在签订本合同当日支付全部车款。

3. 车辆交付
   甲方应在收到全部车款后3个工作日内交付车辆。

4. 双方权利义务
   （略）

5. 违约责任
   （略）

6. 争议解决
   本合同履行过程中发生的争议，双方协商解决；协商不成的，可向当地人民法院起诉。

合同签订日期：[日期]

（此为系统生成电子合同预览）
''')
        layout.addWidget(detail_text)
        
        close_btn = QPushButton('关闭')
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def apply_price_reduction(self, vehicle_id):
        vehicle = VehicleService.get_vehicle(vehicle_id)
        if not vehicle:
            return
        
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QDoubleSpinBox, QTextEdit, QPushButton, QHBoxLayout
        
        dialog = QDialog(self)
        dialog.setWindowTitle('调整售价')
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        
        current_price = QLabel(f"{vehicle['intended_price']:,.0f} 元")
        form.addRow('当前售价:', current_price)
        
        new_price_spin = QDoubleSpinBox()
        new_price_spin.setRange(0, 10000000)
        new_price_spin.setValue(vehicle['intended_price'] * 0.95)
        new_price_spin.setPrefix('¥ ')
        form.addRow('新售价:', new_price_spin)
        
        reason_edit = QTextEdit()
        reason_edit.setMaximumHeight(100)
        reason_edit.setPlaceholderText('降价原因...')
        form.addRow('降价原因:', reason_edit)
        
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton('确认调整')
        ok_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        if dialog.exec():
            user = AuthService.get_current_user()
            try:
                TradingService.apply_price_reduction(
                    vehicle_id, new_price_spin.value(),
                    reason_edit.toPlainText(), user['id']
                )
                QMessageBox.information(self, '成功', '售价已调整')
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, '错误', f'调整失败: {str(e)}')
    
    def notify_marketing(self):
        from services.alert_service import AlertService
        
        vehicles = VehicleService.get_overstock_vehicles(30)
        count = len(vehicles)
        
        if count == 0:
            QMessageBox.information(self, '提示', '没有超期库存车辆')
            return
        
        AlertService.create_alert(
            alert_type='overstock_batch',
            title='批量库存降价提醒',
            content=f'共有 {count} 辆车库存超30天，请营销部门关注',
            severity='warning',
            recipient_role='marketing'
        )
        
        QMessageBox.information(self, '成功', f'已向营销部门推送 {count} 条降价提醒')


class OfferDialog(QDialog):
    def __init__(self, parent=None, vehicle_id=None):
        super().__init__(parent)
        self.vehicle_id = vehicle_id
        self.setWindowTitle('新建买家出价')
        self.setMinimumWidth(400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        self.buyer_name_input = QLineEdit()
        form.addRow('买家姓名 *', self.buyer_name_input)
        
        self.buyer_phone_input = QLineEdit()
        form.addRow('联系电话', self.buyer_phone_input)
        
        self.offer_price_spin = QDoubleSpinBox()
        self.offer_price_spin.setRange(0, 10000000)
        self.offer_price_spin.setPrefix('¥ ')
        self.offer_price_spin.setSingleStep(1000)
        form.addRow('出价金额 *', self.offer_price_spin)
        
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        
        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton('提交')
        save_btn.setStyleSheet('background-color: #3498db; color: white; padding: 8px 20px; border-radius: 4px; border: none;')
        save_btn.clicked.connect(self.save_data)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def save_data(self):
        buyer_name = self.buyer_name_input.text().strip()
        offer_price = self.offer_price_spin.value()
        
        if not buyer_name:
            QMessageBox.warning(self, '提示', '请输入买家姓名')
            return
        if offer_price <= 0:
            QMessageBox.warning(self, '提示', '请输入有效出价')
            return
        
        try:
            TradingService.create_buyer_offer(
                self.vehicle_id,
                buyer_name,
                self.buyer_phone_input.text().strip(),
                offer_price
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, '错误', f'提交失败: {str(e)}')
