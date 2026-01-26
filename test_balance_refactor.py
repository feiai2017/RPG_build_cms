#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
五行系统平衡重构测试脚本
对比新旧系统的数值差异
"""

from wuxing_engine import WuxingEngine, Stone

def test_damage_comparison():
    """测试新旧系统的伤害计算对比"""
    engine = WuxingEngine()
    
    print("=== 五行系统平衡重构测试 ===\n")
    
    # 测试配置：木主灵根打火法术，离卦火位放木石
    base_damage = 100
    character_config = {
        "skill_element": "火",
        "main_affinity": "木",
        "cultivation_school": "法修",
        "bagua_config": {
            "stones": {
                "LI": {"1": "logic_enhance", "2": "wood_stone", "3": "fire_stone", "4": "earth_stone"}
            },
            "realm": "金丹"
        },
        "bios_config": {"element_amplify": "火"}
    }
    
    # 新版计算
    new_result = engine.calculate_final_damage_v2(base_damage, character_config)
    
    print("📊 新版伤害计算结果:")
    print(f"基础伤害: {new_result['base_damage']}")
    print(f"加法池总计: {new_result['inc_total']:.3f} ({new_result['inc_total']*100:.1f}%)")
    print(f"加法池有效: {new_result['inc_effective']:.3f} ({new_result['inc_effective']*100:.1f}%)")
    print(f"乘法池总计: {new_result['more_total']:.3f}")
    print(f"最终伤害: {new_result['final_damage']:.1f}")
    print(f"总倍率: {new_result['damage_multiplier']:.2f}x\n")
    
    print("🔍 详细分解:")
    print(f"- 主灵根加成: +{new_result['affinity_inc']*100:.1f}%")
    print(f"- 八卦配置加成: +{new_result['bagua_inc']*100:.1f}%")
    print(f"- 卦域效果加成: +{new_result['trigram_inc']*100:.1f}%")
    print(f"- 流派加成: +{new_result['school_inc']*100:.1f}%")
    print(f"- 循环倍率: {new_result['cycle_more']:.2f}x")
    print(f"- BIOS倍率: {new_result['bios_more']:.2f}x\n")
    
    # 模拟旧版计算（简化版本）
    old_damage = base_damage
    old_damage *= 1.05  # 主灵根
    old_damage *= 1.50  # 卦域（木生火）
    old_damage *= 1.15  # BIOS
    old_damage *= 1.08  # 假设3链循环
    
    print("📊 旧版伤害计算结果（估算）:")
    print(f"基础伤害: {base_damage}")
    print(f"最终伤害: {old_damage:.1f}")
    print(f"总倍率: {old_damage/base_damage:.2f}x\n")
    
    print("⚖️ 对比分析:")
    print(f"新版倍率: {new_result['damage_multiplier']:.2f}x")
    print(f"旧版倍率: {old_damage/base_damage:.2f}x")
    print(f"差异: {((new_result['damage_multiplier'] - old_damage/base_damage) / (old_damage/base_damage) * 100):+.1f}%")
    
    if new_result['damage_multiplier'] < old_damage/base_damage:
        print("✅ 新版成功控制了数值爆炸")
    else:
        print("⚠️ 新版倍率仍然较高")

def test_synergy_effects():
    """测试协同效果的改进"""
    engine = WuxingEngine()
    
    print("\n=== 协同效果测试 ===\n")
    
    # 测试不同数量的灵石
    test_cases = [
        ("少量灵石", [
            Stone('wood1', '木灵石1', '木', '🌿', 'common', 1, 1, 'gem'),
            Stone('fire1', '火灵石1', '火', '🔥', 'common', 1, 1, 'gem')
        ]),
        ("中等数量", [
            Stone('wood1', '木灵石1', '木', '🌿', 'common', 1, 1, 'gem'),
            Stone('fire1', '火灵石1', '火', '🔥', 'common', 1, 1, 'gem'),
            Stone('earth1', '土灵石1', '土', '🪨', 'common', 1, 1, 'gem'),
            Stone('metal1', '金灵石1', '金', '🗡️', 'common', 1, 1, 'gem')
        ]),
        ("大量灵石", [
            Stone('wood1', '木灵石1', '木', '🌿', 'common', 1, 1, 'gem'),
            Stone('wood2', '木灵石2', '木', '🌿', 'common', 1, 1, 'gem'),
            Stone('fire1', '火灵石1', '火', '🔥', 'common', 1, 1, 'gem'),
            Stone('fire2', '火灵石2', '火', '🔥', 'common', 1, 1, 'gem'),
            Stone('earth1', '土灵石1', '土', '🪨', 'common', 1, 1, 'gem'),
            Stone('metal1', '金灵石1', '金', '🗡️', 'common', 1, 1, 'gem'),
            Stone('water1', '水灵石1', '水', '💧', 'common', 1, 1, 'gem')
        ])
    ]
    
    for case_name, stones in test_cases:
        synergy = engine.calculate_element_synergy_v2(stones)
        print(f"📊 {case_name} ({len(stones)}个灵石):")
        print(f"  相生对数: {synergy['support_pairs']}")
        print(f"  相克对数: {synergy['conflict_pairs']}")
        print(f"  inc_delta: {synergy['inc_delta']:+.3f} ({synergy['inc_delta']*100:+.1f}%)")
        print(f"  相生加成: {synergy['generation_bonus']:+.3f}")
        print(f"  相克惩罚: {synergy['destruction_penalty']:+.3f}\n")

def test_softcap_function():
    """测试软上限函数"""
    engine = WuxingEngine()
    
    print("=== 软上限函数测试 ===\n")
    
    test_values = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    
    print("输入值 -> 软上限后 -> 最终倍率")
    print("-" * 35)
    for val in test_values:
        softcapped = engine.softcap_inc(val)
        final_mult = 1 + softcapped
        print(f"{val:4.1f}   -> {softcapped:6.3f}   -> {final_mult:.3f}x")

if __name__ == "__main__":
    test_damage_comparison()
    test_synergy_effects()
    test_softcap_function()
    
    print("\n🎉 平衡重构测试完成！")
    print("\n📋 重构要点总结:")
    print("✅ 统一inc/more语义，避免混淆")
    print("✅ 全局协同从N²改为O(5)，避免重复计数")
    print("✅ 链路效果从乘法改为加法+上限")
    print("✅ 卦域效果倍率下调，移入加法池")
    print("✅ 软上限函数防止数值爆炸")
    print("✅ 保持合理的数值感觉")