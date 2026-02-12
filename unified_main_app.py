# -*- coding: utf-8 -*-
"""
统一RPG系统主应用 (Unified RPG Main Application)
整合app.py和app_five_elements.py的UI组件
设计统一的主界面包含所有功能模块
优化八卦盘视觉效果和交互体验
实现模块间无缝切换和状态保持

运行方式:
streamlit run unified_main_app.py
"""

import streamlit as st
import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 导入统一系统模块
from unified_state_manager import get_state_manager, initialize_unified_system
from wuxing_engine import WuxingEngine
from enhanced_combat_engine import EnhancedCombatEngine
from cultivation_school_system import get_school_manager
from loot_generator import get_loot_generator, get_challenge_manager, get_bd_optimizer
from performance_optimizer import get_performance_optimizer
from help_system import get_help_system
from balance_system import get_balance_system
from unified_interface_modules import render_unified_interface

# 页面配置
st.set_page_config(
    page_title="统一RPG系统",
    layout="wide",
    page_icon="☯️",
    initial_sidebar_state="expanded"
)

# CSS样式
CSS = """
<style>
  .stApp {
    background: linear-gradient(135deg, rgba(255, 244, 214, 0.3) 0%, rgba(236,247,255,0.3) 100%);
  }
  
  .main-header {
    text-align: center;
    padding: 1rem 0;
    background: linear-gradient(90deg, #FF6B6B, #4ECDC4, #45B7D1, #96CEB4, #FFEAA7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2.5rem;
    font-weight: bold;
    margin-bottom: 2rem;
  }
  
  .module-card {
    border: 1px solid rgba(0,0,0,0.1);
    border-radius: 10px;
    padding: 1rem;
    margin: 0.5rem 0;
    background: rgba(255,255,255,0.8);
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }
  
  .status-good {
    color: #28a745;
    font-weight: bold;
  }
  
  .status-warning {
    color: #ffc107;
    font-weight: bold;
  }
  
  .status-error {
    color: #dc3545;
    font-weight: bold;
  }
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

# 系统初始化
@st.cache_resource
def initialize_system():
    """初始化统一RPG系统"""
    try:
        state_manager = initialize_unified_system()
        wuxing_engine = WuxingEngine()
        school_manager = get_school_manager()
        loot_generator = get_loot_generator()
        challenge_manager = get_challenge_manager()
        bd_optimizer = get_bd_optimizer()
        performance_optimizer = get_performance_optimizer()
        help_system = get_help_system()
        balance_system = get_balance_system()
        
        # 应用性能优化
        performance_optimizer.optimize_streamlit_performance()
        
        return {
            "state_manager": state_manager,
            "wuxing_engine": wuxing_engine,
            "school_manager": school_manager,
            "loot_generator": loot_generator,
            "challenge_manager": challenge_manager,
            "bd_optimizer": bd_optimizer,
            "performance_optimizer": performance_optimizer,
            "help_system": help_system,
            "balance_system": balance_system,
            "initialized": True,
            "error": None
        }
    except Exception as e:
        return {
            "initialized": False,
            "error": str(e)
        }

# 主应用入口
def main():
    """主应用入口函数"""
    
    # 显示主标题
    st.markdown('<h1 class="main-header">☯️ 统一RPG数值验证系统 ⚔️</h1>', unsafe_allow_html=True)
    
    # 初始化系统
    system = initialize_system()
    
    if not system["initialized"]:
        st.error(f"❌ 系统初始化失败: {system['error']}")
        st.info("请检查所有依赖模块是否正确安装")
        return
    
    # 系统初始化成功提示
    if "system_initialized" not in st.session_state:
        st.success("✅ 统一RPG系统初始化成功")
        st.session_state["system_initialized"] = True
    
    # 渲染统一界面
    try:
        render_unified_interface()
    except Exception as e:
        st.error(f"❌ 界面渲染错误: {str(e)}")
        st.info("正在尝试恢复...")
        
        # 提供错误恢复选项
        if st.button("🔄 重新初始化系统"):
            st.cache_resource.clear()
            st.rerun()

# 导航函数（从unified_interface_modules导入时需要）
def render_unified_navigation():
    """渲染统一的导航界面"""
    st.sidebar.title("☯️ 统一RPG系统")
    
    # 系统状态概览
    with st.sidebar.expander("📊 系统状态", expanded=True):
        try:
            state_manager = get_state_manager()
            status = state_manager.get_system_status()
            
            st.metric("角色", status["character_name"])
            st.metric("境界", status["character_realm"])
            st.metric("流派", status["character_school"])
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("灵石", status["bagua_stones_count"])
            with col2:
                st.metric("技能", status["active_skills_count"])
            
            if not status["state_consistent"]:
                st.warning("⚠️ 状态不一致")
                for issue in status["consistency_issues"]:
                    st.caption(f"• {issue}")
            else:
                st.success("✅ 状态一致")
                
        except Exception as e:
            st.error(f"状态获取失败: {str(e)}")
    
    # 主要功能模块
    page_mode = st.sidebar.radio(
        "功能模块",
        [
            "🏠 系统概览",
            "☯️ 五行八卦盘",
            "⚔️ 战斗模拟",
            "🎓 流派管理", 
            "💎 刷宝系统",
            "📊 BD分析",
            "🧪 BD评测",
            "⚙️ 系统设置",
            "📚 帮助中心",
            "📊 性能监控",
            "⚖️ 平衡调整",
            "📄 传统界面"
        ]
    )
    
    # 系统工具
    with st.sidebar.expander("🛠️ 系统工具"):
        if st.button("🔄 同步模块", use_container_width=True):
            try:
                state_manager = get_state_manager()
                state_manager.sync_modules()
                st.success("模块同步完成")
            except Exception as e:
                st.error(f"同步失败: {str(e)}")
        
        if st.button("💾 保存状态", use_container_width=True):
            try:
                state_manager = get_state_manager()
                if state_manager.save_state():
                    st.success("状态保存成功")
                else:
                    st.error("状态保存失败")
            except Exception as e:
                st.error(f"保存失败: {str(e)}")
        
        if st.button("🔄 重启系统", use_container_width=True):
            st.cache_resource.clear()
            st.rerun()
    
    return page_mode

if __name__ == "__main__":
    main()
