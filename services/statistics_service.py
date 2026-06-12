from db.database import get_db_connection
from datetime import datetime, date, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import os

class StatisticsService:
    @staticmethod
    def get_inspection_statistics(start_date, end_date, brand=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN r.result = 'pass' THEN 1 ELSE 0 END) as passed,
                SUM(CASE WHEN r.result = 'fail' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN r.status = 'recheck' THEN 1 ELSE 0 END) as rechecks
            FROM inspection_records r
            JOIN vehicles v ON r.vehicle_id = v.id
            WHERE DATE(r.created_at) BETWEEN ? AND ?
        '''
        params = [start_date, end_date]
        
        if brand:
            query += " AND v.brand = ?"
            params.append(brand)
        
        cursor.execute(query, params)
        result = dict(cursor.fetchone())
        
        total = result['total'] or 0
        passed = result['passed'] or 0
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        conn.close()
        return {
            'total': total,
            'passed': passed,
            'failed': result['failed'] or 0,
            'rechecks': result['rechecks'] or 0,
            'pass_rate': pass_rate
        }
    
    @staticmethod
    def get_brand_inspection_stats(start_date, end_date):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                v.brand,
                COUNT(*) as total,
                SUM(CASE WHEN r.status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN r.is_reinspection = 1 THEN 1 ELSE 0 END) as rechecks
            FROM inspection_records r
            JOIN vehicles v ON r.vehicle_id = v.id
            WHERE DATE(r.created_at) BETWEEN ? AND ?
            GROUP BY v.brand
            ORDER BY total DESC
        ''', (start_date, end_date))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    @staticmethod
    def get_inventory_statistics():
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                AVG(julianday('now') - julianday(entry_date)) as avg_stock_days
            FROM vehicles 
            WHERE status = 'for_sale'
        ''')
        result = dict(cursor.fetchone())
        
        cursor.execute('''
            SELECT brand, COUNT(*) as count
            FROM vehicles 
            WHERE status = 'for_sale'
            GROUP BY brand
            ORDER BY count DESC
        ''')
        brand_stats = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'total_inventory': result['total'] or 0,
            'avg_stock_days': result['avg_stock_days'] or 0,
            'brand_breakdown': brand_stats
        }
    
    @staticmethod
    def get_sales_statistics(start_date, end_date):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                COUNT(*) as total_sales,
                SUM(c.final_price) as total_revenue,
                AVG(c.final_price) as avg_price,
                v.brand
            FROM contracts c
            JOIN vehicles v ON c.vehicle_id = v.id
            WHERE DATE(c.sign_date) BETWEEN ? AND ?
            GROUP BY v.brand
            ORDER BY total_sales DESC
        ''', (start_date, end_date))
        rows = cursor.fetchall()
        
        cursor.execute('''
            SELECT 
                AVG(v.intended_price - c.final_price) as avg_price_diff,
                AVG((v.intended_price - c.final_price) / v.intended_price * 100) as avg_price_diff_rate
            FROM contracts c
            JOIN vehicles v ON c.vehicle_id = v.id
            WHERE DATE(c.sign_date) BETWEEN ? AND ?
        ''', (start_date, end_date))
        price_diff = dict(cursor.fetchone())
        
        conn.close()
        
        return {
            'by_brand': [dict(row) for row in rows],
            'avg_price_diff': price_diff['avg_price_diff'] or 0,
            'avg_price_diff_rate': price_diff['avg_price_diff_rate'] or 0
        }
    
    @staticmethod
    def get_daily_inspection_trend(days=30):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as count
            FROM inspection_records
            WHERE created_at >= date('now', ?)
            GROUP BY DATE(created_at)
            ORDER BY date
        ''', (f'-{days} days',))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    @staticmethod
    def get_heatmap_data():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                ps.zone,
                ps.row_num,
                ps.col_num,
                ps.status,
                ps.spot_code,
                v.brand,
                v.model,
                v.status as vehicle_status,
                ps.x_coord,
                ps.y_coord
            FROM parking_spots ps
            LEFT JOIN vehicles v ON ps.vehicle_id = v.id
            ORDER BY ps.zone, ps.row_num, ps.col_num
        ''')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    @staticmethod
    def generate_monthly_report(year, month, output_path):
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year}-12-31"
        else:
            end_date = f"{year}-{month+1:02d}-01"
            end_date = (date.fromisoformat(end_date) - timedelta(days=1)).isoformat()
        
        inspection_stats = StatisticsService.get_inspection_statistics(start_date, end_date)
        brand_stats = StatisticsService.get_brand_inspection_stats(start_date, end_date)
        sales_stats = StatisticsService.get_sales_statistics(start_date, end_date)
        inventory_stats = StatisticsService.get_inventory_statistics()
        
        daily_trend = StatisticsService.get_daily_inspection_trend(30)
        
        doc = SimpleDocTemplate(output_path, pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        
        styles = getSampleStyleSheet()
        story = []
        
        title = Paragraph(f"{year}年{month}月 二手车交易市场运营报告", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 0.5*cm))
        
        story.append(Paragraph("一、检测统计", styles['Heading2']))
        story.append(Spacer(1, 0.3*cm))
        
        inspection_data = [
            ['指标', '数值'],
            ['总检测量', str(inspection_stats['total'])],
            ['通过数量', str(inspection_stats['passed'])],
            ['未通过数量', str(inspection_stats['failed'])],
            ['复检数量', str(inspection_stats['rechecks'])],
            ['通过率', f"{inspection_stats['pass_rate']:.1f}%"],
        ]
        
        t = Table(inspection_data, colWidths=[6*cm, 6*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5*cm))
        
        story.append(Paragraph("二、品牌检测分布", styles['Heading2']))
        story.append(Spacer(1, 0.3*cm))
        
        if brand_stats:
            brand_data = [['品牌', '检测量', '完成量', '复检量']]
            for bs in brand_stats:
                brand_data.append([
                    bs['brand'] or '未知',
                    str(bs['total']),
                    str(bs['completed']),
                    str(bs['rechecks'])
                ])
            
            t2 = Table(brand_data, colWidths=[4*cm, 3*cm, 3*cm, 3*cm])
            t2.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(t2)
        
        story.append(Spacer(1, 0.5*cm))
        
        story.append(Paragraph("三、销售统计", styles['Heading2']))
        story.append(Spacer(1, 0.3*cm))
        
        total_sales = sum(s['total_sales'] for s in sales_stats['by_brand'])
        total_revenue = sum(s['total_revenue'] or 0 for s in sales_stats['by_brand'])
        
        sales_summary = [
            ['指标', '数值'],
            ['总成交量', str(total_sales)],
            ['总成交额', f"{total_revenue:.0f} 元"],
            ['平均成交价差', f"{sales_stats['avg_price_diff']:.0f} 元"],
            ['平均成交价差率', f"{sales_stats['avg_price_diff_rate']:.1f}%"],
        ]
        
        t3 = Table(sales_summary, colWidths=[6*cm, 6*cm])
        t3.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(t3)
        
        story.append(Spacer(1, 0.5*cm))
        
        story.append(Paragraph("四、库存统计", styles['Heading2']))
        story.append(Spacer(1, 0.3*cm))
        
        inventory_data = [
            ['指标', '数值'],
            ['在库车辆数', str(inventory_stats['total_inventory'])],
            ['平均库存天数', f"{inventory_stats['avg_stock_days']:.1f} 天"],
        ]
        
        t4 = Table(inventory_data, colWidths=[6*cm, 6*cm])
        t4.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(t4)
        
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph(f"报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        
        doc.build(story)
        
        return output_path
    
    @staticmethod
    def generate_chart_inspection_trend(days=30):
        daily_trend = StatisticsService.get_daily_inspection_trend(days)
        
        dates = [d['date'] for d in daily_trend]
        counts = [d['count'] for d in daily_trend]
        
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(dates, counts, marker='o', linewidth=2, color='#2196F3')
        ax.set_xlabel('日期')
        ax.set_ylabel('检测数量')
        ax.set_title(f'近{days}天检测趋势')
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        plt.close(fig)
        
        return buf
    
    @staticmethod
    def generate_chart_brand_distribution():
        inventory_stats = StatisticsService.get_inventory_statistics()
        brands = [b['brand'] for b in inventory_stats['brand_breakdown']]
        counts = [b['count'] for b in inventory_stats['brand_breakdown']]
        
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.pie(counts, labels=brands, autopct='%1.1f%%', startangle=90)
        ax.set_title('库存品牌分布')
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        plt.close(fig)
        
        return buf
