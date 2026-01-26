# -*- coding: utf-8 -*-
"""
统一配置管理系统
负责系统配置的加载、验证、保存和版本管理
"""

import json
import yaml
import os
import shutil
import math
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field
import datetime
from enum import Enum
from app_config import get_app_config


class ConfigFormat(Enum):
    """配置文件格式"""
    JSON = "json"
    YAML = "yaml"


class ConfigScope(Enum):
    """配置作用域"""
    GLOBAL = "global"          # 全局配置
    CHARACTER = "character"    # 角色配置
    SESSION = "session"        # 会话配置
    MODULE = "module"          # 模块配置


@dataclass
class ConfigSchema:
    """配置模式定义"""
    name: str
    version: str
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)
    field_types: Dict[str, type] = field(default_factory=dict)
    validation_rules: Dict[str, Any] = field(default_factory=dict)


class ConfigManager:
    """统一配置管理器"""
    
    def __init__(self, config_root: Optional[str] = None):
        if config_root is None:
            config_root = get_app_config().config_root
        self.config_root = Path(config_root)
        self.config_root.mkdir(parents=True, exist_ok=True)
        
        # 配置文件路径
        self.global_config_path = self.config_root / "global_config.yaml"
        self.character_config_dir = self.config_root / "characters"
        self.module_config_dir = self.config_root / "modules"
        self.backup_dir = self.config_root / "backups"
        
        # 创建必要目录
        self.character_config_dir.mkdir(exist_ok=True)
        self.module_config_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        
        # 配置缓存
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        
        # 配置模式定义
        self._schemas: Dict[str, ConfigSchema] = {}
        
        # 初始化默认模式
        self._initialize_default_schemas()
        
        # 加载全局配置
        self._load_global_config()
    
    def _initialize_default_schemas(self) -> None:
        """初始化默认配置模式"""
        # 全局配置模式
        self._schemas["global"] = ConfigSchema(
            name="global",
            version="1.0",
            required_fields=["system_version", "default_language"],
            optional_fields=["ui_theme", "auto_save", "backup_count"],
            field_types={
                "system_version": str,
                "default_language": str,
                "ui_theme": str,
                "auto_save": bool,
                "backup_count": int
            }
        )
        
        # 角色配置模式
        self._schemas["character"] = ConfigSchema(
            name="character",
            version="1.0",
            required_fields=["name", "school", "realm"],
            optional_fields=["level", "attributes", "bagua_config", "preferences"],
            field_types={
                "name": str,
                "school": str,
                "realm": str,
                "level": int,
                "attributes": dict,
                "bagua_config": dict,
                "preferences": dict
            }
        )
        
        # 五行模块配置模式
        self._schemas["five_elements"] = ConfigSchema(
            name="five_elements",
            version="1.0",
            required_fields=["enabled"],
            optional_fields=["stone_library", "calculation_mode", "visual_effects"],
            field_types={
                "enabled": bool,
                "stone_library": dict,
                "calculation_mode": str,
                "visual_effects": bool
            }
        )
        
        # 战斗模块配置模式
        self._schemas["combat"] = ConfigSchema(
            name="combat",
            version="1.0",
            required_fields=["enabled"],
            optional_fields=["simulation_params", "skill_chains", "enemy_presets"],
            field_types={
                "enabled": bool,
                "simulation_params": dict,
                "skill_chains": list,
                "enemy_presets": dict
            }
        )
    
    def _load_global_config(self) -> None:
        """加载全局配置"""
        if self.global_config_path.exists():
            try:
                with open(self.global_config_path, 'r', encoding='utf-8') as f:
                    global_config = yaml.safe_load(f)
                self._config_cache["global"] = global_config or {}
            except Exception as e:
                print(f"加载全局配置失败: {e}")
                self._config_cache["global"] = self._get_default_global_config()
        else:
            self._config_cache["global"] = self._get_default_global_config()
            self._save_global_config()
    
    def _get_default_global_config(self) -> Dict[str, Any]:
        """获取默认全局配置"""
        return {
            "system_version": "1.0.0",
            "default_language": "zh_CN",
            "ui_theme": "light",
            "auto_save": True,
            "backup_count": 10,
            "modules": {
                "five_elements": {"enabled": True},
                "combat": {"enabled": True},
                "character": {"enabled": True},
                "loot": {"enabled": True},
                "ui": {"enabled": True}
            },
            "paths": {
                "data_file": "data.yaml",
                "backup_dir": "backup",
                "export_dir": "exports"
            },
            "performance": {
                "max_simulation_time": 30.0,
                "cache_size": 1000,
                "auto_cleanup": True
            }
        }
    
    def _save_global_config(self) -> bool:
        """保存全局配置"""
        try:
            with open(self.global_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config_cache["global"], f, 
                         allow_unicode=True, default_flow_style=False)
            return True
        except Exception as e:
            print(f"保存全局配置失败: {e}")
            return False
    
    def get_config(self, scope: ConfigScope, name: str = "default") -> Dict[str, Any]:
        """获取配置"""
        cache_key = f"{scope.value}_{name}"
        
        if cache_key in self._config_cache:
            return self._config_cache[cache_key].copy()
        
        # 从文件加载配置
        config_data = self._load_config_from_file(scope, name)
        if config_data:
            self._config_cache[cache_key] = config_data
            return config_data.copy()
        
        # 返回默认配置
        return self._get_default_config(scope, name)
    
    def _load_config_from_file(self, scope: ConfigScope, name: str) -> Optional[Dict[str, Any]]:
        """从文件加载配置"""
        try:
            if scope == ConfigScope.GLOBAL:
                return self._config_cache.get("global", {})
            
            elif scope == ConfigScope.CHARACTER:
                config_file = self.character_config_dir / f"{name}.yaml"
                if config_file.exists():
                    with open(config_file, 'r', encoding='utf-8') as f:
                        return yaml.safe_load(f)
            
            elif scope == ConfigScope.MODULE:
                config_file = self.module_config_dir / f"{name}.yaml"
                if config_file.exists():
                    with open(config_file, 'r', encoding='utf-8') as f:
                        return yaml.safe_load(f)
            
            return None
            
        except Exception as e:
            print(f"加载配置文件失败 ({scope.value}/{name}): {e}")
            return None
    
    def _get_default_config(self, scope: ConfigScope, name: str) -> Dict[str, Any]:
        """获取默认配置"""
        if scope == ConfigScope.GLOBAL:
            return self._get_default_global_config()
        
        elif scope == ConfigScope.CHARACTER:
            return {
                "name": name,
                "school": "sword_cultivator",
                "realm": "炼气",
                "level": 1,
                "attributes": {
                    "str": 25,
                    "agi": 25,
                    "int": 25
                },
                "bagua_config": {
                    "stones": {},
                    "core": {},
                    "seed": 184023
                },
                "preferences": {
                    "auto_calculate": True,
                    "show_details": True
                }
            }
        
        elif scope == ConfigScope.MODULE:
            if name == "five_elements":
                return {
                    "enabled": True,
                    "stone_library": {},
                    "calculation_mode": "standard",
                    "visual_effects": True
                }
            elif name == "combat":
                return {
                    "enabled": True,
                    "simulation_params": {
                        "max_time": 20.0,
                        "dt": 0.1
                    },
                    "skill_chains": [],
                    "enemy_presets": {}
                }
        
        return {}
    
    def set_config(self, scope: ConfigScope, config_data: Dict[str, Any], 
                  name: str = "default") -> bool:
        """设置配置"""
        try:
            # 规范化配置数据（处理NaN/控制字符等不可序列化值）
            sanitized = self._sanitize_config_data(config_data)
            if isinstance(config_data, dict) and isinstance(sanitized, dict):
                config_data.clear()
                config_data.update(sanitized)
            else:
                config_data = sanitized

            # 验证配置数据
            if not self._validate_config(scope, config_data, name, strict=False):
                return False
            
            # 更新缓存
            cache_key = f"{scope.value}_{name}"
            self._config_cache[cache_key] = config_data.copy()
            
            # 保存到文件
            return self._save_config_to_file(scope, config_data, name)
            
        except Exception as e:
            print(f"设置配置失败 ({scope.value}/{name}): {e}")
            return False
    
    def _save_config_to_file(self, scope: ConfigScope, config_data: Dict[str, Any], 
                           name: str) -> bool:
        """保存配置到文件"""
        try:
            if scope == ConfigScope.GLOBAL:
                self._config_cache["global"] = config_data
                return self._save_global_config()
            
            elif scope == ConfigScope.CHARACTER:
                config_file = self.character_config_dir / f"{name}.yaml"
                with open(config_file, 'w', encoding='utf-8') as f:
                    yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False)
                return True
            
            elif scope == ConfigScope.MODULE:
                config_file = self.module_config_dir / f"{name}.yaml"
                with open(config_file, 'w', encoding='utf-8') as f:
                    yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False)
                return True
            
            return False
            
        except Exception as e:
            print(f"保存配置文件失败 ({scope.value}/{name}): {e}")
            return False
    
    def _validate_config(self, scope: ConfigScope, config_data: Dict[str, Any], 
                        name: str, strict: bool = True) -> bool:
        """验证配置数据"""
        try:
            # 获取对应的配置模式
            schema_name = scope.value if scope != ConfigScope.MODULE else name
            schema = self._schemas.get(schema_name)
            
            if not schema:
                return True  # 没有模式定义时跳过验证
            
            if strict:
                # 检查必需字段
                for field in schema.required_fields:
                    if field not in config_data:
                        print(f"配置验证失败: 缺少必需字段 '{field}'")
                        return False
            
            # 检查字段类型
            for field, expected_type in schema.field_types.items():
                if field in config_data:
                    if not isinstance(config_data[field], expected_type):
                        print(f"配置验证失败: 字段 '{field}' 类型错误")
                        return False
            
            return True
            
        except Exception as e:
            print(f"配置验证异常: {e}")
            return False
    
    def update_config(self, scope: ConfigScope, updates: Dict[str, Any], 
                     name: str = "default") -> bool:
        """更新配置（部分更新）"""
        current_config = self.get_config(scope, name)
        current_config.update(updates)
        return self.set_config(scope, current_config, name)
    
    def delete_config(self, scope: ConfigScope, name: str) -> bool:
        """删除配置"""
        try:
            # 从缓存中删除
            cache_key = f"{scope.value}_{name}"
            if cache_key in self._config_cache:
                del self._config_cache[cache_key]
            
            # 删除文件
            if scope == ConfigScope.CHARACTER:
                config_file = self.character_config_dir / f"{name}.yaml"
                if config_file.exists():
                    config_file.unlink()
            
            elif scope == ConfigScope.MODULE:
                config_file = self.module_config_dir / f"{name}.yaml"
                if config_file.exists():
                    config_file.unlink()
            
            return True
            
        except Exception as e:
            print(f"删除配置失败 ({scope.value}/{name}): {e}")
            return False
    
    def list_configs(self, scope: ConfigScope) -> List[str]:
        """列出指定作用域的所有配置"""
        configs = []
        
        try:
            if scope == ConfigScope.CHARACTER:
                for config_file in self.character_config_dir.glob("*.yaml"):
                    configs.append(config_file.stem)
            
            elif scope == ConfigScope.MODULE:
                for config_file in self.module_config_dir.glob("*.yaml"):
                    configs.append(config_file.stem)
            
            elif scope == ConfigScope.GLOBAL:
                configs.append("global")
            
        except Exception as e:
            print(f"列出配置失败 ({scope.value}): {e}")
        
        return configs
    
    def export_config(self, scope: ConfigScope, name: str, 
                     export_path: str, format: ConfigFormat = ConfigFormat.YAML) -> bool:
        """导出配置"""
        try:
            config_data = self.get_config(scope, name)
            
            # 添加导出元数据
            export_data = {
                "metadata": {
                    "export_time": datetime.datetime.now().isoformat(),
                    "scope": scope.value,
                    "name": name,
                    "version": "1.0"
                },
                "config": config_data
            }
            
            # 根据格式保存
            if format == ConfigFormat.JSON:
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
            else:  # YAML
                with open(export_path, 'w', encoding='utf-8') as f:
                    yaml.dump(export_data, f, allow_unicode=True, default_flow_style=False)
            
            return True
            
        except Exception as e:
            print(f"导出配置失败: {e}")
            return False
    
    def import_config(self, import_path: str, scope: ConfigScope, 
                     name: str = None) -> bool:
        """导入配置"""
        try:
            if not os.path.exists(import_path):
                print(f"导入文件不存在: {import_path}")
                return False
            
            # 根据文件扩展名判断格式
            if import_path.endswith('.json'):
                with open(import_path, 'r', encoding='utf-8') as f:
                    import_data = json.load(f)
            else:  # 默认YAML
                with open(import_path, 'r', encoding='utf-8') as f:
                    import_data = yaml.safe_load(f)
            
            # 提取配置数据
            if "config" in import_data:
                config_data = import_data["config"]
                metadata = import_data.get("metadata", {})
                
                # 使用元数据中的名称（如果没有指定）
                if name is None:
                    name = metadata.get("name", "imported")
            else:
                config_data = import_data
                if name is None:
                    name = "imported"
            
            # 规范化配置数据
            config_data = self._sanitize_config_data(config_data)

            # 验证配置数据（导入允许缺字段，修复/校验由后续流程处理）
            if not self._validate_config(scope, config_data, name, strict=False):
                print("导入的配置数据验证失败")
                return False
            
            # 检测配置冲突
            existing_config = self.get_config(scope, name)
            conflicts = self._detect_config_conflicts(existing_config, config_data)
            
            if conflicts:
                # 应用冲突解决策略
                resolved_config = self._resolve_config_conflicts(existing_config, config_data, conflicts)
                config_data = resolved_config
            
            # 设置配置
            return self.set_config(scope, config_data, name)
            
        except Exception as e:
            print(f"导入配置失败: {e}")
            return False
    
    def backup_config(self, scope: ConfigScope, name: str = "default") -> bool:
        """备份配置"""
        try:
            config_data = self.get_config(scope, name)
            
            # 清理同名备份，避免读取时选到旧文件
            for existing in self.backup_dir.glob(f"{scope.value}_{name}_*.yaml"):
                existing.unlink()

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{scope.value}_{name}_{timestamp}.yaml"
            backup_path = self.backup_dir / backup_filename
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False)
            
            # 清理旧备份
            self._cleanup_old_backups()
            
            return True
            
        except Exception as e:
            print(f"备份配置失败: {e}")
            return False
    
    def _cleanup_old_backups(self) -> None:
        """清理旧备份文件"""
        try:
            backup_count = self._config_cache.get("global", {}).get("backup_count", 10)
            backup_files = list(self.backup_dir.glob("*.yaml"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # 删除超出数量的备份
            for backup_file in backup_files[backup_count:]:
                backup_file.unlink()
                
        except Exception as e:
            print(f"清理备份失败: {e}")
    
    def get_config_status(self) -> Dict[str, Any]:
        """获取配置系统状态"""
        return {
            "config_root": str(self.config_root),
            "global_config_exists": self.global_config_path.exists(),
            "character_configs": len(self.list_configs(ConfigScope.CHARACTER)),
            "module_configs": len(self.list_configs(ConfigScope.MODULE)),
            "cached_configs": len(self._config_cache),
            "backup_files": len(list(self.backup_dir.glob("*.yaml"))),
            "schemas_loaded": len(self._schemas)
        }
    
    def _detect_config_conflicts(self, existing_config: Dict[str, Any], 
                                new_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检测配置冲突"""
        conflicts = []
        
        # 检查共同字段的值差异
        common_fields = set(existing_config.keys()) & set(new_config.keys())
        
        for field in common_fields:
            existing_value = existing_config[field]
            new_value = new_config[field]
            
            if existing_value != new_value:
                conflicts.append({
                    "field": field,
                    "existing_value": existing_value,
                    "new_value": new_value,
                    "conflict_type": "value_difference",
                    "severity": self._assess_conflict_severity(field, existing_value, new_value)
                })
        
        # 检查新增字段
        new_fields = set(new_config.keys()) - set(existing_config.keys())
        for field in new_fields:
            conflicts.append({
                "field": field,
                "existing_value": None,
                "new_value": new_config[field],
                "conflict_type": "new_field",
                "severity": "low"
            })
        
        return conflicts
    
    def _resolve_config_conflicts(self, existing_config: Dict[str, Any], 
                                 new_config: Dict[str, Any], 
                                 conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """解决配置冲突"""
        resolved_config = existing_config.copy()
        
        for conflict in conflicts:
            field = conflict["field"]
            severity = conflict["severity"]
            
            # 冲突解决策略
            if severity == "low" or conflict["conflict_type"] == "new_field":
                # 低严重性冲突或新字段：使用新值
                resolved_config[field] = conflict["new_value"]
            elif severity == "medium":
                # 中等严重性冲突：优先使用新值，但记录警告
                resolved_config[field] = conflict["new_value"]
                print(f"配置冲突警告: 字段 '{field}' 从 {conflict['existing_value']} 更改为 {conflict['new_value']}")
            elif severity == "high":
                # 高严重性冲突：优先使用新值，但记录错误
                resolved_config[field] = conflict["new_value"]
                print(f"配置冲突错误: 字段 '{field}' 冲突严重，使用新值 {conflict['new_value']}")
        
        # 添加冲突解决元数据
        resolved_config["_conflict_resolution"] = {
            "timestamp": datetime.datetime.now().isoformat(),
            "conflicts_count": len(conflicts),
            "resolution_strategy": "prefer_new_with_severity_check"
        }
        
        return resolved_config
    
    def _assess_conflict_severity(self, field: str, existing_value: Any, new_value: Any) -> str:
        """评估配置冲突的严重性"""
        # 关键字段的冲突被认为是高严重性
        critical_fields = ["name", "school", "realm", "level"]
        if field in critical_fields:
            return "high"
        
        # 类型不匹配被认为是中等严重性
        if type(existing_value) != type(new_value):
            return "medium"
        
        # 数值差异较大被认为是中等严重性
        if isinstance(existing_value, (int, float)) and isinstance(new_value, (int, float)):
            if abs(existing_value - new_value) > abs(existing_value) * 0.5:  # 差异超过50%
                return "medium"
        
        # 其他情况被认为是低严重性
        return "low"
    
    def validate_all_configs(self) -> Dict[str, Any]:
        """验证所有配置的完整性"""
        validation_results = {
            "total_configs": 0,
            "valid_configs": 0,
            "invalid_configs": 0,
            "validation_errors": []
        }
        
        # 验证角色配置
        character_configs = self.list_configs(ConfigScope.CHARACTER)
        for config_name in character_configs:
            validation_results["total_configs"] += 1
            config_data = self.get_config(ConfigScope.CHARACTER, config_name)
            
            if self._validate_config(ConfigScope.CHARACTER, config_data, config_name, strict=True):
                validation_results["valid_configs"] += 1
            else:
                validation_results["invalid_configs"] += 1
                validation_results["validation_errors"].append({
                    "scope": "character",
                    "name": config_name,
                    "error": "配置验证失败"
                })
        
        # 验证模块配置
        module_configs = self.list_configs(ConfigScope.MODULE)
        for config_name in module_configs:
            validation_results["total_configs"] += 1
            config_data = self.get_config(ConfigScope.MODULE, config_name)
            
            if self._validate_config(ConfigScope.MODULE, config_data, config_name, strict=True):
                validation_results["valid_configs"] += 1
            else:
                validation_results["invalid_configs"] += 1
                validation_results["validation_errors"].append({
                    "scope": "module",
                    "name": config_name,
                    "error": "配置验证失败"
                })
        
        return validation_results

    def _sanitize_config_data(self, data: Any) -> Any:
        """清理不可序列化或不稳定的数据（如NaN、控制字符键）"""
        if isinstance(data, float) and math.isnan(data):
            return None
        
        if isinstance(data, dict):
            cleaned = {}
            for key, value in data.items():
                cleaned_key = self._sanitize_config_key(key)
                cleaned[cleaned_key] = self._sanitize_config_data(value)
            return cleaned
        
        if isinstance(data, list):
            return [self._sanitize_config_data(item) for item in data]
        
        return data

    def _sanitize_config_key(self, key: Any) -> Any:
        """清理配置键中的控制字符，避免序列化/反序列化丢失"""
        if isinstance(key, str):
            if any(ord(ch) < 32 or ch in ("\x7f", "\x85") for ch in key):
                return key.encode("unicode_escape").decode("ascii")
        return key
    
    def repair_corrupted_configs(self) -> Dict[str, Any]:
        """修复损坏的配置文件"""
        repair_results = {
            "repaired_configs": 0,
            "failed_repairs": 0,
            "repair_log": []
        }
        
        # 检查并修复角色配置
        character_configs = self.list_configs(ConfigScope.CHARACTER)
        for config_name in character_configs:
            try:
                config_data = self.get_config(ConfigScope.CHARACTER, config_name)
                
                # 尝试修复缺失的必需字段
                repaired = False
                if "name" not in config_data:
                    config_data["name"] = config_name
                    repaired = True
                
                if "school" not in config_data:
                    config_data["school"] = "sword_cultivator"  # 默认流派
                    repaired = True
                
                if "realm" not in config_data:
                    config_data["realm"] = "炼气"  # 默认境界
                    repaired = True
                
                if "level" not in config_data:
                    config_data["level"] = 1  # 默认等级
                    repaired = True
                
                if repaired:
                    self.set_config(ConfigScope.CHARACTER, config_data, config_name)
                    repair_results["repaired_configs"] += 1
                    repair_results["repair_log"].append({
                        "scope": "character",
                        "name": config_name,
                        "action": "添加缺失的必需字段"
                    })
                
            except Exception as e:
                repair_results["failed_repairs"] += 1
                repair_results["repair_log"].append({
                    "scope": "character",
                    "name": config_name,
                    "action": "修复失败",
                    "error": str(e)
                })
        
        return repair_results


# 全局配置管理器实例
_global_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager()
    return _global_config_manager


def initialize_config_system(config_root: Optional[str] = None) -> ConfigManager:
    """初始化配置系统"""
    global _global_config_manager
    _global_config_manager = ConfigManager(config_root)
    return _global_config_manager
