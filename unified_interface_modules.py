# -*- coding: utf-8 -*-
"""
统一界面模块 (Unified Interface Modules)
整合app.py和app_five_elements.py的UI组件
设计统一的主界面包含所有功能模块
优化八卦盘视觉效果和交互体验
实现模块间无缝切换和状态保持
"""

import streamlit as st
import logging
import copy
from typing import Dict, Any, List, Optional
from unified_state_manager import get_state_manager
from wuxing_engine import WuxingEngine
from wuxing_board import generate_board, NodeType, ELEMENTS
from wuxing_board.board_render import render_board_plotly
from streamlit_plotly_events import plotly_events
from wuxing_rules import evaluate_wuxing_rules, example_builds
from enhanced_combat_engine import EnhancedCombatEngine
from cultivation_school_system import get_school_manager
from loot_generator import get_loot_generator, get_challenge_manager, get_bd_optimizer
from performance_optimizer import get_performance_optimizer, render_performance_dashboard
from help_system import get_help_system
from balance_system import get_balance_system

logger = logging.getLogger(__name__)


def render_system_overview():
    """渲染系统概览页面"""
    st.title("🏠 系统概览")
    st.caption("统一RPG数值验证和游戏系统 - 集成五行八卦、战斗模拟、流派管理和刷宝系统")
    
    state_manager = get_state_manager()
    
    # 角色信息卡片
    with st.container(border=True):
        st.subheader("👤 角色信息")
        
        col1, col2, col3 = st.columns(3)
        
        char_data = state_manager.character_data
        with col1:
            st.metric("角色名称", char_data.get("name", "未设置"))
            st.metric("当前等级", char_data.get("level", 1))
        
        with col2:
            st.metric("修真境界", char_data.get("realm", "炼气"))
            st.metric("修真流派", char_data.get("school", "剑修"))
        
        with col3:
            st.metric("主灵根", char_data.get("affinity_main", "木"))
            bagua_stones = sum(1 for tri_data in state_manager.bagua_configuration.get("stones", {}).values() 
                             for stone in tri_data.values() if stone)
            st.metric("已装灵石", bagua_stones)
    
    # 系统状态
    with st.container(border=True):
        st.subheader("⚙️ 系统状态")
        
        status = state_manager.get_system_status()
        
        col1, col2 = st.columns(2)
        with col1:
            if status["state_consistent"]:
                st.success("✅ 系统状态一致")
            else:
                st.error("❌ 系统状态不一致")
                for issue in status["consistency_issues"]:
                    st.caption(f"• {issue}")
        
        with col2:
            st.info(f"📅 最后同步: {status['last_sync'][:19]}")
    
    # 快速操作
    with st.container(border=True):
        st.subheader("🚀 快速操作")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 同步所有模块", use_container_width=True):
                state_manager.sync_modules()
                st.success("模块同步完成")
        
        with col2:
            if st.button("💾 保存当前状态", use_container_width=True):
                if state_manager.save_state():
                    st.success("状态保存成功")
                else:
                    st.error("状态保存失败")
        
        with col3:
            if st.button("📊 生成系统报告", use_container_width=True):
                st.info("系统报告功能开发中...")


def render_wuxing_bagua_interface():
    """渲染五行八卦盘界面"""
    st.title("☯️ 五行八卦灵石盘")
    st.caption("真正的道教五行八卦理论，体验沉浸式的修真配置")
    
    # 这里会集成app_five_elements.py的完整界面
    # 由于代码量较大，这里先提供框架
    
    state_manager = get_state_manager()
    wuxing_engine = WuxingEngine()
    
    # 获取五行模块状态
    five_elements_state = state_manager.get_module_state("five_elements")
    
    st.info("五行八卦盘界面正在集成中，将包含完整的八卦配置功能")
    
    # 显示当前八卦配置
    with st.expander("当前八卦配置", expanded=True):
        bagua_config = state_manager.bagua_configuration
        
        if bagua_config.get("stones"):
            for trigram, slots in bagua_config["stones"].items():
                if any(slots.values()):
                    st.write(f"**{trigram}**: {[stone for stone in slots.values() if stone]}")
        else:
            st.info("暂无八卦配置")


def render_combat_simulation():
    """渲染战斗模拟界面"""
    st.title("⚔️ 增强战斗模拟")
    st.caption("集成五行八卦效果的深度战斗分析系统")
    
    state_manager = get_state_manager()
    
    # 这里会集成增强的战斗引擎
    st.info("增强战斗模拟界面开发中，将包含：")
    st.markdown("""
    - 🔥 五行八卦效果集成
    - 📊 实时DPS分析
    - 🛡️ 生存能力评估
    - ⚡ 技能链优化建议
    - 📈 战斗数据记录
    """)


def render_school_management():
    """渲染流派管理界面"""
    st.title("🎓 修真流派管理")
    st.caption("管理角色流派、技能解锁和进阶系统")
    
    state_manager = get_state_manager()
    school_manager = get_school_manager()
    
    # 当前流派信息
    with st.container(border=True):
        st.subheader("当前流派")
        
        school_info = state_manager.get_school_info()
        if school_info:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("流派名称", school_info["name"])
                st.metric("元素亲和", school_info["element_affinity"])
            
            with col2:
                st.write("**流派描述**")
                st.caption(school_info["description"])
        else:
            st.warning("未设置流派")
    
    # 可用技能
    with st.container(border=True):
        st.subheader("可解锁技能")
        
        available_skills = state_manager.get_available_skills()
        if available_skills:
            for skill in available_skills:
                with st.expander(f"{skill['name']} (Lv.{skill['level_requirement']})"):
                    st.write(skill['description'])
                    if skill['effects']:
                        st.json(skill['effects'])
        else:
            st.info("暂无可解锁技能")


def render_loot_system():
    """渲染刷宝系统界面"""
    st.title("💎 智能刷宝系统")
    st.caption("基于流派特色的智能掉落和装备优化")
    
    state_manager = get_state_manager()
    loot_generator = get_loot_generator()
    challenge_manager = get_challenge_manager()
    
    # 挑战选择
    with st.container(border=True):
        st.subheader("选择挑战")
        
        char_level = state_manager.character_data.get("level", 1)
        available_challenges = challenge_manager.get_available_challenges(char_level)
        
        if available_challenges:
            challenge_names = [c["name"] for c in available_challenges]
            selected_challenge = st.selectbox("可用挑战", challenge_names)
            
            if selected_challenge:
                challenge = next(c for c in available_challenges if c["name"] == selected_challenge)
                st.write(f"**描述**: {challenge['description']}")
                st.write(f"**等级要求**: {challenge['level_requirement']}")
                
                if st.button("开始挑战"):
                    st.success(f"挑战 {selected_challenge} 开始！")
        else:
            st.info("暂无可用挑战")
    
    # 装备库存
    with st.container(border=True):
        st.subheader("装备库存")
        
        inventory = state_manager.loot_inventory
        if inventory:
            for item in inventory[:5]:  # 显示前5个物品
                st.write(f"• {item.get('name', '未知物品')}")
        else:
            st.info("库存为空")


def render_bd_analysis():
    """渲染BD分析界面"""
    st.title("📊 BD配置分析")
    st.caption("深度分析当前BD配置，提供优化建议")
    
    state_manager = get_state_manager()
    bd_optimizer = get_bd_optimizer()
    
    # 实时BD验证和分析
    with st.container(border=True):
        st.subheader("🔍 实时BD验证")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 验证当前配置", use_container_width=True):
                validation_result = state_manager.validate_bd_configuration()
                
                if validation_result["is_valid"]:
                    st.success("✅ 配置有效")
                else:
                    st.error("❌ 配置存在问题")
                    for error in validation_result["errors"]:
                        st.caption(f"• {error}")
                
                # 显示完整性评分
                completeness = validation_result.get("completeness_score", 0)
                st.metric("配置完整性", f"{completeness:.1%}")
                
                # 显示建议
                if validation_result.get("suggestions"):
                    st.write("**建议**")
                    for suggestion in validation_result["suggestions"]:
                        st.info(f"💡 {suggestion}")
        
        with col2:
            if st.button("⚡ 一键战斗测试", use_container_width=True):
                with st.spinner("执行战斗测试..."):
                    test_result = state_manager.perform_one_click_combat_test()
                
                if test_result["success"]:
                    st.success("✅ 战斗测试完成")
                    
                    # 显示性能分析
                    perf = test_result["performance_analysis"]
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("平均DPS", f"{perf.get('average_dps', 0):.1f}")
                        st.metric("战斗结果", perf.get('result', 'unknown'))
                    
                    with col_b:
                        st.metric("生存评分", f"{perf.get('survivability_score', 0):.1f}")
                        st.metric("效率评级", f"{perf.get('efficiency_rating', 0):.1f}")
                    
                    # 显示优化建议
                    if test_result.get("optimization_suggestions"):
                        st.write("**战斗优化建议**")
                        for suggestion in test_result["optimization_suggestions"]:
                            st.warning(f"⚠️ {suggestion}")
                else:
                    st.error(f"❌ 战斗测试失败: {test_result.get('error', '未知错误')}")
    
    # 实时属性计算和显示
    with st.container(border=True):
        st.subheader("📈 实时属性计算")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 计算当前属性
            current_attrs = state_manager.calculate_realtime_attributes()
            
            # 显示主要属性
            st.write("**核心属性**")
            core_attrs = ["str", "agi", "int", "max_hp", "base_atk"]
            
            attr_cols = st.columns(len(core_attrs))
            for i, attr in enumerate(core_attrs):
                value = current_attrs.get(attr, 0)
                attr_cols[i].metric(attr.upper(), f"{value:.1f}")
            
            # 显示战斗属性
            st.write("**战斗属性**")
            combat_attrs = ["crit_rate", "crit_dmg", "def"]
            
            combat_cols = st.columns(len(combat_attrs))
            for i, attr in enumerate(combat_attrs):
                value = current_attrs.get(attr, 0)
                if attr == "crit_rate":
                    combat_cols[i].metric("暴击率", f"{value:.1%}")
                elif attr == "crit_dmg":
                    combat_cols[i].metric("暴击伤害", f"{value:.2f}x")
                else:
                    combat_cols[i].metric(attr.upper(), f"{value:.1f}")
            
            # 显示元素伤害
            st.write("**元素伤害**")
            element_attrs = [key for key in current_attrs.keys() if key.startswith("elem_dmg_")]
            
            if element_attrs:
                elem_cols = st.columns(min(len(element_attrs), 5))
                for i, attr in enumerate(element_attrs[:5]):
                    element = attr.replace("elem_dmg_", "")
                    value = current_attrs.get(attr, 0)
                    elem_cols[i].metric(f"{element}伤害", f"{value:.1f}")
        
        with col2:
            st.write("**属性来源分析**")
            
            # 分析属性来源
            base_attrs = state_manager.character_data.get("base_attributes", {})
            bagua_bonuses = state_manager._calculate_bagua_bonuses()
            school_bonuses = state_manager._calculate_school_bonuses()
            
            # 显示加成分布
            if bagua_bonuses:
                total_bagua = sum(abs(v) for v in bagua_bonuses.values() if isinstance(v, (int, float)))
                st.metric("八卦加成", f"{total_bagua:.1f}")
            
            if school_bonuses:
                total_school = sum(abs(v) for v in school_bonuses.values() if isinstance(v, (int, float)))
                st.metric("流派加成", f"{total_school:.1f}")
    
    # BD分析和优化建议
    with st.container(border=True):
        st.subheader("🎯 BD优化建议")
        
        if st.button("🔍 分析当前BD", use_container_width=True):
            # 获取优化建议
            suggestions = state_manager.get_bd_optimization_suggestions()
            
            if suggestions:
                # 按优先级分组显示
                high_priority = [s for s in suggestions if s.get("priority") == "high"]
                medium_priority = [s for s in suggestions if s.get("priority") == "medium"]
                low_priority = [s for s in suggestions if s.get("priority") == "low"]
                
                if high_priority:
                    st.write("**🔴 高优先级建议**")
                    for suggestion in high_priority:
                        st.error(f"• {suggestion['description']}")
                        if suggestion.get("suggested_improvement"):
                            st.caption(f"  建议: {suggestion['suggested_improvement']}")
                
                if medium_priority:
                    st.write("**🟡 中优先级建议**")
                    for suggestion in medium_priority:
                        st.warning(f"• {suggestion['description']}")
                        if suggestion.get("suggested_improvement"):
                            st.caption(f"  建议: {suggestion['suggested_improvement']}")
                
                if low_priority:
                    st.write("**🟢 低优先级建议**")
                    for suggestion in low_priority:
                        st.info(f"• {suggestion['description']}")
                        if suggestion.get("suggested_improvement"):
                            st.caption(f"  建议: {suggestion['suggested_improvement']}")
            else:
                st.success("🎉 当前BD配置已经很优秀！")
    
    # 配置对比和调试信息
    with st.container(border=True):
        st.subheader("🔧 配置对比和调试")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**配置快照管理**")
            
            snapshot_name = st.text_input("快照名称", placeholder="输入快照名称")
            
            if st.button("📸 创建配置快照", use_container_width=True):
                if snapshot_name:
                    success = state_manager.create_configuration_snapshot(snapshot_name)
                    if success:
                        st.success(f"快照 '{snapshot_name}' 创建成功")
                    else:
                        st.error("快照创建失败")
                else:
                    st.warning("请输入快照名称")
        
        with col2:
            st.write("**调试信息**")
            
            if st.button("🐛 显示调试信息", use_container_width=True):
                debug_info = {
                    "角色数据": state_manager.character_data,
                    "八卦配置": state_manager.bagua_configuration,
                    "战斗设置": state_manager.combat_settings
                }
                
                with st.expander("调试信息详情", expanded=False):
                    st.json(debug_info)
    
    # 性能分析图表
    with st.container(border=True):
        st.subheader("📊 性能分析图表")
        
        if st.button("📈 生成性能报告", use_container_width=True):
            # 模拟性能数据（实际应用中会从战斗记录获取）
            import pandas as pd
            import numpy as np
            
            # 创建模拟数据
            time_points = np.arange(0, 20, 0.5)
            dps_data = 150 + 30 * np.sin(time_points * 0.5) + np.random.normal(0, 10, len(time_points))
            hp_data = 500 - time_points * 15 + np.random.normal(0, 5, len(time_points))
            
            df = pd.DataFrame({
                "时间": time_points,
                "DPS": np.maximum(0, dps_data),
                "生命值": np.maximum(0, hp_data)
            })
            
            # 显示图表
            col1, col2 = st.columns(2)
            
            with col1:
                st.line_chart(df.set_index("时间")["DPS"])
                st.caption("DPS变化趋势")
            
            with col2:
                st.line_chart(df.set_index("时间")["生命值"])
                st.caption("生命值变化趋势")


def render_system_settings():
    """渲染系统设置界面"""
    st.title("⚙️ 系统设置")
    st.caption("配置系统参数和数据管理")
    
    state_manager = get_state_manager()
    
    # 角色设置
    with st.container(border=True):
        st.subheader("角色设置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_name = st.text_input("角色名称", value=state_manager.character_data.get("name", ""))
            new_level = st.number_input("角色等级", min_value=1, max_value=100, 
                                      value=state_manager.character_data.get("level", 1))
        
        with col2:
            realms = ["炼气", "筑基", "金丹", "元婴", "化神"]
            current_realm = state_manager.character_data.get("realm", "炼气")
            new_realm = st.selectbox("修真境界", realms, index=realms.index(current_realm))
            
            elements = ["木", "火", "土", "金", "水"]
            current_affinity = state_manager.character_data.get("affinity_main", "木")
            new_affinity = st.selectbox("主灵根", elements, index=elements.index(current_affinity))
        
        if st.button("保存角色设置"):
            updates = {
                "name": new_name,
                "level": new_level,
                "realm": new_realm,
                "affinity_main": new_affinity
            }
            state_manager.update_character_data(updates)
            st.success("角色设置已保存")
    
    # 数据管理
    with st.container(border=True):
        st.subheader("数据管理")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("导出配置", use_container_width=True):
                timestamp = st.session_state.get('export_timestamp', '未导出')
                if state_manager.export_configuration(f"rpg_config_{timestamp}.json"):
                    st.success("配置导出成功")
        
        with col2:
            uploaded_file = st.file_uploader("导入配置", type=['json', 'yaml'])
            if uploaded_file and st.button("导入", use_container_width=True):
                # 这里需要处理文件导入逻辑
                st.info("导入功能开发中...")
        
        with col3:
            if st.button("重置系统", use_container_width=True):
                if st.session_state.get('confirm_reset'):
                    # 重置逻辑
                    st.success("系统已重置")
                    st.session_state['confirm_reset'] = False
                else:
                    st.session_state['confirm_reset'] = True
                    st.warning("再次点击确认重置")


def render_traditional_interface():
    """渲染传统界面（原app.py功能）"""
    st.title("📄 传统界面")
    st.caption("保留原有的RPG工具箱功能")
    
    st.info("这里将保留原有app.py的所有功能，包括：")
    st.markdown("""
    - ⚔️ 简单战斗模拟
    - ⛓️ 技能链构建
    - 🧪 MVP验证Demo
    - 🎨 可视化编辑器
    - 📄 原始YAML/时光机
    - 📖 在线白皮书
    """)
    
    # 这里可以嵌入原有的app.py功能
    st.warning("传统界面功能正在迁移中...")


# 主界面路由函数
def render_unified_interface():
    """渲染统一界面的主函数"""
    
    # 渲染导航
    from app import render_unified_navigation
    page_mode = render_unified_navigation()
    
    # 根据选择的页面渲染对应界面
    if page_mode == "🏠 系统概览":
        render_system_overview()
    elif page_mode == "☯️ 五行八卦盘":
        render_wuxing_bagua_interface()
    elif page_mode == "⚔️ 战斗模拟":
        render_combat_simulation()
    elif page_mode == "🎓 流派管理":
        render_school_management()
    elif page_mode == "💎 刷宝系统":
        render_loot_system()
    elif page_mode == "📊 BD分析":
        render_bd_analysis()
    elif page_mode == "⚙️ 系统设置":
        render_system_settings()
    elif page_mode == "📄 传统界面":
        render_traditional_interface()
    else:
        render_system_overview()  # 默认显示系统概览


# 集成五行八卦盘的完整界面
def render_integrated_bagua_interface():
    """集成app_five_elements.py的完整八卦盘界面"""
    
    # 导入五行八卦相关的所有组件
    from app_five_elements import (
        TRIGRAMS, REALMS, STONES, ELEMENTS, ELEMENT_META,
        compile_context, simulate, make_stones
    )
    
    st.title("☯️ 真八卦灵石盘")
    st.caption("基于真正道教五行八卦理论的沉浸式修真体验")
    
    # 获取统一状态管理器
    state_manager = get_state_manager()
    
    # 同步五行模块状态
    five_elements_state = state_manager.get_module_state("five_elements")
    
    # 如果五行模块状态为空，使用默认配置
    if not five_elements_state:
        # 初始化默认的五行八卦配置
        default_config = {
            "realm": "金丹",
            "disciple": state_manager.character_data.get("name", "李长风"),
            "affinity_main": state_manager.character_data.get("affinity_main", "木"),
            "board": {tri: {i: None for i in range(1, 5)} for tri in TRIGRAMS},
            "core": {i: None for i in range(1, 4)},
            "seed": 184023
        }
        
        # 更新八卦配置
        state_manager.update_bagua_configuration({
            "realm": default_config["realm"],
            "stones": default_config["board"],
            "core": default_config["core"],
            "seed": default_config["seed"]
        })
        
        five_elements_state = default_config
    
    # 这里可以嵌入完整的app_five_elements.py界面
    # 由于代码量很大，这里提供一个简化版本
    
    # 顶部HUD
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("弟子", five_elements_state.get("disciple", "李长风"))
        st.metric("境界", five_elements_state.get("realm", "金丹"))
    
    with col2:
        st.metric("主灵根", five_elements_state.get("affinity_main", "木"))
        stones_count = sum(1 for tri_data in five_elements_state.get("board", {}).values() 
                          for stone in tri_data.values() if stone)
        st.metric("已装灵石", stones_count)
    
    with col3:
        st.metric("种子", five_elements_state.get("seed", 184023))
    
    # 八卦盘配置区域
    with st.container(border=True):
        st.subheader("八卦盘配置")
        
        # 这里应该嵌入完整的八卦盘界面
        # 包括灵石库、八卦盘布局、衍算结果等
        
        st.info("完整的八卦盘界面正在集成中...")
        st.markdown("""
        将包含以下功能：
        - 🎯 精确的后天八卦方位布局
        - 💎 五行灵石拖拽配置
        - 🧩 逻辑灵石门控系统
        - 🧠 核心BIOS规则重写
        - ⚡ 实时衍算和效果预览
        - 🔄 配置导入导出
        """)
    
    # 同步配置到统一状态管理器
    if st.button("同步配置到统一系统"):
        state_manager.sync_modules()
        st.success("配置已同步到统一系统")


# 工具函数：状态同步
def sync_traditional_to_unified():
    """将传统界面的状态同步到统一系统"""
    state_manager = get_state_manager()
    
    # 这里可以添加从传统界面同步状态的逻辑
    # 例如从session_state同步到unified_state_manager
    
    pass


def sync_unified_to_traditional():
    """将统一系统的状态同步到传统界面"""
    state_manager = get_state_manager()
    
    # 这里可以添加从统一系统同步状态到传统界面的逻辑
    
    pass

# ==========================================
# 完整集成的五行八卦盘界面
# ==========================================

def render_complete_bagua_interface():
    """渲染完整的五行八卦盘界面（集成app_five_elements.py）"""
    
    # CSS样式（从app_five_elements.py移植）
    CSS = """
    <style>
      .bagua {
        border: 1px solid rgba(80, 200, 255, 0.45);
        border-radius: 999px;
        background: radial-gradient(circle at 50% 45%, rgba(8,20,32,0.96) 0%, rgba(6,14,24,0.96) 45%, rgba(4,10,18,0.98) 100%);
        padding: 28px;
        box-shadow: 0 0 0 1px rgba(80,200,255,0.25), 0 0 28px rgba(0,180,255,0.35), inset 0 0 50px rgba(0,0,0,0.65);
        position: relative;
        overflow: hidden;
        max-width: 980px;
        margin: 0 auto;
      }

      /* ?????? */
      .bagua::before {
        content: "";
        position: absolute;
        inset: -8px;
        background: conic-gradient(
          from -90deg,
          rgba(255, 80, 80, 0.35) 0deg 45deg,
          rgba(255, 200, 80, 0.35) 45deg 90deg,
          rgba(230, 230, 230, 0.28) 90deg 135deg,
          rgba(70, 220, 255, 0.35) 135deg 180deg,
          rgba(60, 120, 255, 0.38) 180deg 225deg,
          rgba(60, 220, 140, 0.35) 225deg 270deg,
          rgba(60, 220, 140, 0.32) 270deg 315deg,
          rgba(255, 80, 80, 0.30) 315deg 360deg
        );
        -webkit-mask: radial-gradient(circle, transparent 0 36%, #000 38% 78%, transparent 80%);
        mask: radial-gradient(circle, transparent 0 36%, #000 38% 78%, transparent 80%);
        opacity: 0.9;
        filter: blur(0.2px);
      }

      /* ????????? */
      .bagua::after {
        content: "";
        position: absolute;
        inset: -28px;
        background:
          repeating-conic-gradient(from -90deg, rgba(120,220,255,0.85) 0 3deg, transparent 3deg 9deg),
          radial-gradient(circle, transparent 0 86%, rgba(120,220,255,0.35) 87%, transparent 88%);
        -webkit-mask: radial-gradient(circle, transparent 0 86%, #000 88% 100%);
        mask: radial-gradient(circle, transparent 0 86%, #000 88% 100%);
        opacity: 0.75;
        filter: drop-shadow(0 0 6px rgba(0,200,255,0.55));
      }

      .bagua-inner {
        position: absolute;
        inset: 18%;
        border-radius: 999px;
        border: 1px solid rgba(120, 220, 255, 0.25);
        box-shadow: inset 0 0 26px rgba(0, 200, 255, 0.22);
        background: radial-gradient(circle, rgba(0,0,0,0) 0 55%, rgba(0,0,0,0.25) 100%);
        pointer-events: none;
        z-index: 1;
      }

      .bagua-grid {
        display: grid;
        grid-template-columns: repeat(5, minmax(110px, 1fr));
        grid-template-areas:
          ". . li . ."
          ". qian . gen ."
          "dui . core . zhen"
          ". kun . xun ."
          ". . kan . .";
        gap: 12px;
        align-items: stretch;
        justify-items: stretch;
        position: relative;
        z-index: 3;
      }

      .bagua-ring-wrap {
        position: relative;
        width: min(760px, 92vw);
        aspect-ratio: 1;
        margin: 10px auto 2px;
        --r-logic: 84px;
        --r-inner: 140px;
        --r-middle: 200px;
        --r-outer: 260px;
        --r-label: 315px;
      }

      .ring-layer { position: absolute; inset: 0; }

      .ring-layer .slot {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: rotate(var(--angle)) translate(var(--radius)) rotate(calc(-1 * var(--angle)));
        transform-origin: center;
      }

      .ring-label .slot { --radius: var(--r-label); pointer-events: none; }
      .ring-logic .slot { --radius: var(--r-logic); }
      .ring-inner .slot { --radius: var(--r-inner); }
      .ring-middle .slot { --radius: var(--r-middle); }
      .ring-outer .slot { --radius: var(--r-outer); }

      .tri-label {
        min-width: 96px;
        text-align: center;
        padding: 6px 10px;
        border-radius: 999px;
        border: 1px solid rgba(120,220,255,0.35);
        background: rgba(8,18,28,0.72);
        color: #dff6ff;
        box-shadow: 0 0 16px rgba(0,180,255,0.18);
        font-size: 12px;
        letter-spacing: 0.6px;
      }

      .ring-core .core-center {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: min(240px, 42%);
      }

      .bagua .ring-layer div[data-testid="stButton"] > button {
        width: 42px !important;
        height: 42px !important;
        padding: 0 !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
      }

      .bagua .ring-logic div[data-testid="stButton"] > button {
        width: 34px !important;
        height: 34px !important;
        font-size: 12px !important;
      }

      .bagua .ring-outer div[data-testid="stButton"] > button {
        width: 46px !important;
        height: 46px !important;
      }

      @media (max-width: 1200px) {
        .bagua-ring-wrap {
          --r-logic: 70px;
          --r-inner: 118px;
          --r-middle: 170px;
          --r-outer: 220px;
          --r-label: 260px;
          width: min(640px, 90vw);
        }
      }


      .bagua-cell { width: 100%; }
      .bagua-core { grid-area: core; }
      .bagua-li { grid-area: li; }
      .bagua-kan { grid-area: kan; }
      .bagua-qian { grid-area: qian; }
      .bagua-gen { grid-area: gen; }
      .bagua-dui { grid-area: dui; }
      .bagua-zhen { grid-area: zhen; }
      .bagua-kun { grid-area: kun; }
      .bagua-xun { grid-area: xun; }

      .elem-tag {
        display: inline-flex;
        gap: 8px;
        align-items: center;
        padding: 3px 10px;
        border-radius: 999px;
        border: 1px solid rgba(0,0,0,0.12);
        background: rgba(255,255,255,0.78);
        font-size: 12px;
      }

        .bagua .tiny {
    color: rgba(200, 230, 255, 0.7);
  }

.bagua .elem-tag {
        background: rgba(10,18,28,0.60);
        border: 1px solid rgba(120,220,255,0.25);
        color: #d7f2ff;
        box-shadow: 0 0 10px rgba(0,180,255,0.15);
      }

      .tri-head {
        border-radius: 14px;
        padding: 8px 10px;
        border: 1px solid rgba(120,220,255,0.25);
        background: rgba(10, 18, 28, 0.78);
        box-shadow: inset 0 0 18px rgba(0,200,255,0.12);
        margin-bottom: 10px;
        backdrop-filter: blur(2px);
      }

      .bagua div[data-testid="stButton"] > button {
        border-radius: 12px !important;
        border: 1px solid rgba(120,220,255,0.35) !important;
        background: rgba(8,18,28,0.86) !important;
        color: #dff6ff !important;
        padding: 0.46rem 0.62rem !important;
        box-shadow: 0 0 12px rgba(0,200,255,0.18), inset 0 0 12px rgba(0,120,255,0.18);
      }

      .bagua div[data-testid="stButton"] > button:hover {
        border-color: rgba(120,220,255,0.7) !important;
        box-shadow: 0 0 18px rgba(0,200,255,0.35);
        transform: translateY(-1px);
      }

      .core-shell {
        position: relative;
        min-height: 160px;
      }

      .core-shell > * {
        position: relative;
        z-index: 2;
      }

      .core-orb {
        position: absolute;
        inset: 14px;
        border-radius: 999px;
        background:
          radial-gradient(circle at 35% 35%, rgba(255,255,255,0.90) 0 18%, rgba(0,0,0,0) 19% 100%),
          radial-gradient(circle at 65% 65%, rgba(0,0,0,0.90) 0 18%, rgba(0,0,0,0) 19% 100%),
          conic-gradient(from 90deg, rgba(255,255,255,0.85) 0 50%, rgba(0,0,0,0.85) 50% 100%);
        border: 1px solid rgba(120,220,255,0.35);
        box-shadow: 0 0 20px rgba(0,200,255,0.35), inset 0 0 30px rgba(0,0,0,0.6);
        opacity: 0.85;
        z-index: 1;
        pointer-events: none;
      }

      @media (max-width: 1200px) {
        .bagua {
          border-radius: 22px;
          padding: 18px;
        }
        .bagua-grid {
          grid-template-columns: repeat(3, minmax(110px, 1fr));
          grid-template-areas:
            "li li li"
            "qian core gen"
            "dui core zhen"
            "kun core xun"
            "kan kan kan";
        }
      }
    </style>
    """
    
    st.markdown(CSS, unsafe_allow_html=True)
    
    st.title("☯️ 真八卦灵石盘")
    st.caption("基于真正道教五行八卦理论的沉浸式修真体验")
    
    # 获取统一状态管理器
    state_manager = get_state_manager()
    wuxing_engine = WuxingEngine()
    
    # 初始化八卦配置（如果不存在）
    if not hasattr(st.session_state, 'bagua_initialized'):
        # 从统一状态管理器获取配置
        bagua_config = state_manager.bagua_configuration
        
        # 初始化session state
        st.session_state.realm = bagua_config.get("realm", "金丹")
        st.session_state.disciple = state_manager.character_data.get("name", "李长风")
        st.session_state.affinity_main = state_manager.character_data.get("affinity_main", "木")
        st.session_state.seed = bagua_config.get("seed", 184023)
        
        # 八卦盘配置
        st.session_state.board = bagua_config.get("stones", {
            tri: {i: None for i in range(1, 5)} 
            for tri in ["QIAN", "DUI", "LI", "ZHEN", "XUN", "KAN", "GEN", "KUN"]
        })
        st.session_state.core = bagua_config.get("core", {i: None for i in range(1, 4)})
        
        st.session_state.bagua_initialized = True
    
    # 顶部HUD
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1.5])
    
    with col1:
        st.markdown("### ☯️ 真八卦灵石盘")
        st.caption(f"弟子：{st.session_state.disciple} | 境界：{st.session_state.realm} | 主灵根：{st.session_state.affinity_main}")
    
    with col2:
        # 计算已装灵石数量
        stones_count = sum(1 for tri_data in st.session_state.board.values() 
                          for stone in tri_data.values() if stone)
        total_slots = len(st.session_state.board) * 4  # 8卦 * 4槽位
        st.metric("槽位", f"{stones_count}/{total_slots}")
    
    with col3:
        # 简化的带宽计算
        bandwidth_used = stones_count * 2  # 简化计算
        bandwidth_max = wuxing_engine.get_realm_config(st.session_state.realm)["bw_max"]
        st.metric("带宽", f"{bandwidth_used}/{bandwidth_max}")
    
    with col4:
        st.metric("种子", st.session_state.seed)
    
    st.divider()
    
    # 三栏布局
    col_lib, col_center, col_status = st.columns([1.2, 2.5, 1.2])
    
    # 左栏：灵石库
    with col_lib:
        st.markdown("#### 📦 灵石库")
        
        with st.expander("⚙️ 弟子/境界", expanded=True):
            new_disciple = st.text_input("弟子名", value=st.session_state.disciple)
            new_realm = st.selectbox("境界", 
                                   list(wuxing_engine.realms.keys()), 
                                   index=list(wuxing_engine.realms.keys()).index(st.session_state.realm))
            new_affinity = st.selectbox("主灵根", 
                                      wuxing_engine.elements, 
                                      index=wuxing_engine.elements.index(st.session_state.affinity_main))
            new_seed = st.number_input("Seed", min_value=0, max_value=999999999, 
                                     value=st.session_state.seed, step=1)
            
            # 更新配置
            if (new_disciple != st.session_state.disciple or 
                new_realm != st.session_state.realm or 
                new_affinity != st.session_state.affinity_main or 
                new_seed != st.session_state.seed):
                
                st.session_state.disciple = new_disciple
                st.session_state.realm = new_realm
                st.session_state.affinity_main = new_affinity
                st.session_state.seed = new_seed
                
                # 同步到统一状态管理器
                state_manager.update_character_data({
                    "name": new_disciple,
                    "realm": new_realm,
                    "affinity_main": new_affinity
                })
                state_manager.update_bagua_configuration({
                    "seed": new_seed
                })
        
        # 灵石选择界面（简化版）
        st.markdown("---")
        st.markdown("**五行灵石**")
        
        for element in wuxing_engine.elements:
            meta = wuxing_engine.get_element_meta(element)
            if st.button(f"{meta['icon']} {element}灵石", key=f"stone_{element}", use_container_width=True):
                st.session_state.selected_stone = f"gem_{element}"
        
        st.markdown("---")
        st.markdown("**逻辑灵石**")
        
        logic_stones = ["血危", "过热"]
        for logic in logic_stones:
            if st.button(f"🧩 逻辑·{logic}", key=f"logic_{logic}", use_container_width=True):
                st.session_state.selected_stone = f"logic_{logic}"
        
        st.markdown("---")
        st.markdown("**核心BIOS**")
        
        bios_list = ["疯狂义体", "五行逆转", "算力超频"]
        for bios in bios_list:
            if st.button(f"🧠 {bios}", key=f"bios_{bios}", use_container_width=True):
                st.session_state.selected_stone = f"core_{bios}"
    
    # 中栏：八卦盘
    with col_center:
        st.markdown('<div class="bagua">', unsafe_allow_html=True)
        st.markdown("<div class='bagua-inner'></div>", unsafe_allow_html=True)
        
        # 五行图例
        legend_cols = st.columns(5)
        for i, element in enumerate(wuxing_engine.elements):
            meta = wuxing_engine.get_element_meta(element)
            legend_cols[i].markdown(
                f'<div class="elem-tag" style="justify-content:center; width:100%; border-color:{meta["color"]}; background:{meta["bg"]};">'
                f'{meta["icon"]} <b>{element}</b>域</div>',
                unsafe_allow_html=True,
            )
        
        st.markdown("<div style='margin:8px 0; font-size:12px; text-align:center;'>八卦方位：上离下坎，左兑右震，左上乾右上艮，左下坤右下巽</div>", unsafe_allow_html=True)
        
        # 核心区域
        # ??????
        realm_cfg = wuxing_engine.get_realm_config(st.session_state.realm)
        tri_unlock = realm_cfg["tri_unlock"]

        RING_ORDER = ["LI", "GEN", "ZHEN", "XUN", "KAN", "KUN", "DUI", "QIAN"]
        ANGLES = {
            "LI": -90,
            "GEN": -45,
            "ZHEN": 0,
            "XUN": 45,
            "KAN": 90,
            "KUN": 135,
            "DUI": 180,
            "QIAN": -135,
        }

        def render_core_cell() -> None:
            st.markdown("<div class='bagua-cell bagua-core'>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown("<div class='core-shell'>", unsafe_allow_html=True)
                st.markdown("<div class='core-orb'></div>", unsafe_allow_html=True)
                st.markdown("**?? ?????BIOS**")

                core_cols = st.columns(3)
                for i in range(1, 4):
                    core_stone = st.session_state.core.get(i)
                    label = "??" if core_stone else "?"

                    if core_cols[i-1].button(label, key=f"core_{i}", use_container_width=True):
                        if hasattr(st.session_state, 'selected_stone') and st.session_state.selected_stone.startswith('core_'):
                            st.session_state.core[i] = st.session_state.selected_stone
                            # ??????????
                            state_manager.update_bagua_configuration({"core": st.session_state.core})
                            st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        def ring_slot_label(tri: str, idx: int, locked: bool) -> str:
            if locked:
                return "?"
            stone = st.session_state.board.get(tri, {}).get(idx)
            if not stone:
                return "?"
            if idx == 1 or stone.startswith('logic_'):
                return "?"
            elem = stone.split('_', 1)[1] if '_' in stone else "?"
            return wuxing_engine.get_element_meta(elem)["icon"]

        def render_ring(idx: int, ring_class: str, tip: str) -> None:
            st.markdown(f"<div class='ring-layer {ring_class}'>", unsafe_allow_html=True)
            for tri in RING_ORDER:
                angle = ANGLES[tri]
                locked = idx > tri_unlock
                st.markdown(f"<div class='slot' style='--angle:{angle}deg'>", unsafe_allow_html=True)
                if st.button(ring_slot_label(tri, idx, locked), key=f"{tri}_{idx}", disabled=locked, help=tip):
                    if hasattr(st.session_state, 'selected_stone'):
                        selected = st.session_state.selected_stone

                        can_place = True
                        error_msg = ""

                        if idx == 1 and not selected.startswith('logic_'):
                            can_place = False
                            error_msg = "???????????"
                        elif idx > 1 and selected.startswith('logic_'):
                            can_place = False
                            error_msg = "???????????"
                        elif selected.startswith('core_'):
                            can_place = False
                            error_msg = "??BIOS??????"

                        if can_place:
                            if tri not in st.session_state.board:
                                st.session_state.board[tri] = {}
                            st.session_state.board[tri][idx] = selected

                            state_manager.update_bagua_configuration({"stones": st.session_state.board})
                            st.rerun()
                        else:
                            st.error(error_msg)
                st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='bagua-ring-wrap'>", unsafe_allow_html=True)

        # ????????
        st.markdown("<div class='ring-layer ring-label'>", unsafe_allow_html=True)
        for tri in RING_ORDER:
            angle = ANGLES[tri]
            info = wuxing_engine.trigrams[tri]
            element = info["elem"]
            meta = wuxing_engine.get_element_meta(element)
            st.markdown(
                f"<div class='slot label' style='--angle:{angle}deg'>"
                f"<div class='tri-label' style='border-color:{meta['color']};'>"
                f"{info['symbol']} {info['name']}<div class='tiny'>{meta['icon']} {element}?</div>"
                f"</div></div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

        render_ring(1, "ring-logic", "???")
        render_ring(2, "ring-inner", "???")
        render_ring(3, "ring-middle", "???")
        render_ring(4, "ring-outer", "???")

        st.markdown("<div class='ring-layer ring-core'>", unsafe_allow_html=True)
        st.markdown("<div class='core-center'>", unsafe_allow_html=True)
        with st.container(border=True):
            render_core_cell()
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 右栏：衍算结果
    with col_status:
        st.markdown("#### 🔮 衍算结果")
        
        # 计算当前配置效果
        current_config = {
            "stones": st.session_state.board,
            "core": st.session_state.core,
            "realm": st.session_state.realm
        }
        
        try:
            effects = wuxing_engine.calculate_comprehensive_effects(current_config)
            
            # 显示基本信息
            st.metric("总灵石数", effects.get("total_stones", 0))
            
            # 五行分布
            st.markdown("**五行分布**")
            element_counts = effects.get("element_counts", {})
            for element in wuxing_engine.elements:
                count = element_counts.get(element, 0)
                meta = wuxing_engine.get_element_meta(element)
                if count > 0:
                    st.write(f"{meta['icon']} {element}: {count}")
            
            # 配置状态
            if effects.get("is_valid_configuration", True):
                st.success("✅ 配置有效")
            else:
                st.error("❌ 配置无效")
                for error in effects.get("validation_errors", []):
                    st.caption(f"• {error}")
            
            # 综合倍率
            overall_mult = effects.get("overall_power_multiplier", 1.0)
            st.metric("综合倍率", f"{overall_mult:.2f}x")
            
        except Exception as e:
            st.error(f"计算错误: {str(e)}")
        
        # 操作按钮
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 重新计算", use_container_width=True):
                st.rerun()
        
        with col2:
            if st.button("💾 保存配置", use_container_width=True):
                state_manager.save_state()
                st.success("配置已保存")
    
    # 底部详情
    st.markdown("### 📝 配置详情")
    
    with st.container(border=True):
        if hasattr(st.session_state, 'selected_stone'):
            st.write(f"**选中灵石**: {st.session_state.selected_stone}")
        else:
            st.info("点击灵石库选择灵石，然后点击八卦盘槽位进行放置")
        
        # 显示当前配置摘要
        total_stones = sum(1 for tri_data in st.session_state.board.values() 
                          for stone in tri_data.values() if stone)
        core_stones = sum(1 for stone in st.session_state.core.values() if stone)
        
        st.write(f"当前配置：{total_stones} 个灵石，{core_stones} 个核心BIOS")



def render_wuxing_board_interface():
    """??????????"""
    st.title("?? ????")
    st.caption("???? + ???????????????")

    if st.toggle("???????Legacy?", value=False):
        render_complete_bagua_interface()
        return

    layout = generate_board()

    if "board_element_filter" not in st.session_state:
        st.session_state.board_element_filter = "??"
    if "board_type_filter" not in st.session_state:
        st.session_state.board_type_filter = "??"
    if "board_show_bridges" not in st.session_state:
        st.session_state.board_show_bridges = True
    if "board_show_labels" not in st.session_state:
        st.session_state.board_show_labels = True
    if "board_show_ring_guides" not in st.session_state:
        st.session_state.board_show_ring_guides = True
    if "board_search_query" not in st.session_state:
        st.session_state.board_search_query = ""

    if "board_selected_nodes" not in st.session_state:
        st.session_state.board_selected_nodes = set()
    if "board_hover_node" not in st.session_state:
        st.session_state.board_hover_node = None

    search_matches = set()
    left_col, right_col = st.columns([4, 1], gap="large")
    with right_col:
        st.markdown("### Filters")
        with st.container(border=True):
            st.radio("????", ["??"] + ELEMENTS, key="board_element_filter")
            st.radio("????", ["??"] + [t.value for t in NodeType], key="board_type_filter")
            search_query = st.text_input("Search node", key="board_search_query", placeholder="node_id / tag / keyword")
            st.toggle("????", key="board_show_bridges")
            st.toggle("????", key="board_show_labels")
            st.toggle("????", key="board_show_ring_guides")
            if search_query:
                q = search_query.strip().lower()
                for n in layout.nodes:
                    if q in n.node_id.lower() or q in n.element.lower() or q in n.type.value.lower() or any(q in t.lower() for t in n.tags):
                        search_matches.add(n.node_id)
                if search_matches:
                    preview = ", ".join(list(sorted(search_matches))[:6])
                    st.caption(f"Matches: {preview}")
            if st.button("????", use_container_width=True):
                st.session_state.board_element_filter = "??"
                st.session_state.board_type_filter = "??"
                st.session_state.board_selected_nodes = set()
                st.session_state.board_hover_node = None
                st.session_state.board_search_query = ""
                st.rerun()
            st.markdown("---")
            st.caption("Legend: ? small  ? medium  ? keystone  ? socket  ? bridge  ? convert")

    highlight_element = None if st.session_state.board_element_filter == "??" else st.session_state.board_element_filter
    highlight_type = None if st.session_state.board_type_filter == "??" else NodeType(st.session_state.board_type_filter)
    show_bridges = st.session_state.board_show_bridges
    show_labels = st.session_state.board_show_labels
    show_ring_guides = st.session_state.board_show_ring_guides

    with left_col:
        fig = render_board_plotly(
            layout.nodes,
            layout.edges,
            highlight_element=highlight_element,
            highlight_type=highlight_type,
            show_bridges=show_bridges,
            show_labels=show_labels,
            show_ring_guides=show_ring_guides,
            selected_nodes=st.session_state.board_selected_nodes,
            height=780,
            hovered_node=st.session_state.board_hover_node,
            search_matches=search_matches,
        )

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        events = plotly_events(
            fig,
            click_event=True,
            select_event=False,
            hover_event=True,
            override_height=780,
            key="wuxing-board",
        )
        if events:
            event = events[0]
            node_id = event.get("customdata")
            event_type = event.get("event")
            if node_id:
                if event_type == "plotly_hover":
                    st.session_state.board_hover_node = node_id
                    st.rerun()
                elif event_type == "plotly_unhover":
                    st.session_state.board_hover_node = None
                    st.rerun()
                else:
                    if node_id in st.session_state.board_selected_nodes:
                        st.session_state.board_selected_nodes.remove(node_id)
                    else:
                        st.session_state.board_selected_nodes.add(node_id)
                    st.session_state.board_hover_node = node_id
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
def render_wuxing_bagua_interface():
    """渲染五行棋盘界面（新布局）"""
    render_wuxing_board_interface()


def render_help_center():
    """渲染帮助中心界面"""
    help_system = get_help_system()
    help_system.render_help_interface()


def render_performance_monitoring():
    """渲染性能监控界面"""
    st.title("📊 系统性能监控")
    st.caption("监控系统性能，识别和解决性能问题")

    render_performance_dashboard()

    optimizer = get_performance_optimizer()
    with st.container(border=True):
        st.subheader("🚀 性能优化")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 分析性能瓶颈", use_container_width=True):
                suggestions = optimizer.get_optimization_suggestions()
                if suggestions:
                    st.subheader("优化建议")
                    for suggestion in suggestions:
                        if suggestion["priority"] == "high":
                            st.error(f"🔴 {suggestion['issue']}")
                        else:
                            st.warning(f"🟡 {suggestion['issue']}")
                        st.caption(f"建议: {suggestion['suggestion']}")
                else:
                    st.success("✅ 系统性能良好，暂无优化建议")
        with col2:
            if st.button("⚡ 应用自动优化", use_container_width=True):
                with st.spinner("正在应用性能优化..."):
                    if optimizer.apply_automatic_optimizations():
                        st.success("✅ 性能优化完成")
                    else:
                        st.error("❌ 性能优化失败")


def render_balance_adjustment():
    """渲染平衡调整界面"""
    balance_system = get_balance_system()
    balance_system.render_balance_interface()


def render_unified_interface():
    """渲染统一界面的主函数"""
    from unified_main_app import render_unified_navigation
    page_mode = render_unified_navigation()

    if page_mode == "🏠 系统概览":
        render_system_overview()
    elif page_mode == "☯️ 五行八卦盘":
        render_wuxing_bagua_interface()
    elif page_mode == "⚔️ 战斗模拟":
        render_combat_simulation()
    elif page_mode == "🎓 流派管理":
        render_school_management()
    elif page_mode == "💎 刷宝系统":
        render_loot_system()
    elif page_mode == "📊 BD分析":
        render_bd_analysis()
    elif page_mode == "⚙️ 系统设置":
        render_system_settings()
    elif page_mode == "📄 传统界面":
        render_traditional_interface()
    elif page_mode == "📚 帮助中心":
        render_help_center()
    elif page_mode == "📊 性能监控":
        render_performance_monitoring()
    elif page_mode == "⚖️ 平衡调整":
        render_balance_adjustment()
