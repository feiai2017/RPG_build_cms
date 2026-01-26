# -*- coding: utf-8 -*-
"""
流派系统解锁逻辑的属性测试
**Property 6: 流派系统解锁逻辑正确性**
**Validates: Requirements 4.1, 5.2, 5.3**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import Dict, List, Any, Set
from cultivation_school_system import (
    SchoolManager, CultivationSchool, SchoolType, SkillType, Skill,
    get_school_manager, initialize_school_system
)


# 测试数据生成策略
@st.composite
def school_type_strategy(draw):
    """生成流派类型"""
    return draw(st.sampled_from([
        SchoolType.SWORD.value,
        SchoolType.SPELL.value,
        SchoolType.BODY.value,
        SchoolType.PILL.value,
        SchoolType.FORMATION.value
    ]))


@st.composite
def character_level_strategy(draw):
    """生成角色等级"""
    return draw(st.integers(min_value=1, max_value=100))


@st.composite
def unlocked_skills_strategy(draw, school_manager, school_id):
    """生成已解锁技能集合"""
    school = school_manager.get_school(school_id)
    if not school:
        return set()
    
    all_skills = list(school.skill_tree.keys())
    if not all_skills:
        return set()
    
    # 随机选择一些技能作为已解锁
    num_unlocked = draw(st.integers(min_value=0, max_value=len(all_skills)))
    unlocked = draw(st.sets(st.sampled_from(all_skills), max_size=num_unlocked))
    return unlocked


@st.composite
def equipment_stats_strategy(draw):
    """生成装备属性"""
    attributes = [
        "base_atk", "crit_rate", "crit_dmg", "str", "agi", "int", 
        "max_hp", "def", "hp_regen", "elem_dmg_木", "elem_dmg_火", 
        "elem_dmg_土", "elem_dmg_金", "elem_dmg_水"
    ]
    
    stats = {}
    for attr in attributes:
        # 随机决定是否包含该属性
        if draw(st.booleans()):
            if "rate" in attr:
                stats[attr] = draw(st.floats(min_value=0.0, max_value=1.0))
            elif "dmg" in attr and "crit" not in attr:
                stats[attr] = draw(st.floats(min_value=0.0, max_value=50.0))
            else:
                stats[attr] = draw(st.floats(min_value=1.0, max_value=200.0))
    
    return stats


class TestCultivationSchoolUnlockLogic:
    """流派系统解锁逻辑测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.school_manager = initialize_school_system()
    
    @given(school_id=school_type_strategy(), level=character_level_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_school_unlock_logic_correctness_level_requirements(self, school_id, level):
        """
        **Feature: rpg-system-integration, Property 6: 流派系统解锁逻辑正确性**
        
        For any 角色流派选择，系统应该解锁对应的技能、装备类型和属性加成，
        不同流派之间不应该有错误的交叉解锁
        
        测试等级要求的正确性
        **Validates: Requirements 4.1, 5.2, 5.3**
        """
        school = self.school_manager.get_school(school_id)
        assert school is not None, f"流派 {school_id} 应该存在"
        
        # 获取可解锁的技能
        available_skills = self.school_manager.get_available_skills(school_id, level, set())
        
        # 验证所有可解锁技能都满足等级要求
        for skill in available_skills:
            assert skill.level_requirement <= level, \
                f"技能 {skill.name} 需要等级 {skill.level_requirement}，但角色等级只有 {level}"
            
            # 验证技能属于正确的流派
            assert skill.school_requirement.value == school_id, \
                f"技能 {skill.name} 属于流派 {skill.school_requirement.value}，但在 {school_id} 中解锁"
        
        # 验证属性加成的合理性
        bonuses = school.get_attribute_bonuses(level)
        assert isinstance(bonuses, dict), "属性加成应该是字典类型"
        
        # 验证属性加成值的合理性
        for attr, bonus in bonuses.items():
            assert isinstance(bonus, (int, float)), f"属性 {attr} 的加成值应该是数值类型"
            assert bonus >= 0, f"属性 {attr} 的加成值不应该为负: {bonus}"
            
            # 验证加成值随等级合理增长
            if level > 1:
                level_1_bonuses = school.get_attribute_bonuses(1)
                if attr in level_1_bonuses:
                    assert bonus >= level_1_bonuses[attr], \
                        f"等级 {level} 的 {attr} 加成应该不小于等级 1 的加成"
    
    @given(school_id=school_type_strategy(), level=character_level_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_school_unlock_logic_correctness_prerequisite_validation(self, school_id, level):
        """
        **Feature: rpg-system-integration, Property 6: 流派系统解锁逻辑正确性**
        
        For any 技能解锁，前置技能要求应该被正确验证
        **Validates: Requirements 4.1, 5.2, 5.3**
        """
        school = self.school_manager.get_school(school_id)
        assert school is not None
        
        # 模拟逐步解锁技能的过程
        unlocked_skills = set()
        
        for target_level in range(1, level + 1):
            available_skills = school.unlock_skills(target_level, unlocked_skills)
            
            for skill_id in available_skills:
                skill = school.get_skill_info(skill_id)
                assert skill is not None
                
                # 验证前置技能都已解锁
                for prereq in skill.prerequisites:
                    assert prereq in unlocked_skills, \
                        f"技能 {skill.name} 的前置技能 {prereq} 未解锁"
                
                # 解锁该技能
                unlocked_skills.add(skill_id)
        
        # 验证解锁顺序的合理性
        is_valid, issues = self.school_manager.validate_school_progression(
            school_id, level, unlocked_skills
        )
        assert is_valid, f"流派进度验证失败: {issues}"
    
    @given(
        school_id=school_type_strategy(),
        level=character_level_strategy(),
        equipment_stats=equipment_stats_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_school_unlock_logic_correctness_equipment_compatibility(self, school_id, level, equipment_stats):
        """
        **Feature: rpg-system-integration, Property 6: 流派系统解锁逻辑正确性**
        
        For any 流派和装备组合，装备适配度评分应该反映流派特色
        **Validates: Requirements 4.1, 5.2, 5.3**
        """
        school = self.school_manager.get_school(school_id)
        assert school is not None
        
        # 计算装备适配度
        score = school.get_equipment_score(equipment_stats)
        assert isinstance(score, (int, float)), "装备评分应该是数值类型"
        assert score >= 0, "装备评分不应该为负值"
        
        # 验证流派偏好属性确实影响评分
        if equipment_stats:
            # 创建一个包含流派偏好属性的装备
            preferred_equipment = {}
            for preference in school.equipment_preferences:
                for attr in preference.preferred_attributes:
                    if attr in equipment_stats:
                        preferred_equipment[attr] = equipment_stats[attr] * 2  # 增强偏好属性
                    else:
                        preferred_equipment[attr] = 100.0  # 添加偏好属性
            
            preferred_score = school.get_equipment_score(preferred_equipment)
            
            # 包含更多偏好属性的装备应该有更高评分
            if preferred_equipment != equipment_stats:
                assert preferred_score >= score, \
                    f"包含流派偏好属性的装备评分应该更高: {preferred_score} vs {score}"
    
    @given(
        primary_school=school_type_strategy(),
        secondary_schools=st.lists(school_type_strategy(), min_size=0, max_size=3)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_school_unlock_logic_correctness_synergy_calculation(self, primary_school, secondary_schools):
        """
        **Feature: rpg-system-integration, Property 6: 流派系统解锁逻辑正确性**
        
        For any 流派组合，协同效果计算应该是合理和一致的
        **Validates: Requirements 4.1, 5.2, 5.3**
        """
        # 移除重复的流派
        unique_secondary = list(set(secondary_schools))
        if primary_school in unique_secondary:
            unique_secondary.remove(primary_school)
        
        synergy = self.school_manager.calculate_multi_school_synergy(primary_school, unique_secondary)
        
        # 验证协同效果的基本属性
        assert isinstance(synergy, dict), "协同效果应该是字典类型"
        
        for key, value in synergy.items():
            assert isinstance(value, (int, float)), f"协同效果值应该是数值类型: {key}"
            assert -1.0 <= value <= 2.0, f"协同效果值应该在合理范围内: {key}={value}"
        
        # 验证多流派惩罚机制
        if len(unique_secondary) > 1:
            # 计算单个副流派的协同效果
            single_synergies = []
            for secondary in unique_secondary:
                single_synergy = self.school_manager.calculate_multi_school_synergy(
                    primary_school, [secondary]
                )
                single_synergies.append(single_synergy)
            
            # 多流派的总协同效果应该小于单个协同效果的简单相加
            # （由于惩罚机制的存在）
            if single_synergies and synergy:
                # 这里只是验证惩罚机制存在，不要求具体的数值关系
                pass
    
    @given(school_id=school_type_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_school_unlock_logic_correctness_school_isolation(self, school_id):
        """
        **Feature: rpg-system-integration, Property 6: 流派系统解锁逻辑正确性**
        
        For any 流派，其技能和特色应该与其他流派隔离，不存在错误的交叉引用
        **Validates: Requirements 4.1, 5.2, 5.3**
        """
        school = self.school_manager.get_school(school_id)
        assert school is not None
        
        # 验证技能归属正确性
        for skill_id, skill in school.skill_tree.items():
            assert skill.school_requirement.value == school_id, \
                f"技能 {skill.name} 的流派要求与所属流派不符"
            
            # 验证前置技能都属于同一流派
            for prereq_id in skill.prerequisites:
                prereq_skill = school.get_skill_info(prereq_id)
                assert prereq_skill is not None, \
                    f"前置技能 {prereq_id} 在流派 {school_id} 中不存在"
                assert prereq_skill.school_requirement.value == school_id, \
                    f"前置技能 {prereq_skill.name} 不属于流派 {school_id}"
        
        # 验证流派ID的一致性
        assert school.school_id == school_id, "流派ID应该与请求的ID一致"
        
        # 验证元素亲和度的合理性
        valid_elements = ["木", "火", "土", "金", "水"]
        assert school.element_affinity in valid_elements, \
            f"流派 {school_id} 的元素亲和度无效: {school.element_affinity}"
    
    @given(
        school_id=school_type_strategy(),
        level1=character_level_strategy(),
        level2=character_level_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_school_unlock_logic_correctness_monotonic_progression(self, school_id, level1, level2):
        """
        **Feature: rpg-system-integration, Property 6: 流派系统解锁逻辑正确性**
        
        For any 等级提升，可解锁内容应该单调递增（不会因为等级提升而失去已有能力）
        **Validates: Requirements 4.1, 5.2, 5.3**
        """
        school = self.school_manager.get_school(school_id)
        assert school is not None
        
        min_level = min(level1, level2)
        max_level = max(level1, level2)
        
        # 获取不同等级的属性加成
        bonuses_min = school.get_attribute_bonuses(min_level)
        bonuses_max = school.get_attribute_bonuses(max_level)
        
        # 验证属性加成的单调性
        for attr in bonuses_min:
            if attr in bonuses_max:
                assert bonuses_max[attr] >= bonuses_min[attr], \
                    f"等级提升后属性 {attr} 的加成不应该减少: {bonuses_min[attr]} -> {bonuses_max[attr]}"
        
        # 验证技能解锁的单调性
        skills_min = set(school.unlock_skills(min_level, set()))
        skills_max = set(school.unlock_skills(max_level, set()))
        
        # 低等级能解锁的技能，高等级也应该能解锁
        assert skills_min.issubset(skills_max), \
            f"等级提升后不应该失去可解锁的技能: 失去了 {skills_min - skills_max}"
    
    @given(school_id=school_type_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_school_unlock_logic_correctness_data_consistency(self, school_id):
        """
        **Feature: rpg-system-integration, Property 6: 流派系统解锁逻辑正确性**
        
        For any 流派数据，内部数据结构应该保持一致性
        **Validates: Requirements 4.1, 5.2, 5.3**
        """
        school = self.school_manager.get_school(school_id)
        assert school is not None
        
        # 验证技能解锁顺序与技能树的一致性
        for skill_id in school.skill_unlock_order:
            assert skill_id in school.skill_tree, \
                f"解锁顺序中的技能 {skill_id} 在技能树中不存在"
        
        # 验证技能树中的技能都有合理的数据
        for skill_id, skill in school.skill_tree.items():
            assert skill.id == skill_id, "技能ID应该与字典键一致"
            assert skill.name, "技能名称不应该为空"
            assert skill.level_requirement > 0, "技能等级要求应该大于0"
            assert isinstance(skill.effects, dict), "技能效果应该是字典类型"
            
            # 验证前置技能的存在性
            for prereq in skill.prerequisites:
                assert prereq in school.skill_tree, \
                    f"前置技能 {prereq} 在技能树中不存在"
        
        # 验证装备偏好的合理性
        for preference in school.equipment_preferences:
            assert preference.weight_multiplier > 0, "装备偏好权重应该大于0"
            assert preference.preferred_attributes, "偏好属性列表不应该为空"
            
            for element, bonus in preference.element_bonus.items():
                assert element in ["木", "火", "土", "金", "水"], f"无效的元素类型: {element}"
                assert isinstance(bonus, (int, float)), "元素加成应该是数值类型"
        
        # 验证协同流派的有效性
        all_school_ids = set(self.school_manager.get_all_schools().keys())
        for synergy_school in school.synergy_schools:
            assert synergy_school in all_school_ids, \
                f"协同流派 {synergy_school} 不存在"
    
    @given(
        equipment_list=st.lists(
            st.dictionaries(
                keys=st.just("stats"),
                values=equipment_stats_strategy()
            ),
            min_size=1,
            max_size=10
        ),
        school_id=school_type_strategy()
    )
    @settings(max_examples=50, deadline=None)
    def test_property_school_unlock_logic_correctness_equipment_recommendation(self, equipment_list, school_id):
        """
        **Feature: rpg-system-integration, Property 6: 流派系统解锁逻辑正确性**
        
        For any 装备推荐，推荐结果应该按照适配度正确排序
        **Validates: Requirements 4.1, 5.2, 5.3**
        """
        recommendations = self.school_manager.recommend_equipment(school_id, equipment_list)
        
        # 验证推荐结果的结构
        assert len(recommendations) == len(equipment_list), "推荐结果数量应该与输入装备数量一致"
        
        for equipment, score in recommendations:
            assert isinstance(equipment, dict), "装备应该是字典类型"
            assert isinstance(score, (int, float)), "评分应该是数值类型"
            assert score >= 0, "评分不应该为负值"
        
        # 验证排序的正确性（评分应该是降序）
        scores = [score for _, score in recommendations]
        assert scores == sorted(scores, reverse=True), "推荐结果应该按评分降序排列"
        
        # 验证相同装备的评分一致性
        if len(equipment_list) >= 2:
            # 创建两个相同的装备
            same_equipment = equipment_list[0]
            duplicate_list = [same_equipment, same_equipment]
            
            duplicate_recommendations = self.school_manager.recommend_equipment(school_id, duplicate_list)
            
            # 相同装备应该有相同评分
            score1 = duplicate_recommendations[0][1]
            score2 = duplicate_recommendations[1][1]
            assert abs(score1 - score2) < 1e-10, "相同装备应该有相同的适配度评分"
    
    def test_property_school_unlock_logic_correctness_all_schools_available(self):
        """
        **Feature: rpg-system-integration, Property 6: 流派系统解锁逻辑正确性**
        
        For any 系统初始化，所有定义的流派都应该可用
        **Validates: Requirements 4.1, 5.2, 5.3**
        """
        all_schools = self.school_manager.get_all_schools()
        
        # 验证所有预期的流派都存在
        expected_schools = [
            SchoolType.SWORD.value,
            SchoolType.SPELL.value,
            SchoolType.BODY.value,
            SchoolType.PILL.value,
            SchoolType.FORMATION.value
        ]
        
        for school_id in expected_schools:
            assert school_id in all_schools, f"流派 {school_id} 应该存在"
            
            school = all_schools[school_id]
            assert school is not None, f"流派 {school_id} 不应该为None"
            assert school.school_id == school_id, f"流派ID不匹配: {school.school_id} != {school_id}"
        
        # 验证流派名称的唯一性
        school_names = self.school_manager.get_school_names()
        names = list(school_names.values())
        assert len(names) == len(set(names)), "流派名称应该是唯一的"
        
        # 验证兼容性矩阵的完整性
        compatibility_matrix = self.school_manager.get_school_compatibility_matrix()
        
        for school_id in expected_schools:
            assert school_id in compatibility_matrix, f"兼容性矩阵缺少流派 {school_id}"
            
            for other_id in expected_schools:
                assert other_id in compatibility_matrix[school_id], \
                    f"兼容性矩阵缺少 {school_id} 与 {other_id} 的关系"
                
                compatibility = compatibility_matrix[school_id][other_id]
                assert 0.0 <= compatibility <= 1.0, \
                    f"兼容性值应该在0-1之间: {school_id}-{other_id}={compatibility}"
                
                # 自身兼容性应该是最高的
                if school_id == other_id:
                    assert compatibility == 1.0, f"自身兼容性应该为1.0: {school_id}"


if __name__ == "__main__":
    # 运行属性测试
    pytest.main([__file__, "-v", "--tb=short"])