from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QLabel, QMessageBox, QHeaderView, QGroupBox, QFormLayout, QSpinBox,
    QTextEdit, QProgressBar, QFrame
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QBrush, QFont
from services.inspection_service import InspectionService
from services.scheduling_service import SchedulingService
from services.auth_service import AuthService
from datetime import datetime

class InspectionWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.current_record_id = None
        self.setup_ui()
        self.refresh()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel('检测终端')
        title.setStyleSheet('font-size: 20px; font-weight: bold; color: #2c3e50;')
        layout.addWidget(title)
        
        current_group = QGroupBox('当前检测任务')
        current_layout = QVBoxLayout(current_group)
        
        self.current_info = QLabel('暂无进行中的检测任务')
        self.current_info.setStyleSheet('font-size: 14px; padding: 10px;')
        current_layout.addWidget(self.current_info)
        
        self.timer_label = QLabel('00:00:00')
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet('font-size: 32px; font-weight: bold; color: #3498db; font-family: monospace;')
        current_layout.addWidget(self.timer_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        current_layout.addWidget(self.progress_bar)
        
        btn_layout = QHBoxLayout()
        
        self.start_btn = QPushButton('▶ 开始检测')
        self.start_btn.setStyleSheet('''
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px 20px;
                border-radius: 4px;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #229954; }
        ''')
        self.start_btn.clicked.connect(self.start_inspection)
        btn_layout.addWidget(self.start_btn)
        
        self.complete_btn = QPushButton('✓ 完成检测')
        self.complete_btn.setStyleSheet('''
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 20px;
                border-radius: 4px;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #2980b9; }
        ''')
        self.complete_btn.clicked.connect(self.complete_inspection)
        self.complete_btn.setEnabled(False)
        btn_layout.addWidget(self.complete_btn)
        
        self.adjust_btn = QPushButton('🔄 申请调整')
        self.adjust_btn.setStyleSheet('''
            QPushButton {
                background-color: #f39c12;
                color: white;
                padding: 10px 20px;
                border-radius: 4px;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #e67e22; }
        ''')
        self.adjust_btn.clicked.connect(self.request_adjustment)
        btn_layout.addWidget(self.adjust_btn)
        
        current_layout.addLayout(btn_layout)
        layout.addWidget(current_group)
        
        schedule_group = QGroupBox('今日排程')
        schedule_layout = QVBoxLayout(schedule_group)
        
        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(6)
        self.schedule_table.setHorizontalHeaderLabels([
            'ID', 'VIN码', '品牌型号', '检测项目', '工位', '时间'
        ])
        self.schedule_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.schedule_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.schedule_table.setEditTriggers(QTableWidget.NoEditTriggers)
        schedule_layout.addWidget(self.schedule_table)
        
        layout.addWidget(schedule_group, 1)
        
        scoring_group = QGroupBox('检测评分')
        scoring_layout = QFormLayout(scoring_group)
        
        self.water_damage_spin = QSpinBox()
        self.water_damage_spin.setRange(0, 100)
        self.water_damage_spin.setValue(0)
        scoring_layout.addRow('泡水风险 (0-100):', self.water_damage_spin)
        
        self.fire_damage_spin = QSpinBox()
        self.fire_damage_spin.setRange(0, 100)
        self.fire_damage_spin.setValue(0)
        scoring_layout.addRow('火烧风险 (0-100):', self.fire_damage_spin)
        
        self.major_accident_spin = QSpinBox()
        self.major_accident_spin.setRange(0, 100)
        self.major_accident_spin.setValue(0)
        scoring_layout.addRow('重大事故风险 (0-100):', self.major_accident_spin)
        
        self.appearance_spin = QSpinBox()
        self.appearance_spin.setRange(0, 100)
        self.appearance_spin.setValue(80)
        scoring_layout.addRow('外观评分 (0-100):', self.appearance_spin)
        
        self.chassis_spin = QSpinBox()
        self.chassis_spin.setRange(0, 100)
        self.chassis_spin.setValue(80)
        scoring_layout.addRow('底盘评分 (0-100):', self.chassis_spin)
        
        self.engine_spin = QSpinBox()
        self.engine_spin.setRange(0, 100)
        self.engine_spin.setValue(80)
        scoring_layout.addRow('发动机评分 (0-100):', self.engine_spin)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText('检测备注...')
        scoring_layout.addRow('检测备注:', self.notes_edit)
        
        layout.addWidget(scoring_group)
    
    def refresh(self):
        user = AuthService.get_current_user()
        if not user:
            return
        
        inspector = AuthService.get_inspector_by_user_id(user['id'])
        if not inspector:
            return
        
        inspector_id = inspector['id']
        
        current = InspectionService.get_current_inspection(inspector_id)
        if current:
            self.current_record_id = current['id']
            self.current_info.setText(
                f"正在检测: {current['brand']} {current.get('model', '')} ({current['vin']})\n"
                f"工位: {current['workstation_name']} | 项目: {current['inspection_stage']}"
            )
            self.start_btn.setEnabled(False)
            self.complete_btn.setEnabled(True)
            
            try:
                start_time = datetime.strptime(current['start_time'], '%Y-%m-%d %H:%M:%S')
                elapsed = datetime.now() - start_time
                hours = int(elapsed.total_seconds() // 3600)
                minutes = int((elapsed.total_seconds() % 3600) // 60)
                seconds = int(elapsed.total_seconds() % 60)
                self.timer_label.setText(f'{hours:02d}:{minutes:02d}:{seconds:02d}')
            except:
                pass
        else:
            self.current_record_id = None
            self.current_info.setText('暂无进行中的检测任务')
            self.start_btn.setEnabled(True)
            self.complete_btn.setEnabled(False)
            self.timer_label.setText('00:00:00')
        
        schedules = SchedulingService.get_today_schedules_by_inspector(inspector_id)
        self.schedule_table.setRowCount(len(schedules))
        
        for row, sched in enumerate(schedules):
            self.schedule_table.setItem(row, 0, QTableWidgetItem(str(sched['id'])))
            self.schedule_table.setItem(row, 1, QTableWidgetItem(sched['vin']))
            self.schedule_table.setItem(row, 2, QTableWidgetItem(f"{sched['brand']} {sched.get('model', '')}"))
            self.schedule_table.setItem(row, 3, QTableWidgetItem(sched.get('inspection_type', '')))
            self.schedule_table.setItem(row, 4, QTableWidgetItem(sched['workstation_name']))
            self.schedule_table.setItem(row, 5, QTableWidgetItem(f"{sched['start_time']} - {sched['end_time']}"))
    
    def update_timer(self):
        if self.current_record_id:
            text = self.timer_label.text()
            try:
                parts = text.split(':')
                hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
                seconds += 1
                if seconds >= 60:
                    seconds = 0
                    minutes += 1
                if minutes >= 60:
                    minutes = 0
                    hours += 1
                self.timer_label.setText(f'{hours:02d}:{minutes:02d}:{seconds:02d}')
            except:
                pass
    
    def start_inspection(self):
        current_row = self.schedule_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, '提示', '请先选择一条排程')
            return
        
        schedule_id = int(self.schedule_table.item(current_row, 0).text())
        user = AuthService.get_current_user()
        inspector = AuthService.get_inspector_by_user_id(user['id'])
        
        try:
            record_id = InspectionService.start_inspection(schedule_id, inspector['id'])
            QMessageBox.information(self, '成功', '检测已开始')
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, '错误', f'开始检测失败: {str(e)}')
    
    def complete_inspection(self):
        if not self.current_record_id:
            QMessageBox.warning(self, '提示', '没有进行中的检测')
            return
        
        scores = {
            'water_damage': self.water_damage_spin.value(),
            'fire_damage': self.fire_damage_spin.value(),
            'major_accident': self.major_accident_spin.value(),
            'appearance': self.appearance_spin.value(),
            'chassis': self.chassis_spin.value(),
            'engine': self.engine_spin.value(),
        }
        
        details = self.notes_edit.toPlainText()
        
        reply = QMessageBox.question(
            self, '确认完成',
            '确定要完成本次检测吗？',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                result = InspectionService.complete_inspection(
                    self.current_record_id, scores, details
                )
                
                if result['needs_reinspection']:
                    QMessageBox.warning(
                        self, '复检提醒',
                        '检测完成，但触发复检条件！\n原因:\n' + '\n'.join(result['reasons'])
                    )
                else:
                    QMessageBox.information(self, '成功', '检测已完成')
                
                self.refresh()
                self.notes_edit.clear()
            except Exception as e:
                QMessageBox.critical(self, '错误', f'完成检测失败: {str(e)}')
    
    def request_adjustment(self):
        current_row = self.schedule_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, '提示', '请先选择一条排程')
            return
        
        schedule_id = int(self.schedule_table.item(current_row, 0).text())
        user = AuthService.get_current_user()
        
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle('申请调整排程')
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel('请输入调整原因:'))
        
        reason_edit = QTextEdit()
        reason_edit.setMaximumHeight(150)
        layout.addWidget(reason_edit)
        
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton('提交申请')
        ok_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        if dialog.exec():
            reason = reason_edit.toPlainText()
            if not reason:
                QMessageBox.warning(self, '提示', '请输入调整原因')
                return
            
            try:
                SchedulingService.request_schedule_adjustment(schedule_id, user['id'], reason)
                QMessageBox.information(self, '成功', '调整申请已提交，等待主管审批')
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, '错误', f'申请失败: {str(e)}')
