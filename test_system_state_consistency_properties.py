# -*- coding: utf-8 -*-
"""
系统状态统一性的属性测试
**Property 10: 系统状态统一性**
**Validates: Requirements 3.5**
"""

import pytest
import tempfile
import shutil
import os
import json
import copy
from hypothesis import given, strategies as st, settings
from typing import Dict, Any, List, Optional, Tuple
from unified_state_manager import UnifiedStateManager, get_state_manager, initialize_unified_system
from wuxing_engine import WuxingEngine
from cultivation_school_system import get_school_manager
from loot_generator import get_loot_generator, get_challenge_manager, get_bd_optimizer


# 测试数据生成策略
@st.composite
def complete_system_state_strategy(draw):
    """生成完整系统状态的策略"""
    trigrams = ["QIAN", "DUI", "LI", "ZHEN", "XUN", "KAN", "GEN", "KUN"]
    elements = ["木", "火", "土", "金", "水"]
    schools = ["sword_cultivator", "spell_cultivator", "body_cultivator", "pill_cultivator", "formation_cultivator"]
    realms = ["炼气", "筑基", "金丹", "元婴", "化神"]
    
    # 生成角色数据
    character_data = {
        "name": draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        "level": draw(st.integers(min_value=1, max_value=100)),
        "school": draw(st.sampled_from(schools)),
        "realm": draw(st.sampled_from(realms)),
        "base_attributes": {
            "str": draw(st.integers(min_value=10, max_value=100)),
            "agi": draw(st.integers(min_value=10, max_value=100)),
            "int": draw(st.integers(min_value=10, max_value=100)),
            "max_hp": draw(st.integers(min_value=200, max_value=5000)),
            "base_atk": draw(st.integers(min_value=20, max_value=500)),
            "crit_rate": draw(st.floats(min_value=0.01, max_value=0.5)),
            "crit_dmg": draw(st.floats(min_value=1.1, max_value=3.0))
        },
        "affinity_main": draw(st.sampled_from(elements))
    }
    
    # 生成八卦配置
    bagua_stones = {}
    for tri in trigrams:
        bagua_stones[tri] = {}
        for slot in range(1, 5):
            if slot == 1:
                # 逻辑位
                bagua_stones[tri][slot] = draw(st.sampled_from(["logic_blood", "logic_heat", None]))
            else:
                # 五行灵石位
                bagua_stones[tri][slot] = draw(st.sampled_from([f"gem_{elem}" for elem in elements] + [None]))
    
    bagua_configuration = {
        "stones": bagua_stones,
        "core": {
            1: draw(st.sampled_from(["core_mad", "core_invert", "core_overclock", None])),
            2: draw(st.sampled_from(["core_mad", "core_invert", "core_overclock", None])),
            3: draw(st.sampled_from(["core_mad", "core_invert", "core_overclock", None]))
        },
        "seed": draw(st.integers(min_value=0, max_value=999999))
    }
    
    # 生成战斗设置
    skills = ["mvp_basic_attack", "mvp_crit_execute", "mvp_emergency_mend"]
    modifiers = ["mvp_mod_damage_20", "mvp_mod_crit_10", "mvp_mod_haste", "mvp_mod_tough"]
    
    combat_settings = {
        "selected_skills": draw(st.lists(st.sampled_from(skills), max_size=3)),
        "skill_chain": {
            "main_skill": draw(st.sampled_from(skills + [None])),
            "main_mods": draw(st.lists(st.sampled_from(modifiers), max_size=3)),
            "triggers": []
        },
        "simulation_params": {
            "enemy_hp": draw(st.integers(min_value=1000, max_value=10000)),
            "enemy_dps": draw(st.integers(min_value=10, max_value=100)),
            "max_time": draw(st.floats(min_value=10.0, max_value=30.0))
        }
    }
    
    # 生成掉落库存
    loot_inventory = []
    for _ in range(draw(st.integers(min_value=0, max_value=5))):
        loot_inventory.append({
            "name": draw(st.text(min_size=1, max_size=15)),
            "type": draw(st.sampled_from(["weapon", "armor", "accessory", "stone"])),
            "rarity": draw(st.sampled_from(["common", "rare", "epic", "legendary"])),
            "stats": {
                "atk": draw(st.integers(min_value=0, max_value=50)),
                "def": draw(st.integers(min_value=0, max_value=50)),
                "hp": draw(st.integers(min_value=0, max_value=200))
            }
        })
    
    return {
        "character_data": character_data,
        "bagua_configuration": bagua_configuration,
        "combat_settings": combat_settings,
        "loot_inventory": loot_inventory
    }


@st.composite
def system_operation_strategy(draw):
    """生成系统操作的策略"""
    operations = [
        "update_character",
        "update_bagua", 
        "update_combat",
        "change_school",
        "unlock_skill",
        "save_load",
        "sync_modules"
    ]
    
    return {
        "operation": draw(st.sampled_from(operations)),
        "repeat_count": draw(st.integers(min_value=1, max_value=3))
    }


class TestSystemStateConsistency:
    """系统状态统一性测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.state_manager = UnifiedStateManager(config_dir=self.temp_dir)
    
    def teardown_method(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def _verify_system_state_consistency(self, state_manager: UnifiedStateManager) -> Tuple[bool, List[str]]:
        """验证系统状态一致性的辅助方法"""
        issues = []
        
        try:
            # 获取所有模块状态
            five_elements_state = state_manager.get_module_state("five_elements")
            combat_state = state_manager.get_module_state("combat")
            character_state = state_manager.get_module_state("character")
            loot_state = state_manager.get_module_state("loot")
            ui_state = state_manager.get_module_state("ui")
            
            # 验证角色基础信息一致性
            char_name = state_manager.character_data.get("name")
            char_realm = state_manager.character_data.get("realm")
            char_school = state_manager.character_data.get("school")
            char_affinity = state_manager.character_data.get("affinity_main")
            
            # 检查五行模块一致性
            if five_elements_state.get("disciple") != char_name:
                issues.append(f"五行模块角色名不一致: {five_elements_state.get('disciple')} vs {char_name}")
            
            if five_elements_state.get("realm") != char_realm:
                issues.append(f"五行模块境界不一致: {five_elements_state.get('realm')} vs {char_realm}")
            
            if five_elements_state.get("affinity_main") != char_affinity:
                issues.append(f"五行模块主灵根不一致: {five_elements_state.get('affinity_main')} vs {char_affinity}")
            
            # 检查角色模块一致性
            char_module_data = character_state.get("character_data", {})
            if char_module_data.get("name") != char_name:
                issues.append(f"角色模块名称不一致: {char_module_data.get('name')} vs {char_name}")
            
            if char_module_data.get("realm") != char_realm:
                issues.append(f"角色模块境界不一致: {char_module_data.get('realm')} vs {char_realm}")
            
            if char_module_data.get("school") != char_school:
                issues.append(f"角色模块流派不一致: {char_module_data.get('school')} vs {char_school}")
            
            # 检查UI模块一致性
            if ui_state.get("active_character") != char_name:
                issues.append(f"UI模块角色名不一致: {ui_state.get('active_character')} vs {char_name}")
            
            if ui_state.get("current_realm") != char_realm:
                issues.append(f"UI模块境界不一致: {ui_state.get('current_realm')} vs {char_realm}")
            
            # 检查掉落模块一致性
            if loot_state.get("character_school") != char_school:
                issues.append(f"掉落模块流派不一致: {loot_state.get('character_school')} vs {char_school}")
            
            # 检查八卦配置一致性
            bagua_config = state_manager.bagua_configuration
            five_elem_board = five_elements_state.get("board", {})
            five_elem_core = five_elements_state.get("core", {})
            ui_bagua_state = ui_state.get("bagua_state", {})
            
            if bagua_config.get("stones") != five_elem_board:
                issues.append("八卦配置与五行模块不一致")
            
            if bagua_config.get("core") != five_elem_core:
                issues.append("核心配置与五行模块不一致")
            
            if ui_bagua_state.get("stones") != bagua_config.get("stones"):
                issues.append("UI八卦状态与主配置不一致")
            
            # 检查战斗模块属性同步
            combat_stats = combat_state.get("character_stats", {})
            base_attrs = state_manager.character_data.get("base_attributes", {})
            
            # 验证基础属性在战斗模块中存在且合理
            for attr_name, base_value in base_attrs.items():
                combat_value = combat_stats.get(attr_name)
                if combat_value is None:
                    issues.append(f"战斗模块缺少属性: {attr_name}")
                elif isinstance(base_value, (int, float)) and isinstance(combat_value, (int, float)):
                    if combat_value < base_value * 0.5:  # 允许一定的变化范围，但不应该过度偏离
                        issues.append(f"战斗模块属性异常偏低: {attr_name} = {combat_value} (基础值: {base_value})")
            
        except Exception as e:
            issues.append(f"状态验证过程出错: {str(e)}")
        
        return len(issues) == 0, issues
    
    @given(system_state=complete_system_state_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_system_state_consistency_unified_data_storage(self, system_state):
        """
        **Feature: rpg-system-integration, Property 10: 系统状态统一性**
        
        测试系统使用统一的数据存储和配置管理
        For any 系统运行状态，所有模块应该使用统一的数据存储和配置管理，不存在数据孤岛或不一致的状态
        **Validates: Requirements 3.5**
        """
        # 设置完整的系统状态
        self.state_manager.update_character_data(system_state["character_data"])
        self.state_manager.update_bagua_configuration(system_state["bagua_configuration"])
        self.state_manager.update_combat_settings(system_state["combat_settings"])
        self.state_manager.loot_inventory = system_state["loot_inventory"]
        
        # 强制同步所有模块
        self.state_manager.sync_modules()
        
        # 验证系统状态一致性
        is_consistent, issues = self._verify_system_state_consistency(self.state_manager)
        
        # 系统应该保持完全一致性
        assert is_consistent, f"系统状态不一致: {issues}"
        
        # 验证统一状态管理器的内置一致性检查
        builtin_consistent, builtin_issues = self.state_manager.validate_state_consistency()
        assert builtin_consistent, f"内置一致性检查失败: {builtin_issues}"
        
        # 验证系统状态概览反映正确信息
        system_status = self.state_manager.get_system_status()
        assert system_status["state_consistent"] == True
        assert system_status["character_name"] == system_state["character_data"]["name"]
        assert system_status["character_realm"] == system_state["character_data"]["realm"]
        assert system_status["character_school"] == system_state["character_data"]["school"]
    
    @given(
        initial_state=complete_system_state_strategy(),
        operations=st.lists(system_operation_strategy(), min_size=1, max_size=5)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_system_state_consistency_operation_sequences(self, initial_state, operations):
        """
        **Feature: rpg-system-integration, Property 10: 系统状态统一性**
        
        测试系统操作序列中的状态一致性
        For any 系统操作序列，每个操作后系统都应该保持状态一致性
        **Validates: Requirements 3.5**
        """
        # 设置初始状态
        self.state_manager.update_character_data(initial_state["character_data"])
        self.state_manager.update_bagua_configuration(initial_state["bagua_configuration"])
        self.state_manager.update_combat_settings(initial_state["combat_settings"])
        self.state_manager.loot_inventory = initial_state["loot_inventory"]
        
        # 验证初始状态一致性
        initial_consistent, initial_issues = self._verify_system_state_consistency(self.state_manager)
        assert initial_consistent, f"初始状态不一致: {initial_issues}"
        
        # 执行操作序列
        for operation in operations:
            op_type = operation["operation"]
            repeat_count = operation["repeat_count"]
            
            for _ in range(repeat_count):
                try:
                    if op_type == "update_character":
                        # 更新角色数据
                        updates = {
                            "level": self.state_manager.character_data.get("level", 1) + 1
                        }
                        self.state_manager.update_character_data(updates)
                    
                    elif op_type == "update_bagua":
                        # 更新八卦配置
                        current_seed = self.state_manager.bagua_configuration.get("seed", 0)
                        updates = {"seed": (current_seed + 1) % 1000000}
                        self.state_manager.update_bagua_configuration(updates)
                    
                    elif op_type == "update_combat":
                        # 更新战斗设置
                        updates = {
                            "simulation_params": {
                                "enemy_hp": 3000,
                                "enemy_dps": 25,
                                "max_time": 20.0
                            }
                        }
                        self.state_manager.update_combat_settings(updates)
                    
                    elif op_type == "change_school":
                        # 更改流派
                        schools = ["sword_cultivator", "spell_cultivator", "body_cultivator"]
                        current_school = self.state_manager.character_data.get("school", "sword_cultivator")
                        new_school = schools[(schools.index(current_school) + 1) % len(schools)]
                        self.state_manager.change_character_school(new_school)
                    
                    elif op_type == "sync_modules":
                        # 强制同步模块
                        self.state_manager.sync_modules()
                    
                    elif op_type == "save_load":
                        # 保存和加载状态
                        save_success = self.state_manager.save_state()
                        if save_success:
                            load_success = self.state_manager.load_state()
                            assert load_success, "状态加载失败"
                    
                    # 每次操作后验证状态一致性
                    op_consistent, op_issues = self._verify_system_state_consistency(self.state_manager)
                    assert op_consistent, f"操作 {op_type} 后状态不一致: {op_issues}"
                    
                except Exception as e:
                    # 如果操作失败，至少系统状态应该保持一致
                    fallback_consistent, fallback_issues = self._verify_system_state_consistency(self.state_manager)
                    assert fallback_consistent, f"操作 {op_type} 失败后状态不一致: {fallback_issues}"
    
    @given(
        state1=complete_system_state_strategy(),
        state2=complete_system_state_strategy()
    )
    @settings(max_examples=50, deadline=None)
    def test_property_system_state_consistency_state_transitions(self, state1, state2):
        """
        **Feature: rpg-system-integration, Property 10: 系统状态统一性**
        
        测试系统状态转换过程中的一致性
        For any 系统状态转换，转换过程和结果都应该保持模块间数据一致性
        **Validates: Requirements 3.5**
        """
        # 设置第一个状态
        self.state_manager.update_character_data(state1["character_data"])
        self.state_manager.update_bagua_configuration(state1["bagua_configuration"])
        self.state_manager.update_combat_settings(state1["combat_settings"])
        self.state_manager.loot_inventory = state1["loot_inventory"]
        
        # 验证第一个状态的一致性
        state1_consistent, state1_issues = self._verify_system_state_consistency(self.state_manager)
        assert state1_consistent, f"状态1不一致: {state1_issues}"
        
        # 转换到第二个状态
        self.state_manager.update_character_data(state2["character_data"])
        self.state_manager.update_bagua_configuration(state2["bagua_configuration"])
        self.state_manager.update_combat_settings(state2["combat_settings"])
        self.state_manager.loot_inventory = state2["loot_inventory"]
        
        # 验证第二个状态的一致性
        state2_consistent, state2_issues = self._verify_system_state_consistency(self.state_manager)
        assert state2_consistent, f"状态2不一致: {state2_issues}"
        
        # 验证状态确实发生了变化（如果两个状态不同）
        if state1["character_data"]["name"] != state2["character_data"]["name"]:
            current_name = self.state_manager.character_data.get("name")
            assert current_name == state2["character_data"]["name"], "角色名称未正确更新"
        
        if state1["character_data"]["realm"] != state2["character_data"]["realm"]:
            current_realm = self.state_manager.character_data.get("realm")
            assert current_realm == state2["character_data"]["realm"], "角色境界未正确更新"
    
    @given(system_state=complete_system_state_strategy())
    @settings(max_examples=50, deadline=None)
    def test_property_system_state_consistency_persistence_roundtrip(self, system_state):
        """
        **Feature: rpg-system-integration, Property 10: 系统状态统一性**
        
        测试数据持久化过程中的状态一致性
        For any 系统状态，保存和加载后应该保持完全一致的状态
        **Validates: Requirements 3.5**
        """
        # 设置系统状态
        self.state_manager.update_character_data(system_state["character_data"])
        self.state_manager.update_bagua_configuration(system_state["bagua_configuration"])
        self.state_manager.update_combat_settings(system_state["combat_settings"])
        self.state_manager.loot_inventory = system_state["loot_inventory"]
        
        # 验证保存前状态一致性
        pre_save_consistent, pre_save_issues = self._verify_system_state_consistency(self.state_manager)
        assert pre_save_consistent, f"保存前状态不一致: {pre_save_issues}"
        
        # 获取保存前的详细状态
        pre_save_character = copy.deepcopy(self.state_manager.character_data)
        pre_save_bagua = copy.deepcopy(self.state_manager.bagua_configuration)
        pre_save_combat = copy.deepcopy(self.state_manager.combat_settings)
        pre_save_loot = copy.deepcopy(self.state_manager.loot_inventory)
        
        # 保存状态
        save_success = self.state_manager.save_state()
        assert save_success, "状态保存失败"
        
        # 创建新的状态管理器并加载
        new_state_manager = UnifiedStateManager(config_dir=self.temp_dir)
        load_success = new_state_manager.load_state()
        assert load_success, "状态加载失败"
        
        # 验证加载后状态一致性
        post_load_consistent, post_load_issues = self._verify_system_state_consistency(new_state_manager)
        assert post_load_consistent, f"加载后状态不一致: {post_load_issues}"
        
        # 验证数据完全一致
        assert new_state_manager.character_data == pre_save_character, "角色数据不一致"
        assert new_state_manager.bagua_configuration == pre_save_bagua, "八卦配置不一致"
        assert new_state_manager.combat_settings == pre_save_combat, "战斗设置不一致"
        assert new_state_manager.loot_inventory == pre_save_loot, "掉落库存不一致"
    
    @given(system_state=complete_system_state_strategy())
    @settings(max_examples=50, deadline=None)
    def test_property_system_state_consistency_module_isolation(self, system_state):
        """
        **Feature: rpg-system-integration, Property 10: 系统状态统一性**
        
        测试模块隔离性和数据共享的一致性
        For any 系统状态，各模块应该通过统一接口访问数据，不存在直接的数据依赖
        **Validates: Requirements 3.5**
        """
        # 设置系统状态
        self.state_manager.update_character_data(system_state["character_data"])
        self.state_manager.update_bagua_configuration(system_state["bagua_configuration"])
        self.state_manager.update_combat_settings(system_state["combat_settings"])
        self.state_manager.loot_inventory = system_state["loot_inventory"]
        
        # 获取各模块状态
        five_elements_state = self.state_manager.get_module_state("five_elements")
        combat_state = self.state_manager.get_module_state("combat")
        character_state = self.state_manager.get_module_state("character")
        loot_state = self.state_manager.get_module_state("loot")
        ui_state = self.state_manager.get_module_state("ui")
        
        # 验证每个模块都能获取到完整且一致的状态
        assert isinstance(five_elements_state, dict), "五行模块状态应该是字典"
        assert isinstance(combat_state, dict), "战斗模块状态应该是字典"
        assert isinstance(character_state, dict), "角色模块状态应该是字典"
        assert isinstance(loot_state, dict), "掉落模块状态应该是字典"
        assert isinstance(ui_state, dict), "UI模块状态应该是字典"
        
        # 验证关键数据在各模块中的一致性
        char_name = system_state["character_data"]["name"]
        char_realm = system_state["character_data"]["realm"]
        char_school = system_state["character_data"]["school"]
        
        # 所有涉及角色信息的模块都应该有一致的数据
        modules_with_char_name = [
            ("five_elements", five_elements_state.get("disciple")),
            ("character", character_state.get("character_data", {}).get("name")),
            ("ui", ui_state.get("active_character"))
        ]
        
        for module_name, module_char_name in modules_with_char_name:
            assert module_char_name == char_name, f"{module_name}模块角色名不一致: {module_char_name} vs {char_name}"
        
        modules_with_char_realm = [
            ("five_elements", five_elements_state.get("realm")),
            ("character", character_state.get("character_data", {}).get("realm")),
            ("ui", ui_state.get("current_realm"))
        ]
        
        for module_name, module_char_realm in modules_with_char_realm:
            assert module_char_realm == char_realm, f"{module_name}模块境界不一致: {module_char_realm} vs {char_realm}"
        
        # 验证模块状态的完整性（每个模块都应该有必要的数据）
        assert "disciple" in five_elements_state, "五行模块缺少弟子信息"
        assert "realm" in five_elements_state, "五行模块缺少境界信息"
        assert "board" in five_elements_state, "五行模块缺少八卦盘信息"
        
        assert "character_stats" in combat_state, "战斗模块缺少角色属性"
        assert "bagua_effects" in combat_state, "战斗模块缺少八卦效果"
        
        assert "character_data" in character_state, "角色模块缺少角色数据"
        assert "school_info" in character_state, "角色模块缺少流派信息"
        
        assert "character_school" in loot_state, "掉落模块缺少角色流派"
        assert "character_level" in loot_state, "掉落模块缺少角色等级"


if __name__ == "__main__":
    # 运行属性测试
    pytest.main([__file__, "-v", "--tb=short"])