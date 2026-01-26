# -*- coding: utf-8 -*-
"""
增强数据持久化功能测试
测试新增的自动保存、配置快照、冲突解决等功能
"""

import pytest
import tempfile
import shutil
import os
import json
from unified_state_manager import UnifiedStateManager
from config_manager import ConfigManager, ConfigScope


class TestEnhancedPersistence:
    """增强数据持久化功能测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.state_manager = UnifiedStateManager(config_dir=self.temp_dir)
        self.config_manager = ConfigManager(config_root=self.temp_dir)
    
    def teardown_method(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_auto_save_functionality(self):
        """测试自动保存功能"""
        # 启用自动保存
        self.state_manager.enable_auto_save(interval_seconds=10)
        assert hasattr(self.state_manager, '_auto_save_enabled')
        assert self.state_manager._auto_save_enabled == True
        assert self.state_manager._auto_save_interval == 10
        
        # 禁用自动保存
        self.state_manager.disable_auto_save()
        assert self.state_manager._auto_save_enabled == False
    
    def test_configuration_snapshot(self):
        """测试配置快照功能"""
        # 设置一些测试数据
        test_character_data = {
            "name": "快照测试角色",
            "level": 25,
            "school": "sword_cultivator",
            "realm": "筑基"
        }
        self.state_manager.update_character_data(test_character_data)
        
        # 创建配置快照
        snapshot_success = self.state_manager.create_configuration_snapshot("test_snapshot")
        assert snapshot_success, "创建配置快照应该成功"
        
        # 验证快照文件存在
        snapshot_dir = self.state_manager.config_dir / "snapshots"
        assert snapshot_dir.exists(), "快照目录应该存在"
        
        snapshot_files = list(snapshot_dir.glob("test_snapshot_*.json"))
        assert len(snapshot_files) > 0, "应该存在快照文件"
        
        # 修改当前配置
        modified_data = {"name": "修改后的角色", "level": 50}
        self.state_manager.update_character_data(modified_data)
        
        # 恢复快照
        snapshot_file = snapshot_files[0]
        restore_success = self.state_manager.restore_configuration_snapshot(str(snapshot_file))
        assert restore_success, "恢复配置快照应该成功"
        
        # 验证配置已恢复
        restored_data = self.state_manager.character_data
        assert restored_data["name"] == "快照测试角色", "角色名称应该恢复"
        assert restored_data["level"] == 25, "角色等级应该恢复"
    
    def test_import_validation_and_conflict_resolution(self):
        """测试导入验证和冲突解决功能"""
        # 设置初始配置
        initial_config = {
            "name": "原始角色",
            "school": "sword_cultivator",
            "realm": "炼气",
            "level": 10
        }
        self.state_manager.update_character_data(initial_config)
        
        # 创建冲突的导入文件
        conflicting_config = {
            "character": {
                "name": "导入角色",  # 冲突
                "school": "spell_cultivator",  # 冲突
                "realm": "筑基",  # 冲突
                "level": 20,  # 冲突
                "new_field": "新字段"  # 新增字段
            }
        }
        
        import_file = os.path.join(self.temp_dir, "conflicting_import.json")
        with open(import_file, 'w', encoding='utf-8') as f:
            json.dump(conflicting_config, f, ensure_ascii=False, indent=2)
        
        # 导入配置（应该触发冲突解决）
        import_success = self.state_manager.import_configuration(import_file)
        assert import_success, "导入配置应该成功"
        
        # 验证冲突解决结果
        imported_data = self.state_manager.character_data
        assert imported_data["name"] == "导入角色", "应该使用导入的角色名称"
        assert imported_data["school"] == "spell_cultivator", "应该使用导入的流派"
        assert "new_field" in imported_data, "应该包含新增字段"
    
    def test_config_manager_conflict_detection(self):
        """测试配置管理器的冲突检测功能"""
        # 设置基础配置
        base_config = {
            "name": "基础角色",
            "school": "sword_cultivator",
            "level": 15
        }
        self.config_manager.set_config(ConfigScope.CHARACTER, base_config, "test_character")
        
        # 创建冲突配置的导出文件
        conflicting_export = {
            "metadata": {
                "export_time": "2024-01-01T00:00:00",
                "scope": "character",
                "name": "test_character",
                "version": "1.0"
            },
            "config": {
                "name": "冲突角色",  # 冲突
                "school": "spell_cultivator",  # 冲突
                "level": 25,  # 冲突
                "new_attribute": "新属性"  # 新字段
            }
        }
        
        export_file = os.path.join(self.temp_dir, "conflicting_export.json")
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(conflicting_export, f, ensure_ascii=False, indent=2)
        
        # 导入冲突配置
        import_success = self.config_manager.import_config(export_file, ConfigScope.CHARACTER, "test_character")
        assert import_success, "导入冲突配置应该成功"
        
        # 验证冲突解决
        resolved_config = self.config_manager.get_config(ConfigScope.CHARACTER, "test_character")
        assert resolved_config["name"] == "冲突角色", "应该使用导入的名称"
        assert resolved_config["school"] == "spell_cultivator", "应该使用导入的流派"
        assert "new_attribute" in resolved_config, "应该包含新属性"
        assert "_conflict_resolution" in resolved_config, "应该包含冲突解决元数据"
    
    def test_config_validation_and_repair(self):
        """测试配置验证和修复功能"""
        # 创建不完整的配置
        incomplete_config = {
            "name": "不完整角色"
            # 缺少 school, realm, level 等必需字段
        }
        self.config_manager.set_config(ConfigScope.CHARACTER, incomplete_config, "incomplete_character")
        
        # 验证所有配置
        validation_results = self.config_manager.validate_all_configs()
        assert validation_results["total_configs"] > 0, "应该有配置需要验证"
        assert validation_results["invalid_configs"] > 0, "应该检测到无效配置"
        
        # 修复损坏的配置
        repair_results = self.config_manager.repair_corrupted_configs()
        assert repair_results["repaired_configs"] > 0, "应该修复了一些配置"
        
        # 验证修复后的配置
        repaired_config = self.config_manager.get_config(ConfigScope.CHARACTER, "incomplete_character")
        assert "school" in repaired_config, "应该添加了缺失的流派字段"
        assert "realm" in repaired_config, "应该添加了缺失的境界字段"
        assert "level" in repaired_config, "应该添加了缺失的等级字段"
    
    def test_backup_cleanup(self):
        """测试备份清理功能"""
        # 创建多个备份文件来测试清理功能
        backup_dir = self.state_manager.backup_dir
        
        # 创建15个模拟备份文件
        for i in range(15):
            backup_file = backup_dir / f"state_backup_2024010{i:02d}_120000.json"
            backup_file.write_text('{"test": "backup"}')
        
        # 验证创建了15个备份文件
        backup_files_before = list(backup_dir.glob("state_backup_*.json"))
        assert len(backup_files_before) == 15, "应该有15个备份文件"
        
        # 触发备份清理（通过保存状态）
        self.state_manager.save_state()
        
        # 验证只保留了最近10个备份
        backup_files_after = list(backup_dir.glob("state_backup_*.json"))
        assert len(backup_files_after) <= 11, "应该只保留最近10个备份文件（加上新创建的1个）"
    
    def test_enhanced_export_import_with_metadata(self):
        """测试增强的导出导入功能（包含元数据）"""
        # 设置测试数据
        test_data = {
            "name": "元数据测试角色",
            "school": "formation_cultivator",
            "realm": "金丹",
            "level": 35,
            "custom_field": "自定义数据"
        }
        self.state_manager.update_character_data(test_data)
        
        # 导出配置
        export_file = os.path.join(self.temp_dir, "metadata_export.json")
        export_success = self.state_manager.export_configuration(export_file, "json")
        assert export_success, "导出配置应该成功"
        
        # 验证导出文件包含元数据
        with open(export_file, 'r', encoding='utf-8') as f:
            export_data = json.load(f)
        
        assert "export_timestamp" in export_data, "应该包含导出时间戳"
        assert "export_version" in export_data, "应该包含导出版本"
        assert "character" in export_data, "应该包含角色数据"
        
        # 清空当前数据
        self.state_manager.character_data = {}
        
        # 导入配置
        import_success = self.state_manager.import_configuration(export_file)
        assert import_success, "导入配置应该成功"
        
        # 验证导入的数据
        imported_data = self.state_manager.character_data
        assert imported_data["name"] == "元数据测试角色", "角色名称应该匹配"
        assert imported_data["school"] == "formation_cultivator", "流派应该匹配"
        assert imported_data["custom_field"] == "自定义数据", "自定义字段应该匹配"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])