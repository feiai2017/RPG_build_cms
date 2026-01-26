#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流派系统演示脚本
展示流派系统的核心功能和与统一状态管理器的集成
"""

from unified_state_manager import UnifiedStateManager
from cultivation_school_system import SchoolType, get_school_manager


def demo_cultivation_system():
    """演示流派系统的核心功能"""
    print("=== RPG流派系统演示 ===\n")
    
    # 初始化系统
    state_manager = UnifiedStateManager()
    school_manager = get_school_manager()
    
    print("1. 查看所有可用流派:")
    all_schools = school_manager.get_all_schools()
    for school_id, school in all_schools.items():
        print(f"   - {school.name} ({school_id}): {school.description}")
    
    print("\n2. 角色初始状态:")
    character_data = state_manager.character_data
    print(f"   姓名: {character_data.get('name', '未知')}")
    print(f"   等级: {character_data.get('level', 1)}")
    print(f"   流派: {character_data.get('school', '未知')}")
    
    # 获取当前流派信息
    school_info = state_manager.get_school_info()
    print(f"   流派名称: {school_info.get('name', '未知')}")
    print(f"   元素亲和: {school_info.get('element_affinity', '未知')}")
    
    print("\n3. 当前流派属性加成:")
    bonuses = school_info.get('attribute_bonuses', {})
    for attr, bonus in bonuses.items():
        print(f"   {attr}: +{bonus}")
    
    print("\n4. 可解锁技能:")
    available_skills = state_manager.get_available_skills()
    for skill in available_skills[:3]:  # 只显示前3个
        print(f"   - {skill['name']} (等级{skill['level_requirement']}): {skill['description']}")
    
    print("\n5. 切换到法修流派:")
    success = state_manager.change_character_school(SchoolType.SPELL.value)
    if success:
        print("   流派切换成功!")
        new_school_info = state_manager.get_school_info()
        print(f"   新流派: {new_school_info['name']}")
        print(f"   元素亲和: {new_school_info['element_affinity']}")
        
        print("   新的属性加成:")
        new_bonuses = new_school_info.get('attribute_bonuses', {})
        for attr, bonus in new_bonuses.items():
            print(f"     {attr}: +{bonus}")
    
    print("\n6. 提升等级并解锁技能:")
    state_manager.update_character_data({"level": 10})
    new_skills = state_manager.get_available_skills()
    
    if new_skills:
        first_skill = new_skills[0]
        unlock_success = state_manager.unlock_skill(first_skill['id'])
        if unlock_success:
            print(f"   成功解锁技能: {first_skill['name']}")
            print(f"   技能效果: {first_skill['effects']}")
    
    print("\n7. 装备推荐演示:")
    equipment_list = [
        {
            "name": "火焰法杖",
            "stats": {"int": 30, "elem_dmg_火": 20, "max_hp": 100}
        },
        {
            "name": "普通剑",
            "stats": {"base_atk": 40, "crit_rate": 0.1}
        },
        {
            "name": "法师长袍",
            "stats": {"int": 15, "max_hp": 150, "elem_dmg_火": 10}
        }
    ]
    
    recommendations = state_manager.recommend_equipment_for_school(equipment_list)
    print("   装备推荐排序 (按适配度):")
    for i, (equipment, score) in enumerate(recommendations, 1):
        print(f"   {i}. {equipment['name']} (适配度: {score:.1f})")
    
    print("\n8. 系统状态概览:")
    system_status = state_manager.get_system_status()
    print(f"   角色: {system_status['character_name']} (等级 {state_manager.character_data['level']})")
    print(f"   境界: {system_status['character_realm']}")
    print(f"   流派: {system_status['character_school']}")
    print(f"   八卦灵石数: {system_status['bagua_stones_count']}")
    print(f"   状态一致性: {'正常' if system_status['state_consistent'] else '异常'}")
    
    print("\n=== 演示完成 ===")


if __name__ == "__main__":
    demo_cultivation_system()