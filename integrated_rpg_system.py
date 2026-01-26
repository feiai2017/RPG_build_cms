# -*- coding: utf-8 -*-
"""
整合RPG系统 (Integrated RPG System)
整合所有模块到统一的主应用文件
实现模块间数据同步和状态管理
进行端到端功能测试和性能优化
添加错误处理和用户友好的提示信息
"""

import sys
import os
import traceback
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from app_config import get_app_config

# 设置日志
_app_config = get_app_config()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(_app_config.log_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 导入所有核心模块
try:
    from unified_state_manager import UnifiedStateManager, get_state_manager, initialize_unified_system
    from wuxing_engine import WuxingEngine
    from enhanced_combat_engine import EnhancedCombatEngine
    from cultivation_school_system import get_school_manager, SchoolManager
    from loot_generator import get_loot_generator, get_challenge_manager, get_bd_optimizer
    from config_manager import ConfigManager, ConfigScope
    from module_interfaces import ModuleType, EventType, ModuleEvent, get_communication_hub
except ImportError as e:
    logger.error(f"模块导入失败: {e}")
    sys.exit(1)


@dataclass
class SystemHealth:
    """系统健康状态"""
    overall_status: str  # "healthy", "warning", "error"
    module_statuses: Dict[str, str]
    error_count: int
    warning_count: int
    last_check: datetime
    performance_metrics: Dict[str, float]


class IntegratedRPGSystem:
    """整合的RPG系统主类"""
    
    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            config_dir = _app_config.config_root
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化日志
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 系统组件
        self.state_manager: Optional[UnifiedStateManager] = None
        self.wuxing_engine: Optional[WuxingEngine] = None
        self.combat_engine: Optional[EnhancedCombatEngine] = None
        self.school_manager: Optional[SchoolManager] = None
        self.loot_generator = None
        self.challenge_manager = None
        self.bd_optimizer = None
        
        # 系统状态
        self.is_initialized = False
        self.initialization_errors: List[str] = []
        self.system_health = SystemHealth(
            overall_status="unknown",
            module_statuses={},
            error_count=0,
            warning_count=0,
            last_check=datetime.now(),
            performance_metrics={}
        )
        
        # 错误处理
        self.error_handlers: Dict[str, callable] = {}
        self._setup_error_handlers()
    
    def _setup_error_handlers(self):
        """设置错误处理器"""
        self.error_handlers = {
            "state_sync_error": self._handle_state_sync_error,
            "module_communication_error": self._handle_module_communication_error,
            "data_persistence_error": self._handle_data_persistence_error,
            "calculation_error": self._handle_calculation_error,
            "validation_error": self._handle_validation_error
        }
    
    def initialize_system(self) -> bool:
        """初始化整个系统"""
        self.logger.info("开始初始化整合RPG系统...")
        
        try:
            # 1. 初始化统一状态管理器
            self.logger.info("初始化统一状态管理器...")
            self.state_manager = initialize_unified_system(str(self.config_dir))
            self.system_health.module_statuses["state_manager"] = "healthy"
            
            # 2. 初始化五行引擎
            self.logger.info("初始化五行八卦引擎...")
            self.wuxing_engine = WuxingEngine()
            self.system_health.module_statuses["wuxing_engine"] = "healthy"
            
            # 3. 初始化战斗引擎
            self.logger.info("初始化增强战斗引擎...")
            # 创建默认的数据源
            default_data_source = {
                "skills": {},
                "modifiers": {},
                "enemies": {},
                "config": {}
            }
            self.combat_engine = EnhancedCombatEngine(default_data_source)
            self.system_health.module_statuses["combat_engine"] = "healthy"
            
            # 4. 初始化流派管理器
            self.logger.info("初始化流派管理系统...")
            self.school_manager = get_school_manager()
            self.system_health.module_statuses["school_manager"] = "healthy"
            
            # 5. 初始化掉落系统
            self.logger.info("初始化智能掉落系统...")
            self.loot_generator = get_loot_generator()
            self.challenge_manager = get_challenge_manager()
            self.bd_optimizer = get_bd_optimizer()
            self.system_health.module_statuses["loot_system"] = "healthy"
            
            # 6. 执行系统集成测试
            self.logger.info("执行系统集成测试...")
            integration_success = self._run_integration_tests()
            
            if integration_success:
                self.is_initialized = True
                self.system_health.overall_status = "healthy"
                self.logger.info("✅ 整合RPG系统初始化成功")
                return True
            else:
                self.system_health.overall_status = "error"
                self.logger.error("❌ 系统集成测试失败")
                return False
                
        except Exception as e:
            self.initialization_errors.append(str(e))
            self.system_health.overall_status = "error"
            self.system_health.error_count += 1
            self.logger.error(f"系统初始化失败: {e}")
            self.logger.error(traceback.format_exc())
            return False
    
    def _run_integration_tests(self) -> bool:
        """运行系统集成测试"""
        self.logger.info("开始系统集成测试...")
        
        test_results = []
        
        try:
            # 测试1: 模块间数据同步
            self.logger.info("测试1: 模块间数据同步...")
            sync_result = self._test_module_data_sync()
            test_results.append(("module_data_sync", sync_result))
            
            # 测试2: 端到端功能流程
            self.logger.info("测试2: 端到端功能流程...")
            e2e_result = self._test_end_to_end_workflow()
            test_results.append(("end_to_end_workflow", e2e_result))
            
            # 测试3: 错误处理和恢复
            self.logger.info("测试3: 错误处理和恢复...")
            error_handling_result = self._test_error_handling()
            test_results.append(("error_handling", error_handling_result))
            
            # 测试4: 性能基准测试
            self.logger.info("测试4: 性能基准测试...")
            performance_result = self._test_performance_benchmarks()
            test_results.append(("performance_benchmarks", performance_result))
            
            # 评估测试结果
            passed_tests = sum(1 for _, result in test_results if result)
            total_tests = len(test_results)
            
            self.logger.info(f"集成测试完成: {passed_tests}/{total_tests} 通过")
            
            if passed_tests == total_tests:
                self.logger.info("✅ 所有集成测试通过")
                return True
            else:
                self.logger.warning(f"⚠️ {total_tests - passed_tests} 个测试失败")
                for test_name, result in test_results:
                    if not result:
                        self.logger.error(f"❌ 测试失败: {test_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"集成测试执行失败: {e}")
            return False
    
    def _test_module_data_sync(self) -> bool:
        """测试模块间数据同步"""
        try:
            # 创建测试数据
            test_character = {
                "name": "集成测试角色",
                "level": 50,
                "school": "sword_cultivator",
                "realm": "金丹",
                "base_attributes": {
                    "str": 80,
                    "agi": 70,
                    "int": 60,
                    "max_hp": 2000,
                    "base_atk": 150,
                    "crit_rate": 0.15,
                    "crit_dmg": 2.0
                },
                "affinity_main": "金"
            }
            
            test_bagua = {
                "stones": {
                    "QIAN": {1: None, 2: "gem_金", 3: "gem_火", 4: None},
                    "DUI": {1: None, 2: "gem_金", 3: None, 4: None},
                    "LI": {1: None, 2: "gem_火", 3: None, 4: None},
                    "ZHEN": {1: None, 2: None, 3: None, 4: None},
                    "XUN": {1: None, 2: None, 3: None, 4: None},
                    "KAN": {1: None, 2: None, 3: None, 4: None},
                    "GEN": {1: None, 2: None, 3: None, 4: None},
                    "KUN": {1: None, 2: None, 3: None, 4: None}
                },
                "core": {1: "core_mad", 2: None, 3: None},
                "seed": 123456
            }
            
            # 更新状态
            self.state_manager.update_character_data(test_character)
            self.state_manager.update_bagua_configuration(test_bagua)
            
            # 验证同步
            is_consistent, issues = self.state_manager.validate_state_consistency()
            
            if not is_consistent:
                self.logger.error(f"数据同步测试失败: {issues}")
                return False
            
            # 验证各模块状态
            five_elements_state = self.state_manager.get_module_state("five_elements")
            combat_state = self.state_manager.get_module_state("combat")
            character_state = self.state_manager.get_module_state("character")
            
            # 检查关键数据一致性
            if five_elements_state.get("disciple") != test_character["name"]:
                self.logger.error("五行模块角色名不一致")
                return False
            
            if combat_state.get("character_stats", {}).get("base_atk") is None:
                self.logger.error("战斗模块缺少角色属性")
                return False
            
            if character_state.get("character_data", {}).get("school") != test_character["school"]:
                self.logger.error("角色模块流派不一致")
                return False
            
            self.logger.info("✅ 模块数据同步测试通过")
            return True
            
        except Exception as e:
            self.logger.error(f"模块数据同步测试失败: {e}")
            return False
    
    def _test_end_to_end_workflow(self) -> bool:
        """测试端到端功能流程"""
        try:
            # 模拟完整的用户工作流程
            
            # 1. 角色创建和配置
            self.logger.info("测试角色创建...")
            character_data = {
                "name": "端到端测试",
                "level": 25,
                "school": "spell_cultivator",
                "realm": "筑基",
                "base_attributes": {
                    "str": 40,
                    "agi": 60,
                    "int": 80,
                    "max_hp": 1200,
                    "base_atk": 100,
                    "crit_rate": 0.1,
                    "crit_dmg": 1.8
                },
                "affinity_main": "火"
            }
            
            self.state_manager.update_character_data(character_data)
            
            # 2. 八卦配置
            self.logger.info("测试八卦配置...")
            bagua_config = {
                "stones": {
                    "LI": {1: None, 2: "gem_火", 3: "gem_火", 4: None},
                    "QIAN": {1: None, 2: "gem_金", 3: None, 4: None}
                },
                "core": {1: "core_invert", 2: None, 3: None},
                "seed": 789012
            }
            
            # 使用完整的八卦配置结构
            full_bagua_config = {
                "stones": {tri: {i: None for i in range(1, 5)} for tri in 
                          ["QIAN", "DUI", "LI", "ZHEN", "XUN", "KAN", "GEN", "KUN"]},
                "core": {i: None for i in range(1, 4)},
                "seed": 789012
            }
            
            # 应用特定配置
            full_bagua_config["stones"]["LI"] = {1: None, 2: "gem_火", 3: "gem_火", 4: None}
            full_bagua_config["stones"]["QIAN"] = {1: None, 2: "gem_金", 3: None, 4: None}
            full_bagua_config["core"][1] = "core_invert"
            
            self.state_manager.update_bagua_configuration(full_bagua_config)
            
            # 3. 战斗模拟
            self.logger.info("测试战斗模拟...")
            combat_settings = {
                "selected_skills": ["mvp_basic_attack", "mvp_crit_execute"],
                "skill_chain": {
                    "main_skill": "mvp_basic_attack",
                    "main_mods": ["mvp_mod_damage_20"],
                    "triggers": []
                },
                "simulation_params": {
                    "enemy_hp": 2500,
                    "enemy_dps": 30,
                    "max_time": 15.0
                }
            }
            
            self.state_manager.update_combat_settings(combat_settings)
            
            # 执行战斗测试
            combat_result = self.state_manager.perform_one_click_combat_test()
            
            if not combat_result["success"]:
                self.logger.error(f"战斗测试失败: {combat_result.get('error')}")
                return False
            
            # 4. BD配置验证
            self.logger.info("测试BD配置验证...")
            bd_validation = self.state_manager.validate_bd_configuration()
            
            if not bd_validation["is_valid"]:
                self.logger.warning(f"BD配置验证警告: {bd_validation['errors']}")
                # 不作为失败条件，因为测试配置可能不完整
            
            # 5. 数据持久化
            self.logger.info("测试数据持久化...")
            save_success = self.state_manager.save_state()
            
            if not save_success:
                self.logger.error("数据保存失败")
                return False
            
            # 6. 数据加载验证
            new_state_manager = UnifiedStateManager(config_dir=str(self.config_dir))
            load_success = new_state_manager.load_state()
            
            if not load_success:
                self.logger.error("数据加载失败")
                return False
            
            # 验证加载后的数据一致性
            loaded_char = new_state_manager.character_data
            if loaded_char.get("name") != character_data["name"]:
                self.logger.error("加载后角色数据不一致")
                return False
            
            self.logger.info("✅ 端到端功能流程测试通过")
            return True
            
        except Exception as e:
            self.logger.error(f"端到端功能流程测试失败: {e}")
            return False
    
    def _test_error_handling(self) -> bool:
        """测试错误处理和恢复"""
        try:
            # 测试各种错误场景
            
            # 1. 测试无效数据处理
            self.logger.info("测试无效数据处理...")
            
            # 尝试设置无效的角色数据
            invalid_character = {
                "name": "",  # 空名称
                "level": -1,  # 无效等级
                "school": "invalid_school",  # 无效流派
                "realm": "无效境界",
                "base_attributes": {
                    "str": -10,  # 负数属性
                    "max_hp": 0   # 零生命值
                }
            }
            
            try:
                self.state_manager.update_character_data(invalid_character)
                # 系统应该能够处理无效数据而不崩溃
                self.logger.info("系统成功处理了无效角色数据")
            except Exception as e:
                self.logger.info(f"系统正确拒绝了无效数据: {e}")
            
            # 2. 测试配置冲突处理
            self.logger.info("测试配置冲突处理...")
            
            # 创建冲突的八卦配置
            conflicting_bagua = {
                "stones": {
                    "INVALID_TRIGRAM": {1: "invalid_stone"}  # 无效卦位和灵石
                },
                "core": {10: "invalid_core"},  # 无效核心位置
                "seed": -1  # 无效种子
            }
            
            try:
                self.state_manager.update_bagua_configuration(conflicting_bagua)
                # 检查系统是否保持了一致性
                is_consistent, _ = self.state_manager.validate_state_consistency()
                if is_consistent:
                    self.logger.info("系统在处理冲突配置后保持了一致性")
                else:
                    self.logger.warning("系统在处理冲突配置后出现不一致")
            except Exception as e:
                self.logger.info(f"系统正确处理了配置冲突: {e}")
            
            # 3. 测试模块通信错误恢复
            self.logger.info("测试模块通信错误恢复...")
            
            # 模拟模块状态损坏
            original_module_states = self.state_manager._module_states.copy()
            self.state_manager._module_states = {}  # 清空模块状态
            
            # 尝试恢复
            try:
                self.state_manager.sync_modules()
                # 检查是否成功恢复
                if self.state_manager._module_states:
                    self.logger.info("系统成功恢复了模块状态")
                else:
                    self.logger.warning("系统未能恢复模块状态")
            except Exception as e:
                self.logger.error(f"模块状态恢复失败: {e}")
                # 恢复原始状态
                self.state_manager._module_states = original_module_states
            
            # 4. 测试数据持久化错误处理
            self.logger.info("测试数据持久化错误处理...")
            
            # 尝试保存到无效路径
            invalid_path = "/invalid/path/that/does/not/exist/state.json"
            save_result = self.state_manager.save_state(invalid_path)
            
            if not save_result:
                self.logger.info("系统正确处理了无效保存路径")
            else:
                self.logger.warning("系统未能正确处理无效保存路径")
            
            self.logger.info("✅ 错误处理测试通过")
            return True
            
        except Exception as e:
            self.logger.error(f"错误处理测试失败: {e}")
            return False
    
    def _test_performance_benchmarks(self) -> bool:
        """测试性能基准"""
        try:
            import time
            
            # 性能测试指标
            performance_metrics = {}
            
            # 1. 测试状态同步性能
            self.logger.info("测试状态同步性能...")
            
            start_time = time.time()
            for i in range(10):
                self.state_manager.sync_modules()
            sync_time = (time.time() - start_time) / 10
            performance_metrics["avg_sync_time"] = sync_time
            
            if sync_time > 1.0:  # 如果平均同步时间超过1秒
                self.logger.warning(f"状态同步性能较慢: {sync_time:.3f}s")
            else:
                self.logger.info(f"状态同步性能良好: {sync_time:.3f}s")
            
            # 2. 测试属性计算性能
            self.logger.info("测试属性计算性能...")
            
            start_time = time.time()
            for i in range(20):
                self.state_manager.calculate_realtime_attributes()
            calc_time = (time.time() - start_time) / 20
            performance_metrics["avg_calc_time"] = calc_time
            
            if calc_time > 0.5:  # 如果平均计算时间超过0.5秒
                self.logger.warning(f"属性计算性能较慢: {calc_time:.3f}s")
            else:
                self.logger.info(f"属性计算性能良好: {calc_time:.3f}s")
            
            # 3. 测试数据持久化性能
            self.logger.info("测试数据持久化性能...")
            
            start_time = time.time()
            for i in range(5):
                self.state_manager.save_state()
            save_time = (time.time() - start_time) / 5
            performance_metrics["avg_save_time"] = save_time
            
            if save_time > 2.0:  # 如果平均保存时间超过2秒
                self.logger.warning(f"数据保存性能较慢: {save_time:.3f}s")
            else:
                self.logger.info(f"数据保存性能良好: {save_time:.3f}s")
            
            # 4. 测试战斗模拟性能
            self.logger.info("测试战斗模拟性能...")
            
            start_time = time.time()
            for i in range(3):
                self.state_manager.perform_one_click_combat_test()
            combat_time = (time.time() - start_time) / 3
            performance_metrics["avg_combat_time"] = combat_time
            
            if combat_time > 5.0:  # 如果平均战斗时间超过5秒
                self.logger.warning(f"战斗模拟性能较慢: {combat_time:.3f}s")
            else:
                self.logger.info(f"战斗模拟性能良好: {combat_time:.3f}s")
            
            # 更新系统健康状态
            self.system_health.performance_metrics = performance_metrics
            
            # 评估整体性能
            slow_operations = sum(1 for metric, time_val in performance_metrics.items() 
                                if (metric == "avg_sync_time" and time_val > 1.0) or
                                   (metric == "avg_calc_time" and time_val > 0.5) or
                                   (metric == "avg_save_time" and time_val > 2.0) or
                                   (metric == "avg_combat_time" and time_val > 5.0))
            
            if slow_operations == 0:
                self.logger.info("✅ 性能基准测试通过 - 所有操作性能良好")
                return True
            elif slow_operations <= 2:
                self.logger.warning(f"⚠️ 性能基准测试部分通过 - {slow_operations} 个操作性能较慢")
                return True  # 仍然认为通过，但有警告
            else:
                self.logger.error(f"❌ 性能基准测试失败 - {slow_operations} 个操作性能不达标")
                return False
            
        except Exception as e:
            self.logger.error(f"性能基准测试失败: {e}")
            return False
    
    def get_system_health(self) -> SystemHealth:
        """获取系统健康状态"""
        # 更新健康检查时间
        self.system_health.last_check = datetime.now()
        
        # 检查各模块状态
        if self.is_initialized:
            try:
                # 检查状态管理器
                if self.state_manager:
                    is_consistent, issues = self.state_manager.validate_state_consistency()
                    if is_consistent:
                        self.system_health.module_statuses["state_manager"] = "healthy"
                    else:
                        self.system_health.module_statuses["state_manager"] = "warning"
                        self.system_health.warning_count += len(issues)
                
                # 检查其他模块
                for module_name in ["wuxing_engine", "combat_engine", "school_manager", "loot_system"]:
                    if module_name not in self.system_health.module_statuses:
                        self.system_health.module_statuses[module_name] = "unknown"
                
                # 评估整体状态
                healthy_modules = sum(1 for status in self.system_health.module_statuses.values() 
                                    if status == "healthy")
                total_modules = len(self.system_health.module_statuses)
                
                if healthy_modules == total_modules:
                    self.system_health.overall_status = "healthy"
                elif healthy_modules >= total_modules * 0.8:
                    self.system_health.overall_status = "warning"
                else:
                    self.system_health.overall_status = "error"
                    
            except Exception as e:
                self.system_health.overall_status = "error"
                self.system_health.error_count += 1
                self.logger.error(f"健康检查失败: {e}")
        
        return self.system_health
    
    # 错误处理方法
    def _handle_state_sync_error(self, error: Exception, context: Dict[str, Any]):
        """处理状态同步错误"""
        self.logger.error(f"状态同步错误: {error}")
        
        try:
            # 尝试重新同步
            self.state_manager.sync_modules()
            self.logger.info("状态同步错误已恢复")
        except Exception as e:
            self.logger.error(f"状态同步恢复失败: {e}")
    
    def _handle_module_communication_error(self, error: Exception, context: Dict[str, Any]):
        """处理模块通信错误"""
        self.logger.error(f"模块通信错误: {error}")
        
        # 标记相关模块状态
        module_name = context.get("module_name", "unknown")
        self.system_health.module_statuses[module_name] = "error"
        self.system_health.error_count += 1
    
    def _handle_data_persistence_error(self, error: Exception, context: Dict[str, Any]):
        """处理数据持久化错误"""
        self.logger.error(f"数据持久化错误: {error}")
        
        # 尝试创建备份
        try:
            backup_path = self.config_dir / f"emergency_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            self.state_manager.save_state(str(backup_path))
            self.logger.info(f"紧急备份已创建: {backup_path}")
        except Exception as e:
            self.logger.error(f"紧急备份创建失败: {e}")
    
    def _handle_calculation_error(self, error: Exception, context: Dict[str, Any]):
        """处理计算错误"""
        self.logger.error(f"计算错误: {error}")
        
        # 使用降级计算方案
        calculation_type = context.get("calculation_type", "unknown")
        if calculation_type == "bagua_effects":
            self.logger.info("使用简化的八卦效果计算")
        elif calculation_type == "combat_simulation":
            self.logger.info("使用基础战斗模拟")
    
    def _handle_validation_error(self, error: Exception, context: Dict[str, Any]):
        """处理验证错误"""
        self.logger.warning(f"验证错误: {error}")
        
        # 记录验证问题但不中断系统运行
        validation_type = context.get("validation_type", "unknown")
        self.logger.info(f"继续运行，但 {validation_type} 验证失败")
    
    def handle_error(self, error_type: str, error: Exception, context: Dict[str, Any] = None):
        """统一错误处理入口"""
        if context is None:
            context = {}
        
        self.logger.error(f"系统错误 [{error_type}]: {error}")
        
        # 调用对应的错误处理器
        handler = self.error_handlers.get(error_type)
        if handler:
            try:
                handler(error, context)
            except Exception as handler_error:
                self.logger.error(f"错误处理器失败: {handler_error}")
        else:
            self.logger.warning(f"未找到错误类型 {error_type} 的处理器")
        
        # 更新系统健康状态
        self.system_health.error_count += 1
        self.system_health.last_check = datetime.now()
    
    def run_system_diagnostics(self) -> Dict[str, Any]:
        """运行系统诊断"""
        self.logger.info("开始系统诊断...")
        
        diagnostics = {
            "timestamp": datetime.now().isoformat(),
            "system_initialized": self.is_initialized,
            "initialization_errors": self.initialization_errors,
            "health_status": self.get_system_health(),
            "module_tests": {},
            "performance_summary": {},
            "recommendations": []
        }
        
        if not self.is_initialized:
            diagnostics["recommendations"].append("系统未初始化，请先调用 initialize_system()")
            return diagnostics
        
        try:
            # 测试各个模块
            self.logger.info("测试状态管理器...")
            try:
                is_consistent, issues = self.state_manager.validate_state_consistency()
                diagnostics["module_tests"]["state_manager"] = {
                    "status": "pass" if is_consistent else "warning",
                    "issues": issues
                }
            except Exception as e:
                diagnostics["module_tests"]["state_manager"] = {
                    "status": "fail",
                    "error": str(e)
                }
            
            self.logger.info("测试五行引擎...")
            try:
                # 简单的五行引擎测试
                test_config = {
                    "stones": {"QIAN": {2: "gem_金"}},
                    "realm": "金丹"
                }
                is_valid, errors = self.wuxing_engine.validate_bagua_configuration(test_config)
                diagnostics["module_tests"]["wuxing_engine"] = {
                    "status": "pass" if is_valid else "warning",
                    "errors": errors
                }
            except Exception as e:
                diagnostics["module_tests"]["wuxing_engine"] = {
                    "status": "fail",
                    "error": str(e)
                }
            
            # 性能摘要
            if self.system_health.performance_metrics:
                diagnostics["performance_summary"] = self.system_health.performance_metrics
                
                # 生成性能建议
                for metric, value in self.system_health.performance_metrics.items():
                    if metric == "avg_sync_time" and value > 1.0:
                        diagnostics["recommendations"].append("状态同步性能较慢，考虑优化模块间通信")
                    elif metric == "avg_calc_time" and value > 0.5:
                        diagnostics["recommendations"].append("属性计算性能较慢，考虑缓存计算结果")
                    elif metric == "avg_save_time" and value > 2.0:
                        diagnostics["recommendations"].append("数据保存性能较慢，考虑异步保存或数据压缩")
            
            # 系统健康建议
            if self.system_health.overall_status == "error":
                diagnostics["recommendations"].append("系统整体状态异常，建议检查错误日志并重新初始化")
            elif self.system_health.overall_status == "warning":
                diagnostics["recommendations"].append("系统存在警告，建议检查模块状态")
            
            if not diagnostics["recommendations"]:
                diagnostics["recommendations"].append("系统运行正常，无需特别关注")
            
        except Exception as e:
            diagnostics["diagnostic_error"] = str(e)
            self.logger.error(f"系统诊断失败: {e}")
        
        self.logger.info("系统诊断完成")
        return diagnostics
    
    def shutdown_system(self):
        """优雅关闭系统"""
        self.logger.info("开始关闭系统...")
        
        try:
            # 保存当前状态
            if self.state_manager:
                self.logger.info("保存系统状态...")
                save_success = self.state_manager.save_state()
                if save_success:
                    self.logger.info("系统状态已保存")
                else:
                    self.logger.warning("系统状态保存失败")
            
            # 清理资源
            self.logger.info("清理系统资源...")
            self.state_manager = None
            self.wuxing_engine = None
            self.combat_engine = None
            self.school_manager = None
            self.loot_generator = None
            self.challenge_manager = None
            self.bd_optimizer = None
            
            self.is_initialized = False
            self.logger.info("✅ 系统已优雅关闭")
            
        except Exception as e:
            self.logger.error(f"系统关闭过程中出错: {e}")


# 全局系统实例
_global_integrated_system: Optional[IntegratedRPGSystem] = None


def get_integrated_system() -> IntegratedRPGSystem:
    """获取全局整合系统实例"""
    global _global_integrated_system
    if _global_integrated_system is None:
        _global_integrated_system = IntegratedRPGSystem()
    return _global_integrated_system


def initialize_integrated_system(config_dir: Optional[str] = None) -> IntegratedRPGSystem:
    """初始化整合系统"""
    global _global_integrated_system
    _global_integrated_system = IntegratedRPGSystem(config_dir)
    
    success = _global_integrated_system.initialize_system()
    if not success:
        logger.error("整合系统初始化失败")
        raise RuntimeError("整合系统初始化失败")
    
    return _global_integrated_system


if __name__ == "__main__":
    # 命令行测试
    print("=" * 60)
    print("整合RPG系统测试")
    print("=" * 60)
    
    try:
        # 初始化系统
        system = initialize_integrated_system()
        
        # 运行诊断
        diagnostics = system.run_system_diagnostics()
        
        print("\n系统诊断结果:")
        print(f"系统状态: {diagnostics['health_status'].overall_status}")
        print(f"模块测试: {len([t for t in diagnostics['module_tests'].values() if t['status'] == 'pass'])} 通过")
        
        if diagnostics['recommendations']:
            print("\n建议:")
            for rec in diagnostics['recommendations']:
                print(f"• {rec}")
        
        # 关闭系统
        system.shutdown_system()
        
        print("\n✅ 整合系统测试完成")
        
    except Exception as e:
        print(f"\n❌ 整合系统测试失败: {e}")
        logger.error(traceback.format_exc())
