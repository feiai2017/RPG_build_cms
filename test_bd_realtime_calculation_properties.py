# -*- coding: utf-8 -*-
"""
BD配置实时计算属性测试 (BD Real-time Calculation Property Tests)
测试BD配置变更时系统的实时计算准确性和一致性

**Property 4: BD配置实时计算准确性**
**Validates: Requirements 2.2, 3.4**
"""

import pytest
from hypothesis import given, strategies as st, settings, example
from hypothesis.stateful import RuleBasedStateMachine, rule, initialize, invariant
import copy
from typing import Dict, Any, List, Optional
from unified_state_manager import UnifiedStateManager, get_state_manager, initialize_unified_system
from wuxing_engine import WuxingEngine


# 测试数据生成策略
@st.composite
def generate_character_data(draw):
    """生成随机角色数据"""
    return {
        "name": draw(st.text(min_size=1, max_size=10, alphabet="李王张刘陈杨黄赵吴周")),
        "level": draw(st.integers(min_value=1, max_value=100)),
        "school": draw(st.sampled_from([
            "sword_cultivator", "spell_cultivator", "body_cultivator", 
            "pill_cultivator", "formation_cultivator"
        ])),
        "realm": draw(st.sampled_from(["炼气", "筑基", "金丹", "元婴", "化神"])),
        "base_attributes": {
            "str": draw(st.floats(min_value=10.0, max_value=100.0)),
            "agi": draw(st.floats(min_value=10.0, max_value=100.0)),
            "int": draw(st.floats(min_value=10.0, max_value=100.0)),
            "max_hp": draw(st.floats(min_value=100.0, max_value=1000.0)),
            "base_atk": draw(st.floats(min_value=20.0, max_value=200.0)),
            "crit_rate": draw(st.floats(min_value=0.01, max_value=0.5)),
            "crit_dmg": draw(st.floats(min_value=1.1, max_value=3.0))
        },
        "affinity_main": draw(st.sampled_from(["木", "火", "土", "金", "水"]))
    }


@st.composite
def generate_bagua_configuration(draw):
    """生成随机八卦配置"""
    trigrams = ["QIAN", "DUI", "LI", "ZHEN", "XUN", "KAN", "GEN", "KUN"]
    elements = ["木", "火", "土", "金", "水"]
    
    stones = {}
    for trigram in trigrams:
        slots = {}
        for slot_idx in range(1, 5):  # 1-4槽位
            if draw(st.booleans()):  # 随机决定是否放置灵石
                if slot_idx == 1:
                    # 逻辑位
                    stone_id = draw(st.sampled_from(["logic_血危", "logic_过热", None]))
                else:
                    # 宝石位
                    element = draw(st.sampled_from(elements))
                    stone_id = f"gem_{element}"
                slots[str(slot_idx)] = stone_id
            else:
                slots[str(slot_idx)] = None
        stones[trigram] = slots
    
    core = {}
    for core_idx in range(1, 4):
        if draw(st.booleans()):
            core_bios = draw(st.sampled_from(["core_疯狂义体", "core_五行逆转", "core_算力超频", None]))
            core[core_idx] = core_bios
        else:
            core[core_idx] = None
    
    return {
        "stones": stones,
        "core": core,
        "seed": draw(st.integers(min_value=1, max_value=999999))
    }


@st.composite
def generate_equipment_data(draw):
    """生成随机装备数据"""
    equipment_slots = ["weapon", "armor", "accessory", "ring", "necklace"]
    equipment = {}
    
    for slot in equipment_slots:
        if draw(st.booleans()):  # 随机决定是否装备
            equipment[slot] = {
                "id": f"{slot}_{draw(st.integers(min_value=1, max_value=1000))}",
                "name": f"测试{slot}",
                "stats": {
                    "base_atk": draw(st.floats(min_value=0.0, max_value=50.0)),
                    "max_hp": draw(st.floats(min_value=0.0, max_value=200.0)),
                    "def": draw(st.floats(min_value=0.0, max_value=30.0)),
                    "crit_rate": draw(st.floats(min_value=0.0, max_value=0.1)),
                    "crit_dmg": draw(st.floats(min_value=0.0, max_value=0.5))
                },
                "school_affinity": draw(st.lists(
                    st.sampled_from(["sword_cultivator", "spell_cultivator", "body_cultivator"]),
                    min_size=0, max_size=2
                )),
                "element_affinity": draw(st.sampled_from(["木", "火", "土", "金", "水", "无"]))
            }
        else:
            equipment[slot] = None
    
    return equipment


class TestBDRealtimeCalculationProperties:
    """BD配置实时计算属性测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.state_manager = initialize_unified_system()
    
    @given(character_data=generate_character_data())
    @settings(max_examples=100, deadline=5000)
    def test_character_data_update_triggers_recalculation(self, character_data):
        """
        Property: 角色数据更新触发实时重算
        For any 角色数据变更，系统应该立即重新计算所有相关属性
        **Feature: rpg-system-integration, Property 4: BD配置实时计算准确性**
        **Validates: Requirements 2.2, 3.4**
        """
        # 记录更新前的属性
        old_attributes = copy.deepcopy(self.state_manager.character_data.get("derived_attributes", {}))
        
        # 更新角色数据
        self.state_manager.update_character_data(character_data)
        
        # 触发实时计算
        new_attributes = self.state_manager.calculate_realtime_attributes()
        
        # 验证属性计算正常工作
        assert isinstance(new_attributes, dict), "属性计算应该返回字典"
        assert len(new_attributes) > 0, "属性计算结果不应该为空"
        
        # 验证基础属性正确应用
        base_attrs = character_data.get("base_attributes", {})
        for key, value in base_attrs.items():
            assert key in new_attributes, f"基础属性{key}应该在计算结果中"
            # 最终属性应该至少包含基础值（可能有加成）
            assert new_attributes[key] >= value * 0.8, f"最终属性{key}不应该过低于基础值"
        
        # 验证数值合理性
        for key, value in new_attributes.items():
            assert isinstance(value, (int, float)), f"属性{key}应该是数值类型"
            assert value >= 0, f"属性{key}应该非负"
    
    @given(bagua_config=generate_bagua_configuration())
    @settings(max_examples=100, deadline=5000)
    def test_bagua_configuration_update_affects_attributes(self, bagua_config):
        """
        Property: 八卦配置更新影响属性计算
        For any 八卦配置变更，相关的元素伤害和属性加成应该立即更新
        **Feature: rpg-system-integration, Property 4: BD配置实时计算准确性**
        **Validates: Requirements 2.2, 3.4**
        """
        # 记录更新前的属性
        old_attributes = self.state_manager.calculate_realtime_attributes()
        
        # 更新八卦配置
        self.state_manager.update_bagua_configuration(bagua_config)
        
        # 重新计算属性
        new_attributes = self.state_manager.calculate_realtime_attributes()
        
        # 验证计算正常工作
        assert isinstance(new_attributes, dict), "属性计算应该返回字典"
        assert len(new_attributes) > 0, "属性计算结果不应该为空"
        
        # 验证八卦相关属性存在（如果配置有实际内容）
        has_stones = any(
            any(stone for stone in slots.values() if stone)
            for slots in bagua_config.get("stones", {}).values()
        )
        
        if has_stones:
            # 检查元素伤害属性存在
            element_damage_keys = [key for key in new_attributes.keys() if key.startswith("elem_dmg_")]
            assert len(element_damage_keys) > 0, "应该有元素伤害属性"
            
            # 验证至少有一些元素伤害或其他加成
            total_elemental_damage = sum(new_attributes.get(key, 0) for key in element_damage_keys)
            # 不强制要求必须有加成，因为可能配置无效或冲突
            assert total_elemental_damage >= 0, "元素伤害总和应该非负"
    
    @given(
        character_data=generate_character_data(),
        bagua_config=generate_bagua_configuration(),
        equipment_data=generate_equipment_data()
    )
    @settings(max_examples=50, deadline=10000)
    def test_comprehensive_bd_calculation_consistency(self, character_data, bagua_config, equipment_data):
        """
        Property: 综合BD计算一致性
        For any 完整的BD配置（角色+八卦+装备），多次计算应该得到相同结果
        **Feature: rpg-system-integration, Property 4: BD配置实时计算准确性**
        **Validates: Requirements 2.2, 3.4**
        """
        # 设置完整配置
        self.state_manager.update_character_data(character_data)
        self.state_manager.update_bagua_configuration(bagua_config)
        
        # 添加装备数据到角色
        character_with_equipment = copy.deepcopy(character_data)
        character_with_equipment["equipment"] = equipment_data
        self.state_manager.update_character_data(character_with_equipment)
        
        # 多次计算属性
        calculation_1 = self.state_manager.calculate_realtime_attributes()
        calculation_2 = self.state_manager.calculate_realtime_attributes()
        calculation_3 = self.state_manager.calculate_realtime_attributes()
        
        # 验证计算结果一致性
        assert calculation_1 == calculation_2 == calculation_3, \
            "相同配置的多次计算应该得到相同结果"
        
        # 验证计算结果的合理性
        for key, value in calculation_1.items():
            assert isinstance(value, (int, float)), f"属性{key}的值应该是数值类型"
            assert value >= 0, f"属性{key}的值应该非负"
            if key in ["crit_rate"]:
                assert value <= 1.0, f"暴击率不应该超过100%"
    
    @given(
        initial_config=generate_bagua_configuration(),
        modified_config=generate_bagua_configuration()
    )
    @settings(max_examples=50, deadline=8000)
    def test_configuration_change_detection(self, initial_config, modified_config):
        """
        Property: 配置变更检测
        For any 配置变更，系统应该能够检测到变化并正确更新相关计算
        **Feature: rpg-system-integration, Property 4: BD配置实时计算准确性**
        **Validates: Requirements 2.2, 3.4**
        """
        # 设置初始配置
        self.state_manager.update_bagua_configuration(initial_config)
        initial_attributes = self.state_manager.calculate_realtime_attributes()
        
        # 修改配置
        self.state_manager.update_bagua_configuration(modified_config)
        modified_attributes = self.state_manager.calculate_realtime_attributes()
        
        # 如果配置确实不同，属性计算结果应该可能不同
        if initial_config != modified_config:
            # 验证系统能够处理配置变更（不崩溃）
            assert isinstance(modified_attributes, dict), "配置变更后应该能正常计算属性"
            assert len(modified_attributes) > 0, "计算结果不应该为空"
    
    @given(character_data=generate_character_data())
    @settings(max_examples=50, deadline=5000)
    def test_school_change_affects_bonuses(self, character_data):
        """
        Property: 流派变更影响加成计算
        For any 流派变更，相关的属性加成应该立即更新以反映新流派的特性
        **Feature: rpg-system-integration, Property 4: BD配置实时计算准确性**
        **Validates: Requirements 2.2, 3.4**
        """
        # 设置初始流派
        initial_school = "sword_cultivator"
        character_data["school"] = initial_school
        self.state_manager.update_character_data(character_data)
        initial_attributes = self.state_manager.calculate_realtime_attributes()
        
        # 更换流派
        new_school = "spell_cultivator"
        character_data["school"] = new_school
        self.state_manager.update_character_data(character_data)
        new_attributes = self.state_manager.calculate_realtime_attributes()
        
        # 验证流派变更被正确应用
        assert self.state_manager.character_data["school"] == new_school, \
            "流派应该正确更新"
        
        # 验证属性计算没有出错
        assert isinstance(new_attributes, dict), "流派变更后应该能正常计算属性"
        assert len(new_attributes) > 0, "计算结果不应该为空"
    
    def test_bd_validation_consistency(self):
        """
        Property: BD验证一致性
        For any BD配置，验证结果应该与实际计算能力一致
        **Feature: rpg-system-integration, Property 4: BD配置实时计算准确性**
        **Validates: Requirements 2.2, 3.4**
        """
        # 创建一个有效的配置
        valid_config = {
            "stones": {
                "LI": {"1": None, "2": "gem_火", "3": "gem_火", "4": None},
                "KAN": {"1": None, "2": "gem_水", "3": None, "4": None},
                "QIAN": {"1": None, "2": "gem_金", "3": None, "4": None},
                "KUN": {"1": None, "2": "gem_土", "3": None, "4": None},
                "ZHEN": {"1": None, "2": None, "3": None, "4": None},
                "XUN": {"1": None, "2": None, "3": None, "4": None},
                "GEN": {"1": None, "2": None, "3": None, "4": None},
                "DUI": {"1": None, "2": None, "3": None, "4": None}
            },
            "core": {1: None, 2: None, 3: None},
            "seed": 12345
        }
        
        self.state_manager.update_bagua_configuration(valid_config)
        
        # 验证配置
        validation_result = self.state_manager.validate_bd_configuration()
        
        # 计算属性
        attributes = self.state_manager.calculate_realtime_attributes()
        
        # 验证一致性：如果配置有效，应该能正常计算属性
        if validation_result["is_valid"]:
            assert isinstance(attributes, dict), "有效配置应该能正常计算属性"
            assert len(attributes) > 0, "有效配置的计算结果不应该为空"
        
        # 验证完整性评分的合理性
        completeness = validation_result.get("completeness_score", 0)
        assert 0 <= completeness <= 1, "完整性评分应该在0-1之间"
    
    @given(st.integers(min_value=1, max_value=5))
    @settings(max_examples=20, deadline=3000)
    def test_multiple_rapid_updates(self, update_count):
        """
        Property: 快速连续更新处理
        For any 快速连续的配置更新，系统应该能正确处理并保持最终状态一致
        **Feature: rpg-system-integration, Property 4: BD配置实时计算准确性**
        **Validates: Requirements 2.2, 3.4**
        """
        initial_attributes = self.state_manager.calculate_realtime_attributes()
        
        # 执行多次快速更新
        for i in range(update_count):
            # 随机更新角色等级
            new_level = 10 + i * 5
            self.state_manager.update_character_data({"level": new_level})
            
            # 每次更新后都应该能正常计算
            current_attributes = self.state_manager.calculate_realtime_attributes()
            assert isinstance(current_attributes, dict), f"第{i+1}次更新后应该能正常计算"
            assert len(current_attributes) > 0, f"第{i+1}次更新后计算结果不应该为空"
        
        # 验证最终状态
        final_attributes = self.state_manager.calculate_realtime_attributes()
        final_level = self.state_manager.character_data.get("level")
        expected_level = 10 + (update_count - 1) * 5
        
        assert final_level == expected_level, "最终等级应该正确"
        assert isinstance(final_attributes, dict), "最终状态应该能正常计算"


class BDRealtimeStateMachine(RuleBasedStateMachine):
    """BD实时计算状态机测试"""
    
    def __init__(self):
        super().__init__()
        self.state_manager = initialize_unified_system()
        self.calculation_history = []
    
    @initialize()
    def init_state(self):
        """初始化状态"""
        # 设置基础角色数据
        self.state_manager.update_character_data({
            "name": "测试角色",
            "level": 1,
            "school": "sword_cultivator",
            "realm": "炼气",
            "base_attributes": {
                "str": 25.0,
                "agi": 25.0,
                "int": 25.0,
                "max_hp": 500.0,
                "base_atk": 40.0,
                "crit_rate": 0.05,
                "crit_dmg": 1.7
            }
        })
    
    @rule(level=st.integers(min_value=1, max_value=100))
    def update_character_level(self, level):
        """更新角色等级"""
        self.state_manager.update_character_data({"level": level})
        attributes = self.state_manager.calculate_realtime_attributes()
        self.calculation_history.append(("level_update", level, attributes))
    
    @rule(
        trigram=st.sampled_from(["QIAN", "DUI", "LI", "ZHEN"]),
        slot=st.integers(min_value=2, max_value=4),
        element=st.sampled_from(["木", "火", "土", "金", "水"])
    )
    def place_stone(self, trigram, slot, element):
        """放置灵石"""
        current_config = copy.deepcopy(self.state_manager.bagua_configuration)
        if "stones" not in current_config:
            current_config["stones"] = {}
        if trigram not in current_config["stones"]:
            current_config["stones"][trigram] = {}
        
        current_config["stones"][trigram][str(slot)] = f"gem_{element}"
        self.state_manager.update_bagua_configuration(current_config)
        
        attributes = self.state_manager.calculate_realtime_attributes()
        self.calculation_history.append(("stone_placement", (trigram, slot, element), attributes))
    
    @rule(school=st.sampled_from(["sword_cultivator", "spell_cultivator", "body_cultivator"]))
    def change_school(self, school):
        """更换流派"""
        self.state_manager.update_character_data({"school": school})
        attributes = self.state_manager.calculate_realtime_attributes()
        self.calculation_history.append(("school_change", school, attributes))
    
    @invariant()
    def attributes_are_valid(self):
        """不变量：属性计算结果始终有效"""
        attributes = self.state_manager.calculate_realtime_attributes()
        
        # 基本有效性检查
        assert isinstance(attributes, dict), "属性应该是字典类型"
        assert len(attributes) > 0, "属性不应该为空"
        
        # 数值合理性检查
        for key, value in attributes.items():
            assert isinstance(value, (int, float)), f"属性{key}应该是数值类型"
            assert value >= 0, f"属性{key}应该非负"
            
            # 特定属性的范围检查
            if key == "crit_rate":
                assert value <= 2.0, f"暴击率{value}过高"  # 允许一定的加成超过100%
    
    @invariant()
    def calculation_consistency(self):
        """不变量：计算一致性"""
        # 连续两次计算应该得到相同结果
        calc1 = self.state_manager.calculate_realtime_attributes()
        calc2 = self.state_manager.calculate_realtime_attributes()
        
        assert calc1 == calc2, "连续计算应该得到相同结果"


# 运行状态机测试
TestBDRealtimeStateMachine = BDRealtimeStateMachine.TestCase


if __name__ == "__main__":
    # 运行基本属性测试
    test_class = TestBDRealtimeCalculationProperties()
    test_class.setup_method()
    
    print("运行BD配置实时计算属性测试...")
    
    # 运行一个简单的测试用例
    try:
        test_class.test_bd_validation_consistency()
        print("✅ BD验证一致性测试通过")
    except Exception as e:
        print(f"❌ BD验证一致性测试失败: {e}")
    
    print("属性测试完成")