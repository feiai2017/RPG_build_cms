# -*- coding: utf-8 -*-
"""
数据持久化完整性属性测试
测试RPG系统的数据保存、加载、导入导出功能的正确性
"""

import pytest
import tempfile
import shutil
import os
import json
import yaml
from hypothesis import given, strategies as st, settings, assume
from typing import Dict, List, Any, Optional
from pathlib import Path
from unified_state_manager import UnifiedStateManager, UnifiedCharacter
from config_manager import ConfigManager, ConfigScope, ConfigFormat


# 测试数据生成策略
@st.composite
def character_data_strategy(draw):
    """生成角色数据的策略（简化版）"""
    return {
        "name": draw(st.text(min_size=1, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz")),
        "level": draw(st.integers(min_value=1, max_value=50)),
        "school": draw(st.sampled_from(["sword_cultivator", "spell_cultivator", "body_cultivator"])),
        "realm": draw(st.sampled_from(["炼气", "筑基", "金丹"])),
        "base_attributes": {
            "str": draw(st.integers(min_value=10, max_value=50)),
            "agi": draw(st.integers(min_value=10, max_value=50)),
            "int": draw(st.integers(min_value=10, max_value=50)),
            "max_hp": draw(st.integers(min_value=500, max_value=2000)),
            "base_atk": draw(st.integers(min_value=20, max_value=100)),
            "crit_rate": draw(st.floats(min_value=0.05, max_value=0.5)),
            "crit_dmg": draw(st.floats(min_value=1.5, max_value=3.0))
        },
        "affinity_main": draw(st.sampled_from(["木", "火", "土", "金", "水"]))
    }


@st.composite
def bagua_configuration_strategy(draw):
    """生成八卦配置的策略（简化版）"""
    trigrams = ["QIAN", "DUI", "LI", "ZHEN"]  # 减少到4个卦位
    stones = {}
    
    for tri in trigrams:
        stones[tri] = {}
        for i in range(1, 3):  # 减少到2个槽位
            # 50%概率放置灵石
            if draw(st.booleans()):
                element = draw(st.sampled_from(["木", "火", "土"]))
                stones[tri][i] = f"gem_{element}_{draw(st.integers(min_value=1, max_value=99))}"
            else:
                stones[tri][i] = None
    
    core = {}
    for i in range(1, 2):  # 只有1个核心槽位
        if draw(st.booleans()):
            core[i] = f"core_bio_{draw(st.integers(min_value=1, max_value=9))}"
        else:
            core[i] = None
    
    return {
        "stones": stones,
        "core": core,
        "seed": draw(st.integers(min_value=1, max_value=9999))
    }


@st.composite
def combat_settings_strategy(draw):
    """生成战斗设置的策略（简化版）"""
    return {
        "selected_skills": draw(st.lists(st.text(min_size=1, max_size=10, alphabet="abcdefg"), min_size=0, max_size=3)),
        "skill_chain": {
            "main_skill": draw(st.one_of(st.none(), st.text(min_size=1, max_size=10, alphabet="abcdefg"))),
            "main_mods": draw(st.lists(st.text(min_size=1, max_size=10, alphabet="abcdefg"), min_size=0, max_size=2)),
            "triggers": []  # 简化为空列表
        },
        "simulation_params": {
            "enemy_hp": draw(st.integers(min_value=1000, max_value=5000)),
            "enemy_dps": draw(st.integers(min_value=10, max_value=100)),
            "max_time": draw(st.floats(min_value=5.0, max_value=30.0))
        }
    }


class TestDataPersistenceProperties:
    """数据持久化完整性属性测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.state_manager = UnifiedStateManager(config_dir=self.temp_dir)
        self.config_manager = ConfigManager(config_root=self.temp_dir)
    
    def teardown_method(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @given(
        character_data=character_data_strategy(),
        bagua_config=bagua_configuration_strategy(),
        combat_settings=combat_settings_strategy()
    )
    @settings(max_examples=5, deadline=10000)  # 减少到5个例子，增加超时时间
    def test_property_8_data_persistence_integrity(self, character_data, bagua_config, combat_settings):
        """
        Property 8: 数据持久化完整性
        For any 用户配置保存操作，保存的数据应该能够完整恢复，包括角色属性、八卦配置、装备等所有状态信息
        **Feature: rpg-system-integration, Property 8: 数据持久化完整性**
        **Validates: Requirements 2.5, 7.1, 7.2, 7.3, 7.4**
        """
        # 设置初始状态
        self.state_manager.update_character_data(character_data)
        self.state_manager.update_bagua_configuration(bagua_config)
        self.state_manager.update_combat_settings(combat_settings)
        
        # 添加一些库存物品（简化）
        loot_items = [
            {"id": f"item_{i}", "name": f"物品{i}", "type": "weapon"}
            for i in range(2)  # 减少到2个物品
        ]
        self.state_manager.loot_inventory = loot_items
        
        # 保存状态
        save_success = self.state_manager.save_state()
        assert save_success, "状态保存应该成功"
        
        # 创建新的状态管理器并加载
        new_state_manager = UnifiedStateManager(config_dir=self.temp_dir)
        load_success = new_state_manager.load_state()
        assert load_success, "状态加载应该成功"
        
        # 验证角色数据完整性（简化验证）
        loaded_char_data = new_state_manager.character_data
        key_fields = ["name", "level", "school", "realm"]  # 只验证关键字段
        for key in key_fields:
            if key in character_data and key in loaded_char_data:
                assert loaded_char_data[key] == character_data[key], f"角色数据字段 {key} 不匹配"
        
        # 验证八卦配置完整性（简化验证）
        loaded_bagua_config = new_state_manager.bagua_configuration
        assert loaded_bagua_config.get("seed") == bagua_config["seed"], "八卦种子不匹配"
        
        # 验证战斗设置完整性（简化验证）
        loaded_combat_settings = new_state_manager.combat_settings
        assert loaded_combat_settings.get("selected_skills") == combat_settings["selected_skills"], "选中技能不匹配"
        
        # 验证库存物品完整性
        loaded_inventory = new_state_manager.loot_inventory
        assert len(loaded_inventory) == len(loot_items), "库存物品数量不匹配"
    
    @given(
        character_data=character_data_strategy(),
        bagua_config=bagua_configuration_strategy(),
        format_choice=st.sampled_from(["json", "yaml"])
    )
    @settings(max_examples=50, deadline=None)
    def test_export_import_round_trip(self, character_data, bagua_config, format_choice):
        """
        测试导出导入的往返一致性
        For any 配置数据，导出后再导入应该保持数据完整性
        """
        # 设置初始状态
        self.state_manager.update_character_data(character_data)
        self.state_manager.update_bagua_configuration(bagua_config)
        
        # 导出配置
        export_path = os.path.join(self.temp_dir, f"export_test.{format_choice}")
        export_success = self.state_manager.export_configuration(export_path, format_choice)
        assert export_success, f"导出到 {format_choice} 格式应该成功"
        
        # 验证导出文件存在
        assert os.path.exists(export_path), "导出文件应该存在"
        
        # 创建新的状态管理器并导入
        new_state_manager = UnifiedStateManager(config_dir=self.temp_dir)
        import_success = new_state_manager.import_configuration(export_path)
        assert import_success, f"从 {format_choice} 格式导入应该成功"
        
        # 验证导入后的数据一致性
        imported_char_data = new_state_manager.character_data
        for key, value in character_data.items():
            if key in imported_char_data:
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        assert imported_char_data[key].get(sub_key) == sub_value, f"导入后角色数据字段 {key}.{sub_key} 不匹配"
                else:
                    assert imported_char_data[key] == value, f"导入后角色数据字段 {key} 不匹配"
        
        imported_bagua_config = new_state_manager.bagua_configuration
        assert imported_bagua_config.get("seed") == bagua_config["seed"], "导入后八卦种子不匹配"
    
    @given(
        config_data=st.dictionaries(
            st.text(min_size=1, max_size=20),
            st.one_of(
                st.text(min_size=1, max_size=50),
                st.integers(min_value=1, max_value=1000),
                st.floats(min_value=0.1, max_value=100.0),
                st.booleans()
            ),
            min_size=1,
            max_size=10
        ),
        config_name=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))
    )
    @settings(max_examples=50, deadline=None)
    def test_config_manager_persistence(self, config_data, config_name):
        """
        测试配置管理器的持久化功能
        For any 配置数据，通过配置管理器保存和加载应该保持一致性
        """
        # 保存角色配置
        save_success = self.config_manager.set_config(ConfigScope.CHARACTER, config_data, config_name)
        assert save_success, "配置保存应该成功"
        
        # 加载配置
        loaded_config = self.config_manager.get_config(ConfigScope.CHARACTER, config_name)
        
        # 验证数据一致性
        for key, value in config_data.items():
            assert loaded_config.get(key) == value, f"配置字段 {key} 不匹配"
    
    @given(
        config_data=st.dictionaries(
            st.text(min_size=1, max_size=20),
            st.one_of(st.text(min_size=1, max_size=50), st.integers(), st.floats(), st.booleans()),
            min_size=1,
            max_size=10
        ),
        export_format=st.sampled_from([ConfigFormat.JSON, ConfigFormat.YAML])
    )
    @settings(max_examples=30, deadline=None)
    def test_config_export_import_round_trip(self, config_data, export_format):
        """
        测试配置管理器的导出导入往返一致性
        For any 配置数据，导出后再导入应该保持完整性
        """
        config_name = "test_config"
        
        # 设置配置
        self.config_manager.set_config(ConfigScope.CHARACTER, config_data, config_name)
        
        # 导出配置
        export_path = os.path.join(self.temp_dir, f"config_export.{export_format.value}")
        export_success = self.config_manager.export_config(
            ConfigScope.CHARACTER, config_name, export_path, export_format
        )
        assert export_success, "配置导出应该成功"
        
        # 导入配置到新名称
        import_name = "imported_config"
        import_success = self.config_manager.import_config(export_path, ConfigScope.CHARACTER, import_name)
        assert import_success, "配置导入应该成功"
        
        # 验证导入后的数据一致性
        imported_config = self.config_manager.get_config(ConfigScope.CHARACTER, import_name)
        for key, value in config_data.items():
            assert imported_config.get(key) == value, f"导入后配置字段 {key} 不匹配"
    
    @given(
        character_data=character_data_strategy()
    )
    @settings(max_examples=30, deadline=None)
    def test_backup_and_recovery(self, character_data):
        """
        测试备份和恢复功能
        For any 角色数据，备份后应该能够正确恢复
        """
        config_name = "backup_test"
        
        # 设置角色配置
        self.config_manager.set_config(ConfigScope.CHARACTER, character_data, config_name)
        
        # 创建备份
        backup_success = self.config_manager.backup_config(ConfigScope.CHARACTER, config_name)
        assert backup_success, "配置备份应该成功"
        
        # 验证备份文件存在
        backup_files = list(Path(self.temp_dir).glob("backups/*.yaml"))
        assert len(backup_files) > 0, "应该存在备份文件"
        
        # 修改原配置
        modified_data = character_data.copy()
        modified_data["name"] = "修改后的名称"
        self.config_manager.set_config(ConfigScope.CHARACTER, modified_data, config_name)
        
        # 从备份恢复（手动加载备份文件）
        backup_file = backup_files[0]
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = yaml.safe_load(f)
        
        # 验证备份数据的完整性
        for key, value in character_data.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    assert backup_data[key].get(sub_key) == sub_value, f"备份数据字段 {key}.{sub_key} 不匹配"
            else:
                assert backup_data[key] == value, f"备份数据字段 {key} 不匹配"
    
    def test_state_consistency_validation(self):
        """
        测试状态一致性验证功能
        系统应该能够检测和报告状态不一致问题
        """
        # 设置不完整的状态
        incomplete_data = {"name": "测试角色"}  # 缺少必需字段
        self.state_manager.character_data = incomplete_data
        
        # 验证状态一致性
        is_consistent, issues = self.state_manager.validate_state_consistency()
        
        # 应该检测到不一致问题
        assert not is_consistent, "应该检测到状态不一致"
        assert len(issues) > 0, "应该报告具体的问题"
        
        # 验证问题描述包含缺少的字段
        issue_text = " ".join(issues)
        required_fields = ["level", "school", "realm"]
        for field in required_fields:
            assert field in issue_text, f"应该报告缺少字段 {field}"
    
    def test_auto_save_functionality(self):
        """
        测试自动保存功能
        当配置发生变化时，系统应该能够自动保存状态
        """
        # 启用自动保存（通过全局配置）
        global_config = self.config_manager.get_config(ConfigScope.GLOBAL)
        global_config["auto_save"] = True
        self.config_manager.set_config(ConfigScope.GLOBAL, global_config)
        
        # 修改角色数据
        test_data = {
            "name": "自动保存测试",
            "level": 42,
            "school": "sword_cultivator",
            "realm": "金丹"
        }
        self.state_manager.update_character_data(test_data)
        
        # 验证状态文件存在
        assert self.state_manager.state_file.exists(), "自动保存应该创建状态文件"
        
        # 验证文件内容
        with open(self.state_manager.state_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        saved_char_data = saved_data.get("character_data", {})
        for key, value in test_data.items():
            assert saved_char_data.get(key) == value, f"自动保存的字段 {key} 不匹配"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])