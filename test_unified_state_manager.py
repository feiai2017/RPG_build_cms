# -*- coding: utf-8 -*-
"""
统一状态管理器的属性测试
**Property 3: 模块数据同步一致性**
**Validates: Requirements 3.2, 3.3, 3.4**
"""

import pytest
import tempfile
import shutil
import os
import json
from hypothesis import given, strategies as st, settings
from typing import Dict, Any, List
from unified_state_manager import UnifiedStateManager, UnifiedCharacter
from module_interfaces import ModuleType, EventType, ModuleEvent, get_communication_hub
from config_manager import ConfigManager, ConfigScope


# 测试数据生成策略
@st.composite
def character_data_strategy(draw):
    """生成角色数据的策略"""
    return {
        "name": draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        "level": draw(st.integers(min_value=1, max_value=100)),
        "school": draw(st.sampled_from(["sword_cultivator", "spell_cultivator", "body_cultivator", "pill_cultivator", "formation_cultivator"])),
        "realm": draw(st.sampled_from(["炼气", "筑基", "金丹", "元婴", "化神"])),
        "base_attributes": {
            "str": draw(st.integers(min_value=1, max_value=100)),
            "agi": draw(st.integers(min_value=1, max_value=100)),
            "int": draw(st.integers(min_value=1, max_value=100)),
            "max_hp": draw(st.integers(min_value=100, max_value=10000)),
            "base_atk": draw(st.integers(min_value=10, max_value=1000)),
            "crit_rate": draw(st.floats(min_value=0.0, max_value=1.0)),
            "crit_dmg": draw(st.floats(min_value=1.0, max_value=5.0))
        },
        "affinity_main": draw(st.sampled_from(["木", "火", "土", "金", "水"]))
    }


@st.composite
def bagua_configuration_strategy(draw):
    """生成八卦配置的策略"""
    trigrams = ["QIAN", "DUI", "LI", "ZHEN", "XUN", "KAN", "GEN", "KUN"]
    stones = ["gem_wood", "gem_fire", "gem_earth", "gem_metal", "gem_water", 
              "logic_blood", "logic_heat", None]
    
    bagua_stones = {}
    for tri in trigrams:
        bagua_stones[tri] = {}
        for slot in range(1, 5):
            # 逻辑位只能放逻辑灵石或空
            if slot == 1:
                bagua_stones[tri][slot] = draw(st.sampled_from(["logic_blood", "logic_heat", None]))
            else:
                # 其他位置可以放五行灵石或空
                bagua_stones[tri][slot] = draw(st.sampled_from(["gem_wood", "gem_fire", "gem_earth", "gem_metal", "gem_water", None]))
    
    core_bios = {}
    for slot in range(1, 4):
        core_bios[slot] = draw(st.sampled_from(["core_mad", "core_invert", "core_overclock", None]))
    
    return {
        "stones": bagua_stones,
        "core": core_bios,
        "seed": draw(st.integers(min_value=0, max_value=999999))
    }


@st.composite
def combat_settings_strategy(draw):
    """生成战斗设置的策略"""
    skills = ["mvp_basic_attack", "mvp_crit_execute", "mvp_emergency_mend"]
    modifiers = ["mvp_mod_damage_20", "mvp_mod_crit_10", "mvp_mod_haste", "mvp_mod_tough"]
    
    return {
        "selected_skills": draw(st.lists(st.sampled_from(skills), max_size=3)),
        "skill_chain": {
            "main_skill": draw(st.sampled_from(skills + [None])),
            "main_mods": draw(st.lists(st.sampled_from(modifiers), max_size=3)),
            "triggers": draw(st.lists(st.dictionaries(
                keys=st.sampled_from(["condition", "skill", "mods"]),
                values=st.one_of(
                    st.sampled_from(["on_hit", "on_crit", "hp_lt_30"]),
                    st.sampled_from(skills),
                    st.lists(st.sampled_from(modifiers), max_size=2)
                )
            ), max_size=2))
        },
        "simulation_params": {
            "enemy_hp": draw(st.integers(min_value=1000, max_value=20000)),
            "enemy_dps": draw(st.integers(min_value=10, max_value=200)),
            "max_time": draw(st.floats(min_value=10.0, max_value=60.0))
        }
    }


class TestUnifiedStateManager:
    """统一状态管理器测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.state_manager = UnifiedStateManager(config_dir=self.temp_dir)
    
    def teardown_method(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @given(character_data=character_data_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_module_data_sync_consistency_character_updates(self, character_data):
        """
        **Feature: rpg-system-integration, Property 3: 模块数据同步一致性**
        
        测试角色数据更新时，所有相关模块的数据状态保持一致
        For any 用户在任意模块中的配置修改，所有相关模块的数据状态应该保持一致，不存在数据不同步的情况
        **Validates: Requirements 3.2, 3.3, 3.4**
        """
        # 更新角色数据
        self.state_manager.update_character_data(character_data)
        
        # 获取各模块状态
        five_elements_state = self.state_manager.get_module_state("five_elements")
        combat_state = self.state_manager.get_module_state("combat")
        character_state = self.state_manager.get_module_state("character")
        ui_state = self.state_manager.get_module_state("ui")
        
        # 验证角色基础信息在所有相关模块中一致
        assert five_elements_state.get("disciple") == character_data["name"]
        assert five_elements_state.get("realm") == character_data["realm"]
        assert five_elements_state.get("affinity_main") == character_data["affinity_main"]
        
        assert character_state.get("character_data", {}).get("name") == character_data["name"]
        assert character_state.get("character_data", {}).get("realm") == character_data["realm"]
        assert character_state.get("character_data", {}).get("school") == character_data["school"]
        
        assert ui_state.get("active_character") == character_data["name"]
        assert ui_state.get("current_realm") == character_data["realm"]
        
        # 验证属性数据在战斗模块中正确同步
        combat_stats = combat_state.get("character_stats", {})
        for attr_name, attr_value in character_data["base_attributes"].items():
            assert combat_stats.get(attr_name) is not None
            # 基础属性应该被包含（可能有加成）
            if attr_name in ["str", "agi", "int", "max_hp", "base_atk"]:
                assert combat_stats.get(attr_name) >= attr_value
    
    @given(bagua_config=bagua_configuration_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_module_data_sync_consistency_bagua_updates(self, bagua_config):
        """
        **Feature: rpg-system-integration, Property 3: 模块数据同步一致性**
        
        测试八卦配置更新时，所有相关模块的数据状态保持一致
        For any 用户在五行八卦模块中的配置修改，战斗和角色模块应该立即同步更新
        **Validates: Requirements 3.2, 3.3, 3.4**
        """
        # 更新八卦配置
        self.state_manager.update_bagua_configuration(bagua_config)
        
        # 获取各模块状态
        five_elements_state = self.state_manager.get_module_state("five_elements")
        combat_state = self.state_manager.get_module_state("combat")
        ui_state = self.state_manager.get_module_state("ui")
        
        # 验证八卦配置在五行模块中正确存储
        assert five_elements_state.get("board") == bagua_config["stones"]
        assert five_elements_state.get("core") == bagua_config["core"]
        assert five_elements_state.get("seed") == bagua_config["seed"]
        
        # 验证八卦效果在战斗模块中正确计算
        bagua_effects = combat_state.get("bagua_effects", {})
        assert isinstance(bagua_effects, dict)
        
        # 验证UI状态正确反映八卦配置
        ui_bagua_state = ui_state.get("bagua_state", {})
        assert ui_bagua_state.get("stones") == bagua_config["stones"]
        assert ui_bagua_state.get("core") == bagua_config["core"]
        assert ui_bagua_state.get("seed") == bagua_config["seed"]
    
    @given(
        character_data=character_data_strategy(),
        bagua_config=bagua_configuration_strategy(),
        combat_settings=combat_settings_strategy()
    )
    @settings(max_examples=50, deadline=None)
    def test_property_module_data_sync_consistency_full_system(self, character_data, bagua_config, combat_settings):
        """
        **Feature: rpg-system-integration, Property 3: 模块数据同步一致性**
        
        测试完整系统中所有模块数据同步的一致性
        For any 系统中的任意配置组合，所有模块的数据状态应该保持完全一致
        **Validates: Requirements 3.2, 3.3, 3.4**
        """
        # 依次更新所有配置
        self.state_manager.update_character_data(character_data)
        self.state_manager.update_bagua_configuration(bagua_config)
        self.state_manager.update_combat_settings(combat_settings)
        
        # 验证状态一致性
        is_consistent, issues = self.state_manager.validate_state_consistency()
        
        # 系统应该保持一致性
        assert is_consistent, f"状态不一致: {issues}"
        
        # 获取系统状态概览
        system_status = self.state_manager.get_system_status()
        
        # 验证系统状态反映正确的配置
        assert system_status["character_name"] == character_data["name"]
        assert system_status["character_realm"] == character_data["realm"]
        assert system_status["character_school"] == character_data["school"]
        assert system_status["state_consistent"] == True
        
        # 验证各模块状态的关键一致性点
        five_elements_state = self.state_manager.get_module_state("five_elements")
        combat_state = self.state_manager.get_module_state("combat")
        character_state = self.state_manager.get_module_state("character")
        ui_state = self.state_manager.get_module_state("ui")
        
        # 角色名称在所有模块中一致
        assert five_elements_state.get("disciple") == character_data["name"]
        assert character_state.get("character_data", {}).get("name") == character_data["name"]
        assert ui_state.get("active_character") == character_data["name"]
        
        # 境界信息在所有模块中一致
        assert five_elements_state.get("realm") == character_data["realm"]
        assert character_state.get("character_data", {}).get("realm") == character_data["realm"]
        assert ui_state.get("current_realm") == character_data["realm"]
    
    @given(
        initial_data=character_data_strategy(),
        updated_data=character_data_strategy()
    )
    @settings(max_examples=50, deadline=None)
    def test_property_module_data_sync_consistency_state_transitions(self, initial_data, updated_data):
        """
        **Feature: rpg-system-integration, Property 3: 模块数据同步一致性**
        
        测试状态转换过程中的数据同步一致性
        For any 状态转换过程，中间状态和最终状态都应该保持模块间数据一致性
        **Validates: Requirements 3.2, 3.3, 3.4**
        """
        # 设置初始状态
        self.state_manager.update_character_data(initial_data)
        
        # 验证初始状态一致性
        initial_consistent, _ = self.state_manager.validate_state_consistency()
        assert initial_consistent, "初始状态应该保持一致性"
        
        # 更新到新状态
        self.state_manager.update_character_data(updated_data)
        
        # 验证更新后状态一致性
        final_consistent, _ = self.state_manager.validate_state_consistency()
        assert final_consistent, "更新后状态应该保持一致性"
        
        # 验证状态确实发生了变化
        current_character = self.state_manager.get_module_state("character").get("character_data", {})
        assert current_character.get("name") == updated_data["name"]
        assert current_character.get("realm") == updated_data["realm"]
        assert current_character.get("school") == updated_data["school"]
    
    @given(
        character_data=character_data_strategy(),
        bagua_config=bagua_configuration_strategy()
    )
    @settings(max_examples=50, deadline=None)
    def test_property_module_data_sync_consistency_save_load_roundtrip(self, character_data, bagua_config):
        """
        **Feature: rpg-system-integration, Property 3: 模块数据同步一致性**
        
        测试保存和加载过程中的数据同步一致性
        For any 保存和加载操作，加载后的状态应该与保存前完全一致
        **Validates: Requirements 3.2, 3.3, 3.4**
        """
        # 设置状态
        self.state_manager.update_character_data(character_data)
        self.state_manager.update_bagua_configuration(bagua_config)
        
        # 获取保存前的状态
        original_five_elements = self.state_manager.get_module_state("five_elements")
        original_combat = self.state_manager.get_module_state("combat")
        original_character = self.state_manager.get_module_state("character")
        original_ui = self.state_manager.get_module_state("ui")
        
        # 保存状态
        save_success = self.state_manager.save_state()
        assert save_success, "状态保存应该成功"
        
        # 创建新的状态管理器并加载
        new_state_manager = UnifiedStateManager(config_dir=self.temp_dir)
        load_success = new_state_manager.load_state()
        assert load_success, "状态加载应该成功"
        
        # 获取加载后的状态
        loaded_five_elements = new_state_manager.get_module_state("five_elements")
        loaded_combat = new_state_manager.get_module_state("combat")
        loaded_character = new_state_manager.get_module_state("character")
        loaded_ui = new_state_manager.get_module_state("ui")
        
        # 验证关键数据一致性
        assert loaded_five_elements.get("disciple") == original_five_elements.get("disciple")
        assert loaded_five_elements.get("realm") == original_five_elements.get("realm")
        assert loaded_five_elements.get("affinity_main") == original_five_elements.get("affinity_main")
        
        assert loaded_character.get("character_data", {}).get("name") == original_character.get("character_data", {}).get("name")
        assert loaded_character.get("character_data", {}).get("realm") == original_character.get("character_data", {}).get("realm")
        
        assert loaded_ui.get("active_character") == original_ui.get("active_character")
        assert loaded_ui.get("current_realm") == original_ui.get("current_realm")
        
        # 验证加载后状态一致性
        is_consistent, issues = new_state_manager.validate_state_consistency()
        assert is_consistent, f"加载后状态应该保持一致性: {issues}"


if __name__ == "__main__":
    # 运行属性测试
    pytest.main([__file__, "-v", "--tb=short"])