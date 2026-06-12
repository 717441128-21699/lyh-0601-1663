from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem,
    QToolTip
)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QBrush, QPen, QFont, QPainter
from services.statistics_service import StatisticsService

class ParkingMapWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.refresh()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel('车库平面图')
        title.setStyleSheet('font-size: 20px; font-weight: bold; color: #2c3e50;')
        layout.addWidget(title)
        
        legend_group = QGroupBox('图例')
        legend_layout = QHBoxLayout(legend_group)
        
        legend_items = [
            ('空车位', '#ecf0f1'),
            ('待检测', '#f39c12'),
            ('检测中', '#e67e22'),
            ('待复检', '#e74c3c'),
            ('检测通过', '#27ae60'),
            ('检测未通过', '#c0392b'),
            ('在售', '#3498db'),
            ('已售出', '#2c3e50'),
        ]
        
        for name, color in legend_items:
            item_layout = QHBoxLayout()
            color_label = QLabel()
            color_label.setFixedSize(20, 20)
            color_label.setStyleSheet(f'background-color: {color}; border: 1px solid #999;')
            item_layout.addWidget(color_label)
            item_layout.addWidget(QLabel(name))
            legend_layout.addLayout(item_layout)
        
        legend_layout.addStretch()
        layout.addWidget(legend_group)
        
        self.view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.view.setStyleSheet('''
            QGraphicsView {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
        ''')
        layout.addWidget(self.view, 1)
        
        stats_layout = QHBoxLayout()
        
        self.total_spots_label = QLabel('总车位: 0')
        self.total_spots_label.setStyleSheet('font-size: 14px; font-weight: bold;')
        stats_layout.addWidget(self.total_spots_label)
        
        self.occupied_label = QLabel('已占用: 0')
        self.occupied_label.setStyleSheet('font-size: 14px; font-weight: bold; color: #3498db;')
        stats_layout.addWidget(self.occupied_label)
        
        self.empty_label = QLabel('空车位: 0')
        self.empty_label.setStyleSheet('font-size: 14px; font-weight: bold; color: #27ae60;')
        stats_layout.addWidget(self.empty_label)
        
        refresh_btn = QPushButton('🔄 刷新')
        refresh_btn.setStyleSheet('''
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        ''')
        refresh_btn.clicked.connect(self.refresh)
        stats_layout.addWidget(refresh_btn)
        
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
    
    def get_spot_color(self, spot):
        if spot['status'] == 'empty' or spot.get('vehicle_status') is None:
            return '#ecf0f1'
        
        vehicle_status = spot.get('vehicle_status', '')
        color_map = {
            'pending_inspection': '#f39c12',
            'inspecting': '#e67e22',
            'reinspection': '#e74c3c',
            'inspection_passed': '#27ae60',
            'inspection_failed': '#c0392b',
            'inspection_completed': '#27ae60',
            'for_sale': '#3498db',
            'sold': '#2c3e50',
        }
        return color_map.get(vehicle_status, '#95a5a6')
    
    def get_status_text(self, status):
        status_map = {
            'pending_inspection': '待检测',
            'inspecting': '检测中',
            'reinspection': '待复检',
            'inspection_passed': '检测通过',
            'inspection_failed': '检测未通过',
            'inspection_completed': '检测完成',
            'for_sale': '在售',
            'sold': '已售出',
        }
        return status_map.get(status, status)
    
    def refresh(self):
        self.scene.clear()
        
        heatmap_data = StatisticsService.get_heatmap_data()
        
        zones = {}
        for spot in heatmap_data:
            zone = spot['zone']
            if zone not in zones:
                zones[zone] = []
            zones[zone].append(spot)
        
        x_offset = 30
        y_offset = 40
        spot_width = 70
        spot_height = 45
        spot_spacing = 6
        zone_spacing = 100
        
        total_spots = len(heatmap_data)
        occupied = sum(1 for s in heatmap_data if s['status'] == 'occupied' and s.get('vehicle_status'))
        empty = total_spots - occupied
        
        self.total_spots_label.setText(f'总车位: {total_spots}')
        self.occupied_label.setText(f'已占用: {occupied}')
        self.empty_label.setText(f'空车位: {empty}')
        
        current_x = x_offset
        
        for zone_name in sorted(zones.keys()):
            zone_spots = zones[zone_name]
            
            rows = max(s['row_num'] for s in zone_spots)
            cols = max(s['col_num'] for s in zone_spots)
            
            zone_label = QGraphicsTextItem(f'{zone_name}区')
            zone_font = QFont('Microsoft YaHei', 12, QFont.Bold)
            zone_label.setFont(zone_font)
            zone_label.setPos(current_x, y_offset - 30)
            zone_label.setDefaultTextColor(QColor('#2c3e50'))
            self.scene.addItem(zone_label)
            
            for spot in zone_spots:
                row = spot['row_num'] - 1
                col = spot['col_num'] - 1
                
                x = current_x + col * (spot_width + spot_spacing)
                y = y_offset + row * (spot_height + spot_spacing)
                
                color = self.get_spot_color(spot)
                
                rect_item = ParkingSpotItem(
                    QRectF(x, y, spot_width, spot_height),
                    spot,
                    self
                )
                rect_item.setBrush(QBrush(QColor(color)))
                rect_item.setPen(QPen(QColor('#bdc3c7')))
                self.scene.addItem(rect_item)
                
                text = QGraphicsTextItem(spot['spot_code'])
                text_font = QFont('Microsoft YaHei', 8)
                text.setFont(text_font)
                text.setPos(x + 5, y + 4)
                
                if spot['status'] == 'empty' or not spot.get('vehicle_status'):
                    text.setDefaultTextColor(QColor('#95a5a6'))
                else:
                    text.setDefaultTextColor(QColor('#ffffff'))
                self.scene.addItem(text)
            
            current_x += cols * (spot_width + spot_spacing) + zone_spacing
        
        if self.scene.sceneRect().width() > 0:
            self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)


class ParkingSpotItem(QGraphicsRectItem):
    def __init__(self, rect, spot_data, parent_widget):
        super().__init__(rect)
        self.spot_data = spot_data
        self.parent_widget = parent_widget
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.PointingHandCursor)
    
    def hoverEnterEvent(self, event):
        spot = self.spot_data
        if spot['status'] == 'occupied' and spot.get('vehicle_status'):
            status_text = self.parent_widget.get_status_text(spot.get('vehicle_status', ''))
            tooltip = (
                f'车位: {spot["spot_code"]}\n'
                f'品牌: {spot.get("brand", "未知")}\n'
                f'型号: {spot.get("model", "")}\n'
                f'状态: {status_text}'
            )
        else:
            tooltip = f'车位: {spot["spot_code"]}\n状态: 空闲'
        
        QToolTip.showText(event.screenPos(), tooltip)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        QToolTip.hideText()
        super().hoverLeaveEvent(event)
