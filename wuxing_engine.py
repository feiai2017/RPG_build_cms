# -*- coding: utf-8 -*-
"""
增强的五行八卦计算引擎 (WuxingEngine)
基于现有app_five_elements.py重构，实现真正的五行相生相克计算逻辑
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import copy
import math


@dataclass
class Stone:
    """灵石数据结构"""
    id: str
    name: str
    element: str  # 木火土金水 or 无
    icon: str
    rarity: str
    bandwidth: int
    stock_total: int
    kind: str  # gem / logic / core
    effects: Dict[str, Dict[str, float]] = field(default_factory=dict)  # inner/middle/outer
    logic: Dict[str, str] = field(default_factory=dict)
    core_rules: Dict[str, str] = field(default_factory=dict)
    desc: str = ""


class WuxingEngine:
    """增强的五行八卦计算引擎
    
    基于现有app_five_elements.py重构，实现真正的五行相生相克计算逻辑
    添加八卦方位验证和卦象效果计算，优化灵石配置验证和属性加成计算
    """
    
    def __init__(self):
        # 五行基础定义
        self.elements = ["木", "火", "土", "金", "水"]
        
        # 五行相生关系：木→火→土→金→水→木
        self.generation_cycle = {
            "木": "火", 
            "火": "土", 
            "土": "金", 
            "金": "水", 
            "水": "木"
        }
        
        # 五行相克关系：木克土，土克水，水克火，火克金，金克木
        self.destruction_cycle = {
            "木": "土", 
            "土": "水", 
            "水": "火", 
            "火": "金", 
            "金": "木"
        }
        
        # 后天八卦方位和五行归属（严格按照传统后天八卦理论）
        self.trigrams = {
            "QIAN": {"name": "乾", "symbol": "☰", "elem": "金", "direction": "西北", "pos": (1, 1)},
            "DUI": {"name": "兑", "symbol": "☱", "elem": "金", "direction": "西", "pos": (2, 0)},
            "LI": {"name": "离", "symbol": "☲", "elem": "火", "direction": "南", "pos": (0, 2)},
            "ZHEN": {"name": "震", "symbol": "☳", "elem": "木", "direction": "东", "pos": (2, 4)},
            "XUN": {"name": "巽", "symbol": "☴", "elem": "木", "direction": "东南", "pos": (3, 3)},
            "KAN": {"name": "坎", "symbol": "☵", "elem": "水", "direction": "北", "pos": (4, 2)},
            "GEN": {"name": "艮", "symbol": "☶", "elem": "土", "direction": "东北", "pos": (1, 3)},
            "KUN": {"name": "坤", "symbol": "☷", "elem": "土", "direction": "西南", "pos": (3, 1)},
        }
        
        # 八卦环形顺序（按后天八卦方位：离→坤→兑→乾→坎→艮→震→巽）
        self.bagua_ring = ["LI", "KUN", "DUI", "QIAN", "KAN", "GEN", "ZHEN", "XUN"]
        
        # 五行效果系数（基于app_five_elements.py的实际数值）
        self.synergy_coefficients = {
            "generation": 1.5,      # 相生加成50%
            "destruction": 0.8,     # 相克减成20%
            "harmony": 1.2,         # 和谐加成20%
            "conflict": 0.7,        # 冲突减成30%
            "trigram_generation": 1.5,  # 卦域相生50%
            "trigram_destruction": 0.8, # 卦域相克20%
            "chain_generation": 1.15,   # 卦内相生链15%
            "chain_destruction": 0.9,   # 卦内相克链10%
            "ring_generation": 1.2,     # 卦环相生20%
            "ring_destruction": 0.85,   # 卦环相克15%
        }
        
        # 境界配置（从app_five_elements.py移植）
        self.realms = {
            "炼气": {"tri_unlock": 2, "core_slots": 1, "bw_safe": 18, "bw_max": 26},
            "筑基": {"tri_unlock": 3, "core_slots": 1, "bw_safe": 24, "bw_max": 34},
            "金丹": {"tri_unlock": 4, "core_slots": 2, "bw_safe": 30, "bw_max": 42},
            "元婴": {"tri_unlock": 4, "core_slots": 2, "bw_safe": 36, "bw_max": 50},
            "化神": {"tri_unlock": 4, "core_slots": 3, "bw_safe": 42, "bw_max": 58},
        }
        
        # 槽位层级定义
        self.layer_names = {2: "内", 3: "中", 4: "外"}
        self.layer_keys = {2: "inner", 3: "middle", 4: "outer"}
        
        # 五行元素元数据
        self.element_meta = {
            "木": {"color": "#2E7D32", "bg": "rgba(46,125,50,0.10)", "icon": "🌿"},
            "火": {"color": "#C62828", "bg": "rgba(198,40,40,0.10)", "icon": "🔥"},
            "土": {"color": "#8D6E63", "bg": "rgba(141,110,99,0.12)", "icon": "🪨"},
            "金": {"color": "#B8860B", "bg": "rgba(184,134,11,0.12)", "icon": "🗡️"},
            "水": {"color": "#1565C0", "bg": "rgba(21,101,192,0.10)", "icon": "💧"},
            "无": {"color": "#444", "bg": "rgba(0,0,0,0.05)", "icon": "∅"},
        }
    
    def is_generation(self, element_a: str, element_b: str) -> bool:
        """检查两个元素是否为相生关系"""
        if element_a not in self.elements or element_b not in self.elements:
            return False
        return self.generation_cycle.get(element_a) == element_b
    
    def is_destruction(self, element_a: str, element_b: str) -> bool:
        """检查两个元素是否为相克关系"""
        if element_a not in self.elements or element_b not in self.elements:
            return False
        return self.destruction_cycle.get(element_a) == element_b
    
    def get_counter_element(self, element: str) -> str:
        """获取克制指定元素的元素"""
        for source, target in self.destruction_cycle.items():
            if target == element:
                return source
        return "无"
    
    def calculate_element_synergy_v2(self, stones: List[Stone]) -> Dict[str, float]:
        """计算五行灵石的协同效果 (重构版本)
        
        使用统一的inc/more语义，避免数值爆炸
        返回格式: {"inc_delta": float, "more_mult": float}
        """
        if not stones:
            return {"inc_delta": 0.0, "more_mult": 1.0}
        
        # 统计各元素数量（仅计算五行灵石）
        element_counts = {}
        for stone in stones:
            if stone.element in self.elements and stone.kind == "gem":
                element_counts[stone.element] = element_counts.get(stone.element, 0) + 1
        
        if not element_counts:
            return {"inc_delta": 0.0, "more_mult": 1.0}
        
        # 基于元素计数的配对上限统计 (O(5)，避免N²)
        support_pairs = 0
        conflict_pairs = 0
        
        for element in self.elements:
            count = element_counts.get(element, 0)
            if count == 0:
                continue
                
            # 相生配对数: min(当前元素数量, 被生元素数量)
            generated_element = self.generation_cycle.get(element)
            if generated_element:
                generated_count = element_counts.get(generated_element, 0)
                support_pairs += min(count, generated_count)
            
            # 相克配对数: min(当前元素数量, 被克元素数量)
            destroyed_element = self.destruction_cycle.get(element)
            if destroyed_element:
                destroyed_count = element_counts.get(destroyed_element, 0)
                conflict_pairs += min(count, destroyed_count)
        
        # 计算全局协同inc_delta
        inc_gen = min(0.06 * support_pairs, 0.24)    # 相生最多+24%
        inc_des = -min(0.05 * conflict_pairs, 0.20)  # 相克最多-20%
        
        total_inc = inc_gen + inc_des
        
        return {
            "inc_delta": total_inc,
            "more_mult": 1.0,
            "support_pairs": support_pairs,
            "conflict_pairs": conflict_pairs,
            "generation_bonus": inc_gen,
            "destruction_penalty": inc_des
        }
    
    def validate_bagua_configuration(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证八卦配置的合理性"""
        errors = []
        
        # 检查八卦方位是否正确
        if "stones" not in config:
            errors.append("配置中缺少八卦灵石数据")
            return False, errors
        
        stones_config = config["stones"]
        
        # 验证八卦名称
        for trigram_name in stones_config.keys():
            if trigram_name not in self.trigrams:
                errors.append(f"无效的八卦名称: {trigram_name}")
        
        # 验证八卦方位布局（后天八卦顺序）
        expected_positions = {
            "LI": "南",
            "KUN": "西南", 
            "DUI": "西",
            "QIAN": "西北",
            "KAN": "北",
            "GEN": "东北",
            "ZHEN": "东",
            "XUN": "东南"
        }
        
        for trigram_name, expected_dir in expected_positions.items():
            if trigram_name in self.trigrams:
                actual_dir = self.trigrams[trigram_name]["direction"]
                if actual_dir != expected_dir:
                    errors.append(f"八卦方位错误: {trigram_name}应在{expected_dir}，实际在{actual_dir}")
        
        # 验证灵石配置合理性
        for trigram_name, slots in stones_config.items():
            if trigram_name not in self.trigrams:
                continue
                
            trigram_element = self.trigrams[trigram_name]["elem"]
            
            for slot_idx, stone_id in slots.items():
                if stone_id is None:
                    continue
                
                # 这里需要实际的石头数据来验证，暂时跳过具体验证
                # 在实际使用时会传入完整的石头库
                pass
        
        return len(errors) == 0, errors
    
    def get_trigram_effects(self, trigram: str, stones: List[Stone]) -> Dict[str, float]:
        """获取特定卦位的效果加成
        
        基于app_five_elements.py的卦域相生相克逻辑
        """
        if trigram not in self.trigrams:
            return {}
        
        trigram_info = self.trigrams[trigram]
        trigram_element = trigram_info["elem"]
        
        effects = {
            "base_multiplier": 1.0,
            "element_synergy": 0.0,
            "position_bonus": 0.0,
            "resonance_effect": 0.0
        }
        
        # 计算卦位与灵石的元素协同（卦域相生相克）
        for stone in stones:
            if stone.element not in self.elements or stone.kind != "gem":
                continue
            
            if self.is_generation(stone.element, trigram_element):
                # 灵石生卦位：+50%
                effects["element_synergy"] += 0.5
            elif self.is_generation(trigram_element, stone.element):
                # 卦位生灵石：+30%
                effects["element_synergy"] += 0.3
            elif self.is_destruction(stone.element, trigram_element):
                # 灵石克卦位：-20%
                effects["element_synergy"] -= 0.2
            elif self.is_destruction(trigram_element, stone.element):
                # 卦位克灵石：-15%
                effects["element_synergy"] -= 0.15
            elif stone.element == trigram_element:
                # 同元素小幅加成：+10%
                effects["element_synergy"] += 0.1
        
        # 计算方位加成（特定方位有特殊效果）
        direction_bonuses = {
            "南": 0.1,    # 离火，攻击加成
            "北": 0.1,    # 坎水，防御加成
            "东": 0.05,   # 震木，生命加成
            "西": 0.05,   # 兑金，暴击加成
            "西北": 0.08, # 乾金，领导加成
            "东南": 0.06, # 巽木，灵活加成
            "东北": 0.07, # 艮土，稳定加成
            "西南": 0.07, # 坤土，承载加成
        }
        
        direction = trigram_info["direction"]
        effects["position_bonus"] = direction_bonuses.get(direction, 0.0)
        
        # 计算共鸣效果（同类型灵石数量）
        element_counts = {}
        for stone in stones:
            if stone.element in self.elements and stone.kind == "gem":
                element_counts[stone.element] = element_counts.get(stone.element, 0) + 1
        
        if trigram_element in element_counts and element_counts[trigram_element] >= 2:
            # 每多一个同元素灵石增加15%共鸣效果
            effects["resonance_effect"] += 0.15 * (element_counts[trigram_element] - 1)
        
        # 计算最终倍率
        final_multiplier = effects["base_multiplier"]
        final_multiplier += effects["element_synergy"]
        final_multiplier += effects["position_bonus"]
        final_multiplier += effects["resonance_effect"]
        
        # 限制倍率范围
        final_multiplier = max(0.3, min(3.0, final_multiplier))
        effects["final_multiplier"] = final_multiplier
        
        return effects
    
    def calculate_comprehensive_effects_v2(self, full_config: Dict[str, Any]) -> Dict[str, Any]:
        """计算完整八卦配置的综合效果 (重构版本)
        
        使用统一的inc/more语义，避免数值爆炸
        """
        if "stones" not in full_config:
            return {"error": "配置数据不完整"}
        
        stones_config = full_config["stones"]
        realm = full_config.get("realm", "金丹")
        realm_cfg = self.realms.get(realm, self.realms["金丹"])
        tri_unlock = realm_cfg["tri_unlock"]
        
        all_stones = []
        element_counts = {e: 0 for e in self.elements}
        
        # 收集所有灵石
        for trigram_name, slots in stones_config.items():
            if trigram_name not in self.trigrams:
                continue
            
            for slot_idx, stone_id in slots.items():
                if stone_id is None or int(slot_idx) > tri_unlock:
                    continue
                
                # 创建或获取石头对象
                if isinstance(stone_id, str):
                    stone = Stone(
                        id=stone_id,
                        name=f"Stone_{stone_id}",
                        element=self._infer_element_from_id(stone_id),
                        icon="",
                        rarity="common",
                        bandwidth=1,
                        stock_total=1,
                        kind=self._infer_kind_from_id(stone_id, int(slot_idx))
                    )
                else:
                    stone = stone_id  # 假设传入的是Stone对象
                
                all_stones.append(stone)
                
                # 统计五行元素（仅gem类型）
                if stone.kind == "gem" and stone.element in self.elements:
                    element_counts[stone.element] += 1
        
        # 1. 全局协同效果 (新版本)
        global_synergy = self.calculate_element_synergy_v2(all_stones)
        
        # 2. 卦内链路效果 (新版本)
        chain_effects = self._calculate_chain_effects_v2(stones_config, tri_unlock)
        
        # 3. 环形链路效果 (新版本)
        ring_effects = self._calculate_ring_effects_v2(stones_config, tri_unlock)
        
        # 4. 五行循环效果 (新版本)
        generation_chains = self._find_generation_chains(element_counts)
        cycle_more = self.calculate_cycle_bonus_v2(generation_chains)
        
        # 5. 共鸣效果 (简化版本)
        resonance_inc = self._calculate_resonance_inc(element_counts)
        
        # 验证配置合理性
        is_valid, validation_errors = self.validate_bagua_configuration(full_config)
        
        # 汇总所有inc_delta
        total_inc = (
            global_synergy.get("inc_delta", 0.0) +
            chain_effects.get("inc_delta", 0.0) +
            ring_effects.get("inc_delta", 0.0) +
            resonance_inc
        )
        
        # 应用软上限和clamp
        total_inc = self.clamp(total_inc, -0.5, 2.5)
        effective_inc = self.softcap_inc(total_inc)
        
        # 汇总所有more倍率
        total_more = cycle_more
        total_more = self.clamp(total_more, 0.5, 3.5)
        
        return {
            "global_synergy": global_synergy,
            "chain_effects": chain_effects,
            "ring_effects": ring_effects,
            "cycle_effects": {
                "generation_chains": generation_chains,
                "cycle_more": cycle_more
            },
            "resonance_inc": resonance_inc,
            "element_counts": element_counts,
            "total_stones": len(all_stones),
            "is_valid_configuration": is_valid,
            "validation_errors": validation_errors,
            
            # 新的统一结果
            "total_inc_delta": total_inc,
            "effective_inc_delta": effective_inc,
            "total_more_mult": total_more,
            "final_multiplier": total_more * (1 + effective_inc)
        }
    
    def _find_generation_chains(self, element_counts: Dict[str, int]) -> List[List[str]]:
        """寻找相生链"""
        chains = []
        elements_with_stones = [e for e, count in element_counts.items() if count > 0]
        
        # 寻找最长的相生链
        for start_elem in elements_with_stones:
            chain = [start_elem]
            current = start_elem
            
            while True:
                next_elem = self.generation_cycle.get(current)
                if next_elem and next_elem in elements_with_stones and next_elem not in chain:
                    chain.append(next_elem)
                    current = next_elem
                else:
                    break
            
            if len(chain) >= 3:  # 至少3个元素才算有效链
                chains.append(chain)
        
        return chains
    
    def calculate_comprehensive_effects_v3(self, full_config: Dict[str, Any]) -> Dict[str, Any]:
        """计算完整八卦配置的综合效果 (P1级别改进版本)
        
        集成逻辑灵石增幅器和中宫辅灵石系统
        """
        if "stones" not in full_config:
            return {"error": "配置数据不完整"}
        
        stones_config = full_config["stones"]
        realm = full_config.get("realm", "金丹")
        main_affinity = full_config.get("main_affinity", "木")
        realm_cfg = self.realms.get(realm, self.realms["金丹"])
        tri_unlock = realm_cfg["tri_unlock"]
        
        all_stones = []
        element_counts = {e: 0 for e in self.elements}
        logic_effects = {}
        
        # 收集所有灵石和逻辑灵石效果
        for trigram_name, slots in stones_config.items():
            if trigram_name not in self.trigrams:
                continue
            
            # 处理逻辑灵石（第1槽）
            logic_stone_id = slots.get("1")
            base_trigram_inc = 0.0  # 基础卦域inc
            base_chain_limit = 0.15  # 基础链路上限
            
            logic_effect = self.calculate_logic_stone_effects_v2(
                trigram_name, logic_stone_id, base_trigram_inc, base_chain_limit
            )
            logic_effects[trigram_name] = logic_effect
            
            # 处理其他槽位的灵石
            for slot_idx, stone_id in slots.items():
                if stone_id is None or int(slot_idx) > tri_unlock:
                    continue
                
                # 创建或获取石头对象
                if isinstance(stone_id, str):
                    stone = Stone(
                        id=stone_id,
                        name=f"Stone_{stone_id}",
                        element=self._infer_element_from_id(stone_id),
                        icon="",
                        rarity="common",
                        bandwidth=1,
                        stock_total=1,
                        kind=self._infer_kind_from_id(stone_id, int(slot_idx))
                    )
                else:
                    stone = stone_id  # 假设传入的是Stone对象
                
                all_stones.append(stone)
                
                # 统计五行元素（仅gem类型）
                if stone.kind == "gem" and stone.element in self.elements:
                    element_counts[stone.element] += 1
        
        # 处理中宫辅灵石（P1-2改进）
        center_stone_id = stones_config.get("CENTER", {}).get("1")  # 假设中宫第1槽
        center_effects = self.calculate_center_auxiliary_stone_effects(main_affinity, center_stone_id)
        
        # 如果中宫提供节点，增加对应元素计数
        if center_effects["provides_node"]:
            effective_element = center_effects["effective_element"]
            if effective_element in element_counts:
                element_counts[effective_element] += 1
        
        # 1. 全局协同效果
        global_synergy = self.calculate_element_synergy_v2(all_stones)
        
        # 2. 卦内链路效果（考虑逻辑灵石增强）
        chain_effects = self._calculate_chain_effects_v3(stones_config, tri_unlock, logic_effects)
        
        # 3. 环形链路效果
        ring_effects = self._calculate_ring_effects_v2(stones_config, tri_unlock)
        
        # 4. 五行循环效果
        generation_chains = self._find_generation_chains(element_counts)
        cycle_more = self.calculate_cycle_bonus_v2(generation_chains)
        
        # 5. 共鸣效果（考虑中宫辅灵石）
        resonance_inc = self._calculate_resonance_inc(element_counts)
        if center_effects["provides_node"]:
            resonance_inc += center_effects["resonance_bonus"]
        
        # 6. 逻辑灵石总体效果
        total_logic_inc = sum(effect.get("trigram_inc_bonus", 0.0) for effect in logic_effects.values())
        
        # 验证配置合理性
        is_valid, validation_errors = self.validate_bagua_configuration(full_config)
        
        # 汇总所有inc_delta
        total_inc = (
            global_synergy.get("inc_delta", 0.0) +
            chain_effects.get("inc_delta", 0.0) +
            ring_effects.get("inc_delta", 0.0) +
            resonance_inc +
            total_logic_inc
        )
        
        # 应用软上限和clamp
        total_inc = self.clamp(total_inc, -0.5, 2.5)
        effective_inc = self.softcap_inc(total_inc)
        
        # 汇总所有more倍率
        total_more = cycle_more
        total_more = self.clamp(total_more, 0.5, 3.5)
        
        return {
            "global_synergy": global_synergy,
            "chain_effects": chain_effects,
            "ring_effects": ring_effects,
            "cycle_effects": {
                "generation_chains": generation_chains,
                "cycle_more": cycle_more
            },
            "resonance_inc": resonance_inc,
            "logic_effects": logic_effects,
            "center_effects": center_effects,
            "element_counts": element_counts,
            "total_stones": len(all_stones),
            "is_valid_configuration": is_valid,
            "validation_errors": validation_errors,
            
            # 新的统一结果
            "total_inc_delta": total_inc,
            "effective_inc_delta": effective_inc,
            "total_more_mult": total_more,
            "final_multiplier": total_more * (1 + effective_inc)
        }
    
    def _infer_logic_type(self, logic_stone_id: str) -> str:
        """从逻辑灵石ID推断类型"""
        logic_id_lower = logic_stone_id.lower()
        
        if "amplifier" in logic_id_lower or "放大" in logic_stone_id or "强化" in logic_stone_id:
            return "amplifier"
        elif "router" in logic_id_lower or "路由" in logic_stone_id or "连接" in logic_stone_id:
            return "router"
        elif "activator" in logic_id_lower or "主动" in logic_stone_id or "触发" in logic_stone_id:
            return "activator"
        else:
            return "basic"
    
    def _calculate_chain_effects_v3(self, stones_config: Dict[str, Any], tri_unlock: int, 
                                   logic_effects: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """计算卦内链路效果 (P1级别改进版本)
        
        考虑逻辑灵石对链路上限的增强
        """
        chain_effects = {
            "generation_chains": [],
            "destruction_chains": [],
            "inc_delta": 0.0
        }
        
        for trigram_name, slots in stones_config.items():
            if trigram_name not in self.trigrams:
                continue
            
            inc = 0.0
            # 检查内→中→外的相生相克链 (2条边)
            edges = [(2, 3), (3, 4)]  # 内→中, 中→外
            
            for slot_a, slot_b in edges:
                if slot_a > tri_unlock or slot_b > tri_unlock:
                    continue
                    
                stone_a_id = slots.get(str(slot_a))
                stone_b_id = slots.get(str(slot_b))
                
                if not stone_a_id or not stone_b_id:
                    continue
                
                elem_a = self._infer_element_from_id(stone_a_id)
                elem_b = self._infer_element_from_id(stone_b_id)
                
                if elem_a in self.elements and elem_b in self.elements:
                    if self.is_generation(elem_a, elem_b):
                        chain_effects["generation_chains"].append(
                            f"{self.trigrams[trigram_name]['name']}{self.layer_names.get(slot_a, str(slot_a))}→{self.layer_names.get(slot_b, str(slot_b))}"
                        )
                        inc += 0.06  # 每段相生+6%
                    elif self.is_destruction(elem_a, elem_b):
                        chain_effects["destruction_chains"].append(
                            f"{self.trigrams[trigram_name]['name']}{self.layer_names.get(slot_a, str(slot_a))}×{self.layer_names.get(slot_b, str(slot_b))}"
                        )
                        inc -= 0.05  # 每段相克-5%
            
            # 应用逻辑灵石的链路上限增强
            base_limit = 0.15  # 基础上限+15%
            logic_effect = logic_effects.get(trigram_name, {})
            chain_limit_bonus = logic_effect.get("chain_limit_bonus", 0.0)
            enhanced_limit = base_limit + chain_limit_bonus
            
            # 单个卦位的链路贡献clamp到增强后的上限
            trigram_inc = max(-0.12, min(enhanced_limit, inc))
            chain_effects["inc_delta"] += trigram_inc
        
        return chain_effects
    
    def _calculate_resonance_inc(self, element_counts: Dict[str, int]) -> float:
        """计算共鸣效果inc_delta (简化版本)"""
        total_stones = sum(element_counts.values())
        if total_stones < 4:
            return 0.0
        
        counts_sorted = sorted(element_counts.values(), reverse=True)
        dom_count = counts_sorted[0]
        min_count = min(count for count in counts_sorted if count > 0)
        
        # 均衡检测：五行接近平衡
        if (dom_count - min_count) <= 1:
            return 0.15  # 均衡加成+15%
        # 共鸣检测：某元素数量≥3
        elif dom_count >= 3:
            resonance_bonus = (dom_count - 2) * 0.08  # 每多1个+8%
            
            # 偏科弱点：过度偏向某元素
            if dom_count >= 4:
                second_count = counts_sorted[1] if len(counts_sorted) > 1 else 0
                if (dom_count - second_count) >= 3:
                    weakness_penalty = (dom_count - 2) * 0.06  # 每多1个-6%
                    return resonance_bonus - weakness_penalty
            
            return resonance_bonus
        
        return 0.0
    
    def _calculate_chain_effects_v2(self, stones_config: Dict[str, Any], tri_unlock: int) -> Dict[str, Any]:
        """计算卦内链路效果 (重构版本)
        
        从每段乘法改为每段加法+总上限，避免指数爆炸
        """
        chain_effects = {
            "generation_chains": [],
            "destruction_chains": [],
            "inc_delta": 0.0  # 改为inc_delta
        }
        
        for trigram_name, slots in stones_config.items():
            if trigram_name not in self.trigrams:
                continue
            
            inc = 0.0
            # 检查内→中→外的相生相克链 (2条边)
            edges = [(2, 3), (3, 4)]  # 内→中, 中→外
            
            for slot_a, slot_b in edges:
                if slot_a > tri_unlock or slot_b > tri_unlock:
                    continue
                    
                stone_a_id = slots.get(str(slot_a))
                stone_b_id = slots.get(str(slot_b))
                
                if not stone_a_id or not stone_b_id:
                    continue
                
                elem_a = self._infer_element_from_id(stone_a_id)
                elem_b = self._infer_element_from_id(stone_b_id)
                
                if elem_a in self.elements and elem_b in self.elements:
                    if self.is_generation(elem_a, elem_b):
                        chain_effects["generation_chains"].append(
                            f"{self.trigrams[trigram_name]['name']}{self.layer_names.get(slot_a, str(slot_a))}→{self.layer_names.get(slot_b, str(slot_b))}"
                        )
                        inc += 0.06  # 每段相生+6%
                    elif self.is_destruction(elem_a, elem_b):
                        chain_effects["destruction_chains"].append(
                            f"{self.trigrams[trigram_name]['name']}{self.layer_names.get(slot_a, str(slot_a))}×{self.layer_names.get(slot_b, str(slot_b))}"
                        )
                        inc -= 0.05  # 每段相克-5%
            
            # 单个卦位的链路贡献clamp到[-12%, +15%]
            trigram_inc = max(-0.12, min(0.15, inc))
            chain_effects["inc_delta"] += trigram_inc
        
        return chain_effects
    
    def _calculate_ring_effects_v2(self, stones_config: Dict[str, Any], tri_unlock: int) -> Dict[str, Any]:
        """计算环形链路效果 (重构版本)
        
        从每段乘法改为每段加法+总上限，避免指数爆炸
        """
        ring_effects = {
            "ring_chains": [],
            "inc_delta": 0.0  # 改为inc_delta
        }
        
        if tri_unlock < 2:  # 需要至少内环位
            return ring_effects
        
        # 收集八卦环形节点（每卦内环位的元素）
        ring_elements = []
        for trigram in self.bagua_ring:
            stone_id = stones_config.get(trigram, {}).get("2")  # 内环位
            if stone_id:
                element = self._infer_element_from_id(stone_id)
                if element in self.elements:
                    ring_elements.append(element)
                else:
                    ring_elements.append("无")
            else:
                ring_elements.append("无")
        
        # 检查环形相生相克 (最多8条边)
        inc = 0.0
        for i in range(len(ring_elements)):
            curr_elem = ring_elements[i]
            next_elem = ring_elements[(i + 1) % len(ring_elements)]
            
            if curr_elem == "无" or next_elem == "无":
                continue
            
            if self.is_generation(curr_elem, next_elem):
                ring_effects["ring_chains"].append(f"{curr_elem}→{next_elem}")
                inc += 0.03  # 每段相生+3%
            elif self.is_destruction(curr_elem, next_elem):
                ring_effects["ring_chains"].append(f"{curr_elem}×{next_elem}")
                inc -= 0.03  # 每段相克-3%
        
        # 环路总和clamp到[-18%, +24%]
        ring_effects["inc_delta"] = max(-0.18, min(0.24, inc))
        
        return ring_effects
    
    def _calculate_circuit_effects(self, stones_config: Dict[str, Any], tri_unlock: int) -> Dict[str, Any]:
        """计算卦脉导通效果（三连卦段）"""
        circuit_effects = {
            "active_circuits": [],
            "circuit_bonus": 0.0
        }
        
        if tri_unlock < 2:  # 需要至少内环位
            return circuit_effects
        
        # 定义三连卦段（基于app_five_elements.py）
        circuits = [
            ("LI", "KUN", "DUI"),    # 离→坤→兑
            ("DUI", "QIAN", "KAN"),  # 兑→乾→坎
            ("KAN", "GEN", "ZHEN"),  # 坎→艮→震
            ("ZHEN", "XUN", "LI"),   # 震→巽→离
        ]
        
        for tri_a, tri_b, tri_c in circuits:
            # 检查三个卦位是否都有内环位灵石
            elements = []
            for tri in (tri_a, tri_b, tri_c):
                stone_id = stones_config.get(tri, {}).get("2")
                if stone_id:
                    element = self._infer_element_from_id(stone_id)
                    if element in self.elements:
                        elements.append(element)
                    else:
                        break
                else:
                    break
            
            if len(elements) == 3:
                elem_a, elem_b, elem_c = elements
                # 连段内不允许强相克
                if not (self.is_destruction(elem_a, elem_b) or self.is_destruction(elem_b, elem_c)):
                    circuit_name = f"{self.trigrams[tri_a]['name']}-{self.trigrams[tri_b]['name']}-{self.trigrams[tri_c]['name']}"
                    circuit_effects["active_circuits"].append(circuit_name)
                    circuit_effects["circuit_bonus"] += 8.0  # 每个导通卦段+8点属性
        
        return circuit_effects
    
    def calculate_cycle_bonus_v2(self, generation_chains: List[List[str]]) -> float:
        """计算五行循环加成 (重构版本)
        
        保留为稀有乘区，但降档倍率
        """
        if not generation_chains:
            return 1.0
            
        max_chain_length = max(len(chain) for chain in generation_chains)
        
        if max_chain_length >= 5:
            return 1.25  # 完整五行循环 +25% (原1.50)
        elif max_chain_length >= 4:
            return 1.15  # 四元素链 +15% (原1.30)
        elif max_chain_length >= 3:
            return 1.08  # 三元素链 +8% (原1.15)
        else:
            return 1.0   # 无循环
    
    @staticmethod
    def softcap_inc(x: float) -> float:
        """加法池软上限函数
        
        0~1.0 全额，超过1.0只算一半，避免后期堆爆
        """
        if x <= 1.0:
            return x
        return 1.0 + (x - 1.0) * 0.5
    
    @staticmethod
    def clamp(value: float, min_val: float, max_val: float) -> float:
        """数值限制函数"""
        return max(min_val, min(max_val, value))
    
    def _infer_element_from_id(self, stone_id: str) -> str:
        """从石头ID推断元素类型（增强实现）"""
        stone_id_lower = stone_id.lower()
        
        # 直接匹配五行字符
        if "木" in stone_id or "wood" in stone_id_lower or "翠" in stone_id:
            return "木"
        elif "火" in stone_id or "fire" in stone_id_lower or "赤" in stone_id or "焰" in stone_id:
            return "火"
        elif "土" in stone_id or "earth" in stone_id_lower or "厚" in stone_id:
            return "土"
        elif "金" in stone_id or "metal" in stone_id_lower or "魄" in stone_id:
            return "金"
        elif "水" in stone_id or "water" in stone_id_lower or "玄" in stone_id or "冰" in stone_id:
            return "水"
        # 特殊类型
        elif "logic" in stone_id_lower or "逻辑" in stone_id or "bios" in stone_id_lower or "核心" in stone_id:
            return "无"
        else:
            return "无"
    
    def calculate_logic_stone_effects_v2(self, trigram: str, logic_stone_id: Optional[str], 
                                         base_trigram_inc: float, base_chain_limit: float) -> Dict[str, float]:
        """计算逻辑灵石效果 (重构版本)
        
        从"激活开关"改为"增幅/改造器"，避免门票税
        """
        if not logic_stone_id:
            # 没有逻辑灵石时，卦位仍然激活，只是没有额外效果
            return {
                "trigram_inc_bonus": 0.0,
                "chain_limit_bonus": 0.0,
                "special_effect": "none"
            }
        
        # 根据逻辑灵石类型提供不同效果
        logic_type = self._infer_logic_type(logic_stone_id)
        
        if logic_type == "amplifier":
            # 放大器：卦域inc额外+8%，链路上限+5%
            return {
                "trigram_inc_bonus": 0.08,
                "chain_limit_bonus": 0.05,
                "special_effect": "amplifier"
            }
        elif logic_type == "router":
            # 路由器：允许跨卦链路连接（暂时简化为链路上限+10%）
            return {
                "trigram_inc_bonus": 0.0,
                "chain_limit_bonus": 0.10,
                "special_effect": "router"
            }
        elif logic_type == "activator":
            # 主动化：被动属性变触发效果（暂时简化为触发时+15%）
            return {
                "trigram_inc_bonus": 0.15,
                "chain_limit_bonus": 0.0,
                "special_effect": "activator"
            }
        else:
            # 默认逻辑灵石：小幅增强
            return {
                "trigram_inc_bonus": 0.05,
                "chain_limit_bonus": 0.02,
                "special_effect": "basic"
            }
    
    def calculate_center_auxiliary_stone_effects(self, main_affinity: str, center_stone_id: Optional[str]) -> Dict[str, Any]:
        """计算中宫辅灵石效果 (P1-2: 火/水公平补位)
        
        中宫阵眼允许插入"辅灵石"，为火/水主灵根提供额外节点
        """
        if not center_stone_id or main_affinity not in ["火", "水"]:
            return {
                "provides_node": False,
                "effective_element": None,
                "resonance_bonus": 0.0
            }
        
        # 中宫辅灵石视为主灵根元素的节点
        effective_element = main_affinity
        
        return {
            "provides_node": True,
            "effective_element": effective_element,
            "resonance_bonus": 0.08,  # 额外+8%共鸣加成
            "description": f"中宫辅灵石作为{effective_element}节点，参与同元素共鸣和循环链"
        }
    
    def _infer_kind_from_id(self, stone_id: str, slot_idx: int) -> str:
        """从石头ID和槽位推断石头类型"""
        stone_id_lower = stone_id.lower()
        
        if "logic" in stone_id_lower or "逻辑" in stone_id:
            return "logic"
        elif "core" in stone_id_lower or "bios" in stone_id_lower or "核心" in stone_id:
            return "core"
        elif "auxiliary" in stone_id_lower or "辅助" in stone_id or "辅灵" in stone_id:
            return "auxiliary"  # 新增辅助灵石类型
        elif slot_idx == 1:
            return "logic"  # 第1位默认为逻辑位
        else:
            return "gem"    # 其他位默认为宝石
    
    def calculate_element_affinity_inc(self, element: str, main_affinity: str) -> float:
        """计算主灵根亲和度inc_delta (重构版本)
        
        返回inc_delta而不是倍率
        """
        if element not in self.elements:
            return 0.0
        
        if element == main_affinity:
            return 0.20  # 主灵根+20%
        elif self.is_generation(main_affinity, element):
            return 0.05  # 主灵根所生+5%
        elif self.is_destruction(element, main_affinity):
            return -0.05  # 克主灵根-5%
        else:
            return 0.0   # 其他无加成
    
    def calculate_trigram_domain_effects_v2(self, trigram: str, stone_element: str) -> float:
        """计算卦域相生相克效果 (重构版本)
        
        返回inc_delta，不再是乘法倍率
        """
        if trigram not in self.trigrams or stone_element not in self.elements:
            return 0.0
        
        trigram_element = self.trigrams[trigram]["elem"]
        
        if self.is_generation(stone_element, trigram_element):
            return 0.25  # 灵石生卦位 +25%
        elif self.is_generation(trigram_element, stone_element):
            return 0.12  # 卦位生灵石 +12%
        elif self.is_destruction(stone_element, trigram_element):
            return -0.12  # 灵石克卦位 -12%
        elif self.is_destruction(trigram_element, stone_element):
            return -0.08  # 卦位克灵石 -8%
        elif stone_element == trigram_element:
            return 0.15  # 同元素共鸣 +15%
        else:
            return 0.0
    
    def get_element_meta(self, element: str) -> Dict[str, str]:
        """获取元素的视觉元数据"""
        return self.element_meta.get(element, self.element_meta["无"])
    
    def get_realm_config(self, realm: str) -> Dict[str, int]:
        """获取境界配置"""
        return self.realms.get(realm, self.realms["金丹"])
    
    def calculate_final_damage_v2(self, base_damage: float, character_config: Dict[str, Any]) -> Dict[str, Any]:
        """新版伤害计算管线 (重构版本)
        
        使用统一的inc/more语义，避免数值爆炸
        """
        inc = 0.0      # 加法池
        more = 1.0     # 乘法池
        
        # 1) 主灵根: 改为inc
        skill_element = character_config.get("skill_element", "火")
        main_affinity = character_config.get("main_affinity", "木")
        inc += self.calculate_element_affinity_inc(skill_element, main_affinity)
        
        # 2) 八卦效果: 全部贡献inc
        bagua_config = character_config.get("bagua_config", {})
        if bagua_config:
            bagua_effects = self.calculate_comprehensive_effects_v2(bagua_config)
            
            inc += bagua_effects.get("total_inc_delta", 0.0)
            
            # 3) 循环: 保留为稀有乘区
            more *= bagua_effects.get("total_more_mult", 1.0)
        
        # 4) BIOS: 保留为乘区，控制在1.05~1.30
        bios_config = character_config.get("bios_config", {})
        bios_more = self._calculate_bios_more(bios_config)
        more *= bios_more
        
        # 5) 流派: 建议inc
        cultivation_school = character_config.get("cultivation_school", "剑修")
        inc += self._calculate_school_inc(cultivation_school, skill_element)
        
        # 6) 卦域效果: 只取相关卦位的inc
        relevant_trigram = self._get_relevant_trigram(skill_element)
        if relevant_trigram and bagua_config:
            trigram_inc = self.calculate_trigram_domain_effects_v2(relevant_trigram, skill_element)
            inc += trigram_inc
        
        # 7) 软上限和clamp
        inc = self.clamp(inc, -0.5, 2.5)
        inc_eff = self.softcap_inc(inc)
        more = self.clamp(more, 0.5, 3.5)
        
        final_damage = base_damage * more * (1 + inc_eff)
        
        return {
            "base_damage": base_damage,
            "inc_total": inc,
            "inc_effective": inc_eff,
            "more_total": more,
            "final_damage": final_damage,
            "damage_multiplier": final_damage / base_damage if base_damage > 0 else 1.0,
            
            # 详细分解
            "affinity_inc": self.calculate_element_affinity_inc(skill_element, main_affinity),
            "bagua_inc": bagua_effects.get("total_inc_delta", 0.0) if bagua_config else 0.0,
            "trigram_inc": trigram_inc if relevant_trigram and bagua_config else 0.0,
            "school_inc": self._calculate_school_inc(cultivation_school, skill_element),
            "cycle_more": bagua_effects.get("total_more_mult", 1.0) if bagua_config else 1.0,
            "bios_more": bios_more
        }
    
    def _calculate_bios_more(self, bios_config: Dict[str, Any]) -> float:
        """计算BIOS效果倍率 (控制在1.05~1.30)"""
        if not bios_config:
            return 1.0
        
        more = 1.0
        
        # 示例BIOS效果
        if "element_amplify" in bios_config:
            more *= 1.15  # 元素增幅+15%
        
        if "balance_adjust" in bios_config:
            more *= 1.10  # 平衡调节+10%
        
        if "five_element_invert" in bios_config:
            more *= 1.05  # 五行逆转+5%
        
        return self.clamp(more, 1.0, 1.30)
    
    def _calculate_school_inc(self, school: str, skill_element: str) -> float:
        """计算流派加成inc_delta"""
        school_bonuses = {
            "剑修": {"金": 0.08, "木": 0.04},
            "法修": {"火": 0.08, "水": 0.06},
            "体修": {"土": 0.08, "水": 0.04},
            "丹修": {"木": 0.08, "土": 0.04},
            "阵修": {"水": 0.08, "金": 0.04}
        }
        
        return school_bonuses.get(school, {}).get(skill_element, 0.0)
    
    def _get_relevant_trigram(self, skill_element: str) -> Optional[str]:
        """获取技能元素对应的主要卦位"""
        element_to_trigram = {
            "火": "LI",    # 离火
            "水": "KAN",   # 坎水
            "木": "ZHEN",  # 震木 (也可以是巽)
            "金": "QIAN",  # 乾金 (也可以是兑)
            "土": "KUN"    # 坤土 (也可以是艮)
        }
        
        return element_to_trigram.get(skill_element)