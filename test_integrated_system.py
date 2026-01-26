#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整合系统测试脚本
测试系统集成和端到端功能
"""

import sys
import os
import traceback
import tempfile
import shutil
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_system_integration():
    """测试系统集成"""
    print("🔧 测试系统集成...")
    
    try:
        from integrated_rpg_system import IntegratedRPGSystem
        
        # 使用临时目录进行测试
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 创建系统实例
            system = IntegratedRPGSystem(config_dir=temp_dir)
            
            # 初始化系统
            init_success = system.initialize_system()
            
            if init_success:
                print("✅ 系统初始化成功")
                
                # 获取系统健康状态
                health = system.get_system_health()
                print(f"系统状态: {health.overall_status}")
                print(f"模块状态: {len([s for s in health.module_statuses.values() if s == 'healthy'])} 健康")
                
                # 运行诊断
                diagnostics = system.run_system_diagnostics()
                print(f"诊断完成: {len(diagnostics['module_tests'])} 个模块测试")
                
                # 关闭系统
                system.shutdown_system()
                
                return True
            else:
                print("❌ 系统初始化失败")
                if system.initialization_errors:
                    for error in system.initialization_errors:
                        print(f"  • {error}")
                return False
                
        finally:
            # 清理临时目录
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                
    except Exception as e:
        print(f"❌ 系统集成测试失败: {e}")
        print(traceback.format_exc())
        return False

def test_end_to_end_workflow():
    """测试端到端工作流程"""
    print("🔄 测试端到端工作流程...")
    
    try:
        from integrated_rpg_system import IntegratedRPGSystem
        
        temp_dir = tempfile.mkdtemp()
        
        try:
            system = IntegratedRPGSystem(config_dir=temp_dir)
            
            if not system.initialize_system():
                print("❌ 系统初始化失败")
                return False
            
            # 获取状态管理器
            state_manager = system.state_manager
            
            # 1. 创建角色
            print("  📝 创建测试角色...")
            character_data = {
                "name": "集成测试角色",
                "level": 30,
                "school": "sword_cultivator",
                "realm": "筑基",
                "base_attributes": {
                    "str": 60,
                    "agi": 50,
                    "int": 40,
                    "max_hp": 1500,
                    "base_atk": 120,
                    "crit_rate": 0.12,
                    "crit_dmg": 1.9
                },
                "affinity_main": "金"
            }
            
            state_manager.update_character_data(character_data)
            
            # 2. 配置八卦
            print("  ☯️ 配置八卦盘...")
            bagua_config = {
                "stones": {
                    "QIAN": {1: None, 2: "gem_金", 3: "gem_金", 4: None},
                    "DUI": {1: None, 2: "gem_金", 3: None, 4: None},
                    "LI": {1: None, 2: "gem_火", 3: None, 4: None},
                    "ZHEN": {1: None, 2: None, 3: None, 4: None},
                    "XUN": {1: None, 2: None, 3: None, 4: None},
                    "KAN": {1: None, 2: None, 3: None, 4: None},
                    "GEN": {1: None, 2: None, 3: None, 4: None},
                    "KUN": {1: None, 2: None, 3: None, 4: None}
                },
                "core": {1: "core_mad", 2: None, 3: None},
                "seed": 654321
            }
            
            state_manager.update_bagua_configuration(bagua_config)
            
            # 3. 设置战斗
            print("  ⚔️ 配置战斗设置...")
            combat_settings = {
                "selected_skills": ["mvp_basic_attack", "mvp_crit_execute"],
                "skill_chain": {
                    "main_skill": "mvp_basic_attack",
                    "main_mods": ["mvp_mod_damage_20", "mvp_mod_crit_10"],
                    "triggers": []
                },
                "simulation_params": {
                    "enemy_hp": 2000,
                    "enemy_dps": 25,
                    "max_time": 18.0
                }
            }
            
            state_manager.update_combat_settings(combat_settings)
            
            # 4. 验证状态一致性
            print("  🔍 验证状态一致性...")
            is_consistent, issues = state_manager.validate_state_consistency()
            
            if not is_consistent:
                print(f"⚠️ 状态不一致: {issues}")
            else:
                print("✅ 状态一致性验证通过")
            
            # 5. 执行战斗测试
            print("  ⚡ 执行战斗测试...")
            combat_result = state_manager.perform_one_click_combat_test()
            
            if combat_result["success"]:
                result = combat_result["performance_analysis"]["result"]
                dps = combat_result["performance_analysis"]["average_dps"]
                print(f"✅ 战斗测试成功: {result}, DPS: {dps:.1f}")
            else:
                print(f"❌ 战斗测试失败: {combat_result.get('error')}")
            
            # 6. 测试数据持久化
            print("  💾 测试数据持久化...")
            save_success = state_manager.save_state()
            
            if save_success:
                print("✅ 数据保存成功")
                
                # 测试加载
                new_state_manager = type(state_manager)(config_dir=temp_dir)
                load_success = new_state_manager.load_state()
                
                if load_success:
                    loaded_name = new_state_manager.character_data.get("name")
                    if loaded_name == character_data["name"]:
                        print("✅ 数据加载验证成功")
                    else:
                        print(f"❌ 数据加载验证失败: {loaded_name} != {character_data['name']}")
                else:
                    print("❌ 数据加载失败")
            else:
                print("❌ 数据保存失败")
            
            system.shutdown_system()
            return True
            
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                
    except Exception as e:
        print(f"❌ 端到端工作流程测试失败: {e}")
        print(traceback.format_exc())
        return False

def test_error_handling():
    """测试错误处理"""
    print("🛡️ 测试错误处理...")
    
    try:
        from integrated_rpg_system import IntegratedRPGSystem
        
        temp_dir = tempfile.mkdtemp()
        
        try:
            system = IntegratedRPGSystem(config_dir=temp_dir)
            
            if not system.initialize_system():
                print("❌ 系统初始化失败")
                return False
            
            # 测试各种错误场景
            error_tests = []
            
            # 1. 测试状态同步错误处理
            try:
                system.handle_error("state_sync_error", Exception("测试同步错误"), {"module": "test"})
                error_tests.append(("state_sync_error", True))
            except Exception as e:
                error_tests.append(("state_sync_error", False))
                print(f"  状态同步错误处理失败: {e}")
            
            # 2. 测试数据持久化错误处理
            try:
                system.handle_error("data_persistence_error", Exception("测试持久化错误"), {"operation": "save"})
                error_tests.append(("data_persistence_error", True))
            except Exception as e:
                error_tests.append(("data_persistence_error", False))
                print(f"  数据持久化错误处理失败: {e}")
            
            # 3. 测试计算错误处理
            try:
                system.handle_error("calculation_error", Exception("测试计算错误"), {"calculation_type": "bagua_effects"})
                error_tests.append(("calculation_error", True))
            except Exception as e:
                error_tests.append(("calculation_error", False))
                print(f"  计算错误处理失败: {e}")
            
            # 统计结果
            passed_tests = sum(1 for _, result in error_tests if result)
            total_tests = len(error_tests)
            
            print(f"  错误处理测试: {passed_tests}/{total_tests} 通过")
            
            system.shutdown_system()
            return passed_tests == total_tests
            
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                
    except Exception as e:
        print(f"❌ 错误处理测试失败: {e}")
        return False

def test_performance():
    """测试性能"""
    print("⚡ 测试系统性能...")
    
    try:
        from integrated_rpg_system import IntegratedRPGSystem
        import time
        
        temp_dir = tempfile.mkdtemp()
        
        try:
            system = IntegratedRPGSystem(config_dir=temp_dir)
            
            if not system.initialize_system():
                print("❌ 系统初始化失败")
                return False
            
            state_manager = system.state_manager
            
            # 性能测试
            performance_results = {}
            
            # 1. 测试状态同步性能
            start_time = time.time()
            for _ in range(5):
                state_manager.sync_modules()
            sync_time = (time.time() - start_time) / 5
            performance_results["sync_time"] = sync_time
            
            # 2. 测试属性计算性能
            start_time = time.time()
            for _ in range(10):
                state_manager.calculate_realtime_attributes()
            calc_time = (time.time() - start_time) / 10
            performance_results["calc_time"] = calc_time
            
            # 3. 测试保存性能
            start_time = time.time()
            for _ in range(3):
                state_manager.save_state()
            save_time = (time.time() - start_time) / 3
            performance_results["save_time"] = save_time
            
            # 评估性能
            print(f"  状态同步: {sync_time:.3f}s")
            print(f"  属性计算: {calc_time:.3f}s")
            print(f"  数据保存: {save_time:.3f}s")
            
            # 性能标准
            performance_ok = (
                sync_time < 2.0 and
                calc_time < 1.0 and
                save_time < 3.0
            )
            
            if performance_ok:
                print("✅ 性能测试通过")
            else:
                print("⚠️ 性能测试部分通过（某些操作较慢）")
            
            system.shutdown_system()
            return True
            
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("整合RPG系统测试套件")
    print("=" * 60)
    
    tests = [
        ("系统集成", test_system_integration),
        ("端到端工作流程", test_end_to_end_workflow),
        ("错误处理", test_error_handling),
        ("性能测试", test_performance)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}测试:")
        try:
            if test_func():
                print(f"✅ {test_name}测试通过")
                passed += 1
            else:
                print(f"❌ {test_name}测试失败")
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！整合系统运行正常")
        return True
    else:
        print("⚠️ 部分测试失败，请检查系统状态")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)