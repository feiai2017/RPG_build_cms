# -*- coding: utf-8 -*-
"""
五行八卦计算引擎的属性测试
Property-based tests for WuxingEngine
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import Dict, List, Any
from wuxing_engine import WuxingEngine, Stone


# 测试数据生成策略
@st.composite
def element_strategy(draw):
    """生成有效的五行元素"""
    return draw(st.sampled_from(["木", "火", "土", "金", "水"]))


@st.composite
def stone_strategy(draw):
    """生成测试用的灵石对象"""
    element = draw(st.sampled_from(["木", "火", "土", "金", "水", "无"]))
    stone_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    
    return Stone(
        id=stone_id,
        name=f"测试灵石_{stone_id}",
        element=element,
        icon="🔮",
        rarity=draw(st.sampled_from(["common", "rare", "epic", "legendary"])),
        bandwidth=draw(st.integers(min_value=1, max_value=10)),
        stock_total=draw(st.integers(min_value=1, max_value=5)),
        kind=draw(st.sampled_from(["gem", "logic", "core"])),
        effects={},
        logic={},
        core_rules={},
        desc="测试用灵石"
    )


@st.composite
def stones_list_strategy(draw):
    """生成灵石列表"""
    return draw(st.lists(stone_strategy(), min_size=0, max_size=15))


@st.composite
def bagua_configuration_strategy(draw):
    """生成八卦配置"""
    trigrams = ["QIAN", "DUI", "LI", "ZHEN", "XUN", "KAN", "GEN", "KUN"]
    
    stones_config = {}
    for trigram in trigrams:
        slots = {}
        for slot_idx in range(1, 5):  # 4个槽位
            # 随机决定是否放置灵石
            has_stone = draw(st.booleans())
            if has_stone:
                element = draw(st.sampled_from(["木", "火", "土", "金", "水"]))
                stone_id = f"gem_{element}_{slot_idx}"
            else:
                stone_id = None
            slots[slot_idx] = stone_id
        stones_config[trigram] = slots
    
    return {"stones": stones_config}


class TestWuxingEngine:
    """五行八卦计算引擎测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.engine = WuxingEngine()
    
    # Property 1: 五行相生相克计算正确性
    # **Validates: Requirements 1.2, 1.3, 1.4**
    
    @given(element_a=element_strategy(), element_b=element_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_wuxing_generation_destruction_correctness(self, element_a, element_b):
        """
        **Feature: rpg-system-integration, Property 1: 五行相生相克计算正确性**
        
        For any 五行灵石配置，当形成相生关系时，系统计算的属性加成应该为正值；
        当形成相克关系时，应该应用负面效果或警告
        """
        # 测试相生关系的正确性
        is_gen = self.engine.is_generation(element_a, element_b)
        is_dest = self.engine.is_destruction(element_a, element_b)
        
        # 相生和相克不能同时为真
        assert not (is_gen and is_dest), f"元素{element_a}和{element_b}不能同时为相生和相克关系"
        
        # 验证相生关系的传递性：如果A生B，B生C，那么A不直接生C
        if is_gen:
            element_c = self.engine.generation_cycle.get(element_b)
            if element_c:
                assert not self.engine.is_generation(element_a, element_c), \
                    f"相生关系不应该有传递性: {element_a}->{element_b}->{element_c}"
        
        # 验证相克关系的合理性
        if is_dest:
            # 被克的元素不应该反过来克制克制者
            assert not self.engine.is_destruction(element_b, element_a), \
                f"相克关系不应该是双向的: {element_a}克{element_b}，但{element_b}不应该克{element_a}"
    
    @given(stones=stones_list_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_element_synergy_calculation_consistency(self, stones):
        """
        **Feature: rpg-system-integration, Property 1: 五行相生相克计算正确性**
        
        For any 灵石组合，协同效果计算应该是一致的和合理的
        """
        # 过滤出有效的五行灵石
        valid_stones = [s for s in stones if s.element in self.engine.elements]
        
        if not valid_stones:
            return  # 跳过没有有效灵石的情况
        
        synergy = self.engine.calculate_element_synergy(valid_stones)
        
        # 验证返回结果的结构
        required_keys = ["generation_bonus", "destruction_penalty", "harmony_bonus", 
                        "conflict_penalty", "total_multiplier"]
        for key in required_keys:
            assert key in synergy, f"协同效果结果缺少必需字段: {key}"
        
        # 验证数值合理性
        assert 0.5 <= synergy["total_multiplier"] <= 2.0, \
            f"总倍率应该在合理范围内: {synergy['total_multiplier']}"
        
        # 验证相生加成为正值
        assert synergy["generation_bonus"] >= 0, \
            f"相生加成应该为非负值: {synergy['generation_bonus']}"
        
        # 验证相克惩罚为正值（表示惩罚程度）
        assert synergy["destruction_penalty"] >= 0, \
            f"相克惩罚应该为非负值: {synergy['destruction_penalty']}"
    
    @given(stones=stones_list_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_synergy_calculation_deterministic(self, stones):
        """
        **Feature: rpg-system-integration, Property 1: 五行相生相克计算正确性**
        
        For any 相同的灵石配置，多次计算应该得到相同的结果
        """
        valid_stones = [s for s in stones if s.element in self.engine.elements]
        
        if not valid_stones:
            return
        
        # 多次计算相同配置
        result1 = self.engine.calculate_element_synergy(valid_stones)
        result2 = self.engine.calculate_element_synergy(valid_stones)
        
        # 结果应该完全一致
        assert result1 == result2, "相同配置的协同效果计算结果应该一致"
    
    @given(element=element_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_counter_element_correctness(self, element):
        """
        **Feature: rpg-system-integration, Property 1: 五行相生相克计算正确性**
        
        For any 五行元素，其克制者应该能够克制它
        """
        counter = self.engine.get_counter_element(element)
        
        if counter != "无":
            # 克制者应该能克制原元素
            assert self.engine.is_destruction(counter, element), \
                f"克制元素{counter}应该能够克制{element}"
            
            # 原元素不应该克制其克制者
            assert not self.engine.is_destruction(element, counter), \
                f"被克制元素{element}不应该反过来克制{counter}"
    
    @given(stones=stones_list_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_synergy_monotonicity(self, stones):
        """
        **Feature: rpg-system-integration, Property 1: 五行相生相克计算正确性**
        
        For any 灵石配置，添加相生关系的灵石应该增加正面效果，
        添加相克关系的灵石应该增加负面效果
        """
        valid_stones = [s for s in stones if s.element in self.engine.elements and s.kind == "gem"]
        
        if len(valid_stones) < 2:
            return
        
        # 计算原始协同效果
        original_synergy = self.engine.calculate_element_synergy(valid_stones)
        
        # 添加一个与现有灵石形成相生关系的新灵石
        first_element = valid_stones[0].element
        generated_element = self.engine.generation_cycle.get(first_element)
        
        if generated_element:
            new_stone = Stone(
                id="test_generation",
                name="测试相生石",
                element=generated_element,
                icon="🔮",
                rarity="common",
                bandwidth=1,
                stock_total=1,
                kind="gem"
            )
            
            enhanced_stones = valid_stones + [new_stone]
            enhanced_synergy = self.engine.calculate_element_synergy(enhanced_stones)
            
            # 相生关系应该增加正面效果
            assert enhanced_synergy["generation_bonus"] >= original_synergy["generation_bonus"], \
                "添加相生关系的灵石应该增加或保持相生加成"


class TestWuxingEngineBaguaValidation:
    """八卦方位布局验证测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.engine = WuxingEngine()
    
    # Property 2: 八卦方位布局一致性
    # **Validates: Requirements 1.1**
    
    @given(config=bagua_configuration_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_bagua_position_layout_consistency(self, config):
        """
        **Feature: rpg-system-integration, Property 2: 八卦方位布局一致性**
        
        For any 八卦盘界面渲染，所有卦位应该严格按照后天八卦方位排列
        （乾西北、兑西、离南、震东、巽东南、坎北、艮东北、坤西南）
        """
        # 验证八卦方位的正确性
        expected_directions = {
            "QIAN": "西北",
            "DUI": "西", 
            "LI": "南",
            "ZHEN": "东",
            "XUN": "东南",
            "KAN": "北",
            "GEN": "东北",
            "KUN": "西南"
        }
        
        for trigram_name, expected_direction in expected_directions.items():
            assert trigram_name in self.engine.trigrams, f"缺少八卦定义: {trigram_name}"
            
            actual_direction = self.engine.trigrams[trigram_name]["direction"]
            assert actual_direction == expected_direction, \
                f"八卦{trigram_name}方位错误: 期望{expected_direction}，实际{actual_direction}"
    
    def test_property_bagua_ring_order_consistency(self):
        """
        **Feature: rpg-system-integration, Property 2: 八卦方位布局一致性**
        
        For any 八卦环形排列，应该按照正确的顺序连接
        """
        # 验证八卦环形顺序
        expected_ring = ["LI", "KUN", "DUI", "QIAN", "KAN", "GEN", "ZHEN", "XUN"]
        
        assert self.engine.bagua_ring == expected_ring, \
            f"八卦环形顺序错误: 期望{expected_ring}，实际{self.engine.bagua_ring}"
        
        # 验证环形连接的连续性
        for i in range(len(self.engine.bagua_ring)):
            current = self.engine.bagua_ring[i]
            next_trigram = self.engine.bagua_ring[(i + 1) % len(self.engine.bagua_ring)]
            
            # 确保相邻的八卦都有定义
            assert current in self.engine.trigrams, f"八卦环中的{current}未定义"
            assert next_trigram in self.engine.trigrams, f"八卦环中的{next_trigram}未定义"
    
    @given(config=bagua_configuration_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_bagua_configuration_validation_consistency(self, config):
        """
        **Feature: rpg-system-integration, Property 2: 八卦方位布局一致性**
        
        For any 八卦配置验证，应该返回一致的验证结果
        """
        is_valid, errors = self.engine.validate_bagua_configuration(config)
        
        # 验证返回值类型
        assert isinstance(is_valid, bool), "验证结果应该是布尔值"
        assert isinstance(errors, list), "错误列表应该是列表类型"
        
        # 如果有错误，is_valid应该为False
        if errors:
            assert not is_valid, "有验证错误时，is_valid应该为False"
        
        # 多次验证相同配置应该得到相同结果
        is_valid2, errors2 = self.engine.validate_bagua_configuration(config)
        assert is_valid == is_valid2, "相同配置的验证结果应该一致"
        assert errors == errors2, "相同配置的错误列表应该一致"
    
    def test_property_trigram_element_assignment_consistency(self):
        """
        **Feature: rpg-system-integration, Property 2: 八卦方位布局一致性**
        
        For any 八卦，其五行归属应该符合传统后天八卦理论
        """
        # 验证后天八卦的五行归属
        expected_elements = {
            "QIAN": "金",  # 乾卦属金
            "DUI": "金",   # 兑卦属金
            "LI": "火",    # 离卦属火
            "ZHEN": "木",  # 震卦属木
            "XUN": "木",   # 巽卦属木
            "KAN": "水",   # 坎卦属水
            "GEN": "土",   # 艮卦属土
            "KUN": "土"    # 坤卦属土
        }
        
        for trigram_name, expected_element in expected_elements.items():
            assert trigram_name in self.engine.trigrams, f"缺少八卦定义: {trigram_name}"
            
            actual_element = self.engine.trigrams[trigram_name]["elem"]
            assert actual_element == expected_element, \
                f"八卦{trigram_name}五行归属错误: 期望{expected_element}，实际{actual_element}"
    
    @given(trigram=st.sampled_from(["QIAN", "DUI", "LI", "ZHEN", "XUN", "KAN", "GEN", "KUN"]),
           stones=stones_list_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_trigram_effects_calculation_bounds(self, trigram, stones):
        """
        **Feature: rpg-system-integration, Property 2: 八卦方位布局一致性**
        
        For any 卦位效果计算，结果应该在合理的数值范围内
        """
        valid_stones = [s for s in stones if s.element in self.engine.elements]
        
        effects = self.engine.get_trigram_effects(trigram, valid_stones)
        
        # 验证返回结果的结构
        required_keys = ["base_multiplier", "element_synergy", "position_bonus", "resonance_effect"]
        for key in required_keys:
            assert key in effects, f"卦位效果结果缺少必需字段: {key}"
        
        # 验证数值范围的合理性
        if "final_multiplier" in effects:
            assert 0.3 <= effects["final_multiplier"] <= 3.0, \
                f"卦位效果倍率应该在合理范围内: {effects['final_multiplier']}"
        
        # 基础倍率应该为1.0
        assert effects["base_multiplier"] == 1.0, \
            f"基础倍率应该为1.0: {effects['base_multiplier']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])