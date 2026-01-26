#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BD实时验证和优化系统测试脚本
验证Task 8的完整实现
"""

from unified_state_manager import initialize_unified_system
import json


def test_bd_realtime_system():
    """测试BD实时验证和优化系统的完整功能"""
    print("=== BD实时系统测试开始 ===")
    
    # 初始化系统
    state_manager = initialize_unified_system()
    
    # 1. 测试实时属性计算
    print("\n1. 测试实时属性计算...")
    attributes = state_manager.calculate_realtime_attributes()
    print(f"✅ 计算出 {len(attributes)} 个属性")
    for key, value in list(attributes.items())[:5]:  # 显示前5个
        print(f"   {key}: {value:.2f}")
    
    # 2. 测试BD配置验证
    print("\n2. 测试BD配置验证...")
    validation = state_manager.validate_bd_configuration()
    print(f"✅ 配置有效性: {validation['is_valid']}")
    print(f"✅ 完整性评分: {validation['completeness_score']:.1%}")
    if validation['errors']:
        print(f"   错误: {validation['errors']}")
    if validation['warnings']:
        print(f"   警告: {validation['warnings']}")
    
    # 3. 测试优化建议
    print("\n3. 测试优化建议...")
    suggestions = state_manager.get_bd_optimization_suggestions()
    print(f"✅ 生成了 {len(suggestions)} 条优化建议")
    for i, suggestion in enumerate(suggestions[:3], 1):  # 显示前3条
        print(f"   {i}. {suggestion['description']}")
    
    # 4. 测试配置变更的实时响应
    print("\n4. 测试配置变更实时响应...")
    old_attrs = state_manager.calculate_realtime_attributes()
    
    # 更新角色等级
    state_manager.update_character_data({"level": 10})
    new_attrs = state_manager.calculate_realtime_attributes()
    
    # 检查属性是否有变化
    changes = 0
    for key in old_attrs:
        if abs(old_attrs[key] - new_attrs.get(key, 0)) > 0.01:
            changes += 1
    
    print(f"✅ 等级变更后，{changes} 个属性发生了变化")
    
    # 5. 测试一键战斗测试
    print("\n5. 测试一键战斗测试...")
    try:
        combat_result = state_manager.perform_one_click_combat_test()
        if combat_result["success"]:
            perf = combat_result["performance_analysis"]
            print(f"✅ 战斗测试成功")
            print(f"   平均DPS: {perf.get('average_dps', 0):.1f}")
            print(f"   战斗结果: {perf.get('result', 'unknown')}")
            print(f"   战斗时长: {perf.get('fight_duration', 0):.1f}秒")
        else:
            print(f"❌ 战斗测试失败: {combat_result.get('error', 'unknown')}")
    except Exception as e:
        print(f"❌ 战斗测试失败: {e}")
    
    # 6. 测试系统状态概览
    print("\n6. 测试系统状态概览...")
    status = state_manager.get_system_status()
    print(f"✅ 角色: {status['character_name']} ({status['character_realm']})")
    print(f"✅ 流派: {status['character_school']}")
    print(f"✅ 灵石数量: {status['bagua_stones_count']}")
    print(f"✅ 状态一致性: {status['state_consistent']}")
    
    print("\n=== BD实时系统测试完成 ===")


if __name__ == "__main__":
    test_bd_realtime_system()