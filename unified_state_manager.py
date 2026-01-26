# -*- coding: utf-8 -*-
"""
统一状态管理器 (UnifiedStateManager)
整合RPG系统的核心状态管理，实现模块间数据同步和统一配置管理
"""

import json
import yaml
import copy
import os
import datetime
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from pathlib import Path
from cultivation_school_system import get_school_manager, SchoolManager
from app_config import get_app_config


@dataclass
class UnifiedCharacter:
    """统一角色数据模型"""
    # 基础信息
    name: str
    level: int
    school: str
    realm: str
    
    # 属性
    base_attributes: Dict[str, float] = field(default_factory=dict)
    derived_attributes: Dict[str, float] = field(default_factory=dict)
    
    # 五行八卦配置
    bagua_stones: Dict[str, Dict[int, Optional[str]]] = field(default_factory=dict)
    core_bios: Dict[int, Optional[str]] = field(default_factory=dict)
    
    # 装备和物品
    equipment: Dict[str, Optional[str]] = field(default_factory=dict)
    inventory: List[str] = field(default_factory=list)
    
    # 进度数据
    unlocked_skills: List[str] = field(default_factory=list)
    completed_challenges: List[str] = field(default_factory=list)
    cultivation_progress: Dict[str, float] = field(default_factory=dict)


class UnifiedStateManager:
    """统一状态管理器 - 负责所有模块的数据同步和状态管理"""
    
    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            config_dir = get_app_config().config_root
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化流派管理器
        self.school_manager = get_school_manager()
        
        # 核心状态数据
        self.character_data: Dict[str, Any] = {}
        self.bagua_configuration: Dict[str, Any] = {}
        self.combat_settings: Dict[str, Any] = {}
        self.loot_inventory: List[Dict[str, Any]] = []
        
        # 模块同步状态
        self._module_states: Dict[str, Dict[str, Any]] = {
            "five_elements": {},
            "combat": {},
            "character": {},
            "loot": {},
            "ui": {}
        }
        
        # 配置文件路径
        self.state_file = self.config_dir / "unified_state.json"
        self.backup_dir = self.config_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # 自动保存设置
        self._auto_save_enabled = False
        self._auto_save_interval = 30
        
        # 初始化默认状态
        self._initialize_default_state()
    
    def _initialize_default_state(self) -> None:
        """初始化默认状态"""
        if not self.character_data:
            self.character_data = {
                "name": "李长风",
                "level": 1,
                "school": "sword_cultivator",
                "realm": "炼气",
                "base_attributes": {
                    "str": 25,
                    "agi": 25,
                    "int": 25,
                    "max_hp": 500,
                    "base_atk": 40,
                    "crit_rate": 0.05,
                    "crit_dmg": 1.7
                },
                "derived_attributes": {},
                "affinity_main": "木"
            }
        
        if not self.bagua_configuration:
            self.bagua_configuration = {
                "stones": {tri: {i: None for i in range(1, 5)} for tri in 
                          ["QIAN", "DUI", "LI", "ZHEN", "XUN", "KAN", "GEN", "KUN"]},
                "core": {i: None for i in range(1, 4)},
                "seed": 184023
            }
        
        if not self.combat_settings:
            self.combat_settings = {
                "selected_skills": [],
                "skill_chain": {"main_skill": None, "main_mods": [], "triggers": []},
                "simulation_params": {
                    "enemy_hp": 3000,
                    "enemy_dps": 20,
                    "max_time": 20.0
                }
            }
    
    def sync_modules(self) -> None:
        """同步所有模块的数据状态"""
        # 同步角色数据到五行模块
        self._sync_to_five_elements()
        
        # 同步五行配置到战斗模块
        self._sync_to_combat()
        
        # 同步战斗数据到角色管理
        self._sync_to_character()
        
        # 同步掉落数据
        self._sync_to_loot()
        
        # 触发UI更新
        self._sync_to_ui()
    
    def _sync_to_five_elements(self) -> None:
        """同步数据到五行八卦模块"""
        self._module_states["five_elements"] = {
            "realm": self.character_data.get("realm", "炼气"),
            "disciple": self.character_data.get("name", "李长风"),
            "affinity_main": self.character_data.get("affinity_main", "木"),
            "board": self.bagua_configuration.get("stones", {}),
            "core": self.bagua_configuration.get("core", {}),
            "seed": self.bagua_configuration.get("seed", 184023)
        }
    
    def _sync_to_combat(self) -> None:
        """同步数据到战斗模块"""
        # 从五行配置计算属性加成
        bagua_bonuses = self._calculate_bagua_bonuses()
        
        # 从流派系统计算属性加成
        school_bonuses = self._calculate_school_bonuses()
        
        # 合并基础属性、五行加成和流派加成
        final_attributes = copy.deepcopy(self.character_data.get("base_attributes", {}))
        for key, value in bagua_bonuses.items():
            final_attributes[key] = final_attributes.get(key, 0) + value
        for key, value in school_bonuses.items():
            final_attributes[key] = final_attributes.get(key, 0) + value
        
        self._module_states["combat"] = {
            "character_stats": final_attributes,
            "skill_chain": self.combat_settings.get("skill_chain", {}),
            "simulation_params": self.combat_settings.get("simulation_params", {}),
            "bagua_effects": bagua_bonuses,
            "school_effects": school_bonuses
        }
    
    def _sync_to_character(self) -> None:
        """同步数据到角色管理模块"""
        school_info = self.get_school_info()
        available_skills = self.get_available_skills()
        
        self._module_states["character"] = {
            "character_data": self.character_data,
            "school_info": school_info,
            "available_skills": available_skills,
            "school_progress": self.character_data.get("cultivation_progress", {}),
            "unlocked_content": self.character_data.get("unlocked_skills", [])
        }
    
    def _sync_to_loot(self) -> None:
        """同步数据到掉落系统"""
        self._module_states["loot"] = {
            "inventory": self.loot_inventory,
            "character_school": self.character_data.get("school", "sword_cultivator"),
            "character_level": self.character_data.get("level", 1)
        }
    
    def _sync_to_ui(self) -> None:
        """同步数据到UI模块"""
        self._module_states["ui"] = {
            "active_character": self.character_data.get("name", "李长风"),
            "current_realm": self.character_data.get("realm", "炼气"),
            "bagua_state": self.bagua_configuration,
            "combat_ready": bool(self.combat_settings.get("skill_chain", {}).get("main_skill"))
        }
    
    def _calculate_bagua_bonuses(self) -> Dict[str, float]:
        """计算五行八卦配置的属性加成（实时计算）"""
        bonuses = {
            "atk": 0.0,
            "def": 0.0,
            "hp": 0.0,
            "crit_rate": 0.0,
            "crit_dmg": 0.0,
            "elem_dmg_木": 0.0,
            "elem_dmg_火": 0.0,
            "elem_dmg_土": 0.0,
            "elem_dmg_金": 0.0,
            "elem_dmg_水": 0.0
        }
        
        # 使用WuxingEngine进行精确计算
        try:
            from wuxing_engine import WuxingEngine
            wuxing_engine = WuxingEngine()
            
            # 计算综合效果
            comprehensive_effects = wuxing_engine.calculate_comprehensive_effects(
                self.bagua_configuration
            )
            
            # 应用全局协同效果
            global_synergy = comprehensive_effects.get("global_synergy", {})
            total_multiplier = global_synergy.get("total_multiplier", 1.0)
            
            # 基础属性加成
            base_bonuses = self._calculate_basic_stone_bonuses()
            for key, value in base_bonuses.items():
                bonuses[key] = value * total_multiplier
            
            # 应用卦位效果
            trigram_effects = comprehensive_effects.get("trigram_effects", {})
            for trigram, effects in trigram_effects.items():
                trigram_mult = effects.get("final_multiplier", 1.0)
                trigram_element = wuxing_engine.trigrams[trigram]["elem"]
                
                # 卦位特定加成
                if trigram_element == "木":
                    bonuses["hp"] += 30.0 * trigram_mult
                elif trigram_element == "火":
                    bonuses["atk"] += 20.0 * trigram_mult
                elif trigram_element == "土":
                    bonuses["def"] += 25.0 * trigram_mult
                elif trigram_element == "金":
                    bonuses["crit_dmg"] += 0.1 * trigram_mult
                elif trigram_element == "水":
                    bonuses["crit_rate"] += 0.02 * trigram_mult
            
            # 应用共鸣效果
            resonance_effects = comprehensive_effects.get("resonance_effects", {})
            resonance_mult = resonance_effects.get("resonance_multiplier", 1.0)
            stability_bonus = resonance_effects.get("stability_bonus", 0.0)
            
            # 共鸣加成应用到所有属性
            for key in bonuses:
                bonuses[key] *= resonance_mult
            
            # 稳定性转化为防御加成
            bonuses["def"] += stability_bonus * 2.0
            
        except Exception as e:
            # 降级到简化计算
            bonuses = self._calculate_basic_stone_bonuses()
        
        return bonuses
    
    def _calculate_basic_stone_bonuses(self) -> Dict[str, float]:
        """计算基础灵石加成（降级方案）"""
        bonuses = {
            "atk": 0.0,
            "def": 0.0,
            "hp": 0.0,
            "crit_rate": 0.0,
            "crit_dmg": 0.0,
            "elem_dmg_木": 0.0,
            "elem_dmg_火": 0.0,
            "elem_dmg_土": 0.0,
            "elem_dmg_金": 0.0,
            "elem_dmg_水": 0.0
        }
        
        stones = self.bagua_configuration.get("stones", {})
        for tri, slots in stones.items():
            for slot_idx, stone_id in slots.items():
                if stone_id and int(slot_idx) > 1:  # 跳过逻辑位
                    # 根据灵石类型和位置计算加成
                    if "gem_wood" in stone_id or "木" in stone_id:
                        bonuses["elem_dmg_木"] += 10.0
                        bonuses["hp"] += 50.0
                    elif "gem_fire" in stone_id or "火" in stone_id:
                        bonuses["elem_dmg_火"] += 11.0
                        bonuses["atk"] += 7.0
                    elif "gem_earth" in stone_id or "土" in stone_id:
                        bonuses["elem_dmg_土"] += 10.0
                        bonuses["def"] += 8.0
                    elif "gem_metal" in stone_id or "金" in stone_id:
                        bonuses["elem_dmg_金"] += 10.0
                        bonuses["atk"] += 5.0
                        bonuses["crit_dmg"] += 0.03
                    elif "gem_water" in stone_id or "水" in stone_id:
                        bonuses["elem_dmg_水"] += 10.0
                        bonuses["crit_rate"] += 0.015
        
        return bonuses
    
    def _calculate_school_bonuses(self) -> Dict[str, float]:
        """计算流派系统的属性加成"""
        school_id = self.character_data.get("school", "sword_cultivator")
        level = self.character_data.get("level", 1)
        
        school = self.school_manager.get_school(school_id)
        if not school:
            return {}
        
        # 获取流派基础加成
        bonuses = school.get_attribute_bonuses(level)
        
        # 计算多流派协同效果（如果有副流派）
        secondary_schools = self.character_data.get("secondary_schools", [])
        if secondary_schools:
            synergy_bonuses = self.school_manager.calculate_multi_school_synergy(
                school_id, secondary_schools
            )
            
            # 将协同加成转换为属性加成
            for key, value in synergy_bonuses.items():
                if "combo" in key:
                    # 协同效果转换为通用属性加成
                    bonuses["base_atk"] = bonuses.get("base_atk", 0) + value * 10
                    bonuses["max_hp"] = bonuses.get("max_hp", 0) + value * 50
        
        return bonuses
    
    def get_module_state(self, module_name: str) -> Dict[str, Any]:
        """获取指定模块的状态数据"""
        return self._module_states.get(module_name, {})
    
    def update_character_data(self, updates: Dict[str, Any]) -> None:
        """更新角色数据"""
        self.character_data.update(updates)
        self.sync_modules()
        self._auto_save_if_enabled()
    
    def update_bagua_configuration(self, updates: Dict[str, Any]) -> None:
        """更新五行八卦配置"""
        self.bagua_configuration.update(updates)
        self.sync_modules()
        self._auto_save_if_enabled()
    
    def update_combat_settings(self, updates: Dict[str, Any]) -> None:
        """更新战斗设置"""
        self.combat_settings.update(updates)
        self.sync_modules()
        self._auto_save_if_enabled()
    
    def change_character_school(self, new_school: str) -> bool:
        """更改角色流派"""
        if not self.school_manager.get_school(new_school):
            return False
        
        self.character_data["school"] = new_school
        
        # 重置流派相关进度（可选）
        # self.character_data["unlocked_skills"] = []
        # self.character_data["cultivation_progress"] = {}
        
        self.sync_modules()
        return True
    
    def unlock_skill(self, skill_id: str) -> bool:
        """解锁技能"""
        school_id = self.character_data.get("school", "sword_cultivator")
        level = self.character_data.get("level", 1)
        unlocked_skills = set(self.character_data.get("unlocked_skills", []))
        
        # 验证技能是否可以解锁
        available_skills = self.school_manager.get_available_skills(
            school_id, level, unlocked_skills
        )
        
        for skill in available_skills:
            if skill.id == skill_id:
                unlocked_skills.add(skill_id)
                self.character_data["unlocked_skills"] = list(unlocked_skills)
                self.sync_modules()
                return True
        
        return False
    
    def get_available_skills(self) -> List[Dict[str, Any]]:
        """获取当前可解锁的技能"""
        school_id = self.character_data.get("school", "sword_cultivator")
        level = self.character_data.get("level", 1)
        unlocked_skills = set(self.character_data.get("unlocked_skills", []))
        
        available_skills = self.school_manager.get_available_skills(
            school_id, level, unlocked_skills
        )
        
        return [
            {
                "id": skill.id,
                "name": skill.name,
                "description": skill.description,
                "level_requirement": skill.level_requirement,
                "effects": skill.effects,
                "element_affinity": skill.element_affinity
            }
            for skill in available_skills
        ]
    
    def get_school_info(self) -> Dict[str, Any]:
        """获取当前流派信息"""
        school_id = self.character_data.get("school", "sword_cultivator")
        school = self.school_manager.get_school(school_id)
        
        if not school:
            return {}
        
        level = self.character_data.get("level", 1)
        bonuses = school.get_attribute_bonuses(level)
        
        return {
            "school_id": school.school_id,
            "name": school.name,
            "element_affinity": school.element_affinity,
            "description": school.description,
            "attribute_bonuses": bonuses,
            "unique_mechanics": school.unique_mechanics,
            "synergy_schools": school.synergy_schools
        }
    
    def recommend_equipment_for_school(self, equipment_list: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], float]]:
        """为当前流派推荐装备"""
        school_id = self.character_data.get("school", "sword_cultivator")
        return self.school_manager.recommend_equipment(school_id, equipment_list)
        self.sync_modules()
    
    def save_state(self, filepath: Optional[str] = None) -> bool:
        """保存当前状态到文件"""
        try:
            if filepath is None:
                filepath = str(self.state_file)
            
            # 创建备份
            if os.path.exists(filepath):
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = self.backup_dir / f"state_backup_{timestamp}.json"
                import shutil
                shutil.copy2(filepath, backup_path)
                
                # 清理旧备份（保留最近10个）
                self._cleanup_old_backups()
            
            # 保存当前状态
            state_data = {
                "character_data": self.character_data,
                "bagua_configuration": self.bagua_configuration,
                "combat_settings": self.combat_settings,
                "loot_inventory": self.loot_inventory,
                "module_states": self._module_states,
                "timestamp": datetime.datetime.now().isoformat(),
                "version": "1.0"
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)
            
            # 清理旧备份（即使本次未创建新备份）
            self._cleanup_old_backups()
            
            return True
            
        except Exception as e:
            print(f"保存状态失败: {e}")
            return False
    
    def load_state(self, filepath: Optional[str] = None) -> bool:
        """从文件加载状态"""
        try:
            if filepath is None:
                filepath = str(self.state_file)
            
            if not os.path.exists(filepath):
                print(f"状态文件不存在: {filepath}")
                return False
            
            with open(filepath, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            
            # 加载各模块状态
            self.character_data = state_data.get("character_data", {})
            self.bagua_configuration = self._normalize_bagua_configuration(
                state_data.get("bagua_configuration", {})
            )
            self.combat_settings = state_data.get("combat_settings", {})
            self.loot_inventory = state_data.get("loot_inventory", [])
            self._module_states = state_data.get("module_states", {})
            
            # 确保状态完整性
            self._initialize_default_state()
            self.sync_modules()
            
            return True
            
        except Exception as e:
            print(f"加载状态失败: {e}")
            return False

    def _auto_save_if_enabled(self) -> None:
        """根据配置触发自动保存"""
        if self._auto_save_enabled or self._read_auto_save_setting():
            self.save_state()

    def _read_auto_save_setting(self) -> bool:
        """读取全局配置中的自动保存开关"""
        try:
            global_config_path = self.config_dir / "global_config.yaml"
            if not global_config_path.exists():
                return False
            with open(global_config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            return bool(data.get("auto_save", False))
        except Exception:
            return False

    def _normalize_bagua_configuration(self, bagua_config: Dict[str, Any]) -> Dict[str, Any]:
        """标准化八卦配置的索引键为整数"""
        if not isinstance(bagua_config, dict):
            return {}
        
        normalized = copy.deepcopy(bagua_config)
        stones = normalized.get("stones", {})
        normalized_stones = {}
        
        if isinstance(stones, dict):
            for tri, slots in stones.items():
                if isinstance(slots, dict):
                    normalized_slots = {}
                    for key, value in slots.items():
                        try:
                            normalized_key = int(key)
                        except (ValueError, TypeError):
                            normalized_key = key
                        normalized_slots[normalized_key] = value
                    normalized_stones[tri] = normalized_slots
                else:
                    normalized_stones[tri] = slots
        
        core = normalized.get("core", {})
        normalized_core = {}
        if isinstance(core, dict):
            for key, value in core.items():
                try:
                    normalized_key = int(key)
                except (ValueError, TypeError):
                    normalized_key = key
                normalized_core[normalized_key] = value
        
        normalized["stones"] = normalized_stones
        normalized["core"] = normalized_core
        return normalized
    
    def export_configuration(self, filepath: str, format: str = "json") -> bool:
        """导出配置到指定格式文件"""
        try:
            export_data = {
                "character": self.character_data,
                "bagua": self.bagua_configuration,
                "combat": self.combat_settings,
                "export_timestamp": datetime.datetime.now().isoformat(),
                "export_version": "1.0"
            }
            
            if format.lower() == "yaml":
                with open(filepath, 'w', encoding='utf-8') as f:
                    yaml.dump(export_data, f, allow_unicode=True, default_flow_style=False)
            else:  # json
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"导出配置失败: {e}")
            return False
    
    def import_configuration(self, filepath: str) -> bool:
        """从文件导入配置"""
        try:
            if not os.path.exists(filepath):
                return False
            
            # 根据文件扩展名判断格式
            if filepath.endswith('.yaml') or filepath.endswith('.yml'):
                with open(filepath, 'r', encoding='utf-8') as f:
                    import_data = yaml.safe_load(f)
            else:  # 默认json
                with open(filepath, 'r', encoding='utf-8') as f:
                    import_data = json.load(f)
            
            # 验证导入数据的完整性
            validation_result = self._validate_import_data(import_data)
            if not validation_result["is_valid"]:
                print(f"导入数据验证失败: {validation_result['errors']}")
                return False
            
            # 检测配置冲突
            conflicts = self._detect_import_conflicts(import_data)
            if conflicts:
                # 应用冲突解决策略
                import_data = self._resolve_import_conflicts(import_data, conflicts)
            
            # 验证和导入数据
            if "character" in import_data:
                self.character_data.update(import_data["character"])
            
            if "bagua" in import_data:
                self.bagua_configuration.update(import_data["bagua"])
            
            if "combat" in import_data:
                self.combat_settings.update(import_data["combat"])
            
            # 同步所有模块
            self.sync_modules()
            
            return True
            
        except Exception as e:
            print(f"导入配置失败: {e}")
            return False
    
    def validate_state_consistency(self) -> Tuple[bool, List[str]]:
        """验证状态一致性"""
        issues = []
        
        # 检查角色数据完整性
        required_char_fields = ["name", "level", "school", "realm"]
        for field in required_char_fields:
            if field not in self.character_data:
                issues.append(f"角色数据缺少必需字段: {field}")
        
        # 检查五行配置完整性
        if "stones" not in self.bagua_configuration:
            issues.append("五行八卦配置缺少灵石数据")
        
        # 检查模块间数据一致性
        char_realm = self.character_data.get("realm")
        five_elem_realm = self._module_states.get("five_elements", {}).get("realm")
        if char_realm != five_elem_realm:
            issues.append(f"角色境界不一致: 角色({char_realm}) vs 五行模块({five_elem_realm})")
        
        return len(issues) == 0, issues
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态概览"""
        is_consistent, issues = self.validate_state_consistency()
        
        return {
            "character_name": self.character_data.get("name", "未知"),
            "character_realm": self.character_data.get("realm", "未知"),
            "character_school": self.character_data.get("school", "未知"),
            "bagua_stones_count": sum(1 for tri_data in self.bagua_configuration.get("stones", {}).values() 
                                    for stone in tri_data.values() if stone),
            "core_bios_count": sum(1 for bios in self.bagua_configuration.get("core", {}).values() if bios),
            "active_skills_count": len(self.combat_settings.get("selected_skills", [])),
            "inventory_items": len(self.loot_inventory),
            "state_consistent": is_consistent,
            "consistency_issues": issues,
            "last_sync": datetime.datetime.now().isoformat()
        }
    
    def _cleanup_old_backups(self) -> None:
        """清理旧备份文件"""
        try:
            backup_files = list(self.backup_dir.glob("state_backup_*.json"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # 保留最近10个备份
            for backup_file in backup_files[10:]:
                backup_file.unlink()
                
        except Exception as e:
            print(f"清理备份失败: {e}")
    
    def _validate_import_data(self, import_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证导入数据的完整性"""
        errors = []
        
        # 检查数据结构
        if not isinstance(import_data, dict):
            errors.append("导入数据必须是字典格式")
            return {"is_valid": False, "errors": errors}
        
        # 验证角色数据
        if "character" in import_data:
            char_data = import_data["character"]
            if not isinstance(char_data, dict):
                errors.append("角色数据必须是字典格式")
            else:
                # 检查必需字段
                required_fields = ["name", "school", "realm"]
                for field in required_fields:
                    if field not in char_data:
                        errors.append(f"角色数据缺少必需字段: {field}")
                
                # 验证字段值
                if "school" in char_data:
                    valid_schools = ["sword_cultivator", "spell_cultivator", "body_cultivator", "pill_cultivator", "formation_cultivator"]
                    if char_data["school"] not in valid_schools:
                        errors.append(f"无效的流派: {char_data['school']}")
                
                if "level" in char_data:
                    if not isinstance(char_data["level"], int) or char_data["level"] < 1:
                        errors.append("角色等级必须是大于0的整数")
        
        # 验证八卦配置
        if "bagua" in import_data:
            bagua_data = import_data["bagua"]
            if not isinstance(bagua_data, dict):
                errors.append("八卦配置必须是字典格式")
            else:
                if "stones" in bagua_data:
                    stones = bagua_data["stones"]
                    if not isinstance(stones, dict):
                        errors.append("灵石配置必须是字典格式")
                    else:
                        valid_trigrams = ["QIAN", "DUI", "LI", "ZHEN", "XUN", "KAN", "GEN", "KUN"]
                        for tri in stones.keys():
                            if tri not in valid_trigrams:
                                errors.append(f"无效的卦位: {tri}")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }
    
    def _detect_import_conflicts(self, import_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检测导入配置与当前配置的冲突"""
        conflicts = []
        
        # 检查角色数据冲突
        if "character" in import_data:
            import_char = import_data["character"]
            current_char = self.character_data
            
            for key, import_value in import_char.items():
                if key in current_char:
                    current_value = current_char[key]
                    if current_value != import_value:
                        conflicts.append({
                            "type": "character_data",
                            "field": key,
                            "current_value": current_value,
                            "import_value": import_value,
                            "severity": "medium"
                        })
        
        # 检查八卦配置冲突
        if "bagua" in import_data:
            import_bagua = import_data["bagua"]
            current_bagua = self.bagua_configuration
            
            # 检查灵石配置冲突
            if "stones" in import_bagua and "stones" in current_bagua:
                import_stones = import_bagua["stones"]
                current_stones = current_bagua["stones"]
                
                for tri, slots in import_stones.items():
                    if tri in current_stones:
                        for slot_idx, stone_id in slots.items():
                            current_stone = current_stones[tri].get(slot_idx)
                            if current_stone and current_stone != stone_id:
                                conflicts.append({
                                    "type": "bagua_stones",
                                    "field": f"{tri}.{slot_idx}",
                                    "current_value": current_stone,
                                    "import_value": stone_id,
                                    "severity": "high"
                                })
        
        return conflicts
    
    def _resolve_import_conflicts(self, import_data: Dict[str, Any], conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """解决导入配置冲突"""
        resolved_data = copy.deepcopy(import_data)
        
        # 应用冲突解决策略：优先使用导入数据，但记录冲突
        conflict_log = []
        
        for conflict in conflicts:
            conflict_log.append({
                "type": conflict["type"],
                "field": conflict["field"],
                "resolution": "prefer_import",
                "old_value": conflict["current_value"],
                "new_value": conflict["import_value"]
            })
        
        # 将冲突日志添加到解决后的数据中
        resolved_data["_conflict_resolution"] = {
            "timestamp": datetime.datetime.now().isoformat(),
            "conflicts_resolved": len(conflicts),
            "resolution_log": conflict_log
        }
        
        return resolved_data
    
    def calculate_realtime_attributes(self) -> Dict[str, float]:
        """实时计算角色的完整属性面板"""
        # 获取基础属性
        base_attrs = copy.deepcopy(self.character_data.get("base_attributes", {}))
        
        # 计算五行八卦加成
        bagua_bonuses = self._calculate_bagua_bonuses()
        
        # 计算流派加成
        school_bonuses = self._calculate_school_bonuses()
        
        # 计算装备加成
        equipment_bonuses = self._calculate_equipment_bonuses()
        
        # 合并所有加成
        final_attributes = {}
        all_keys = set(base_attrs.keys()) | set(bagua_bonuses.keys()) | set(school_bonuses.keys()) | set(equipment_bonuses.keys())
        
        for key in all_keys:
            base_value = base_attrs.get(key, 0.0)
            bagua_bonus = bagua_bonuses.get(key, 0.0)
            school_bonus = school_bonuses.get(key, 0.0)
            equipment_bonus = equipment_bonuses.get(key, 0.0)
            
            # 加法合并（可以根据需要改为乘法）
            final_attributes[key] = base_value + bagua_bonus + school_bonus + equipment_bonus
        
        # 更新派生属性
        self.character_data["derived_attributes"] = final_attributes
        
        return final_attributes
    
    def _calculate_equipment_bonuses(self) -> Dict[str, float]:
        """计算装备属性加成"""
        bonuses = {}
        
        equipment = self.character_data.get("equipment", {})
        for slot, item_data in equipment.items():
            if not item_data:
                continue
            
            item_stats = item_data.get("stats", {})
            for stat, value in item_stats.items():
                bonuses[stat] = bonuses.get(stat, 0.0) + value
        
        return bonuses
    
    def validate_bd_configuration(self) -> Dict[str, Any]:
        """验证BD配置的有效性和完整性"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": [],
            "completeness_score": 0.0
        }
        
        try:
            # 验证八卦配置
            from wuxing_engine import WuxingEngine
            wuxing_engine = WuxingEngine()
            
            is_valid, errors = wuxing_engine.validate_bagua_configuration(self.bagua_configuration)
            validation_result["is_valid"] = is_valid
            validation_result["errors"].extend(errors)
            
            # 计算配置完整性
            stones_config = self.bagua_configuration.get("stones", {})
            total_slots = 0
            filled_slots = 0
            
            realm = self.character_data.get("realm", "炼气")
            realm_config = wuxing_engine.get_realm_config(realm)
            tri_unlock = realm_config["tri_unlock"]
            
            for tri, slots in stones_config.items():
                for slot_idx in range(1, tri_unlock + 1):
                    total_slots += 1
                    if slots.get(str(slot_idx)):
                        filled_slots += 1
            
            validation_result["completeness_score"] = filled_slots / total_slots if total_slots > 0 else 0.0
            
            # 生成建议
            if validation_result["completeness_score"] < 0.5:
                validation_result["suggestions"].append("建议填充更多灵石槽位以提升配置完整性")
            
            # 检查五行平衡
            element_counts = {}
            for tri, slots in stones_config.items():
                for slot_idx, stone_id in slots.items():
                    if stone_id and int(slot_idx) > 1:
                        element = wuxing_engine._infer_element_from_id(stone_id)
                        if element in wuxing_engine.elements:
                            element_counts[element] = element_counts.get(element, 0) + 1
            
            if element_counts:
                max_count = max(element_counts.values())
                min_count = min(element_counts.values())
                if max_count - min_count > 2:
                    validation_result["warnings"].append("五行分布不够均衡，可能影响协同效果")
            
        except Exception as e:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"验证过程出错: {str(e)}")
        
        return validation_result
    
    def get_bd_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """获取BD优化建议"""
        suggestions = []
        
        try:
            # 分析当前配置
            current_attrs = self.calculate_realtime_attributes()
            validation = self.validate_bd_configuration()
            
            # 基于属性分析的建议
            school_id = self.character_data.get("school", "sword_cultivator")
            school = self.school_manager.get_school(school_id)
            
            if school:
                recommended_attrs = school.get_attribute_bonuses(1).keys()
                
                for attr in recommended_attrs:
                    current_value = current_attrs.get(attr, 0)
                    if current_value < 100:  # 假设100是一个合理的基准
                        suggestions.append({
                            "type": "attribute_improvement",
                            "priority": "high",
                            "description": f"提升{attr}属性，当前值({current_value:.1f})偏低",
                            "target_attribute": attr,
                            "current_value": current_value,
                            "suggested_improvement": "通过装备或灵石配置提升"
                        })
            
            # 基于五行配置的建议
            if validation["completeness_score"] < 0.8:
                suggestions.append({
                    "type": "configuration_completeness",
                    "priority": "medium",
                    "description": f"配置完整度({validation['completeness_score']:.1%})可以提升",
                    "suggested_improvement": "填充更多灵石槽位"
                })
            
            # 基于流派匹配的建议
            from loot_generator import get_bd_optimizer
            bd_optimizer = get_bd_optimizer()
            bd_analysis = bd_optimizer.analyze_current_build(self.character_data)
            
            if bd_analysis.get("synergy_score", 0) < 0.7:
                suggestions.append({
                    "type": "synergy_improvement",
                    "priority": "high",
                    "description": "装备与流派的协同度较低",
                    "suggested_improvement": "更换更适合当前流派的装备"
                })
            
        except Exception as e:
            suggestions.append({
                "type": "error",
                "priority": "high",
                "description": f"分析过程出错: {str(e)}",
                "suggested_improvement": "检查配置数据完整性"
            })
        
        return suggestions
    
    def perform_one_click_combat_test(self) -> Dict[str, Any]:
        """执行一键战斗测试"""
        test_result = {
            "success": False,
            "combat_result": {},
            "performance_analysis": {},
            "optimization_suggestions": [],
            "error": None
        }
        
        try:
            # 计算当前属性
            current_attrs = self.calculate_realtime_attributes()
            
            # 简化的战斗模拟（不依赖复杂的战斗引擎）
            base_atk = current_attrs.get("base_atk", 40)
            max_hp = current_attrs.get("max_hp", 500)
            crit_rate = current_attrs.get("crit_rate", 0.05)
            crit_dmg = current_attrs.get("crit_dmg", 1.7)
            
            # 模拟战斗参数
            enemy_hp = 3000.0
            enemy_dps = 20.0
            max_time = 20.0
            
            # 计算平均DPS
            avg_damage_per_hit = base_atk * (1 + crit_rate * (crit_dmg - 1))
            attacks_per_second = 1.0  # 假设每秒1次攻击
            average_dps = avg_damage_per_hit * attacks_per_second
            
            # 计算战斗时长
            time_to_kill = enemy_hp / average_dps if average_dps > 0 else max_time
            
            # 计算生存能力
            damage_taken_per_second = enemy_dps
            time_to_death = max_hp / damage_taken_per_second if damage_taken_per_second > 0 else float('inf')
            
            # 判断战斗结果
            if time_to_kill <= time_to_death and time_to_kill <= max_time:
                result = "WIN"
                actual_time = time_to_kill
            elif time_to_death <= max_time:
                result = "LOSE"
                actual_time = time_to_death
            else:
                result = "TIMEOUT"
                actual_time = max_time
            
            # 计算生存能力评分
            survivability_score = min(1.0, time_to_death / max_time)
            
            # 计算效率评级
            if result == "WIN":
                efficiency_rating = min(1.0, (max_time - actual_time) / max_time)
            else:
                efficiency_rating = 0.0
            
            test_result["success"] = True
            test_result["combat_result"] = {
                "result": result,
                "time": actual_time,
                "damage_dealt": min(enemy_hp, average_dps * actual_time),
                "damage_taken": damage_taken_per_second * actual_time
            }
            
            test_result["performance_analysis"] = {
                "average_dps": average_dps,
                "survivability_score": survivability_score,
                "efficiency_rating": efficiency_rating,
                "fight_duration": actual_time,
                "result": result
            }
            
            # 生成优化建议
            if average_dps < 150:
                test_result["optimization_suggestions"].append("DPS偏低，建议提升攻击力相关属性")
            
            if result != "WIN":
                test_result["optimization_suggestions"].append("战斗失败，建议提升生存能力或输出能力")
            
            if survivability_score < 0.5:
                test_result["optimization_suggestions"].append("生存能力不足，建议提升生命值或防御力")
            
        except Exception as e:
            test_result["error"] = str(e)
        
        return test_result
    
    def enable_auto_save(self, interval_seconds: int = 30) -> None:
        """启用自动保存功能"""
        # 这里可以实现定时自动保存
        # 由于这是一个简化实现，我们只是标记启用状态
        self._auto_save_enabled = True
        self._auto_save_interval = interval_seconds
        print(f"自动保存已启用，间隔: {interval_seconds}秒")
    
    def disable_auto_save(self) -> None:
        """禁用自动保存功能"""
        self._auto_save_enabled = False
        print("自动保存已禁用")
    
    def create_configuration_snapshot(self, name: str) -> bool:
        """创建配置快照"""
        try:
            snapshot_dir = self.config_dir / "snapshots"
            snapshot_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            snapshot_file = snapshot_dir / f"{name}_{timestamp}.json"
            
            snapshot_data = {
                "name": name,
                "timestamp": datetime.datetime.now().isoformat(),
                "character_data": self.character_data,
                "bagua_configuration": self.bagua_configuration,
                "combat_settings": self.combat_settings,
                "loot_inventory": self.loot_inventory
            }
            
            with open(snapshot_file, 'w', encoding='utf-8') as f:
                json.dump(snapshot_data, f, ensure_ascii=False, indent=2)
            
            print(f"配置快照已创建: {snapshot_file}")
            return True
            
        except Exception as e:
            print(f"创建配置快照失败: {e}")
            return False
    
    def restore_configuration_snapshot(self, snapshot_path: str) -> bool:
        """恢复配置快照"""
        try:
            if not os.path.exists(snapshot_path):
                print(f"快照文件不存在: {snapshot_path}")
                return False
            
            with open(snapshot_path, 'r', encoding='utf-8') as f:
                snapshot_data = json.load(f)
            
            # 恢复配置
            if "character_data" in snapshot_data:
                self.character_data = snapshot_data["character_data"]
            
            if "bagua_configuration" in snapshot_data:
                self.bagua_configuration = snapshot_data["bagua_configuration"]
            
            if "combat_settings" in snapshot_data:
                self.combat_settings = snapshot_data["combat_settings"]
            
            if "loot_inventory" in snapshot_data:
                self.loot_inventory = snapshot_data["loot_inventory"]
            
            # 同步所有模块
            self.sync_modules()
            
            print(f"配置快照已恢复: {snapshot_path}")
            return True
            
        except Exception as e:
            print(f"恢复配置快照失败: {e}")
            return False


# 全局状态管理器实例
_global_state_manager: Optional[UnifiedStateManager] = None


def get_state_manager() -> UnifiedStateManager:
    """获取全局状态管理器实例"""
    global _global_state_manager
    if _global_state_manager is None:
        _global_state_manager = UnifiedStateManager()
    return _global_state_manager


def initialize_unified_system(config_dir: Optional[str] = None) -> UnifiedStateManager:
    """初始化统一系统"""
    global _global_state_manager
    _global_state_manager = UnifiedStateManager(config_dir)
    
    # 尝试加载已有状态
    _global_state_manager.load_state()
    
    return _global_state_manager
