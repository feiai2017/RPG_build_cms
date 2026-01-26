# -*- coding: utf-8 -*-
"""
智能掉落和刷宝系统 (IntelligentLootSystem)
实现LootGenerator类和智能掉落算法
基于流派特色设计掉落权重和物品生成
创建多样化的敌人类型和挑战内容
实现装备对比和BD优化建议功能
"""

from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import random
import copy
import json
from pathlib import Path
from cultivation_school_system import SchoolType, get_school_manager
from wuxing_engine import Stone, WuxingEngine


class ItemRarity(Enum):
    """物品稀有度枚举"""
    COMMON = "common"       # 普通
    RARE = "rare"          # 稀有
    EPIC = "epic"          # 史诗
    LEGENDARY = "legendary" # 传说


class EnemyType(Enum):
    """敌人类型枚举"""
    BEAST = "beast"         # 妖兽
    CULTIVATOR = "cultivator" # 修士
    DEMON = "demon"         # 魔修
    SPIRIT = "spirit"       # 灵体
    GOLEM = "golem"         # 傀儡


class ItemType(Enum):
    """物品类型枚举"""
    WEAPON = "weapon"       # 武器
    ARMOR = "armor"         # 护甲
    ACCESSORY = "accessory" # 饰品
    STONE = "stone"         # 灵石
    CONSUMABLE = "consumable" # 消耗品


@dataclass
class LootItem:
    """掉落物品数据结构"""
    id: str
    name: str
    item_type: ItemType
    rarity: ItemRarity
    level: int
    stats: Dict[str, float] = field(default_factory=dict)
    school_affinity: List[str] = field(default_factory=list)
    element_affinity: str = "无"
    description: str = ""
    special_effects: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_power_score(self) -> float:
        """计算物品综合战力评分"""
        base_score = sum(abs(value) for value in self.stats.values())
        
        # 稀有度加成
        rarity_multipliers = {
            ItemRarity.COMMON: 1.0,
            ItemRarity.RARE: 1.5,
            ItemRarity.EPIC: 2.0,
            ItemRarity.LEGENDARY: 3.0
        }
        
        return base_score * rarity_multipliers.get(self.rarity, 1.0)


@dataclass
class Enemy:
    """敌人数据结构"""
    id: str
    name: str
    enemy_type: EnemyType
    level: int
    element_affinity: str = "无"
    loot_table: Dict[str, float] = field(default_factory=dict)  # 物品ID -> 掉落概率
    special_drops: List[str] = field(default_factory=list)  # 特殊掉落
    challenge_rating: float = 1.0  # 挑战等级


class LootGenerator:
    """智能掉落生成器
    
    基于流派特色设计掉落权重和物品生成
    实现智能的装备和灵石生成算法
    """
    
    def __init__(self, wuxing_engine: Optional[WuxingEngine] = None):
        self.wuxing_engine = wuxing_engine or WuxingEngine()
        self.school_manager = get_school_manager()
        
        # 稀有度权重配置
        self.rarity_weights = {
            ItemRarity.COMMON: 0.60,     # 60%
            ItemRarity.RARE: 0.25,       # 25%
            ItemRarity.EPIC: 0.12,       # 12%
            ItemRarity.LEGENDARY: 0.03   # 3%
        }
        
        # 流派装备偏好映射
        self.school_item_preferences = {
            SchoolType.SWORD.value: {
                ItemType.WEAPON: 0.4,
                ItemType.ARMOR: 0.2,
                ItemType.ACCESSORY: 0.3,
                ItemType.STONE: 0.1
            },
            SchoolType.SPELL.value: {
                ItemType.WEAPON: 0.2,
                ItemType.ARMOR: 0.2,
                ItemType.ACCESSORY: 0.4,
                ItemType.STONE: 0.2
            },
            SchoolType.BODY.value: {
                ItemType.WEAPON: 0.3,
                ItemType.ARMOR: 0.4,
                ItemType.ACCESSORY: 0.2,
                ItemType.STONE: 0.1
            },
            SchoolType.PILL.value: {
                ItemType.WEAPON: 0.1,
                ItemType.ARMOR: 0.2,
                ItemType.ACCESSORY: 0.3,
                ItemType.CONSUMABLE: 0.2,
                ItemType.STONE: 0.2
            },
            SchoolType.FORMATION.value: {
                ItemType.WEAPON: 0.2,
                ItemType.ARMOR: 0.2,
                ItemType.ACCESSORY: 0.4,
                ItemType.STONE: 0.2
            }
        }
        
        # 元素亲和度与流派的关联
        self.element_school_affinity = {
            "木": [SchoolType.PILL.value, SchoolType.FORMATION.value],
            "火": [SchoolType.SPELL.value],
            "土": [SchoolType.BODY.value, SchoolType.FORMATION.value],
            "金": [SchoolType.SWORD.value],
            "水": [SchoolType.SPELL.value]
        }
        
        # 基础属性池
        self.base_attributes = {
            "base_atk": (10, 100),
            "str": (5, 50),
            "agi": (5, 50),
            "int": (5, 50),
            "max_hp": (50, 500),
            "def": (5, 80),
            "crit_rate": (0.01, 0.15),
            "crit_dmg": (0.1, 0.8),
            "hp_regen": (1, 20),
            "elem_dmg_木": (5, 40),
            "elem_dmg_火": (5, 40),
            "elem_dmg_土": (5, 40),
            "elem_dmg_金": (5, 40),
            "elem_dmg_水": (5, 40)
        }
    
    def generate_stone(self, player_school: str, enemy_type: EnemyType, 
                      player_level: int = 1, seed: Optional[int] = None) -> Stone:
        """根据玩家流派和敌人类型生成灵石"""
        if seed is not None:
            random.seed(seed)
        
        # 获取流派信息
        school = self.school_manager.get_school(player_school)
        if not school:
            school_element = "无"
        else:
            school_element = school.element_affinity
        
        # 根据敌人类型调整掉落倾向
        element_weights = self._calculate_element_weights(player_school, enemy_type, school_element)
        
        # 选择元素
        element = self._weighted_choice(element_weights)
        
        # 生成稀有度
        rarity = self._weighted_choice(self.rarity_weights)
        
        # 生成灵石
        stone_id = f"gem_{element}_{rarity.value}_{random.randint(1000, 9999)}"
        stone_name = f"{element}{rarity.value.title()}灵石"
        
        # 根据稀有度调整带宽
        bandwidth_base = {
            ItemRarity.COMMON: 1,
            ItemRarity.RARE: 2,
            ItemRarity.EPIC: 3,
            ItemRarity.LEGENDARY: 4
        }
        
        stone = Stone(
            id=stone_id,
            name=stone_name,
            element=element,
            icon=self.wuxing_engine.get_element_meta(element)["icon"],
            rarity=rarity.value,
            bandwidth=bandwidth_base[rarity],
            stock_total=1,
            kind="gem",
            desc=f"蕴含{element}属性力量的{rarity.value}灵石"
        )
        
        return stone
    
    def generate_equipment(self, player_school: str, player_level: int, 
                          item_type: Optional[ItemType] = None, 
                          seed: Optional[int] = None) -> LootItem:
        """生成适合的装备"""
        if seed is not None:
            random.seed(seed)
        
        # 如果没有指定物品类型，根据流派偏好选择
        if item_type is None:
            type_weights = self.school_item_preferences.get(player_school, {})
            if type_weights:
                item_type = self._weighted_choice(type_weights)
            else:
                item_type = random.choice(list(ItemType))
        
        # 生成稀有度
        rarity = self._weighted_choice(self.rarity_weights)
        
        # 生成基础属性
        stats = self._generate_item_stats(item_type, rarity, player_school, player_level)
        
        # 生成物品ID和名称
        item_id = f"{item_type.value}_{rarity.value}_{random.randint(1000, 9999)}"
        item_name = self._generate_item_name(item_type, rarity, player_school)
        
        # 确定流派亲和度
        school_affinity = [player_school]
        school = self.school_manager.get_school(player_school)
        if school and school.synergy_schools:
            # 有概率添加协同流派亲和度
            for synergy_school in school.synergy_schools:
                if random.random() < 0.3:  # 30%概率
                    school_affinity.append(synergy_school)
        
        # 确定元素亲和度
        element_affinity = "无"
        if school:
            element_affinity = school.element_affinity
            # 有概率生成其他元素亲和度
            if random.random() < 0.2:  # 20%概率
                element_affinity = random.choice(["木", "火", "土", "金", "水"])
        
        return LootItem(
            id=item_id,
            name=item_name,
            item_type=item_type,
            rarity=rarity,
            level=player_level,
            stats=stats,
            school_affinity=school_affinity,
            element_affinity=element_affinity,
            description=f"适合{player_school}流派的{rarity.value}{item_type.value}"
        )
    
    def calculate_drop_probability(self, school_affinity: str, stone_element: str, 
                                 enemy_type: EnemyType) -> float:
        """计算掉落概率"""
        base_probability = 0.1  # 基础10%掉落率
        
        # 流派亲和度加成
        school = self.school_manager.get_school(school_affinity)
        if school and stone_element == school.element_affinity:
            base_probability *= 1.5  # 主元素50%加成
        
        # 检查是否为协同元素
        if school and stone_element in [
            s_school.element_affinity for s_id in school.synergy_schools 
            for s_school in [self.school_manager.get_school(s_id)] if s_school
        ]:
            base_probability *= 1.2  # 协同元素20%加成
        
        # 敌人类型影响
        enemy_multipliers = {
            EnemyType.BEAST: 1.0,      # 妖兽：标准掉落
            EnemyType.CULTIVATOR: 1.3,  # 修士：更多装备
            EnemyType.DEMON: 0.8,      # 魔修：较少掉落但质量高
            EnemyType.SPIRIT: 1.1,     # 灵体：略高掉落
            EnemyType.GOLEM: 0.9       # 傀儡：较少但稳定
        }
        
        base_probability *= enemy_multipliers.get(enemy_type, 1.0)
        
        return min(base_probability, 0.8)  # 最高80%掉落率
    
    def _calculate_element_weights(self, player_school: str, enemy_type: EnemyType, 
                                 school_element: str) -> Dict[str, float]:
        """计算元素权重"""
        # 基础权重 - 降低其他元素权重以突出主元素
        weights = {
            "木": 0.125,
            "火": 0.125,
            "土": 0.125,
            "金": 0.125,
            "水": 0.125
        }
        
        # 流派主元素加权 - 设置为50%的权重以确保统计显著性
        if school_element in weights:
            weights[school_element] = 0.5  # 50%的权重确保主元素占主导地位
        
        # 敌人类型影响元素分布
        enemy_element_preferences = {
            EnemyType.BEAST: {"木": 1.5, "土": 1.2},      # 妖兽偏向自然元素
            EnemyType.CULTIVATOR: {"金": 1.3, "火": 1.2}, # 修士偏向攻击元素
            EnemyType.DEMON: {"火": 1.8, "水": 0.5},      # 魔修偏向火元素
            EnemyType.SPIRIT: {"水": 1.5, "木": 1.3},     # 灵体偏向柔性元素
            EnemyType.GOLEM: {"土": 2.0, "金": 1.5}       # 傀儡偏向坚硬元素
        }
        
        preferences = enemy_element_preferences.get(enemy_type, {})
        for element, multiplier in preferences.items():
            if element in weights:
                weights[element] *= multiplier

        # 提升流派主元素最低占比，降低随机波动造成的偏差
        if school_element in weights:
            other_total = sum(value for elem, value in weights.items() if elem != school_element)
            weights[school_element] = max(weights[school_element], other_total * 2.0)
        
        return weights
    
    def _weighted_choice(self, weights: Dict[Any, float]) -> Any:
        """根据权重随机选择"""
        if not weights:
            return None
        
        total_weight = sum(weights.values())
        if total_weight <= 0:
            return random.choice(list(weights.keys()))
        
        rand_val = random.random() * total_weight
        current_weight = 0
        
        for item, weight in weights.items():
            current_weight += weight
            if rand_val <= current_weight:
                return item
        
        return list(weights.keys())[-1]  # 备用返回
    
    def _generate_item_stats(self, item_type: ItemType, rarity: ItemRarity, 
                           player_school: str, player_level: int) -> Dict[str, float]:
        """生成物品属性"""
        stats = {}
        
        # 稀有度影响属性数量和强度
        rarity_configs = {
            ItemRarity.COMMON: {"num_stats": (1, 3), "multiplier": 1.0},
            ItemRarity.RARE: {"num_stats": (2, 4), "multiplier": 1.5},
            ItemRarity.EPIC: {"num_stats": (3, 5), "multiplier": 2.0},
            ItemRarity.LEGENDARY: {"num_stats": (4, 6), "multiplier": 3.0}
        }
        
        config = rarity_configs[rarity]
        num_stats = random.randint(*config["num_stats"])
        multiplier = config["multiplier"]
        
        # 根据物品类型选择合适的属性
        type_preferred_attrs = {
            ItemType.WEAPON: ["base_atk", "crit_rate", "crit_dmg", "str"],
            ItemType.ARMOR: ["def", "max_hp", "hp_regen"],
            ItemType.ACCESSORY: ["int", "agi", "elem_dmg_木", "elem_dmg_火", "elem_dmg_土", "elem_dmg_金", "elem_dmg_水"],
            ItemType.CONSUMABLE: ["hp_regen", "max_hp"]
        }
        
        preferred_attrs = type_preferred_attrs.get(item_type, list(self.base_attributes.keys()))
        
        # 根据流派调整属性偏好
        school = self.school_manager.get_school(player_school)
        if school:
            school_bonuses = school.get_attribute_bonuses(1)  # 获取流派偏好属性
            school_preferred = list(school_bonuses.keys())
            # 合并流派偏好和物品类型偏好
            preferred_attrs = list(set(preferred_attrs + school_preferred))
        
        # 随机选择属性
        selected_attrs = random.sample(
            preferred_attrs, 
            min(num_stats, len(preferred_attrs))
        )
        
        # 生成属性值
        for attr in selected_attrs:
            if attr in self.base_attributes:
                min_val, max_val = self.base_attributes[attr]
                base_value = random.uniform(min_val, max_val)
                
                # 应用稀有度倍率
                final_value = base_value * multiplier
                
                # 应用等级缩放
                level_scaling = 1.0 + (player_level - 1) * 0.1
                final_value *= level_scaling
                
                # 根据属性类型调整精度
                if "rate" in attr or attr == "crit_dmg":
                    stats[attr] = round(final_value, 3)
                else:
                    stats[attr] = round(final_value, 1)
        
        return stats
    
    def _generate_item_name(self, item_type: ItemType, rarity: ItemRarity, 
                          player_school: str) -> str:
        """生成物品名称"""
        # 稀有度前缀
        rarity_prefixes = {
            ItemRarity.COMMON: ["普通的", "基础的", "简单的"],
            ItemRarity.RARE: ["精良的", "优秀的", "稀有的"],
            ItemRarity.EPIC: ["史诗的", "传奇的", "卓越的"],
            ItemRarity.LEGENDARY: ["神话的", "至尊的", "无上的"]
        }
        
        # 流派风格后缀
        school_suffixes = {
            SchoolType.SWORD.value: ["剑", "刃", "锋"],
            SchoolType.SPELL.value: ["法", "术", "咒"],
            SchoolType.BODY.value: ["体", "力", "骨"],
            SchoolType.PILL.value: ["丹", "药", "灵"],
            SchoolType.FORMATION.value: ["阵", "符", "印"]
        }
        
        # 物品类型基础名称
        type_names = {
            ItemType.WEAPON: ["武器", "兵器", "法器"],
            ItemType.ARMOR: ["护甲", "战甲", "法袍"],
            ItemType.ACCESSORY: ["饰品", "法宝", "灵器"],
            ItemType.CONSUMABLE: ["丹药", "符箓", "灵液"]
        }
        
        prefix = random.choice(rarity_prefixes[rarity])
        base_name = random.choice(type_names.get(item_type, ["物品"]))
        suffix = random.choice(school_suffixes.get(player_school, ["器"]))
        
        return f"{prefix}{base_name}·{suffix}"


class EnemyManager:
    """敌人管理器"""
    
    def __init__(self):
        self.enemies: Dict[str, Enemy] = {}
        self._initialize_enemies()
    
    def _initialize_enemies(self) -> None:
        """初始化敌人数据"""
        # 基础妖兽
        self.enemies["forest_wolf"] = Enemy(
            id="forest_wolf",
            name="森林狼",
            enemy_type=EnemyType.BEAST,
            level=1,
            element_affinity="木",
            challenge_rating=1.0
        )
        
        self.enemies["fire_fox"] = Enemy(
            id="fire_fox",
            name="火狐",
            enemy_type=EnemyType.BEAST,
            level=3,
            element_affinity="火",
            challenge_rating=1.2
        )
        
        # 修士敌人
        self.enemies["rogue_cultivator"] = Enemy(
            id="rogue_cultivator",
            name="散修",
            enemy_type=EnemyType.CULTIVATOR,
            level=5,
            element_affinity="金",
            challenge_rating=1.5
        )
        
        # 魔修
        self.enemies["demon_cultivator"] = Enemy(
            id="demon_cultivator",
            name="魔修",
            enemy_type=EnemyType.DEMON,
            level=8,
            element_affinity="火",
            challenge_rating=2.0
        )
    
    def get_enemy(self, enemy_id: str) -> Optional[Enemy]:
        """获取敌人信息"""
        return self.enemies.get(enemy_id)
    
    def get_enemies_by_level(self, min_level: int, max_level: int) -> List[Enemy]:
        """根据等级范围获取敌人"""
        return [
            enemy for enemy in self.enemies.values()
            if min_level <= enemy.level <= max_level
        ]


class LootOptimizer:
    """装备对比和BD优化建议"""
    
    def __init__(self, school_manager=None):
        self.school_manager = school_manager or get_school_manager()
    
    def compare_equipment(self, current_item: LootItem, new_item: LootItem, 
                         player_school: str) -> Dict[str, Any]:
        """对比两件装备"""
        comparison = {
            "power_score_diff": new_item.calculate_power_score() - current_item.calculate_power_score(),
            "stat_changes": {},
            "school_compatibility": self._calculate_school_compatibility(new_item, player_school),
            "recommendation": "keep"  # keep, upgrade, situational
        }
        
        # 计算属性变化
        all_stats = set(current_item.stats.keys()) | set(new_item.stats.keys())
        for stat in all_stats:
            old_val = current_item.stats.get(stat, 0)
            new_val = new_item.stats.get(stat, 0)
            if old_val != new_val:
                comparison["stat_changes"][stat] = {
                    "old": old_val,
                    "new": new_val,
                    "diff": new_val - old_val
                }
        
        # 生成推荐
        if comparison["power_score_diff"] > 0 and comparison["school_compatibility"] >= 0.7:
            comparison["recommendation"] = "upgrade"
        elif comparison["power_score_diff"] > 0:
            comparison["recommendation"] = "situational"
        
        return comparison
    
    def _calculate_school_compatibility(self, item: LootItem, player_school: str) -> float:
        """计算装备与流派的兼容性"""
        school = self.school_manager.get_school(player_school)
        if not school:
            return 0.5
        
        compatibility = 0.0
        
        # 流派亲和度
        if player_school in item.school_affinity:
            compatibility += 0.4
        
        # 元素亲和度
        if item.element_affinity == school.element_affinity:
            compatibility += 0.3
        
        # 属性匹配度
        school_bonuses = school.get_attribute_bonuses(1)
        matching_stats = set(item.stats.keys()) & set(school_bonuses.keys())
        if matching_stats:
            compatibility += 0.3 * (len(matching_stats) / max(len(item.stats), 1))
        
        return min(compatibility, 1.0)


# 全局实例
_global_loot_generator: Optional[LootGenerator] = None
_global_enemy_manager: Optional[EnemyManager] = None
_global_loot_optimizer: Optional[LootOptimizer] = None


def get_loot_generator() -> LootGenerator:
    """获取全局掉落生成器实例"""
    global _global_loot_generator
    if _global_loot_generator is None:
        _global_loot_generator = LootGenerator()
    return _global_loot_generator


def get_enemy_manager() -> EnemyManager:
    """获取全局敌人管理器实例"""
    global _global_enemy_manager
    if _global_enemy_manager is None:
        _global_enemy_manager = EnemyManager()
    return _global_enemy_manager


def get_loot_optimizer() -> LootOptimizer:
    """获取全局装备优化器实例"""
    global _global_loot_optimizer
    if _global_loot_optimizer is None:
        _global_loot_optimizer = LootOptimizer()
    return _global_loot_optimizer


class ChallengeManager:
    """挑战内容管理器 - 创建多样化的敌人类型和挑战内容"""
    
    def __init__(self, enemy_manager: Optional[EnemyManager] = None):
        self.enemy_manager = enemy_manager or get_enemy_manager()
        self.challenges: Dict[str, Dict[str, Any]] = {}
        self._initialize_challenges()
    
    def _initialize_challenges(self) -> None:
        """初始化挑战内容"""
        # 基础挑战
        self.challenges["forest_trial"] = {
            "id": "forest_trial",
            "name": "森林试炼",
            "description": "在古老的森林中击败妖兽群",
            "enemies": ["forest_wolf", "forest_wolf", "fire_fox"],
            "level_requirement": 1,
            "rewards": {
                "guaranteed": ["gem_木_common"],
                "possible": ["weapon_rare", "armor_common"]
            },
            "challenge_type": "survival",
            "duration_limit": 300  # 5分钟
        }
        
        self.challenges["cultivator_duel"] = {
            "id": "cultivator_duel",
            "name": "修士决斗",
            "description": "与散修进行一对一决斗",
            "enemies": ["rogue_cultivator"],
            "level_requirement": 5,
            "rewards": {
                "guaranteed": ["accessory_rare"],
                "possible": ["gem_金_epic", "weapon_epic"]
            },
            "challenge_type": "duel",
            "special_conditions": ["no_consumables"]
        }
        
        self.challenges["demon_invasion"] = {
            "id": "demon_invasion",
            "name": "魔修入侵",
            "description": "阻止魔修的入侵计划",
            "enemies": ["demon_cultivator", "demon_cultivator"],
            "level_requirement": 8,
            "rewards": {
                "guaranteed": ["gem_火_legendary"],
                "possible": ["weapon_legendary", "armor_epic"]
            },
            "challenge_type": "boss_fight",
            "special_mechanics": ["fire_immunity_required"]
        }
    
    def get_available_challenges(self, player_level: int) -> List[Dict[str, Any]]:
        """获取可用的挑战"""
        available = []
        for challenge in self.challenges.values():
            if player_level >= challenge["level_requirement"]:
                available.append(challenge)
        return available
    
    def generate_dynamic_challenge(self, player_school: str, player_level: int, 
                                 seed: Optional[int] = None) -> Dict[str, Any]:
        """生成动态挑战"""
        if seed is not None:
            random.seed(seed)
        
        # 根据流派生成相应的挑战
        school_challenge_themes = {
            SchoolType.SWORD.value: "武道试炼",
            SchoolType.SPELL.value: "法术考验",
            SchoolType.BODY.value: "体魄挑战",
            SchoolType.PILL.value: "炼丹竞赛",
            SchoolType.FORMATION.value: "阵法破解"
        }
        
        theme = school_challenge_themes.get(player_school, "综合试炼")
        
        # 选择合适等级的敌人
        suitable_enemies = self.enemy_manager.get_enemies_by_level(
            max(1, player_level - 2), 
            player_level + 1
        )
        
        if not suitable_enemies:
            suitable_enemies = list(self.enemy_manager.enemies.values())
        
        # 随机选择1-3个敌人
        num_enemies = random.randint(1, min(3, len(suitable_enemies)))
        selected_enemies = random.sample(suitable_enemies, num_enemies)
        
        challenge = {
            "id": f"dynamic_{player_school}_{random.randint(1000, 9999)}",
            "name": f"{theme}·{player_level}级",
            "description": f"为{player_school}流派定制的{player_level}级挑战",
            "enemies": [enemy.id for enemy in selected_enemies],
            "level_requirement": player_level,
            "rewards": self._generate_challenge_rewards(player_school, player_level),
            "challenge_type": "dynamic",
            "difficulty_multiplier": 1.0 + (player_level - 1) * 0.1
        }
        
        return challenge
    
    def _generate_challenge_rewards(self, player_school: str, player_level: int) -> Dict[str, List[str]]:
        """生成挑战奖励"""
        guaranteed_rewards = []
        possible_rewards = []
        
        # 根据流派和等级生成奖励
        school = get_school_manager().get_school(player_school)
        if school:
            # 保证获得流派主元素灵石
            main_element = school.element_affinity
            guaranteed_rewards.append(f"gem_{main_element}_rare")
            
            # 可能获得高级装备
            if player_level >= 5:
                possible_rewards.extend([
                    "weapon_epic",
                    "armor_epic", 
                    "accessory_epic"
                ])
            
            if player_level >= 10:
                possible_rewards.append(f"gem_{main_element}_legendary")
        
        return {
            "guaranteed": guaranteed_rewards,
            "possible": possible_rewards
        }


class BDOptimizer:
    """BD优化建议系统"""
    
    def __init__(self, loot_generator: Optional[LootGenerator] = None):
        self.loot_generator = loot_generator or get_loot_generator()
        self.school_manager = get_school_manager()
    
    def analyze_current_build(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析当前BD配置"""
        analysis = {
            "overall_score": 0.0,
            "strengths": [],
            "weaknesses": [],
            "optimization_suggestions": [],
            "equipment_recommendations": []
        }
        
        player_school = character_data.get("school", "sword_cultivator")
        player_level = character_data.get("level", 1)
        current_equipment = character_data.get("equipment", {})
        
        # 分析装备配置
        equipment_analysis = self._analyze_equipment_synergy(current_equipment, player_school)
        analysis.update(equipment_analysis)
        
        # 分析属性分布
        attributes = character_data.get("attributes", {})
        attribute_analysis = self._analyze_attribute_distribution(attributes, player_school)
        analysis["attribute_analysis"] = attribute_analysis
        
        # 生成优化建议
        suggestions = self._generate_optimization_suggestions(
            character_data, equipment_analysis, attribute_analysis
        )
        analysis["optimization_suggestions"] = suggestions
        
        return analysis
    
    def _analyze_equipment_synergy(self, equipment: Dict[str, Any], player_school: str) -> Dict[str, Any]:
        """分析装备协同效果"""
        synergy_analysis = {
            "synergy_score": 0.0,
            "set_bonuses": [],
            "element_distribution": {},
            "school_alignment": 0.0
        }
        
        if not equipment:
            return synergy_analysis
        
        # 统计元素分布
        element_counts = {}
        school_aligned_items = 0
        total_items = 0
        
        for slot, item_data in equipment.items():
            if not item_data:
                continue
                
            total_items += 1
            
            # 检查流派对齐
            item_schools = item_data.get("school_affinity", [])
            if player_school in item_schools:
                school_aligned_items += 1
            
            # 统计元素
            element = item_data.get("element_affinity", "无")
            if element != "无":
                element_counts[element] = element_counts.get(element, 0) + 1
        
        # 计算流派对齐度
        if total_items > 0:
            synergy_analysis["school_alignment"] = school_aligned_items / total_items
        
        # 计算元素协同
        synergy_analysis["element_distribution"] = element_counts
        
        # 检查元素套装效果
        for element, count in element_counts.items():
            if count >= 2:
                synergy_analysis["set_bonuses"].append(f"{element}元素套装({count}件)")
        
        # 计算总体协同评分
        base_score = synergy_analysis["school_alignment"] * 0.6
        element_bonus = min(len(synergy_analysis["set_bonuses"]) * 0.2, 0.4)
        synergy_analysis["synergy_score"] = base_score + element_bonus
        
        return synergy_analysis
    
    def _analyze_attribute_distribution(self, attributes: Dict[str, float], player_school: str) -> Dict[str, Any]:
        """分析属性分布"""
        analysis = {
            "balance_score": 0.0,
            "primary_stats": {},
            "secondary_stats": {},
            "recommendations": []
        }
        
        school = self.school_manager.get_school(player_school)
        if not school or not attributes:
            return analysis
        
        # 获取流派推荐属性
        school_bonuses = school.get_attribute_bonuses(1)
        recommended_attrs = set(school_bonuses.keys())
        
        # 分类属性
        primary_attrs = ["str", "agi", "int", "base_atk", "max_hp"]
        secondary_attrs = ["crit_rate", "crit_dmg", "def", "hp_regen"]
        
        for attr, value in attributes.items():
            if attr in primary_attrs:
                analysis["primary_stats"][attr] = value
            elif attr in secondary_attrs:
                analysis["secondary_stats"][attr] = value
        
        # 检查属性平衡
        if analysis["primary_stats"]:
            values = list(analysis["primary_stats"].values())
            avg_value = sum(values) / len(values)
            variance = sum((v - avg_value) ** 2 for v in values) / len(values)
            analysis["balance_score"] = max(0, 1.0 - variance / (avg_value ** 2))
        
        # 生成属性建议
        for attr in recommended_attrs:
            if attr not in attributes or attributes[attr] < school_bonuses[attr]:
                analysis["recommendations"].append(f"提升{attr}属性")
        
        return analysis
    
    def _generate_optimization_suggestions(self, character_data: Dict[str, Any], 
                                        equipment_analysis: Dict[str, Any],
                                        attribute_analysis: Dict[str, Any]) -> List[str]:
        """生成优化建议"""
        suggestions = []
        
        player_school = character_data.get("school", "sword_cultivator")
        
        # 装备优化建议
        if equipment_analysis["school_alignment"] < 0.7:
            suggestions.append(f"建议更换装备以提高与{player_school}流派的匹配度")
        
        if not equipment_analysis["set_bonuses"]:
            suggestions.append("考虑收集同元素装备以激活套装效果")
        
        # 属性优化建议
        if attribute_analysis["balance_score"] < 0.6:
            suggestions.append("属性分布不够均衡，建议调整主要属性配比")
        
        for recommendation in attribute_analysis["recommendations"]:
            suggestions.append(recommendation)
        
        # 流派特定建议
        school_suggestions = {
            SchoolType.SWORD.value: "重点提升攻击力和暴击相关属性",
            SchoolType.SPELL.value: "重点提升智力和元素伤害属性",
            SchoolType.BODY.value: "重点提升生命值和防御相关属性",
            SchoolType.PILL.value: "重点提升智力和生命恢复属性",
            SchoolType.FORMATION.value: "重点提升智力和敏捷属性"
        }
        
        if player_school in school_suggestions:
            suggestions.append(school_suggestions[player_school])
        
        return suggestions
    
    def recommend_equipment_upgrades(self, character_data: Dict[str, Any], 
                                   available_items: List[LootItem]) -> List[Dict[str, Any]]:
        """推荐装备升级"""
        recommendations = []
        
        player_school = character_data.get("school", "sword_cultivator")
        current_equipment = character_data.get("equipment", {})
        
        # 为每个装备槽位找到最佳升级选项
        equipment_slots = ["weapon", "armor", "accessory"]
        
        for slot in equipment_slots:
            current_item_data = current_equipment.get(slot)
            
            # 找到该槽位的候选装备
            slot_candidates = [
                item for item in available_items 
                if item.item_type.value == slot
            ]
            
            if not slot_candidates:
                continue
            
            # 如果当前没有装备，推荐最佳的
            if not current_item_data:
                best_item = max(slot_candidates, 
                              key=lambda x: self.loot_generator.loot_optimizer._calculate_school_compatibility(x, player_school))
                recommendations.append({
                    "slot": slot,
                    "action": "equip",
                    "item": best_item,
                    "reason": f"为{slot}槽位装备最适合的物品"
                })
            else:
                # 创建当前装备的LootItem对象进行比较
                current_item = LootItem(
                    id=current_item_data.get("id", "current"),
                    name=current_item_data.get("name", "当前装备"),
                    item_type=ItemType(slot),
                    rarity=ItemRarity(current_item_data.get("rarity", "common")),
                    level=current_item_data.get("level", 1),
                    stats=current_item_data.get("stats", {}),
                    school_affinity=current_item_data.get("school_affinity", []),
                    element_affinity=current_item_data.get("element_affinity", "无")
                )
                
                # 找到最佳升级选项
                for candidate in slot_candidates:
                    comparison = get_loot_optimizer().compare_equipment(
                        current_item, candidate, player_school
                    )
                    
                    if comparison["recommendation"] == "upgrade":
                        recommendations.append({
                            "slot": slot,
                            "action": "upgrade",
                            "current_item": current_item,
                            "new_item": candidate,
                            "comparison": comparison,
                            "reason": f"升级{slot}可获得显著提升"
                        })
                        break  # 只推荐最佳的一个
        
        return recommendations


# 更新全局实例
def get_challenge_manager() -> ChallengeManager:
    """获取全局挑战管理器实例"""
    global _global_challenge_manager
    if '_global_challenge_manager' not in globals():
        globals()['_global_challenge_manager'] = ChallengeManager()
    return globals()['_global_challenge_manager']


def get_bd_optimizer() -> BDOptimizer:
    """获取全局BD优化器实例"""
    global _global_bd_optimizer
    if '_global_bd_optimizer' not in globals():
        globals()['_global_bd_optimizer'] = BDOptimizer()
    return globals()['_global_bd_optimizer']
