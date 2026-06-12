from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QLineEdit, QComboBox, QLabel, QDialog, QFormLayout, QMessageBox,
    QTextEdit, QSpinBox, QDoubleSpinBox, QHeaderView, QGroupBox, QSplitter
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush
from services.vehicle_service import VehicleService
from services.inspection_service import InspectionService

class VehicleManagementWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.refresh()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel('车辆信息管理')
        title.setStyleSheet('font-size: 20px; font-weight: bold; color: #2c3e50;')
        layout.addWidget(title)
        
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('搜索VIN码/品牌/型号...')
        self.search_input.textChanged.connect(self.refresh)
        filter_bar.addWidget(self.search_input)
        
        self.status_combo = QComboBox()
        self.status_combo.addItem('全部状态', None)
        self.status_combo.addItem('待检测', 'pending_inspection')
        self.status_combo.addItem('检测中', 'inspecting')
        self.status_combo.addItem('待复检', 'reinspection')
        self.status_combo.addItem('检测完成', 'inspection_completed')
        self.status_combo.addItem('在售', 'for_sale')
        self.status_combo.addItem('已售出', 'sold')
        self.status_combo.currentIndexChanged.connect(self.refresh)
        filter_bar.addWidget(self.status_combo)
        
        add_btn = QPushButton('➕ 新增车辆')
        add_btn.setStyleSheet('''
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        ''')
        add_btn.clicked.connect(self.show_add_dialog)
        filter_bar.addWidget(add_btn)
        
        filter_bar.addStretch()
        layout.addLayout(filter_bar)
        
        splitter = QSplitter(Qt.Vertical)
        
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            'ID', 'VIN码', '品牌', '型号', '年份', '里程(km)', 
            '意向售价(元)', '状态', '紧急度', '入库时间'
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.show_detail_dialog)
        splitter.addWidget(self.table)
        
        detail_group = QGroupBox('车辆详情')
        detail_layout = QVBoxLayout(detail_group)
        
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        detail_layout.addWidget(self.detail_text)
        
        btn_layout = QHBoxLayout()
        
        edit_btn = QPushButton('编辑')
        edit_btn.clicked.connect(self.show_edit_dialog)
        btn_layout.addWidget(edit_btn)
        
        self.inspection_history_btn = QPushButton('检测历史')
        self.inspection_history_btn.clicked.connect(self.show_inspection_history)
        btn_layout.addWidget(self.inspection_history_btn)
        
        detail_layout.addLayout(btn_layout)
        splitter.addWidget(detail_group)
        
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)
    
    def refresh(self):
        vehicles = VehicleService.list_vehicles(
            status=self.status_combo.currentData(),
            page_size=100
        )
        
        search_text = self.search_input.text().strip().lower()
        if search_text:
            vehicles = [v for v in vehicles 
                       if search_text in str(v.get('vin', '')).lower()
                       or search_text in str(v.get('brand', '')).lower()
                       or search_text in str(v.get('model', '')).lower()]
        
        self.table.setRowCount(len(vehicles))
        
        for row, vehicle in enumerate(vehicles):
            self.table.setItem(row, 0, QTableWidgetItem(str(vehicle['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(vehicle['vin']))
            self.table.setItem(row, 2, QTableWidgetItem(vehicle['brand']))
            self.table.setItem(row, 3, QTableWidgetItem(vehicle.get('model', '')))
            self.table.setItem(row, 4, QTableWidgetItem(str(vehicle.get('year', ''))))
            self.table.setItem(row, 5, QTableWidgetItem(f"{vehicle.get('mileage', 0):,.0f}"))
            self.table.setItem(row, 6, QTableWidgetItem(f"{vehicle.get('intended_price', 0):,.0f}"))
            
            status_item = QTableWidgetItem(self.get_status_text(vehicle['status']))
            status_item.setForeground(QBrush(self.get_status_color(vehicle['status'])))
            self.table.setItem(row, 7, status_item)
            
            urgent_text = '高' if vehicle.get('urgent_level', 1) >= 3 else ('中' if vehicle.get('urgent_level', 1) >= 2 else '低')
            urgent_item = QTableWidgetItem(urgent_text)
            if vehicle.get('urgent_level', 1) >= 3:
                urgent_item.setForeground(QBrush(QColor('#e74c3c')))
            self.table.setItem(row, 8, urgent_item)
            
            self.table.setItem(row, 9, QTableWidgetItem(vehicle.get('entry_date', '')[:10]))
        
        if vehicles:
            self.update_detail(vehicles[0])
            self.table.selectRow(0)
    
    def get_status_text(self, status):
        status_map = {
            'pending_inspection': '待检测',
            'inspecting': '检测中',
            'reinspection': '待复检',
            'inspection_completed': '检测完成',
            'for_sale': '在售',
            'sold': '已售出',
        }
        return status_map.get(status, status)
    
    def get_status_color(self, status):
        color_map = {
            'pending_inspection': QColor('#f39c12'),
            'inspecting': QColor('#3498db'),
            'reinspection': QColor('#e74c3c'),
            'inspection_completed': QColor('#27ae60'),
            'for_sale': QColor('#9b59b6'),
            'sold': QColor('#7f8c8d'),
        }
        return color_map.get(status, QColor('#333'))
    
    def update_detail(self, vehicle):
        detail = f"""车辆基本信息
{'='*40}
VIN码: {vehicle['vin']}
品牌: {vehicle['brand']}
型号: {vehicle.get('model', '-')}
年份: {vehicle.get('year', '-')}
颜色: {vehicle.get('color', '-')}
里程: {vehicle.get('mileage', 0):,.0f} km
意向售价: {vehicle.get('intended_price', 0):,.0f} 元
状态: {self.get_status_text(vehicle['status'])}
紧急度: {vehicle.get('urgent_level', 1)}
车位: {vehicle.get('parking_spot', '-')}

事故记录: {vehicle.get('accident_record', '无')}

备注: {vehicle.get('notes', '-')}

入库时间: {vehicle.get('entry_date', '-')}
"""
        self.detail_text.setText(detail)
    
    def show_add_dialog(self):
        dialog = VehicleEditDialog(self, mode='add')
        if dialog.exec():
            self.refresh()
            QMessageBox.information(self, '成功', '车辆信息添加成功')
    
    def show_edit_dialog(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, '提示', '请先选择一辆车')
            return
        
        vehicle_id = int(self.table.item(current_row, 0).text())
        vehicle = VehicleService.get_vehicle(vehicle_id)
        
        dialog = VehicleEditDialog(self, mode='edit', vehicle=vehicle)
        if dialog.exec():
            self.refresh()
            QMessageBox.information(self, '成功', '车辆信息更新成功')
    
    def show_detail_dialog(self, row, column):
        vehicle_id = int(self.table.item(row, 0).text())
        vehicle = VehicleService.get_vehicle(vehicle_id)
        if vehicle:
            self.update_detail(vehicle)
    
    def show_inspection_history(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, '提示', '请先选择一辆车')
            return
        
        vehicle_id = int(self.table.item(current_row, 0).text())
        history = InspectionService.get_inspection_history(vehicle_id)
        
        dialog = QDialog(self)
        dialog.setWindowTitle('检测历史记录')
        dialog.setMinimumSize(600, 400)
        layout = QVBoxLayout(dialog)
        
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(['检测阶段', '检测师', '工位', '状态', '开始时间', '结束时间'])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setRowCount(len(history))
        
        for row, record in enumerate(history):
            table.setItem(row, 0, QTableWidgetItem(record.get('inspection_stage', '-')))
            table.setItem(row, 1, QTableWidgetItem(record.get('inspector_name', '-')))
            table.setItem(row, 2, QTableWidgetItem(record.get('workstation_name', '-')))
            table.setItem(row, 3, QTableWidgetItem(self.get_inspection_status_text(record.get('status', ''))))
            table.setItem(row, 4, QTableWidgetItem(str(record.get('start_time', '-'))))
            table.setItem(row, 5, QTableWidgetItem(str(record.get('end_time', '-'))))
        
        layout.addWidget(table)
        
        close_btn = QPushButton('关闭')
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def get_inspection_status_text(self, status):
        status_map = {
            'in_progress': '进行中',
            'completed': '已完成',
            'recheck': '待复检',
            'failed': '未通过',
        }
        return status_map.get(status, status)


class VehicleEditDialog(QDialog):
    def __init__(self, parent=None, mode='add', vehicle=None):
        super().__init__(parent)
        self.mode = mode
        self.vehicle = vehicle
        self.setWindowTitle('新增车辆' if mode == 'add' else '编辑车辆')
        self.setMinimumSize(500, 600)
        self.setup_ui()
        
        if mode == 'edit' and vehicle:
            self.fill_data(vehicle)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        self.vin_input = QLineEdit()
        form_layout.addRow('VIN码 *', self.vin_input)
        
        self.brand_input = QLineEdit()
        form_layout.addRow('品牌 *', self.brand_input)
        
        self.model_input = QLineEdit()
        form_layout.addRow('型号', self.model_input)
        
        self.year_spin = QSpinBox()
        self.year_spin.setRange(1990, 2030)
        self.year_spin.setValue(2023)
        form_layout.addRow('年份', self.year_spin)
        
        self.color_input = QLineEdit()
        form_layout.addRow('颜色', self.color_input)
        
        self.mileage_spin = QDoubleSpinBox()
        self.mileage_spin.setRange(0, 1000000)
        self.mileage_spin.setSuffix(' km')
        form_layout.addRow('里程', self.mileage_spin)
        
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 10000000)
        self.price_spin.setPrefix('¥ ')
        self.price_spin.setSingleStep(1000)
        form_layout.addRow('意向售价', self.price_spin)
        
        self.urgent_combo = QComboBox()
        self.urgent_combo.addItem('低', 1)
        self.urgent_combo.addItem('中', 2)
        self.urgent_combo.addItem('高', 3)
        form_layout.addRow('紧急度', self.urgent_combo)
        
        self.parking_spot_input = QLineEdit()
        form_layout.addRow('车位编号', self.parking_spot_input)
        
        self.accident_record_input = QTextEdit()
        self.accident_record_input.setMaximumHeight(80)
        form_layout.addRow('事故记录', self.accident_record_input)
        
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        form_layout.addRow('备注', self.notes_input)
        
        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        
        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton('保存')
        save_btn.setStyleSheet('''
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        ''')
        save_btn.clicked.connect(self.save_data)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def fill_data(self, vehicle):
        self.vin_input.setText(vehicle.get('vin', ''))
        self.brand_input.setText(vehicle.get('brand', ''))
        self.model_input.setText(vehicle.get('model', ''))
        self.year_spin.setValue(vehicle.get('year', 2023))
        self.color_input.setText(vehicle.get('color', ''))
        self.mileage_spin.setValue(vehicle.get('mileage', 0))
        self.price_spin.setValue(vehicle.get('intended_price', 0))
        self.urgent_combo.setCurrentIndex(vehicle.get('urgent_level', 1) - 1)
        self.parking_spot_input.setText(vehicle.get('parking_spot', ''))
        self.accident_record_input.setText(vehicle.get('accident_record', ''))
        self.notes_input.setText(vehicle.get('notes', ''))
    
    def save_data(self):
        vin = self.vin_input.text().strip()
        brand = self.brand_input.text().strip()
        
        if not vin:
            QMessageBox.warning(self, '提示', '请输入VIN码')
            return
        if not brand:
            QMessageBox.warning(self, '提示', '请输入品牌')
            return
        
        data = {
            'vin': vin,
            'brand': brand,
            'model': self.model_input.text().strip(),
            'year': self.year_spin.value(),
            'color': self.color_input.text().strip(),
            'mileage': self.mileage_spin.value(),
            'intended_price': self.price_spin.value(),
            'urgent_level': self.urgent_combo.currentData(),
            'parking_spot': self.parking_spot_input.text().strip(),
            'accident_record': self.accident_record_input.toPlainText().strip(),
            'notes': self.notes_input.toPlainText().strip(),
        }
        
        try:
            if self.mode == 'add':
                if VehicleService.get_vehicle_by_vin(vin):
                    QMessageBox.warning(self, '提示', '该VIN码已存在')
                    return
                VehicleService.add_vehicle(**data)
            else:
                VehicleService.update_vehicle(self.vehicle['id'], **data)
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, '错误', f'保存失败: {str(e)}')
