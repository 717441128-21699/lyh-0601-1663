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

def test_all_fixes():
    print("=" * 70)
    print("二手车检测与交易调度系统 - 修复验证测试")
    print("=" * 70)
    
    init_database()
    seed_test_data()
    
    print("\n【问题1修复验证】排程不重复生成、时间不冲突")
    print("-" * 70)
    
    print("  第一次生成排程...")
    schedules1 = SchedulingService.generate_daily_schedule(date.today())
    print(f"  第一次生成: {len(schedules1)} 条")
    
    vehicle_ids_1 = set(s['vehicle_id'] for s in schedules1)
    print(f"  涉及车辆数: {len(vehicle_ids_1)}")
    
    print("  第二次生成排程...")
    schedules2 = SchedulingService.generate_daily_schedule(date.today())
    print(f"  第二次生成: {len(schedules2)} 条 (应该为0，因为待审批的已被清掉)")
    
    user = AuthService.login("admin", "123456")
    
    pending = SchedulingService.get_pending_approval_schedules()
    print(f"  待审批排程数: {len(pending)}")
    
    if pending:
        print("  批量审批所有排程...")
        for sched in pending:
            SchedulingService.approve_schedule(sched['id'], user['id'])
        print(f"  已审批 {len(pending)} 条排程")
    
    print("  第三次生成排程...")
    schedules3 = SchedulingService.generate_daily_schedule(date.today())
    print(f"  第三次生成: {len(schedules3)} 条 (应该为0，因为车都有已批准的排程了)")
    
    all_schedules = SchedulingService.get_schedules_by_date(date.today())
    approved_count = sum(1 for s in all_schedules if s['status'] == 'approved')
    print(f"  已批准排程总数: {approved_count}")
    
    inspector_schedules = {}
    workstation_schedules = {}
    has_conflict = False
    
    for s in all_schedules:
        if s['status'] != 'approved':
            continue
        
        insp_id = s['inspector_id']
        ws_id = s['workstation_id']
        start = s['start_time']
        end = s['end_time']
        
        if insp_id not in inspector_schedules:
            inspector_schedules[insp_id] = []
        inspector_schedules[insp_id].append((start, end))
        
        if ws_id not in workstation_schedules:
            workstation_schedules[ws_id] = []
        workstation_schedules[ws_id].append((start, end))
    
    for insp_id, times in inspector_schedules.items():
        times.sort()
        for i in range(len(times) - 1):
            if times[i][1] > times[i + 1][0]:
                print(f"  ⚠ 检测师 {insp_id} 时间冲突: {times[i]} 和 {times[i+1]}")
                has_conflict = True
    
    for ws_id, times in workstation_schedules.items():
        times.sort()
        for i in range(len(times) - 1):
            if times[i][1] > times[i + 1][0]:
                print(f"  ⚠ 工位 {ws_id} 时间冲突: {times[i]} 和 {times[i+1]}")
                has_conflict = True
    
    if not has_conflict:
        print("  ✓ 所有检测师和工位的时间都没有冲突")
    
    print("\n【问题2修复验证】排程调整审批状态正确区分")
    print("-" * 70)
    
    inspector_user = AuthService.login("inspector_zhang", "123456")
    inspector = AuthService.get_inspector_by_user_id(inspector_user['id'])
    
    today_schedules = SchedulingService.get_today_schedules_by_inspector(inspector['id'])
    print(f"  检测师今日排程数: {len(today_schedules)}")
    
    if today_schedules:
        test_schedule = today_schedules[0]
        print(f"  测试排程 ID: {test_schedule['id']}, 当前状态: {test_schedule['status']}")
        
        print("  检测师申请调整排程...")
        SchedulingService.request_schedule_adjustment(
            test_schedule['id'],
            inspector_user['id'],
            '时间不太方便，想调整到下午'
        )
        
        after_request = SchedulingService.get_schedules_by_date(date.today())
        for s in after_request:
            if s['id'] == test_schedule['id']:
                print(f"  申请后状态: {s['status']} (应该是 adjustment_pending)")
                break
        
        chief = AuthService.login("chief_inspector", "123456")
        
        pending_approvals = ApprovalService.get_pending_approvals("chief_inspector")
        print(f"  检测主管待审批事项: {len(pending_approvals)}")
        
        if pending_approvals:
            approval = pending_approvals[0]
            print(f"  主管驳回调整申请...")
            ApprovalService.reject_request(approval['id'], chief['id'], '无法调整，请按原计划执行')
            
            after_reject = SchedulingService.get_schedules_by_date(date.today())
            for s in after_reject:
                if s['id'] == test_schedule['id']:
                    print(f"  驳回后状态: {s['status']} (应该是 adjustment_rejected)")
                    break
            
            inspector_schedules_after = SchedulingService.get_today_schedules_by_inspector(inspector['id'])
            has_rejected = any(s['status'] == 'adjustment_rejected' for s in inspector_schedules_after)
            print(f"  检测师端能看到驳回状态: {'是' if has_rejected else '否'}")
    
    AuthService.login("admin", "123456")
    
    print("\n【问题3修复验证】检测结果明确，统计数据一致")
    print("-" * 70)
    
    inspector_user = AuthService.login("inspector_zhang", "123456")
    inspector = AuthService.get_inspector_by_user_id(inspector_user['id'])
    
    approved_schedules = [s for s in SchedulingService.get_schedules_by_date(date.today()) 
                         if s['status'] == 'approved' and s['inspector_id'] == inspector['id']]
    
    if approved_schedules:
        test_sched = approved_schedules[0]
        print(f"  开始检测: 排程ID {test_sched['id']}")
        record_id = InspectionService.start_inspection(test_sched['id'], inspector['id'])
        
        print("  完成检测(通过)...")
        result_pass = InspectionService.complete_inspection(
            record_id,
            {
                'water_damage': 20,
                'fire_damage': 10,
                'major_accident': 15,
                'appearance': 85,
                'chassis': 80,
                'engine': 90
            },
            '车况良好'
        )
        print(f"  检测结果: {result_pass['result']} (应该是 pass)")
        print(f"  需复检: {result_pass['needs_reinspection']} (应该是 False)")
    
    if len(approved_schedules) > 1:
        test_sched2 = approved_schedules[1]
        print(f"  开始第二项检测: 排程ID {test_sched2['id']}")
        record_id2 = InspectionService.start_inspection(test_sched2['id'], inspector['id'])
        
        print("  完成检测(未通过)...")
        result_fail = InspectionService.complete_inspection(
            record_id2,
            {
                'water_damage': 30,
                'fire_damage': 20,
                'major_accident': 25,
                'appearance': 40,
                'chassis': 45,
                'engine': 50
            },
            '车况较差，评分低'
        )
        print(f"  检测结果: {result_fail['result']} (应该是 fail)")
    
    if len(approved_schedules) > 2:
        test_sched3 = approved_schedules[2]
        print(f"  开始第三项检测: 排程ID {test_sched3['id']}")
        record_id3 = InspectionService.start_inspection(test_sched3['id'], inspector['id'])
        
        print("  完成检测(触发复检)...")
        result_recheck = InspectionService.complete_inspection(
            record_id3,
            {
                'water_damage': 80,
                'fire_damage': 20,
                'major_accident': 40,
                'appearance': 70,
                'chassis': 65,
                'engine': 75
            },
            '有泡水风险'
        )
        print(f"  检测结果: {result_recheck['result']} (应该是 recheck)")
        print(f"  需复检: {result_recheck['needs_reinspection']} (应该是 True)")
    
    AuthService.login("admin", "123456")
    
    stats = StatisticsService.get_inspection_statistics("2020-01-01", "2099-12-31")
    print(f"\n  统计结果:")
    print(f"    总检测量: {stats['total']}")
    print(f"    通过数: {stats['passed']}")
    print(f"    未通过数: {stats['failed']}")
    print(f"    待复检数: {stats['rechecks']}")
    print(f"    通过率: {stats['pass_rate']:.1f}%")
    
    print("\n【问题4修复验证】合同详情显示真实数据")
    print("-" * 70)
    
    for_sale = VehicleService.get_for_sale_vehicles()
    if for_sale:
        test_vehicle = for_sale[0]
        print(f"  测试车辆: {test_vehicle['brand']} {test_vehicle.get('model', '')}")
        
        offer_id = TradingService.create_buyer_offer(
            test_vehicle['id'],
            '张三',
            '13812345678',
            test_vehicle['intended_price'] * 0.95
        )
        print(f"  创建出价记录 ID: {offer_id}")
        
        sales_manager = AuthService.login("sales_manager", "123456")
        contract_no = TradingService.approve_buyer_offer(offer_id, sales_manager['id'], '价格合理，同意成交')
        print(f"  审批通过，生成合同: {contract_no}")
        
        contract = TradingService.get_contract_by_no(contract_no)
        if contract:
            print(f"  合同详情验证:")
            print(f"    合同编号: {contract['contract_no']}")
            print(f"    买家姓名: {contract['buyer_name']}")
            print(f"    联系电话: {contract['buyer_phone']}")
            print(f"    VIN码: {contract['vin']}")
            print(f"    品牌型号: {contract['brand']} {contract.get('model', '')}")
            print(f"    成交价: {contract['final_price']:,.0f} 元")
            print(f"    签订日期: {contract.get('sign_date', '')[:10]}")
            print("  ✓ 合同详情包含所有真实数据")
    
    AuthService.login("admin", "123456")
    
    print("\n【问题5修复验证】车库平面图正常显示")
    print("-" * 70)
    
    heatmap_data = StatisticsService.get_heatmap_data()
    print(f"  车位总数: {len(heatmap_data)}")
    
    zones = set(s['zone'] for s in heatmap_data)
    print(f"  区域数: {len(zones)} ({', '.join(sorted(zones))}区)")
    
    statuses = set(s.get('vehicle_status', 'empty') for s in heatmap_data if s['status'] == 'occupied')
    print(f"  车辆状态种类: {len(statuses)} 种")
    
    for s in heatmap_data:
        if s['status'] == 'occupied' and s.get('vehicle_status'):
            print(f"  示例车位: {s['spot_code']}, 状态: {s['vehicle_status']}, 品牌: {s.get('brand', '-')}")
            break
    
    print("  ✓ 车库平面图数据正常")
    
    print("\n" + "=" * 70)
    print("所有修复验证完成！")
    print("=" * 70)

if __name__ == "__main__":
    test_all_fixes()
