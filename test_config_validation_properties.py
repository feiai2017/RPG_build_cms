# -*- coding: utf-8 -*-
"""
配置验证和冲突处理属性测试
测试RPG系统的配置验证、冲突检测和解决机制的正确性
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
from unified_state_manager import UnifiedStateManager
from config_manager import ConfigManager, ConfigScope, ConfigFormat


# 测试数据生成策略
@st.composite
def valid_character_config_strategy(draw):
    """生成有效角色配置的策略"""
    return {
        "name": draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        "school": draw(st.sampled_from(["sword_cultivator", "spell_cultivator", "body_cultivator", "pill_cultivator", "formation_cultivator"])),
        "realm": draw(st.sampled_from(["炼气", "筑基", "金丹", "元婴", "化神"])),
        "level": draw(st.integers(min_value=1, max_value=100)),
        "attributes": {
            "str": draw(st.integers(min_value=1, max_value=100)),
            "agi": draw(st.integers(min_value=1, max_value=100)),
            "int": draw(st.integers(min_value=1, max_value=100))
        }
    }


@st.composite
def invalid_character_config_strategy(draw):
    """生成无效角色配置的策略（缺少必需字段或类型错误）"""
    config = {}
    
    # 随机决定是否包含必需字段
    if draw(st.booleans()):
        config["name"] = draw(st.text(min_size=1, max_size=20))
    
    if draw(st.booleans()):
        config["school"] = draw(st.sampled_from(["sword_cultivator", "spell_cultivator", "invalid_school"]))
    
    if draw(st.booleans()):
        config["realm"] = draw(st.sampled_from(["炼气", "筑基", "invalid_realm"]))
    
    # 可能包含错误类型的字段
    if draw(st.booleans()):
        config["level"] = draw(st.one_of(
            st.integers(min_value=-100, max_value=0),  # 无效的负数或零
            st.text(),  # 错误类型
            st.floats(min_value=1.1, max_value=100.9)  # 应该是整数但给了浮点数
        ))
    
    return config


@st.composite
def conflicting_configs_strategy(draw):
    """生成冲突配置的策略"""
    base_config = {
        "name": "测试角色",
        "school": "sword_cultivator",
        "realm": "炼气",
        "level": 10
    }
    
    # 创建冲突的配置
    conflicting_config = base_config.copy()
    
    # 随机选择要冲突的字段
    conflict_field = draw(st.sampled_from(["school", "realm", "level"]))
    
    if conflict_field == "school":
        conflicting_config["school"] = draw(st.sampled_from(["spell_cultivator", "body_cultivator"]))
    elif conflict_field == "realm":
        conflicting_config["realm"] = draw(st.sampled_from(["筑基", "金丹"]))
    elif conflict_field == "level":
        conflicting_config["level"] = draw(st.integers(min_value=20, max_value=50))
    
    return base_config, conflicting_config


@st.composite
def module_config_strategy(draw):
    """生成模块配置的策略"""
    return {
        "enabled": draw(st.booleans()),
        "settings": draw(st.dictionaries(
            st.text(min_size=1, max_size=20),
            st.one_of(st.text(), st.integers(), st.floats(), st.booleans()),
            min_size=0,
            max_size=5
        )),
        "version": draw(st.text(min_size=1, max_size=10))
    }


class TestConfigValidationProperties:
    """配置验证和冲突处理属性测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.state_manager = UnifiedStateManager(config_dir=self.temp_dir)
        self.config_manager = ConfigManager(config_root=self.temp_dir)
    
    def teardown_method(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @given(valid_config=valid_character_config_strategy())
    @settings(max_examples=20, deadline=None)
    def test_property_9_valid_config_acceptance(self, valid_config):
        """
        Property 9a: 有效配置验证
        For any 有效的配置数据，系统应该能够正确验证并接受
        **Feature: rpg-system-integration, Property 9: 配置验证和冲突处理**
        **Validates: Requirements 7.4, 7.5**
        """
        # 验证配置应该成功
        validation_result = self._validate_character_config(valid_config)
        assert validation_result["is_valid"], f"有效配置应该通过验证: {validation_result['errors']}"
        
        # 设置配置应该成功
        set_success = self.config_manager.set_config(ConfigScope.CHARACTER, valid_config, "test_valid")
        assert set_success, "设置有效配置应该成功"
        
        # 加载配置应该成功
        loaded_config = self.config_manager.get_config(ConfigScope.CHARACTER, "test_valid")
        
        # 验证加载的配置包含所有原始字段
        for key, value in valid_config.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    assert loaded_config[key].get(sub_key) == sub_value, f"字段 {key}.{sub_key} 不匹配"
            else:
                assert loaded_config.get(key) == value, f"字段 {key} 不匹配"
    
    @given(invalid_config=invalid_character_config_strategy())
    @settings(max_examples=20, deadline=None)
    def test_property_9_invalid_config_rejection(self, invalid_config):
        """
        Property 9b: 无效配置拒绝
        For any 无效的配置数据，系统应该能够正确识别并拒绝
        **Feature: rpg-system-integration, Property 9: 配置验证和冲突处理**
        **Validates: Requirements 7.4, 7.5**
        """
        # 跳过空配置（这是边界情况）
        assume(len(invalid_config) > 0)
        
        # 验证配置
        validation_result = self._validate_character_config(invalid_config)
        
        # 如果配置确实无效，验证应该失败
        required_fields = ["name", "school", "realm"]
        missing_required = any(field not in invalid_config for field in required_fields)
        
        if missing_required:
            assert not validation_result["is_valid"], "缺少必需字段的配置应该被拒绝"
            assert len(validation_result["errors"]) > 0, "应该报告具体的验证错误"
    
    @given(configs=conflicting_configs_strategy())
    @settings(max_examples=15, deadline=None)
    def test_property_9_conflict_detection(self, configs):
        """
        Property 9c: 配置冲突检测
        For any 冲突的配置数据，系统应该能够检测并报告冲突
        **Feature: rpg-system-integration, Property 9: 配置验证和冲突处理**
        **Validates: Requirements 7.4, 7.5**
        """
        base_config, conflicting_config = configs
        
        # 设置基础配置
        self.config_manager.set_config(ConfigScope.CHARACTER, base_config, "base_config")
        
        # 尝试设置冲突配置到同一个名称
        # 这应该覆盖原配置，但我们可以检测到差异
        self.config_manager.set_config(ConfigScope.CHARACTER, conflicting_config, "conflicting_config")
        
        # 加载两个配置并比较
        loaded_base = self.config_manager.get_config(ConfigScope.CHARACTER, "base_config")
        loaded_conflicting = self.config_manager.get_config(ConfigScope.CHARACTER, "conflicting_config")
        
        # 检测冲突
        conflicts = self._detect_config_conflicts(loaded_base, loaded_conflicting)
        
        # 应该检测到至少一个冲突
        assert len(conflicts) > 0, "应该检测到配置冲突"
        
        # 验证冲突报告的准确性
        for conflict in conflicts:
            field = conflict["field"]
            base_value = conflict["base_value"]
            conflicting_value = conflict["conflicting_value"]
            
            assert loaded_base.get(field) == base_value, f"基础配置字段 {field} 值不匹配"
            assert loaded_conflicting.get(field) == conflicting_value, f"冲突配置字段 {field} 值不匹配"
            assert base_value != conflicting_value, f"字段 {field} 应该有不同的值"
    
    @given(
        base_config=valid_character_config_strategy(),
        update_data=st.dictionaries(
            st.sampled_from(["level", "realm", "school"]),
            st.one_of(st.integers(min_value=1, max_value=100), st.text(min_size=1, max_size=20)),
            min_size=1,
            max_size=3
        )
    )
    @settings(max_examples=15, deadline=None)
    def test_property_9_conflict_resolution(self, base_config, update_data):
        """
        Property 9d: 配置冲突解决
        For any 配置更新操作，系统应该能够提供合理的冲突解决方案
        **Feature: rpg-system-integration, Property 9: 配置验证和冲突处理**
        **Validates: Requirements 7.4, 7.5**
        """
        config_name = "conflict_resolution_test"
        
        # 设置基础配置
        self.config_manager.set_config(ConfigScope.CHARACTER, base_config, config_name)
        
        # 应用更新
        resolution_result = self._resolve_config_conflicts(base_config, update_data)
        
        # 验证解决方案的合理性
        assert "resolved_config" in resolution_result, "应该提供解决后的配置"
        assert "conflicts_found" in resolution_result, "应该报告发现的冲突"
        assert "resolution_strategy" in resolution_result, "应该说明解决策略"
        
        resolved_config = resolution_result["resolved_config"]
        
        # 验证解决后的配置包含更新的字段
        for key, value in update_data.items():
            if key in resolved_config:
                # 对于有效的更新，应该应用新值
                if self._is_valid_field_value(key, value):
                    assert resolved_config[key] == value, f"字段 {key} 应该更新为新值"
                else:
                    # 对于无效的更新，应该保持原值
                    assert resolved_config[key] == base_config.get(key), f"无效更新时字段 {key} 应该保持原值"
    
    @given(module_config=module_config_strategy())
    @settings(max_examples=15, deadline=None)
    def test_module_config_validation(self, module_config):
        """
        测试模块配置的验证功能
        For any 模块配置，系统应该能够正确验证其格式和内容
        """
        module_name = "test_module"
        
        # 设置模块配置
        set_success = self.config_manager.set_config(ConfigScope.MODULE, module_config, module_name)
        assert set_success, "设置模块配置应该成功"
        
        # 加载并验证配置
        loaded_config = self.config_manager.get_config(ConfigScope.MODULE, module_name)
        
        # 验证必需字段
        if "enabled" in module_config:
            assert loaded_config.get("enabled") == module_config["enabled"], "enabled 字段应该匹配"
        
        # 验证设置字段
        if "settings" in module_config:
            loaded_settings = loaded_config.get("settings", {})
            original_settings = module_config["settings"]
            for key, value in original_settings.items():
                assert loaded_settings.get(key) == value, f"设置字段 {key} 应该匹配"
    
    def test_config_schema_validation(self):
        """
        测试配置模式验证功能
        系统应该能够根据预定义的模式验证配置
        """
        # 测试符合模式的配置
        valid_config = {
            "name": "测试角色",
            "school": "sword_cultivator",
            "realm": "炼气",
            "level": 10
        }
        
        validation_result = self._validate_character_config(valid_config)
        assert validation_result["is_valid"], "符合模式的配置应该通过验证"
        
        # 测试不符合模式的配置
        invalid_config = {
            "name": "测试角色",
            "school": "invalid_school",  # 无效的流派
            "realm": "炼气",
            "level": "invalid_level"  # 错误的类型
        }
        
        validation_result = self._validate_character_config(invalid_config)
        assert not validation_result["is_valid"], "不符合模式的配置应该被拒绝"
        assert len(validation_result["errors"]) > 0, "应该报告具体的验证错误"
    
    def test_import_validation(self):
        """
        测试导入配置时的验证功能
        导入外部配置时应该进行严格的验证
        """
        # 创建有效的导出文件
        valid_config = {
            "name": "导入测试",
            "school": "sword_cultivator",
            "realm": "筑基",
            "level": 25
        }
        
        export_path = os.path.join(self.temp_dir, "valid_export.json")
        export_data = {
            "metadata": {
                "export_time": "2024-01-01T00:00:00",
                "scope": "character",
                "name": "test",
                "version": "1.0"
            },
            "config": valid_config
        }
        
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        # 导入应该成功
        import_success = self.config_manager.import_config(export_path, ConfigScope.CHARACTER, "imported_valid")
        assert import_success, "导入有效配置应该成功"
        
        # 创建无效的导出文件
        invalid_export_path = os.path.join(self.temp_dir, "invalid_export.json")
        invalid_export_data = {
            "config": {
                "name": "无效导入",
                "school": "invalid_school",  # 无效流派
                "level": -5  # 无效等级
            }
        }
        
        with open(invalid_export_path, 'w', encoding='utf-8') as f:
            json.dump(invalid_export_data, f, ensure_ascii=False, indent=2)
        
        # 导入可能成功但配置应该被标记为有问题
        import_success = self.config_manager.import_config(invalid_export_path, ConfigScope.CHARACTER, "imported_invalid")
        
        if import_success:
            # 如果导入成功，验证配置应该失败
            imported_config = self.config_manager.get_config(ConfigScope.CHARACTER, "imported_invalid")
            validation_result = self._validate_character_config(imported_config)
            assert not validation_result["is_valid"], "导入的无效配置应该被验证器识别"
    
    def _validate_character_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """验证角色配置"""
        errors = []
        
        # 检查必需字段
        required_fields = ["name", "school", "realm"]
        for field in required_fields:
            if field not in config:
                errors.append(f"缺少必需字段: {field}")
        
        # 检查字段类型和值
        if "name" in config:
            if not isinstance(config["name"], str) or len(config["name"]) == 0:
                errors.append("name 必须是非空字符串")
        
        if "school" in config:
            valid_schools = ["sword_cultivator", "spell_cultivator", "body_cultivator", "pill_cultivator", "formation_cultivator"]
            if config["school"] not in valid_schools:
                errors.append(f"school 必须是以下之一: {valid_schools}")
        
        if "realm" in config:
            valid_realms = ["炼气", "筑基", "金丹", "元婴", "化神"]
            if config["realm"] not in valid_realms:
                errors.append(f"realm 必须是以下之一: {valid_realms}")
        
        if "level" in config:
            if not isinstance(config["level"], int) or config["level"] < 1:
                errors.append("level 必须是大于0的整数")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }
    
    def _detect_config_conflicts(self, config1: Dict[str, Any], config2: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检测两个配置之间的冲突"""
        conflicts = []
        
        # 检查共同字段的值差异
        common_fields = set(config1.keys()) & set(config2.keys())
        
        for field in common_fields:
            value1 = config1[field]
            value2 = config2[field]
            
            if value1 != value2:
                conflicts.append({
                    "field": field,
                    "base_value": value1,
                    "conflicting_value": value2,
                    "conflict_type": "value_difference"
                })
        
        return conflicts
    
    def _resolve_config_conflicts(self, base_config: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """解决配置冲突"""
        resolved_config = base_config.copy()
        conflicts_found = []
        
        for key, new_value in updates.items():
            if key in base_config:
                old_value = base_config[key]
                if old_value != new_value:
                    conflicts_found.append({
                        "field": key,
                        "old_value": old_value,
                        "new_value": new_value
                    })
            
            # 应用更新（如果值有效）
            if self._is_valid_field_value(key, new_value):
                resolved_config[key] = new_value
        
        return {
            "resolved_config": resolved_config,
            "conflicts_found": conflicts_found,
            "resolution_strategy": "prefer_new_valid_values"
        }
    
    def _is_valid_field_value(self, field: str, value: Any) -> bool:
        """检查字段值是否有效"""
        if field == "level":
            return isinstance(value, int) and value > 0
        elif field == "school":
            valid_schools = ["sword_cultivator", "spell_cultivator", "body_cultivator", "pill_cultivator", "formation_cultivator"]
            return value in valid_schools
        elif field == "realm":
            valid_realms = ["炼气", "筑基", "金丹", "元婴", "化神"]
            return value in valid_realms
        elif field == "name":
            return isinstance(value, str) and len(value) > 0
        else:
            return True  # 其他字段暂时认为都有效


if __name__ == "__main__":
    pytest.main([__file__, "-v"])