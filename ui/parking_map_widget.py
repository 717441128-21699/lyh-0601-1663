from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem,
    QToolTip
)
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QColor, QBrush, QPen, QFont
from services.statistics_service import StatisticsService
from services.vehicle_service import VehicleService

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
            ('在售车辆', '#3498db'),
            ('待检测', '#f39c12'),
            ('检测中', '#e67e22'),
            ('待复检', '#e74c3c'),
            ('已售出', '#27ae60'),
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
        self.view.setRenderHint(self.view.renderHints().Antialiasing)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
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
        refresh_btn.clicked.connect(self.refresh)
        stats_layout.addWidget(refresh_btn)
        
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
    
    def refresh(self):
        self.scene.clear()
        
        heatmap_data = StatisticsService.get_heatmap_data()
        
        zones = {}
        for spot in heatmap_data:
            zone = spot['zone']
            if zone not in zones:
                zones[zone] = []
            zones[zone].append(spot)
        
        x_offset = 20
        y_offset = 20
        spot_width = 60
        spot_height = 40
        spot_spacing = 5
        zone_spacing = 80
        
        total_spots = len(heatmap_data)
        occupied = sum(1 for s in heatmap_data if s['status'] == 'occupied')
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
            zone_label.setFont(QFont('Arial', 12, QFont.Bold))
            zone_label.setPos(current_x, y_offset - 25)
            self.scene.addItem(zone_label)
            
            for spot in zone_spots:
                row = spot['row_num'] - 1
                col = spot['col_num'] - 1
                
                x = current_x + col * (spot_width + spot_spacing)
                y = y_offset + row * (spot_height + spot_spacing)
                
                color = self.get_spot_color(spot)
                
                rect_item = ParkingSpotItem(
                    QRectF(x, y, spot_width, spot_height),
                    spot
                )
                rect_item.setBrush(QBrush(QColor(color)))
                rect_item.setPen(QPen(QColor('#95a5a6')))
                self.scene.addItem(rect_item)
                
                text = QGraphicsTextItem(spot['spot_code'])
                text.setFont(QFont('Arial', 8))
                text.setPos(x + 3, y + 2)
                text.setDefaultTextColor(QColor('#2c3e50'))
                self.scene.addItem(text)
            
            current_x += cols * (spot_width + spot_spacing) + zone_spacing
        
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)


class ParkingSpotItem(QGraphicsRectItem):
    def __init__(self, rect, spot_data):
        super().__init__(rect)
        self.spot_data = spot_data
        self.setAcceptHoverEvents(True)
    
    def hoverEnterEvent(self, event):
        spot = self.spot_data
        if spot['status'] == 'occupied':
            tooltip = f"""车位: {spot['spot_code']}
品牌: {spot.get('brand', '未知')}
型号: {spot.get('model', '')}
状态: {self.get_status_text(spot.get('vehicle_status', ''))}"""
        else:
            tooltip = f"车位: {spot['spot_code']}\n状态: 空闲"
        
        QToolTip.showText(event.screenPos(), tooltip)
        super().hoverEnterEvent(event)
    
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


def get_spot_color(self, spot):
    if spot['status'] == 'empty':
        return '#ecf0f1'
    
    vehicle_status = spot.get('vehicle_status', '')
    color_map = {
        'pending_inspection': '#f39c12',
        'inspecting': '#e67e22',
        'reinspection': '#e74c3c',
        'inspection_completed': '#9b59b6',
        'for_sale': '#3498db',
        'sold': '#27ae60',
    }
    return color_map.get(vehicle_status, '#3498db')


ParkingMapWidget.get_spot_color = get_spot_color
