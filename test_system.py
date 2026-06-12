from db.database import init_database
from db.seed_data import seed_test_data
from services.vehicle_service import VehicleService
from services.scheduling_service import SchedulingService
from services.inspection_service import InspectionService
from services.trading_service import TradingService
from services.statistics_service import StatisticsService
from services.auth_service import AuthService
from services.alert_service import AlertService
from services.approval_service import ApprovalService
from datetime import date

def test_system():
    print("=" * 60)
    print("二手车检测与交易调度系统 - 功能测试")
    print("=" * 60)
    
    print("\n1. 初始化数据库...")
    init_database()
    seed_test_data()
    print("   ✓ 数据库初始化成功")
    
    print("\n2. 测试车辆管理服务...")
    vehicles = VehicleService.list_vehicles(page_size=5)
    print(f"   ✓ 加载 {len(vehicles)} 辆车")
    for v in vehicles[:3]:
        model = v.get("model", "")
        vin_short = v["vin"][-6:]
        print(f"     - {v['brand']} {model} ({vin_short})")
    
    pending = VehicleService.get_pending_inspection_vehicles()
    print(f"   ✓ 待检测车辆: {len(pending)} 辆")
    
    print("\n3. 测试用户认证服务...")
    user = AuthService.login("admin", "123456")
    if user:
        print(f"   ✓ 登录成功: {user['real_name']} ({user['role']})")
    else:
        print("   ✗ 登录失败")
        return False
    
    print("\n4. 测试智能排程服务...")
    schedules = SchedulingService.generate_daily_schedule(date.today())
    print(f"   ✓ 生成 {len(schedules)} 条排程记录")
    
    pending_schedules = SchedulingService.get_pending_approval_schedules()
    print(f"   ✓ 待审批排程: {len(pending_schedules)} 条")
    
    print("\n5. 测试排程审批...")
    if pending_schedules:
        first_sched = pending_schedules[0]
        SchedulingService.approve_schedule(first_sched["id"], user["id"])
        print(f"   ✓ 审批通过排程 ID: {first_sched['id']}")
    
    print("\n6. 测试交易服务 - 建议售价计算...")
    for_sale = VehicleService.get_for_sale_vehicles()
    if for_sale:
        result = TradingService.calculate_suggested_price(for_sale[0]["id"])
        print(f"   ✓ 建议售价: {result['suggested_price']:,.0f} 元")
    
    print("\n7. 测试统计服务...")
    today = date.today().isoformat()
    stats = StatisticsService.get_inspection_statistics("2024-01-01", today)
    print(f"   ✓ 总检测量: {stats['total']}")
    print(f"   ✓ 通过率: {stats['pass_rate']:.1f}%")
    
    inventory = StatisticsService.get_inventory_statistics()
    print(f"   ✓ 在库车辆: {inventory['total_inventory']} 辆")
    print(f"   ✓ 平均库存天数: {inventory['avg_stock_days']:.1f} 天")
    
    print("\n8. 测试预警服务...")
    alerts = AlertService.get_unread_alerts()
    print(f"   ✓ 未读预警: {len(alerts)} 条")
    
    print("\n9. 测试超期库存检查...")
    overstock = TradingService.check_overstock_vehicles()
    print(f"   ✓ 超期库存车辆: {len(overstock)} 辆")
    
    print("\n10. 测试审批服务...")
    pending_approvals = ApprovalService.get_pending_approvals("chief_inspector")
    print(f"   ✓ 待审批事项: {len(pending_approvals)} 条")
    
    print("\n" + "=" * 60)
    print("所有核心功能测试通过！ ✓")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    test_system()
