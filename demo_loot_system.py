# -*- coding: utf-8 -*-
"""
智能掉落和刷宝系统演示
展示LootGenerator类和智能掉落算法的功能
"""

from loot_generator import (
    get_loot_generator, get_enemy_manager, get_loot_optimizer,
    get_challenge_manager, get_bd_optimizer,
    EnemyType, ItemType, ItemRarity
)
from cultivation_school_system import SchoolType


def demo_stone_generation():
    """演示灵石生成"""
    print("=== 灵石生成演示 ===")
    loot_gen = get_loot_generator()
    
    # 为不同流派生成灵石
    schools = [SchoolType.SWORD.value, SchoolType.SPELL.value, SchoolType.BODY.value]
    
    for school in schools:
        print(f"\n{school} 流派灵石生成:")
        for i in range(3):
            stone = loot_gen.generate_stone(
                player_school=school,
                enemy_type=EnemyType.BEAST,
                player_level=5,
                seed=1000 + i
            )
            print(f"  {stone.name} ({stone.element}元素, {stone.rarity})")


def demo_equipment_generation():
    """演示装备生成"""
    print("\n=== 装备生成演示 ===")
    loot_gen = get_loot_generator()
    
    # 为剑修生成不同类型装备
    school = SchoolType.SWORD.value
    item_types = [ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY]
    
    print(f"\n{school} 流派装备生成:")
    for item_type in item_types:
        equipment = loot_gen.generate_equipment(
            player_school=school,
            player_level=10,
            item_type=item_type,
            seed=2000
        )
        print(f"  {equipment.name}")
        print(f"    类型: {equipment.item_type.value}, 稀有度: {equipment.rarity.value}")
        print(f"    属性: {equipment.stats}")
        print(f"    流派亲和: {equipment.school_affinity}")


def demo_drop_probability():
    """演示掉落概率计算"""
    print("\n=== 掉落概率演示 ===")
    loot_gen = get_loot_generator()
    
    school = SchoolType.SWORD.value
    elements = ["木", "火", "土", "金", "水"]
    
    print(f"\n{school} 流派各元素掉落概率:")
    for element in elements:
        prob = loot_gen.calculate_drop_probability(
            school_affinity=school,
            stone_element=element,
            enemy_type=EnemyType.BEAST
        )
        print(f"  {element}元素: {prob:.2%}")


def demo_equipment_comparison():
    """演示装备对比"""
    print("\n=== 装备对比演示 ===")
    loot_gen = get_loot_generator()
    loot_opt = get_loot_optimizer()
    
    school = SchoolType.SWORD.value
    
    # 生成两件武器进行对比
    weapon1 = loot_gen.generate_equipment(
        player_school=school,
        player_level=5,
        item_type=ItemType.WEAPON,
        seed=3000
    )
    
    weapon2 = loot_gen.generate_equipment(
        player_school=school,
        player_level=5,
        item_type=ItemType.WEAPON,
        seed=3001
    )
    
    print(f"\n装备对比:")
    print(f"武器1: {weapon1.name}")
    print(f"  属性: {weapon1.stats}")
    print(f"  战力: {weapon1.calculate_power_score():.1f}")
    
    print(f"武器2: {weapon2.name}")
    print(f"  属性: {weapon2.stats}")
    print(f"  战力: {weapon2.calculate_power_score():.1f}")
    
    comparison = loot_opt.compare_equipment(weapon1, weapon2, school)
    print(f"\n对比结果:")
    print(f"  战力差异: {comparison['power_score_diff']:.1f}")
    print(f"  流派兼容性: {comparison['school_compatibility']:.2%}")
    print(f"  推荐: {comparison['recommendation']}")


def demo_challenge_system():
    """演示挑战系统"""
    print("\n=== 挑战系统演示 ===")
    challenge_mgr = get_challenge_manager()
    
    # 获取可用挑战
    challenges = challenge_mgr.get_available_challenges(player_level=5)
    print(f"\n等级5可用挑战:")
    for challenge in challenges:
        print(f"  {challenge['name']}: {challenge['description']}")
        print(f"    敌人: {challenge['enemies']}")
        print(f"    奖励: {challenge['rewards']}")
    
    # 生成动态挑战
    dynamic_challenge = challenge_mgr.generate_dynamic_challenge(
        player_school=SchoolType.SWORD.value,
        player_level=8,
        seed=4000
    )
    print(f"\n动态挑战:")
    print(f"  {dynamic_challenge['name']}: {dynamic_challenge['description']}")
    print(f"  敌人: {dynamic_challenge['enemies']}")
    print(f"  奖励: {dynamic_challenge['rewards']}")


def demo_bd_optimization():
    """演示BD优化"""
    print("\n=== BD优化演示 ===")
    bd_opt = get_bd_optimizer()
    
    # 模拟角色数据
    character_data = {
        "school": SchoolType.SWORD.value,
        "level": 10,
        "attributes": {
            "str": 30,
            "agi": 25,
            "int": 15,
            "base_atk": 80,
            "max_hp": 600,
            "crit_rate": 0.12,
            "crit_dmg": 0.8
        },
        "equipment": {
            "weapon": {
                "id": "sword_001",
                "name": "精钢长剑",
                "rarity": "rare",
                "level": 8,
                "stats": {"base_atk": 45, "crit_rate": 0.08},
                "school_affinity": [SchoolType.SWORD.value],
                "element_affinity": "金"
            },
            "armor": {
                "id": "armor_001", 
                "name": "轻甲",
                "rarity": "common",
                "level": 6,
                "stats": {"def": 25, "max_hp": 100},
                "school_affinity": [],
                "element_affinity": "无"
            }
        }
    }
    
    # 分析当前BD
    analysis = bd_opt.analyze_current_build(character_data)
    print(f"\nBD分析结果:")
    print(f"  装备协同评分: {analysis['synergy_score']:.2%}")
    print(f"  流派对齐度: {analysis['school_alignment']:.2%}")
    print(f"  套装效果: {analysis['set_bonuses']}")
    print(f"  属性平衡评分: {analysis['attribute_analysis']['balance_score']:.2%}")
    
    print(f"\n优化建议:")
    for suggestion in analysis['optimization_suggestions']:
        print(f"  - {suggestion}")


if __name__ == "__main__":
    print("智能掉落和刷宝系统演示")
    print("=" * 50)
    
    demo_stone_generation()
    demo_equipment_generation()
    demo_drop_probability()
    demo_equipment_comparison()
    demo_challenge_system()
    demo_bd_optimization()
    
    print("\n=== 演示完成 ===")