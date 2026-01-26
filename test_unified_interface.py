#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试统一界面集成
"""

import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_imports():
    """测试所有模块导入"""
    try:
        print("测试模块导入...")
        
        # 测试核心模块
        from unified_state_manager import get_state_manager, initialize_unified_system
        print("✅ unified_state_manager 导入成功")
        
        from wuxing_engine import WuxingEngine
        print("✅ wuxing_engine 导入成功")
        
        from enhanced_combat_engine import EnhancedCombatEngine
        print("✅ enhanced_combat_engine 导入成功")
        
        from cultivation_school_system import get_school_manager
        print("✅ cultivation_school_system 导入成功")
        
        from loot_generator import get_loot_generator, get_challenge_manager, get_bd_optimizer
        print("✅ loot_generator 导入成功")
        
        # 测试界面模块
        from unified_interface_modules import render_unified_interface
        print("✅ unified_interface_modules 导入成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

def test_system_initialization():
    """测试系统初始化"""
    try:
        print("\n测试系统初始化...")
        
        from unified_state_manager import initialize_unified_system
        state_manager = initialize_unified_system()
        
        print("✅ 统一状态管理器初始化成功")
        
        # 测试状态获取
        status = state_manager.get_system_status()
        print(f"✅ 系统状态获取成功: {status['character_name']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 系统初始化失败: {e}")
        return False

def test_wuxing_engine():
    """测试五行引擎"""
    try:
        print("\n测试五行引擎...")
        
        from wuxing_engine import WuxingEngine
        engine = WuxingEngine()
        
        # 测试基本功能
        assert engine.is_generation("木", "火"), "五行相生测试失败"
        assert engine.is_destruction("木", "土"), "五行相克测试失败"
        
        print("✅ 五行引擎基本功能正常")
        
        # 测试配置验证
        test_config = {
            "stones": {
                "QIAN": {1: None, 2: "gem_金", 3: None, 4: None},
                "DUI": {1: None, 2: None, 3: None, 4: None},
                "LI": {1: None, 2: "gem_火", 3: None, 4: None},
                "ZHEN": {1: None, 2: None, 3: None, 4: None},
                "XUN": {1: None, 2: None, 3: None, 4: None},
                "KAN": {1: None, 2: None, 3: None, 4: None},
                "GEN": {1: None, 2: None, 3: None, 4: None},
                "KUN": {1: None, 2: None, 3: None, 4: None}
            },
            "realm": "金丹"
        }
        
        is_valid, errors = engine.validate_bagua_configuration(test_config)
        print(f"✅ 八卦配置验证完成: {'有效' if is_valid else '无效'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 五行引擎测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("统一界面集成测试")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_system_initialization,
        test_wuxing_engine
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✅ 所有测试通过！统一界面集成成功")
        print("\n可以运行以下命令启动统一界面:")
        print("streamlit run unified_main_app.py")
    else:
        print("❌ 部分测试失败，请检查模块依赖")
    
    print("=" * 50)

if __name__ == "__main__":
    main()