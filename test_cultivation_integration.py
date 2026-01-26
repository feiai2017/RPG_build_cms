# -*- coding: utf-8 -*-
"""
流派系统与统一状态管理器集成测试
验证流派系统与现有系统的集成是否正常工作
"""

import pytest
import tempfile
import shutil
from unified_state_manager import UnifiedStateManager
from cultivation_school_system import SchoolType


class TestCultivationIntegration:
    """流派系统集成测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.state_manager = UnifiedStateManager(config_dir=self.temp_dir)
    
    def teardown_method(self):
        """测试后清理"""
        if self.temp_dir:
            shutil.rmtree(self.temp_dir)
    
    def test_school_change_integration(self):
        """测试流派切换的集成功能"""
        # 初始状态
        initial_school = self.state_manager.character_data.get("school", "sword_cultivator")
        assert initial_school == "sword_cultivator"
        
        # 切换到法修
        success = self.state_manager.change_character_school(SchoolType.SPELL.value)
        assert success
        
        # 验证状态同步
        character_state = self.state_manager.get_module_state("character")
        assert character_state["character_data"]["school"] == SchoolType.SPELL.value
        
        # 验证流派信息更新
        school_info = character_state["school_info"]
        assert school_info["name"] == "法修"
        assert school_info["element_affinity"] == "火"
    
    def test_skill_unlock_integration(self):
        """测试技能解锁的集成功能"""
        # 设置为剑修，等级10
        self.state_manager.update_character_data({
            "school": SchoolType.SWORD.value,
            "level": 10
        })
        
        # 获取可用技能
        available_skills = self.state_manager.get_available_skills()
        assert len(available_skills) > 0
        
        # 解锁第一个技能
        first_skill = available_skills[0]
        success = self.state_manager.unlock_skill(first_skill["id"])
        assert success
        
        # 验证技能已解锁
        unlocked_skills = self.state_manager.character_data.get("unlocked_skills", [])
        assert first_skill["id"] in unlocked_skills
    
    def test_attribute_bonuses_integration(self):
        """测试属性加成的集成功能"""
        # 设置基础属性
        base_attrs = {
            "str": 20,
            "agi": 20,
            "int": 20,
            "base_atk": 50,
            "max_hp": 500
        }
        
        self.state_manager.update_character_data({
            "school": SchoolType.BODY.value,
            "level": 5,
            "base_attributes": base_attrs
        })
        
        # 获取战斗模块状态（包含最终属性）
        combat_state = self.state_manager.get_module_state("combat")
        final_stats = combat_state["character_stats"]
        
        # 体修应该有力量和生命值加成
        assert final_stats["str"] > base_attrs["str"]
        assert final_stats["max_hp"] > base_attrs["max_hp"]
        
        # 验证流派效果存在
        school_effects = combat_state.get("school_effects", {})
        assert len(school_effects) > 0
    
    def test_equipment_recommendation_integration(self):
        """测试装备推荐的集成功能"""
        # 设置为剑修
        self.state_manager.update_character_data({
            "school": SchoolType.SWORD.value,
            "level": 15
        })
        
        # 模拟装备列表
        equipment_list = [
            {
                "name": "普通剑",
                "stats": {"base_atk": 30, "crit_rate": 0.05}
            },
            {
                "name": "法杖",
                "stats": {"int": 25, "elem_dmg_火": 15}
            },
            {
                "name": "重甲",
                "stats": {"def": 40, "max_hp": 200}
            }
        ]
        
        # 获取推荐
        recommendations = self.state_manager.recommend_equipment_for_school(equipment_list)
        
        # 验证推荐结果
        assert len(recommendations) == len(equipment_list)
        
        # 剑修应该更偏好攻击属性的装备
        best_equipment, best_score = recommendations[0]
        assert best_score > 0
        
        # 验证排序正确性
        scores = [score for _, score in recommendations]
        assert scores == sorted(scores, reverse=True)
    
    def test_save_load_with_cultivation_data(self):
        """测试包含流派数据的保存和加载"""
        # 设置复杂的流派状态
        self.state_manager.update_character_data({
            "school": SchoolType.FORMATION.value,
            "level": 20,
            "unlocked_skills": ["formation_basic", "formation_mastery"],
            "cultivation_progress": {"formation_mastery": 0.8}
        })
        
        # 保存状态
        save_success = self.state_manager.save_state()
        assert save_success
        
        # 创建新的状态管理器并加载
        new_state_manager = UnifiedStateManager(config_dir=self.temp_dir)
        load_success = new_state_manager.load_state()
        assert load_success
        
        # 验证流派数据正确加载
        loaded_character = new_state_manager.character_data
        assert loaded_character["school"] == SchoolType.FORMATION.value
        assert loaded_character["level"] == 20
        assert "formation_basic" in loaded_character["unlocked_skills"]
        
        # 验证流派信息正确同步
        school_info = new_state_manager.get_school_info()
        assert school_info["name"] == "阵修"
        assert school_info["element_affinity"] == "土"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])