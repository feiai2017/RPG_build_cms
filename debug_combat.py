#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from enhanced_combat_engine import EnhancedCombatEngine
from engine import SkillNode

# 创建简单的测试
data_source = {
    "rules": {
        "base_hp": 500.0,
        "str_to_hp": 20.0,
        "agi_to_crit_rate": 0.002,
        "int_to_inc_elemental": 0.02
    }
}

engine = EnhancedCombatEngine(data_source)

char_data = {
    "base_stats": {"str": 50, "agi": 30, "int": 40},
    "attributes": {"atk": 100, "def": 50}
}

engine.build_hero_with_wuxing(char_data)

skill_data = {
    "name": "基础攻击",
    "damage_components": [{
        "min": 80,
        "max": 120,
        "type": "physical",
        "scaling_source": "atk",
        "scaling_coef": 1.0
    }]
}

root_node = SkillNode(skill_data)

print("开始战斗模拟...")
try:
    result = engine.simulate_enhanced_fight(
        root_node=root_node,
        enemy_hp=1000.0,
        enemy_dps=30.0,
        max_time=10.0,
        seed=12345
    )
    print("战斗模拟成功！")
    print(f"结果: {result.get('result', 'unknown')}")
    print(f"时间: {result.get('time', 0)}")
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()