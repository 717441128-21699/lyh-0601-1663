from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QLabel, QMessageBox, QHeaderView, QGroupBox, QDateEdit, QComboBox,
    QTabWidget, QSplitter
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QPixmap, QImage
from services.statistics_service import StatisticsService
from datetime import datetime, date
import io

class StatisticsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.refresh()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel('统计分析')
        title.setStyleSheet('font-size: 20px; font-weight: bold; color: #2c3e50;')
        layout.addWidget(title)
        
        self.tab_widget = QTabWidget()
        
        self.summary_tab = QWidget()
        self.setup_summary_tab()
        self.tab_widget.addTab(self.summary_tab, '数据概览')
        
        self.inspection_tab = QWidget()
        self.setup_inspection_tab()
        self.tab_widget.addTab(self.inspection_tab, '检测统计')
        
        self.sales_tab = QWidget()
        self.setup_sales_tab()
        self.tab_widget.addTab(self.sales_tab, '销售统计')
        
        self.report_tab = QWidget()
        self.setup_report_tab()
        self.tab_widget.addTab(self.report_tab, '月度报告')
        
        layout.addWidget(self.tab_widget)
    
    def setup_summary_tab(self):
        layout = QVBoxLayout(self.summary_tab)
        
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel('开始日期:'))
        self.summary_start = QDateEdit()
        self.summary_start.setDate(QDate.currentDate().addMonths(-1))
        self.summary_start.setCalendarPopup(True)
        date_layout.addWidget(self.summary_start)
        
        date_layout.addWidget(QLabel('结束日期:'))
        self.summary_end = QDateEdit()
        self.summary_end.setDate(QDate.currentDate())
        self.summary_end.setCalendarPopup(True)
        date_layout.addWidget(self.summary_end)
        
        refresh_btn = QPushButton('刷新')
        refresh_btn.clicked.connect(self.refresh_summary)
        date_layout.addWidget(refresh_btn)
        
        date_layout.addStretch()
        layout.addLayout(date_layout)
        
        stats_layout = QHBoxLayout()
        
        inspection_group = QGroupBox('检测统计')
        inspection_layout = QVBoxLayout(inspection_group)
        
        self.total_inspections_label = QLabel('0')
        self.total_inspections_label.setStyleSheet('font-size: 28px; font-weight: bold; color: #3498db;')
        inspection_layout.addWidget(self.total_inspections_label)
        
        inspection_layout.addWidget(QLabel('总检测量'))
        stats_layout.addWidget(inspection_group)
        
        pass_group = QGroupBox('通过率')
        pass_layout = QVBoxLayout(pass_group)
        
        self.pass_rate_label = QLabel('0%')
        self.pass_rate_label.setStyleSheet('font-size: 28px; font-weight: bold; color: #27ae60;')
        pass_layout.addWidget(self.pass_rate_label)
        
        pass_layout.addWidget(QLabel('检测通过率'))
        stats_layout.addWidget(pass_group)
        
        inventory_group = QGroupBox('库存')
        inventory_layout = QVBoxLayout(inventory_group)
        
        self.total_inventory_label = QLabel('0')
        self.total_inventory_label.setStyleSheet('font-size: 28px; font-weight: bold; color: #9b59b6;')
        inventory_layout.addWidget(self.total_inventory_label)
        
        inventory_layout.addWidget(QLabel('在库车辆'))
        stats_layout.addWidget(inventory_group)
        
        avg_stock_group = QGroupBox('库存天数')
        avg_stock_layout = QVBoxLayout(avg_stock_group)
        
        self.avg_stock_label = QLabel('0天')
        self.avg_stock_label.setStyleSheet('font-size: 28px; font-weight: bold; color: #e67e22;')
        avg_stock_layout.addWidget(self.avg_stock_label)
        
        avg_stock_layout.addWidget(QLabel('平均库存天数'))
        stats_layout.addWidget(avg_stock_group)
        
        layout.addLayout(stats_layout)
        
        chart_group = QGroupBox('检测趋势图')
        chart_layout = QVBoxLayout(chart_group)
        self.trend_chart_label = QLabel()
        self.trend_chart_label.setAlignment(Qt.AlignCenter)
        self.trend_chart_label.setMinimumHeight(300)
        chart_layout.addWidget(self.trend_chart_label)
        layout.addWidget(chart_group, 1)
        
        brand_group = QGroupBox('品牌库存分布')
        brand_layout = QVBoxLayout(brand_group)
        self.brand_chart_label = QLabel()
        self.brand_chart_label.setAlignment(Qt.AlignCenter)
        self.brand_chart_label.setMinimumHeight(300)
        brand_layout.addWidget(self.brand_chart_label)
        layout.addWidget(brand_group, 1)
    
    def setup_inspection_tab(self):
        layout = QVBoxLayout(self.inspection_tab)
        
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel('品牌:'))
        self.brand_combo = QComboBox()
        self.brand_combo.addItem('全部品牌', None)
        filter_layout.addWidget(self.brand_combo)
        
        stats_btn = QPushButton('统计')
        stats_btn.clicked.connect(self.refresh_inspection_stats)
        filter_layout.addWidget(stats_btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        self.inspection_table = QTableWidget()
        self.inspection_table.setColumnCount(5)
        self.inspection_table.setHorizontalHeaderLabels([
            '品牌', '总检测量', '通过数', '未通过数', '复检数'
        ])
        self.inspection_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.inspection_table, 1)
    
    def setup_sales_tab(self):
        layout = QVBoxLayout(self.sales_tab)
        
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel('开始日期:'))
        self.sales_start = QDateEdit()
        self.sales_start.setDate(QDate.currentDate().addMonths(-1))
        self.sales_start.setCalendarPopup(True)
        date_layout.addWidget(self.sales_start)
        
        date_layout.addWidget(QLabel('结束日期:'))
        self.sales_end = QDateEdit()
        self.sales_end.setDate(QDate.currentDate())
        self.sales_end.setCalendarPopup(True)
        date_layout.addWidget(self.sales_end)
        
        stats_btn = QPushButton('统计')
        stats_btn.clicked.connect(self.refresh_sales_stats)
        date_layout.addWidget(stats_btn)
        
        date_layout.addStretch()
        layout.addLayout(date_layout)
        
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(4)
        self.sales_table.setHorizontalHeaderLabels([
            '品牌', '成交量', '成交额(元)', '平均成交价(元)'
        ])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.sales_table, 1)
        
        summary_group = QGroupBox('汇总')
        summary_layout = QHBoxLayout(summary_group)
        
        self.total_sales_label = QLabel('总成交量: 0')
        self.total_sales_label.setStyleSheet('font-size: 16px; font-weight: bold;')
        summary_layout.addWidget(self.total_sales_label)
        
        self.total_revenue_label = QLabel('总成交额: 0元')
        self.total_revenue_label.setStyleSheet('font-size: 16px; font-weight: bold; color: #27ae60;')
        summary_layout.addWidget(self.total_revenue_label)
        
        self.avg_diff_label = QLabel('平均成交价差: 0元')
        self.avg_diff_label.setStyleSheet('font-size: 16px; font-weight: bold; color: #e67e22;')
        summary_layout.addWidget(self.avg_diff_label)
        
        layout.addWidget(summary_group)
    
    def setup_report_tab(self):
        layout = QVBoxLayout(self.report_tab)
        
        select_layout = QHBoxLayout()
        
        select_layout.addWidget(QLabel('年份:'))
        self.year_combo = QComboBox()
        current_year = date.today().year
        for y in range(current_year - 2, current_year + 1):
            self.year_combo.addItem(str(y), y)
        self.year_combo.setCurrentText(str(current_year))
        select_layout.addWidget(self.year_combo)
        
        select_layout.addWidget(QLabel('月份:'))
        self.month_combo = QComboBox()
        for m in range(1, 13):
            self.month_combo.addItem(f'{m}月', m)
        self.month_combo.setCurrentIndex(date.today().month - 1)
        select_layout.addWidget(self.month_combo)
        
        generate_btn = QPushButton('📄 生成月度报告')
        generate_btn.setStyleSheet('''
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #8e44ad; }
        ''')
        generate_btn.clicked.connect(self.generate_monthly_report)
        select_layout.addWidget(generate_btn)
        
        select_layout.addStretch()
        layout.addLayout(select_layout)
        
        self.report_preview = QLabel('选择月份后点击"生成月度报告"按钮')
        self.report_preview.setAlignment(Qt.AlignCenter)
        self.report_preview.setStyleSheet('color: #7f8c8d; padding: 50px;')
        layout.addWidget(self.report_preview, 1)
    
    def refresh(self):
        self.refresh_summary()
        self.refresh_inspection_stats()
        self.refresh_sales_stats()
        self.load_brands()
    
    def load_brands(self):
        from services.vehicle_service import VehicleService
        vehicles = VehicleService.list_vehicles(page_size=1000)
        brands = set(v['brand'] for v in vehicles if v.get('brand'))
        for brand in sorted(brands):
            self.brand_combo.addItem(brand, brand)
    
    def refresh_summary(self):
        start_date = self.summary_start.date().toString('yyyy-MM-dd')
        end_date = self.summary_end.date().toString('yyyy-MM-dd')
        
        inspection_stats = StatisticsService.get_inspection_statistics(start_date, end_date)
        inventory_stats = StatisticsService.get_inventory_statistics()
        
        self.total_inspections_label.setText(str(inspection_stats['total']))
        self.pass_rate_label.setText(f"{inspection_stats['pass_rate']:.1f}%")
        self.total_inventory_label.setText(str(inventory_stats['total_inventory']))
        self.avg_stock_label.setText(f"{inventory_stats['avg_stock_days']:.0f}天")
        
        try:
            trend_buf = StatisticsService.generate_chart_inspection_trend(30)
            pixmap = QPixmap()
            pixmap.loadFromData(trend_buf.getvalue(), 'PNG')
            self.trend_chart_label.setPixmap(pixmap.scaled(
                self.trend_chart_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))
        except Exception as e:
            print(f"Trend chart error: {e}")
        
        try:
            brand_buf = StatisticsService.generate_chart_brand_distribution()
            pixmap = QPixmap()
            pixmap.loadFromData(brand_buf.getvalue(), 'PNG')
            self.brand_chart_label.setPixmap(pixmap.scaled(
                self.brand_chart_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))
        except Exception as e:
            print(f"Brand chart error: {e}")
    
    def refresh_inspection_stats(self):
        start_date = self.summary_start.date().toString('yyyy-MM-dd')
        end_date = self.summary_end.date().toString('yyyy-MM-dd')
        brand = self.brand_combo.currentData()
        
        if brand:
            stats = StatisticsService.get_inspection_statistics(start_date, end_date, brand)
            self.inspection_table.setRowCount(1)
            self.inspection_table.setItem(0, 0, QTableWidgetItem(brand))
            self.inspection_table.setItem(0, 1, QTableWidgetItem(str(stats['total'])))
            self.inspection_table.setItem(0, 2, QTableWidgetItem(str(stats['passed'])))
            self.inspection_table.setItem(0, 3, QTableWidgetItem(str(stats['failed'])))
            self.inspection_table.setItem(0, 4, QTableWidgetItem(str(stats['rechecks'])))
        else:
            brand_stats = StatisticsService.get_brand_inspection_stats(start_date, end_date)
            self.inspection_table.setRowCount(len(brand_stats))
            
            for row, stat in enumerate(brand_stats):
                self.inspection_table.setItem(row, 0, QTableWidgetItem(stat.get('brand', '未知')))
                self.inspection_table.setItem(row, 1, QTableWidgetItem(str(stat['total'])))
                self.inspection_table.setItem(row, 2, QTableWidgetItem(str(stat['completed'])))
                self.inspection_table.setItem(row, 3, QTableWidgetItem('0'))
                self.inspection_table.setItem(row, 4, QTableWidgetItem(str(stat['rechecks'])))
    
    def refresh_sales_stats(self):
        start_date = self.sales_start.date().toString('yyyy-MM-dd')
        end_date = self.sales_end.date().toString('yyyy-MM-dd')
        
        sales_stats = StatisticsService.get_sales_statistics(start_date, end_date)
        
        by_brand = sales_stats.get('by_brand', [])
        self.sales_table.setRowCount(len(by_brand))
        
        total_sales = 0
        total_revenue = 0
        
        for row, stat in enumerate(by_brand):
            self.sales_table.setItem(row, 0, QTableWidgetItem(stat.get('brand', '未知')))
            self.sales_table.setItem(row, 1, QTableWidgetItem(str(stat['total_sales'])))
            self.sales_table.setItem(row, 2, QTableWidgetItem(f"{stat.get('total_revenue', 0):,.0f}"))
            avg_price = stat.get('total_revenue', 0) / stat['total_sales'] if stat['total_sales'] > 0 else 0
            self.sales_table.setItem(row, 3, QTableWidgetItem(f"{avg_price:,.0f}"))
            
            total_sales += stat['total_sales']
            total_revenue += stat.get('total_revenue', 0)
        
        self.total_sales_label.setText(f'总成交量: {total_sales}')
        self.total_revenue_label.setText(f'总成交额: {total_revenue:,.0f}元')
        self.avg_diff_label.setText(f"平均成交价差: {sales_stats.get('avg_price_diff', 0):,.0f}元 ({sales_stats.get('avg_price_diff_rate', 0):.1f}%)")
    
    def generate_monthly_report(self):
        year = self.year_combo.currentData()
        month = self.month_combo.currentData()
        
        import os
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'reports')
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, f'monthly_report_{year}_{month:02d}.pdf')
        
        try:
            StatisticsService.generate_monthly_report(year, month, output_path)
            
            self.report_preview.setText(f'''
            ✅ 月度报告已生成！
            
            报告期间：{year}年{month}月
            
            保存路径：{output_path}
            
            报告包含：
            • 检测统计数据
            • 品牌检测分布
            • 销售统计数据
            • 库存统计数据
            ''')
            self.report_preview.setStyleSheet('color: #27ae60; padding: 50px; font-size: 14px;')
            
            QMessageBox.information(self, '成功', f'月度报告已生成：\n{output_path}')
            
        except Exception as e:
            QMessageBox.critical(self, '错误', f'生成报告失败: {str(e)}')
