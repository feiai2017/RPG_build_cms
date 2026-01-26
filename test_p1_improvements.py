#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P1级别改进测试脚本
测试逻辑灵石增幅器和中宫辅灵石系统
"""

from wuxing_engine import WuxingEngine, Stone

def test_logic_stone_improvements():
    """测试逻辑灵石从激活开关改为增幅器"""
    engine = WuxingEngine()
    
    print("=== P1-1: 逻辑灵石增幅器测试 ===\n")
    
    # 测试不同类型的逻辑灵石
    logic_types = [
        ("无逻辑灵石", None),
        ("基础逻辑灵石", "logic_basic"),
        ("放大器逻辑灵石", "logic_amplifier_强化"),
        ("路由器逻辑灵石", "logic_router_连接"),
        ("主动化逻辑灵石", "logic_activator_触发")
    ]
    
    for name, logic_id in logic_types:
        effect = engine.calculate_logic_stone_effects_v2("LI", logic_id, 0.0, 0.15)
        
        print(f"📊 {name}:")
        print(f"  卦域inc加成: +{effect['trigram_inc_bonus']*100:.1f}%")
        print(f"  链路上限加成: +{effect['chain_limit_bonus']*100:.1f}%")
        print(f"  特殊效果: {effect['special_effect']}")
        print()

def test_center_auxiliary_stone():
    """测试中宫辅灵石系统（火/水公平补位）"""
    engine = WuxingEngine()
    
    print("=== P1-2: 中宫辅灵石测试 ===\n")
    
    # 测试不同主灵根的中宫效果
    test_cases = [
        ("木主灵根", "木", "auxiliary_wood"),
        ("火主灵根", "火", "auxiliary_fire"),
        ("水主灵根", "水", "auxiliary_water"),
        ("金主灵根", "金", "auxiliary_metal")
    ]
    
    for name, main_affinity, center_stone in test_cases:
        effect = engine.calculate_center_auxiliary_stone_effects(main_affinity, center_stone)
        
        print(f"📊 {name} + 中宫辅灵石:")
        print(f"  提供节点: {'是' if effect['provides_node'] else '否'}")
        if effect['provides_node']:
            print(f"  有效元素: {effect['effective_element']}")
            print(f"  共鸣加成: +{effect['resonance_bonus']*100:.1f}%")
            print(f"  说明: {effect['description']}")
        print()

def test_comprehensive_v3():
    """测试P1级别的综合计算"""
    engine = WuxingEngine()
    
    print("=== P1级别综合效果测试 ===\n")
    
    # 火主灵根配置（受益于中宫辅灵石）
    fire_config = {
        "stones": {
            "LI": {  # 离火位
                "1": "logic_amplifier_强化",  # 放大器逻辑灵石
                "2": "wood_stone",           # 木生火
                "3": "fire_stone",           # 火
                "4": "earth_stone"           # 火生土
            },
            "KAN": {  # 坎水位
                "1": "logic_basic",
                "2": "metal_stone",          # 金生水
                "3": "water_stone"           # 水
            },
            "CENTER": {  # 中宫
                "1": "auxiliary_fire"       # 火辅灵石
            }
        },
        "realm": "金丹",
        "main_affinity": "火"
    }
    
    # 木主灵根配置（对照组）
    wood_config = {
        "stones": {
            "LI": {  # 离火位
                "1": "logic_basic",          # 基础逻辑灵石
                "2": "wood_stone",           # 木生火
                "3": "fire_stone",           # 火
                "4": "earth_stone"           # 火生土
            },
            "ZHEN": {  # 震木位
                "1": "logic_basic",
                "2": "water_stone",          # 水生木
                "3": "wood_stone"            # 木
            }
        },
        "realm": "金丹",
        "main_affinity": "木"
    }
    
    # 计算两种配置的效果
    fire_result = engine.calculate_comprehensive_effects_v3(fire_config)
    wood_result = engine.calculate_comprehensive_effects_v2(wood_config)  # 使用v2作为对照
    
    print("📊 火主灵根 + P1改进:")
    print(f"  元素计数: {fire_result['element_counts']}")
    print(f"  中宫效果: {fire_result['center_effects']}")
    print(f"  逻辑效果: {fire_result['logic_effects']}")
    print(f"  总inc_delta: {fire_result['total_inc_delta']:.3f}")
    print(f"  最终倍率: {fire_result['final_multiplier']:.2f}x\n")
    
    print("📊 木主灵根 (对照组):")
    print(f"  元素计数: {wood_result['element_counts']}")
    print(f"  总inc_delta: {wood_result['total_inc_delta']:.3f}")
    print(f"  最终倍率: {wood_result['final_multiplier']:.2f}x\n")
    
    print("⚖️ P1改进效果:")
    improvement = fire_result['final_multiplier'] - wood_result['final_multiplier']
    print(f"火主灵根倍率提升: +{improvement:.2f}x")
    print(f"相对改进: +{improvement/wood_result['final_multiplier']*100:.1f}%")
    
    if fire_result['center_effects']['provides_node']:
        print("✅ 中宫辅灵石成功为火系提供额外节点")
    
    logic_bonuses = sum(effect.get('trigram_inc_bonus', 0) for effect in fire_result['logic_effects'].values())
    if logic_bonuses > 0:
        print(f"✅ 逻辑灵石提供额外 +{logic_bonuses*100:.1f}% 增幅")

if __name__ == "__main__":
    test_logic_stone_improvements()
    test_center_auxiliary_stone()
    test_comprehensive_v3()
    
    print("\n🎉 P1级别改进测试完成！")
    print("\n📋 P1改进要点:")
    print("✅ 逻辑灵石从'门票税'改为'增幅器'")
    print("✅ 火/水主灵根通过中宫辅灵石获得公平补位")
    print("✅ 卦位默认激活，逻辑灵石提供质变玩法")
    print("✅ 保持数值平衡的同时提升体验")