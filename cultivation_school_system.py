# -*- coding: utf-8 -*-
"""
流派系统和角色管理 (CultivationSchoolSystem)
实现多种修真流派（剑修、法修、体修、丹修、阵修）
建立流派特色技能树和装备偏好系统，实现流派协同效果和进阶解锁机制
"""

from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import copy
import json
from pathlib import Path


class SchoolType(Enum):
    """流派类型枚举"""
    SWORD = "sword_cultivator"      # 剑修
    SPELL = "spell_cultivator"      # 法修  
    BODY = "body_cultivator"        # 体修
    PILL = "pill_cultivator"        # 丹修
    FORMATION = "formation_cultivator"  # 阵修


class SkillType(Enum):
    """技能类型枚举"""
    ACTIVE = "active"       # 主动技能
    PASSIVE = "passive"     # 被动技能
    ULTIMATE = "ultimate"   # 终极技能
    SYNERGY = "synergy"     # 协同技能


class EquipmentType(Enum):
    """装备类型枚举"""
    WEAPON = "weapon"       # 武器
    ARMOR = "armor"         # 护甲
    ACCESSORY = "accessory" # 饰品
    CONSUMABLE = "consumable"  # 消耗品


@dataclass
class Skill:
    """技能数据结构"""
    id: str
    name: str
    description: str
    skill_type: SkillType
    school_requirement: SchoolType
    level_requirement: int
    prerequisites: List[str] = field(default_factory=list)
    effects: Dict[str, float] = field(default_factory=dict)
    element_affinity: str = "无"
    unlock_conditions: Dict[str, Any] = field(default_factory=dict)
    synergy_schools: List[SchoolType] = field(default_factory=list)


@dataclass
class EquipmentPreference:
    """装备偏好数据结构"""
    equipment_type: EquipmentType
    preferred_attributes: List[str]
    weight_multiplier: float
    element_bonus: Dict[str, float] = field(default_factory=dict)

class CultivationSchool:
    """修真流派类
    
    实现单个流派的完整功能，包括技能树、装备偏好、属性加成等
    """
    
    def __init__(self, school_id: str, name: str, element_affinity: str, description: str = ""):
        self.school_id = school_id
        self.name = name
        self.element_affinity = element_affinity
        self.description = description
        
        # 技能树系统
        self.skill_tree: Dict[str, Skill] = {}
        self.skill_unlock_order: List[str] = []
        
        # 装备偏好系统
        self.equipment_preferences: List[EquipmentPreference] = []
        
        # 属性加成系统
        self.base_attribute_bonuses: Dict[str, float] = {}
        self.level_scaling_bonuses: Dict[str, float] = {}
        
        # 流派特色
        self.unique_mechanics: Dict[str, Any] = {}
        self.synergy_schools: List[str] = []
        
        # 进阶系统
        self.advancement_tiers: Dict[int, Dict[str, Any]] = {}
        
        # 初始化流派特色
        self._initialize_school_specifics()
    
    def _initialize_school_specifics(self) -> None:
        """初始化流派特色内容"""
        if self.school_id == SchoolType.SWORD.value:
            self._init_sword_cultivator()
        elif self.school_id == SchoolType.SPELL.value:
            self._init_spell_cultivator()
        elif self.school_id == SchoolType.BODY.value:
            self._init_body_cultivator()
        elif self.school_id == SchoolType.PILL.value:
            self._init_pill_cultivator()
        elif self.school_id == SchoolType.FORMATION.value:
            self._init_formation_cultivator()
    
    def _init_sword_cultivator(self) -> None:
        """初始化剑修流派"""
        self.base_attribute_bonuses = {
            "base_atk": 15.0,
            "crit_rate": 0.08,
            "crit_dmg": 0.25,
            "agi": 10.0
        }
        
        self.level_scaling_bonuses = {
            "base_atk": 2.5,
            "crit_rate": 0.002,
            "crit_dmg": 0.01
        }
        
        # 剑修技能树
        self.skill_tree = {
            "sword_basic_slash": Skill(
                id="sword_basic_slash",
                name="基础剑法",
                description="剑修的基础攻击技能，造成物理伤害",
                skill_type=SkillType.ACTIVE,
                school_requirement=SchoolType.SWORD,
                level_requirement=1,
                effects={"damage_multiplier": 1.2, "crit_bonus": 0.1}
            ),
            "sword_qi_burst": Skill(
                id="sword_qi_burst",
                name="剑气爆发",
                description="释放剑气造成范围伤害",
                skill_type=SkillType.ACTIVE,
                school_requirement=SchoolType.SWORD,
                level_requirement=10,
                prerequisites=["sword_basic_slash"],
                effects={"damage_multiplier": 1.8, "area_damage": True}
            ),
            "sword_mastery": Skill(
                id="sword_mastery",
                name="剑道精通",
                description="被动提升剑类武器的伤害和暴击",
                skill_type=SkillType.PASSIVE,
                school_requirement=SchoolType.SWORD,
                level_requirement=5,
                effects={"weapon_damage_bonus": 0.2, "crit_rate_bonus": 0.05}
            )
        }
        
        self.skill_unlock_order = ["sword_basic_slash", "sword_mastery", "sword_qi_burst"]
        
        # 装备偏好
        self.equipment_preferences = [
            EquipmentPreference(
                equipment_type=EquipmentType.WEAPON,
                preferred_attributes=["base_atk", "crit_rate", "crit_dmg"],
                weight_multiplier=1.5,
                element_bonus={"金": 0.2}
            ),
            EquipmentPreference(
                equipment_type=EquipmentType.ARMOR,
                preferred_attributes=["agi", "dodge_rate"],
                weight_multiplier=1.2
            )
        ]
        
        self.unique_mechanics = {
            "sword_combo": "连击系统，连续攻击增加伤害",
            "perfect_parry": "完美格挡可以反击"
        }
        
        self.synergy_schools = [SchoolType.FORMATION.value]  # 与阵修有协同
    
    def _init_spell_cultivator(self) -> None:
        """初始化法修流派"""
        self.base_attribute_bonuses = {
            "int": 20.0,
            "max_hp": 100.0,
            "elem_dmg_火": 15.0,
            "elem_dmg_水": 10.0
        }
        
        self.level_scaling_bonuses = {
            "int": 3.0,
            "elem_dmg_火": 1.5,
            "max_hp": 15.0
        }
        
        # 法修技能树
        self.skill_tree = {
            "spell_fireball": Skill(
                id="spell_fireball",
                name="火球术",
                description="发射火球造成火属性伤害",
                skill_type=SkillType.ACTIVE,
                school_requirement=SchoolType.SPELL,
                level_requirement=1,
                effects={"damage_multiplier": 1.5, "element_type": "火"},
                element_affinity="火"
            ),
            "spell_ice_shield": Skill(
                id="spell_ice_shield",
                name="冰盾术",
                description="创造冰盾提供防护",
                skill_type=SkillType.ACTIVE,
                school_requirement=SchoolType.SPELL,
                level_requirement=8,
                effects={"shield_value": 200, "duration": 10},
                element_affinity="水"
            ),
            "spell_mastery": Skill(
                id="spell_mastery",
                name="法术精通",
                description="被动提升所有法术伤害和法力效率",
                skill_type=SkillType.PASSIVE,
                school_requirement=SchoolType.SPELL,
                level_requirement=5,
                effects={"spell_damage_bonus": 0.25, "mana_efficiency": 0.15}
            )
        }
        
        self.skill_unlock_order = ["spell_fireball", "spell_mastery", "spell_ice_shield"]
        
        # 装备偏好
        self.equipment_preferences = [
            EquipmentPreference(
                equipment_type=EquipmentType.WEAPON,
                preferred_attributes=["int", "elem_dmg_火", "elem_dmg_水"],
                weight_multiplier=1.4,
                element_bonus={"火": 0.25, "水": 0.15}
            ),
            EquipmentPreference(
                equipment_type=EquipmentType.ACCESSORY,
                preferred_attributes=["max_hp", "mana_regen"],
                weight_multiplier=1.3
            )
        ]
        
        self.unique_mechanics = {
            "elemental_mastery": "精通多种元素法术",
            "spell_combination": "可以组合不同元素的法术"
        }
        
        self.synergy_schools = [SchoolType.PILL.value]  # 与丹修有协同
    
    def _init_body_cultivator(self) -> None:
        """初始化体修流派"""
        self.base_attribute_bonuses = {
            "str": 25.0,
            "max_hp": 300.0,
            "def": 20.0,
            "hp_regen": 5.0
        }
        
        self.level_scaling_bonuses = {
            "str": 4.0,
            "max_hp": 25.0,
            "def": 2.0
        }
        
        # 体修技能树
        self.skill_tree = {
            "body_iron_fist": Skill(
                id="body_iron_fist",
                name="铁拳",
                description="强化拳头进行近战攻击",
                skill_type=SkillType.ACTIVE,
                school_requirement=SchoolType.BODY,
                level_requirement=1,
                effects={"damage_multiplier": 1.3, "stun_chance": 0.1}
            ),
            "body_iron_skin": Skill(
                id="body_iron_skin",
                name="铁布衫",
                description="被动提升防御力和生命值",
                skill_type=SkillType.PASSIVE,
                school_requirement=SchoolType.BODY,
                level_requirement=3,
                effects={"def_bonus": 0.3, "hp_bonus": 0.2}
            ),
            "body_berserker": Skill(
                id="body_berserker",
                name="狂暴",
                description="生命值越低攻击力越高",
                skill_type=SkillType.PASSIVE,
                school_requirement=SchoolType.BODY,
                level_requirement=15,
                prerequisites=["body_iron_fist", "body_iron_skin"],
                effects={"low_hp_damage_bonus": 0.5}
            )
        }
        
        self.skill_unlock_order = ["body_iron_fist", "body_iron_skin", "body_berserker"]
        
        # 装备偏好
        self.equipment_preferences = [
            EquipmentPreference(
                equipment_type=EquipmentType.ARMOR,
                preferred_attributes=["def", "max_hp", "hp_regen"],
                weight_multiplier=1.6,
                element_bonus={"土": 0.3}
            ),
            EquipmentPreference(
                equipment_type=EquipmentType.WEAPON,
                preferred_attributes=["str", "base_atk"],
                weight_multiplier=1.2
            )
        ]
        
        self.unique_mechanics = {
            "damage_reduction": "天生减伤能力",
            "hp_scaling": "部分技能伤害基于生命值"
        }
        
        self.synergy_schools = [SchoolType.SWORD.value]  # 与剑修有协同
    
    def _init_pill_cultivator(self) -> None:
        """初始化丹修流派"""
        self.base_attribute_bonuses = {
            "int": 15.0,
            "max_hp": 150.0,
            "hp_regen": 8.0,
            "elem_dmg_木": 12.0
        }
        
        self.level_scaling_bonuses = {
            "int": 2.0,
            "hp_regen": 1.0,
            "elem_dmg_木": 1.2
        }
        
        # 丹修技能树
        self.skill_tree = {
            "pill_healing": Skill(
                id="pill_healing",
                name="治疗丹药",
                description="炼制并使用治疗丹药",
                skill_type=SkillType.ACTIVE,
                school_requirement=SchoolType.PILL,
                level_requirement=1,
                effects={"heal_amount": 150, "heal_over_time": 50}
            ),
            "pill_poison": Skill(
                id="pill_poison",
                name="毒丹",
                description="炼制毒丹对敌人造成持续伤害",
                skill_type=SkillType.ACTIVE,
                school_requirement=SchoolType.PILL,
                level_requirement=12,
                effects={"poison_damage": 30, "duration": 8}
            ),
            "pill_mastery": Skill(
                id="pill_mastery",
                name="炼丹精通",
                description="被动提升丹药效果和炼制成功率",
                skill_type=SkillType.PASSIVE,
                school_requirement=SchoolType.PILL,
                level_requirement=6,
                effects={"pill_effect_bonus": 0.3, "craft_success_rate": 0.2}
            )
        }
        
        self.skill_unlock_order = ["pill_healing", "pill_mastery", "pill_poison"]
        
        # 装备偏好
        self.equipment_preferences = [
            EquipmentPreference(
                equipment_type=EquipmentType.ACCESSORY,
                preferred_attributes=["int", "hp_regen", "elem_dmg_木"],
                weight_multiplier=1.5,
                element_bonus={"木": 0.25}
            ),
            EquipmentPreference(
                equipment_type=EquipmentType.CONSUMABLE,
                preferred_attributes=["heal_bonus", "effect_duration"],
                weight_multiplier=2.0
            )
        ]
        
        self.unique_mechanics = {
            "pill_crafting": "可以炼制各种丹药",
            "support_abilities": "强大的辅助和治疗能力"
        }
        
        self.synergy_schools = [SchoolType.SPELL.value, SchoolType.BODY.value]  # 与法修、体修有协同
    
    def _init_formation_cultivator(self) -> None:
        """初始化阵修流派"""
        self.base_attribute_bonuses = {
            "int": 18.0,
            "agi": 12.0,
            "elem_dmg_土": 10.0,
            "elem_dmg_金": 8.0
        }
        
        self.level_scaling_bonuses = {
            "int": 2.5,
            "agi": 1.5,
            "elem_dmg_土": 1.0
        }
        
        # 阵修技能树
        self.skill_tree = {
            "formation_basic": Skill(
                id="formation_basic",
                name="基础阵法",
                description="布置基础防护阵法",
                skill_type=SkillType.ACTIVE,
                school_requirement=SchoolType.FORMATION,
                level_requirement=1,
                effects={"shield_value": 100, "area_effect": True}
            ),
            "formation_attack": Skill(
                id="formation_attack",
                name="攻击阵法",
                description="布置攻击型阵法",
                skill_type=SkillType.ACTIVE,
                school_requirement=SchoolType.FORMATION,
                level_requirement=10,
                effects={"damage_multiplier": 1.6, "area_damage": True}
            ),
            "formation_mastery": Skill(
                id="formation_mastery",
                name="阵法精通",
                description="被动提升阵法效果和持续时间",
                skill_type=SkillType.PASSIVE,
                school_requirement=SchoolType.FORMATION,
                level_requirement=7,
                effects={"formation_effect_bonus": 0.4, "duration_bonus": 0.5}
            )
        }
        
        self.skill_unlock_order = ["formation_basic", "formation_mastery", "formation_attack"]
        
        # 装备偏好
        self.equipment_preferences = [
            EquipmentPreference(
                equipment_type=EquipmentType.ACCESSORY,
                preferred_attributes=["int", "agi", "elem_dmg_土"],
                weight_multiplier=1.4,
                element_bonus={"土": 0.2, "金": 0.15}
            ),
            EquipmentPreference(
                equipment_type=EquipmentType.WEAPON,
                preferred_attributes=["formation_power", "area_effect"],
                weight_multiplier=1.3
            )
        ]
        
        self.unique_mechanics = {
            "area_control": "控制战场区域",
            "team_support": "为团队提供增益效果"
        }
        
        self.synergy_schools = [SchoolType.SWORD.value, SchoolType.SPELL.value]  # 与剑修、法修有协同
    
    def get_attribute_bonuses(self, level: int) -> Dict[str, float]:
        """获取流派属性加成"""
        bonuses = copy.deepcopy(self.base_attribute_bonuses)
        
        # 添加等级缩放加成
        for attr, scaling in self.level_scaling_bonuses.items():
            if attr in bonuses:
                bonuses[attr] += scaling * (level - 1)
            else:
                bonuses[attr] = scaling * (level - 1)
        
        return bonuses
    
    def unlock_skills(self, character_level: int, unlocked_skills: Set[str] = None) -> List[str]:
        """解锁可用技能"""
        if unlocked_skills is None:
            unlocked_skills = set()
        
        available_skills = []
        
        for skill_id in self.skill_unlock_order:
            if skill_id in unlocked_skills:
                continue
                
            skill = self.skill_tree.get(skill_id)
            if not skill:
                continue
            
            # 检查等级要求
            if character_level < skill.level_requirement:
                continue
            
            # 检查前置技能
            if skill.prerequisites:
                if not all(prereq in unlocked_skills for prereq in skill.prerequisites):
                    continue
            
            available_skills.append(skill_id)
        
        return available_skills
    
    def get_skill_info(self, skill_id: str) -> Optional[Skill]:
        """获取技能信息"""
        return self.skill_tree.get(skill_id)
    
    def calculate_synergy_bonus(self, other_schools: List[str]) -> Dict[str, float]:
        """计算与其他流派的协同加成"""
        synergy_bonus = {}
        
        for school_id in other_schools:
            if school_id in self.synergy_schools:
                # 基础协同加成
                synergy_bonus[f"synergy_with_{school_id}"] = 0.15
                
                # 特定协同效果
                if self.school_id == SchoolType.SWORD.value and school_id == SchoolType.FORMATION.value:
                    synergy_bonus["sword_formation_combo"] = 0.2  # 剑阵合璧
                elif self.school_id == SchoolType.SPELL.value and school_id == SchoolType.PILL.value:
                    synergy_bonus["spell_pill_combo"] = 0.18  # 法丹双修
                elif self.school_id == SchoolType.BODY.value and school_id == SchoolType.PILL.value:
                    synergy_bonus["body_pill_combo"] = 0.22  # 体丹结合
        
        return synergy_bonus
    
    def get_equipment_score(self, equipment_stats: Dict[str, float]) -> float:
        """计算装备对该流派的适配度评分"""
        total_score = 0.0
        
        for preference in self.equipment_preferences:
            preference_score = 0.0
            
            for attr in preference.preferred_attributes:
                if attr in equipment_stats:
                    preference_score += equipment_stats[attr] * preference.weight_multiplier
            
            # 元素加成
            for element, bonus in preference.element_bonus.items():
                element_attr = f"elem_dmg_{element}"
                if element_attr in equipment_stats:
                    preference_score += equipment_stats[element_attr] * bonus
            
            total_score += preference_score
        
        return total_score
    
    def get_advancement_requirements(self, tier: int) -> Dict[str, Any]:
        """获取进阶要求"""
        return self.advancement_tiers.get(tier, {})
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "school_id": self.school_id,
            "name": self.name,
            "element_affinity": self.element_affinity,
            "description": self.description,
            "base_attribute_bonuses": self.base_attribute_bonuses,
            "level_scaling_bonuses": self.level_scaling_bonuses,
            "skill_tree": {k: {
                "id": v.id,
                "name": v.name,
                "description": v.description,
                "skill_type": v.skill_type.value,
                "level_requirement": v.level_requirement,
                "prerequisites": v.prerequisites,
                "effects": v.effects,
                "element_affinity": v.element_affinity
            } for k, v in self.skill_tree.items()},
            "skill_unlock_order": self.skill_unlock_order,
            "unique_mechanics": self.unique_mechanics,
            "synergy_schools": self.synergy_schools
        }

class SchoolManager:
    """流派管理器
    
    管理所有修真流派，处理流派选择、技能解锁、协同效果等
    """
    
    def __init__(self):
        self.schools: Dict[str, CultivationSchool] = {}
        self._initialize_schools()
    
    def _initialize_schools(self) -> None:
        """初始化所有流派"""
        # 剑修
        sword_school = CultivationSchool(
            school_id=SchoolType.SWORD.value,
            name="剑修",
            element_affinity="金",
            description="以剑为道，追求极致的攻击力和敏捷。擅长单体爆发和连击。"
        )
        
        # 法修
        spell_school = CultivationSchool(
            school_id=SchoolType.SPELL.value,
            name="法修",
            element_affinity="火",
            description="精通各种法术，拥有强大的元素攻击能力和范围伤害。"
        )
        
        # 体修
        body_school = CultivationSchool(
            school_id=SchoolType.BODY.value,
            name="体修",
            element_affinity="土",
            description="锻炼肉身，拥有强大的生命力和防御力，近战能力出众。"
        )
        
        # 丹修
        pill_school = CultivationSchool(
            school_id=SchoolType.PILL.value,
            name="丹修",
            element_affinity="木",
            description="精通炼丹之术，拥有强大的辅助和治疗能力。"
        )
        
        # 阵修
        formation_school = CultivationSchool(
            school_id=SchoolType.FORMATION.value,
            name="阵修",
            element_affinity="土",
            description="精通阵法，能够控制战场，为团队提供强大的增益效果。"
        )
        
        self.schools = {
            SchoolType.SWORD.value: sword_school,
            SchoolType.SPELL.value: spell_school,
            SchoolType.BODY.value: body_school,
            SchoolType.PILL.value: pill_school,
            SchoolType.FORMATION.value: formation_school
        }
    
    def get_school(self, school_id: str) -> Optional[CultivationSchool]:
        """获取指定流派"""
        return self.schools.get(school_id)
    
    def get_all_schools(self) -> Dict[str, CultivationSchool]:
        """获取所有流派"""
        return self.schools.copy()
    
    def get_school_names(self) -> Dict[str, str]:
        """获取所有流派名称"""
        return {school_id: school.name for school_id, school in self.schools.items()}
    
    def calculate_character_attributes(self, school_id: str, level: int, 
                                    base_attributes: Dict[str, float]) -> Dict[str, float]:
        """计算角色的最终属性（基础属性 + 流派加成）"""
        school = self.get_school(school_id)
        if not school:
            return base_attributes.copy()
        
        final_attributes = base_attributes.copy()
        school_bonuses = school.get_attribute_bonuses(level)
        
        for attr, bonus in school_bonuses.items():
            if attr in final_attributes:
                final_attributes[attr] += bonus
            else:
                final_attributes[attr] = bonus
        
        return final_attributes
    
    def get_available_skills(self, school_id: str, character_level: int, 
                           unlocked_skills: Set[str] = None) -> List[Skill]:
        """获取角色可解锁的技能"""
        school = self.get_school(school_id)
        if not school:
            return []
        
        if unlocked_skills is None:
            unlocked_skills = set()
        
        available_skill_ids = school.unlock_skills(character_level, unlocked_skills)
        return [school.get_skill_info(skill_id) for skill_id in available_skill_ids 
                if school.get_skill_info(skill_id)]
    
    def calculate_multi_school_synergy(self, primary_school: str, 
                                     secondary_schools: List[str]) -> Dict[str, float]:
        """计算多流派协同效果"""
        primary = self.get_school(primary_school)
        if not primary:
            return {}
        
        total_synergy = {}
        
        # 计算主流派与各副流派的协同
        for secondary_school in secondary_schools:
            if secondary_school == primary_school:
                continue
                
            synergy = primary.calculate_synergy_bonus([secondary_school])
            for key, value in synergy.items():
                if key in total_synergy:
                    total_synergy[key] += value
                else:
                    total_synergy[key] = value
        
        # 多流派惩罚（防止全能角色）
        if len(secondary_schools) > 1:
            penalty_factor = 0.8 ** (len(secondary_schools) - 1)
            for key in total_synergy:
                total_synergy[key] *= penalty_factor
        
        return total_synergy
    
    def recommend_equipment(self, school_id: str, equipment_list: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], float]]:
        """为指定流派推荐装备"""
        school = self.get_school(school_id)
        if not school:
            return []
        
        recommendations = []
        for equipment in equipment_list:
            stats = equipment.get("stats", {})
            score = school.get_equipment_score(stats)
            recommendations.append((equipment, score))
        
        # 按评分排序
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations
    
    def validate_school_progression(self, school_id: str, character_level: int, 
                                  unlocked_skills: Set[str]) -> Tuple[bool, List[str]]:
        """验证流派进度的合理性"""
        school = self.get_school(school_id)
        if not school:
            return False, ["无效的流派ID"]
        
        issues = []
        
        # 检查技能解锁顺序
        for skill_id in unlocked_skills:
            skill = school.get_skill_info(skill_id)
            if not skill:
                issues.append(f"无效的技能ID: {skill_id}")
                continue
            
            # 检查等级要求
            if character_level < skill.level_requirement:
                issues.append(f"技能 {skill.name} 需要等级 {skill.level_requirement}，当前等级 {character_level}")
            
            # 检查前置技能
            for prereq in skill.prerequisites:
                if prereq not in unlocked_skills:
                    prereq_skill = school.get_skill_info(prereq)
                    prereq_name = prereq_skill.name if prereq_skill else prereq
                    issues.append(f"技能 {skill.name} 需要前置技能: {prereq_name}")
        
        return len(issues) == 0, issues
    
    def export_school_data(self, filepath: str) -> bool:
        """导出流派数据到文件"""
        try:
            school_data = {}
            for school_id, school in self.schools.items():
                school_data[school_id] = school.to_dict()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(school_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"导出流派数据失败: {e}")
            return False
    
    def get_school_compatibility_matrix(self) -> Dict[str, Dict[str, float]]:
        """获取流派兼容性矩阵"""
        compatibility = {}
        
        for school_id, school in self.schools.items():
            compatibility[school_id] = {}
            
            for other_id, other_school in self.schools.items():
                if school_id == other_id:
                    compatibility[school_id][other_id] = 1.0  # 自身兼容性最高
                elif other_id in school.synergy_schools:
                    compatibility[school_id][other_id] = 0.8  # 有协同效果
                else:
                    # 基于元素亲和度计算兼容性
                    if school.element_affinity == other_school.element_affinity:
                        compatibility[school_id][other_id] = 0.6  # 同元素中等兼容
                    else:
                        compatibility[school_id][other_id] = 0.4  # 不同元素低兼容
        
        return compatibility


# 全局流派管理器实例
_global_school_manager: Optional[SchoolManager] = None


def get_school_manager() -> SchoolManager:
    """获取全局流派管理器实例"""
    global _global_school_manager
    if _global_school_manager is None:
        _global_school_manager = SchoolManager()
    return _global_school_manager


def initialize_school_system() -> SchoolManager:
    """初始化流派系统"""
    global _global_school_manager
    _global_school_manager = SchoolManager()
    return _global_school_manager