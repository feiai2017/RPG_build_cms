# -*- coding: utf-8 -*-
"""
增强战斗引擎测试
"""

import pytest
from enhanced_combat_engine import EnhancedCombatEngine
from engine import SkillNode
from wuxing_engine import Stone


def test_enhanced_combat_engine_basic():
    """测试增强战斗引擎基本功能"""
    # 创建测试数据
    data_source = {
        "rules": {
            "base_hp": 500.0,
            "str_to_hp": 20.0,
            "agi_to_crit_rate": 0.002,
            "int_to_inc_elemental": 0.02
        }
    }
    
    # 创建引擎
    engine = EnhancedCombatEngine(data_source)
    
    # 测试角色构建
    model_data = {
        "base_stats": {"str": 50, "agi": 30, "int": 40},
        "attributes": {"atk": 100, "def": 50}
    }
    
    engine.build_hero_with_wuxing(model_data)
    
    # 验证基础属性
    assert engine.stats["str"] == 50
    assert engine.stats["agi"] == 30
    assert engine.stats["int"] == 40
    assert engine.stats["atk"] == 100
    assert engine.stats["def"] == 50
    
    # 验证派生属性
    assert engine.stats["max_hp"] > 500  # 基础HP + 力量加成
    assert engine.stats["crit_rate"] > 0.05  # 基础暴击 + 敏捷加成


def test_bagua_configuration():
    """测试八卦配置功能"""
    data_source = {"rules": {}}
    engine = EnhancedCombatEngine(data_source)
    
    # 设置八卦配置
    bagua_config = {
        "stones": {
            "LI": {
                "1": None,
                "2": "gem_fire",
                "3": "gem_wood",
                "4": None
            },
            "KAN": {
                "1": None,
                "2": "gem_water",
                "3": None,
                "4": None
            }
        }
    }
    
    engine.set_bagua_configuration(bagua_config)
    assert engine.bagua_configuration == bagua_config
    
    # 测试元素效果计算
    elemental_effects = engine.calculate_elemental_effects()
    assert isinstance(elemental_effects, dict)
    assert "damage_multiplier" in elemental_effects


def test_combat_simulation():
    """测试战斗模拟功能"""
    data_source = {
        "rules": {
            "base_hp": 1000.0,
            "str_to_hp": 20.0
        }
    }
    
    engine = EnhancedCombatEngine(data_source)
    
    # 构建角色
    model_data = {
        "base_stats": {"str": 100, "agi": 50, "int": 30},
        "attributes": {"atk": 200, "def": 100}
    }
    
    engine.build_hero_with_wuxing(model_data)
    
    # 创建技能节点
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
    
    # 执行战斗模拟
    result = engine.simulate_enhanced_fight(
        root_node=root_node,
        enemy_hp=2000.0,
        enemy_dps=50.0,
        enemy_type="test_boss",
        max_time=15.0,
        seed=12345
    )
    
    # 验证结果
    assert "result" in result
    assert "combat_record" in result
    assert "dps_analysis" in result
    assert "survivability_analysis" in result
    
    # 验证战斗记录
    combat_record = result["combat_record"]
    assert combat_record.enemy_type == "test_boss"
    assert combat_record.duration > 0
    assert combat_record.result in ["WIN", "LOSE", "TIMEOUT"]
    
    # 验证DPS分析
    dps_analysis = result["dps_analysis"]
    assert "average_dps" in dps_analysis
    assert "peak_dps" in dps_analysis
    assert "total_damage" in dps_analysis
    
    # 验证生存能力分析
    survivability = result["survivability_analysis"]
    assert "score" in survivability
    assert 0 <= survivability["score"] <= 100


def test_performance_summary():
    """测试性能总结功能"""
    data_source = {"rules": {"base_hp": 500.0}}
    engine = EnhancedCombatEngine(data_source)
    
    # 初始状态
    summary = engine.get_performance_summary()
    assert summary["total_fights"] == 0
    
    # 模拟一场战斗后
    model_data = {"base_stats": {"str": 50}, "attributes": {"atk": 100}}
    engine.build_hero_with_wuxing(model_data)
    
    skill_data = {
        "name": "测试技能",
        "damage_components": [{
            "min": 50, "max": 100, "type": "physical",
            "scaling_source": "atk", "scaling_coef": 0.8
        }]
    }
    
    root_node = SkillNode(skill_data)
    
    engine.simulate_enhanced_fight(
        root_node=root_node,
        enemy_hp=1000.0,
        enemy_dps=30.0,
        max_time=10.0,
        seed=54321
    )
    
    # 检查性能总结
    summary = engine.get_performance_summary()
    assert summary["total_fights"] == 1
    assert "win_rate" in summary
    assert "average_dps" in summary
    assert "average_survivability" in summary
    assert "latest_record" is not None


def test_combat_report_generation():
    """测试战斗报告生成"""
    data_source = {"rules": {"base_hp": 800.0}}
    engine = EnhancedCombatEngine(data_source)
    
    model_data = {"base_stats": {"str": 60}, "attributes": {"atk": 150}}
    engine.build_hero_with_wuxing(model_data)
    
    skill_data = {
        "name": "火球术",
        "damage_components": [{
            "min": 100, "max": 150, "type": "fire",
            "scaling_source": "atk", "scaling_coef": 1.2
        }]
    }
    
    root_node = SkillNode(skill_data)
    
    result = engine.simulate_enhanced_fight(
        root_node=root_node,
        enemy_hp=1500.0,
        enemy_dps=40.0,
        enemy_type="火焰恶魔",
        max_time=12.0,
        seed=98765
    )
    
    # 生成报告
    combat_record = result["combat_record"]
    report = engine.generate_combat_report(combat_record)
    
    # 验证报告内容
    assert "战斗报告" in report
    assert "火焰恶魔" in report
    assert "伤害统计" in report
    assert "评分" in report
    assert isinstance(report, str)
    assert len(report) > 100  # 确保报告有实质内容


if __name__ == "__main__":
    pytest.main([__file__, "-v"])