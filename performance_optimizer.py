# -*- coding: utf-8 -*-
"""
性能优化器 (Performance Optimizer)
优化系统性能和用户体验
"""

import time
import functools
import streamlit as st
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass
from unified_state_manager import get_state_manager


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    operation_name: str
    execution_time: float
    memory_usage: Optional[float] = None
    cache_hit_rate: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None


class PerformanceOptimizer:
    """系统性能优化器"""
    
    def __init__(self):
        self.metrics_history: Dict[str, list] = {}
        self.cache_enabled = True
        self.optimization_settings = {
            "enable_lazy_loading": True,
            "enable_data_compression": True,
            "enable_smart_caching": True,
            "max_cache_size": 100,
            "cache_ttl": 300  # 5分钟
        }
    
    def measure_performance(self, operation_name: str):
        """性能测量装饰器"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                error_message = None
                result = None
                
                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    success = False
                    error_message = str(e)
                    raise
                finally:
                    execution_time = time.time() - start_time
                    
                    # 记录性能指标
                    metric = PerformanceMetrics(
                        operation_name=operation_name,
                        execution_time=execution_time,
                        success=success,
                        error_message=error_message
                    )
                    
                    self._record_metric(metric)
                
                return result
            return wrapper
        return decorator
    
    def _record_metric(self, metric: PerformanceMetrics):
        """记录性能指标"""
        if metric.operation_name not in self.metrics_history:
            self.metrics_history[metric.operation_name] = []
        
        self.metrics_history[metric.operation_name].append(metric)
        
        # 保持历史记录在合理范围内
        if len(self.metrics_history[metric.operation_name]) > 100:
            self.metrics_history[metric.operation_name] = \
                self.metrics_history[metric.operation_name][-50:]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        summary = {}
        
        for operation, metrics in self.metrics_history.items():
            if not metrics:
                continue
            
            execution_times = [m.execution_time for m in metrics if m.success]
            success_rate = sum(1 for m in metrics if m.success) / len(metrics)
            
            if execution_times:
                summary[operation] = {
                    "avg_time": sum(execution_times) / len(execution_times),
                    "max_time": max(execution_times),
                    "min_time": min(execution_times),
                    "success_rate": success_rate,
                    "total_calls": len(metrics)
                }
        
        return summary
    
    def optimize_streamlit_performance(self):
        """优化Streamlit性能"""
        # 设置页面配置优化
        if not hasattr(st.session_state, 'performance_optimized'):
            # 启用缓存
            if self.optimization_settings["enable_smart_caching"]:
                self._setup_smart_caching()
            
            # 优化会话状态
            self._optimize_session_state()
            
            st.session_state.performance_optimized = True
    
    def _setup_smart_caching(self):
        """设置智能缓存"""
        # 为常用操作设置缓存
        cache_config = {
            "ttl": self.optimization_settings["cache_ttl"],
            "max_entries": self.optimization_settings["max_cache_size"]
        }
        
        # 这里可以设置具体的缓存策略
        pass
    
    def _optimize_session_state(self):
        """优化会话状态"""
        # 清理过期的会话状态
        current_time = time.time()
        
        # 移除超过TTL的缓存项
        keys_to_remove = []
        for key in st.session_state.keys():
            if key.startswith('cache_') and hasattr(st.session_state[key], 'timestamp'):
                if current_time - st.session_state[key].timestamp > self.optimization_settings["cache_ttl"]:
                    keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del st.session_state[key]
    
    def get_optimization_suggestions(self) -> list:
        """获取优化建议"""
        suggestions = []
        summary = self.get_performance_summary()
        
        for operation, stats in summary.items():
            # 检查慢操作
            if stats["avg_time"] > 2.0:
                suggestions.append({
                    "type": "performance",
                    "priority": "high",
                    "operation": operation,
                    "issue": f"操作 '{operation}' 平均耗时 {stats['avg_time']:.2f}s，建议优化",
                    "suggestion": "考虑添加缓存或优化算法"
                })
            
            # 检查成功率
            if stats["success_rate"] < 0.9:
                suggestions.append({
                    "type": "reliability",
                    "priority": "high",
                    "operation": operation,
                    "issue": f"操作 '{operation}' 成功率仅 {stats['success_rate']:.1%}",
                    "suggestion": "检查错误处理和输入验证"
                })
        
        return suggestions
    
    def apply_automatic_optimizations(self):
        """应用自动优化"""
        try:
            # 1. 优化Streamlit性能
            self.optimize_streamlit_performance()
            
            # 2. 优化状态管理器
            state_manager = get_state_manager()
            if hasattr(state_manager, 'optimize_performance'):
                state_manager.optimize_performance()
            
            # 3. 清理内存
            self._cleanup_memory()
            
            return True
        except Exception as e:
            st.error(f"自动优化失败: {str(e)}")
            return False
    
    def _cleanup_memory(self):
        """清理内存"""
        import gc
        gc.collect()


# 全局性能优化器实例
_global_performance_optimizer: Optional[PerformanceOptimizer] = None


def get_performance_optimizer() -> PerformanceOptimizer:
    """获取全局性能优化器实例"""
    global _global_performance_optimizer
    
    if _global_performance_optimizer is None:
        _global_performance_optimizer = PerformanceOptimizer()
    
    return _global_performance_optimizer


def optimize_function(operation_name: str):
    """函数性能优化装饰器"""
    optimizer = get_performance_optimizer()
    return optimizer.measure_performance(operation_name)


# 预定义的性能优化装饰器
@optimize_function("state_sync")
def optimized_state_sync():
    """优化的状态同步"""
    state_manager = get_state_manager()
    return state_manager.sync_modules()


@optimize_function("attribute_calculation")
def optimized_attribute_calculation():
    """优化的属性计算"""
    state_manager = get_state_manager()
    return state_manager.calculate_realtime_attributes()


@optimize_function("combat_simulation")
def optimized_combat_simulation():
    """优化的战斗模拟"""
    state_manager = get_state_manager()
    return state_manager.perform_one_click_combat_test()


# 用户体验优化函数
def enhance_user_experience():
    """增强用户体验"""
    # 添加加载指示器
    if 'loading_states' not in st.session_state:
        st.session_state.loading_states = {}
    
    # 优化错误显示
    if 'error_history' not in st.session_state:
        st.session_state.error_history = []
    
    # 添加操作反馈
    if 'operation_feedback' not in st.session_state:
        st.session_state.operation_feedback = []


def show_loading(operation_name: str):
    """显示加载状态"""
    st.session_state.loading_states[operation_name] = True
    return st.spinner(f"正在执行 {operation_name}...")


def hide_loading(operation_name: str):
    """隐藏加载状态"""
    if operation_name in st.session_state.loading_states:
        del st.session_state.loading_states[operation_name]


def show_operation_feedback(message: str, type: str = "success"):
    """显示操作反馈"""
    feedback = {
        "message": message,
        "type": type,
        "timestamp": time.time()
    }
    
    if 'operation_feedback' not in st.session_state:
        st.session_state.operation_feedback = []
    
    st.session_state.operation_feedback.append(feedback)
    
    # 保持反馈历史在合理范围内
    if len(st.session_state.operation_feedback) > 10:
        st.session_state.operation_feedback = st.session_state.operation_feedback[-5:]
    
    # 显示反馈
    if type == "success":
        st.success(message)
    elif type == "warning":
        st.warning(message)
    elif type == "error":
        st.error(message)
    else:
        st.info(message)


def render_performance_dashboard():
    """渲染性能仪表板"""
    st.subheader("📊 系统性能监控")
    
    optimizer = get_performance_optimizer()
    summary = optimizer.get_performance_summary()
    
    if not summary:
        st.info("暂无性能数据")
        return
    
    # 性能概览
    col1, col2, col3 = st.columns(3)
    
    with col1:
        avg_times = [stats["avg_time"] for stats in summary.values()]
        overall_avg = sum(avg_times) / len(avg_times) if avg_times else 0
        st.metric("平均响应时间", f"{overall_avg:.2f}s")
    
    with col2:
        success_rates = [stats["success_rate"] for stats in summary.values()]
        overall_success = sum(success_rates) / len(success_rates) if success_rates else 1
        st.metric("整体成功率", f"{overall_success:.1%}")
    
    with col3:
        total_calls = sum(stats["total_calls"] for stats in summary.values())
        st.metric("总操作次数", total_calls)
    
    # 详细性能数据
    st.subheader("详细性能数据")
    
    for operation, stats in summary.items():
        with st.expander(f"📈 {operation}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("平均时间", f"{stats['avg_time']:.3f}s")
                st.metric("最大时间", f"{stats['max_time']:.3f}s")
            
            with col2:
                st.metric("最小时间", f"{stats['min_time']:.3f}s")
                st.metric("成功率", f"{stats['success_rate']:.1%}")
    
    # 优化建议
    suggestions = optimizer.get_optimization_suggestions()
    if suggestions:
        st.subheader("🔧 优化建议")
        
        for suggestion in suggestions:
            if suggestion["priority"] == "high":
                st.error(f"🔴 {suggestion['issue']}")
                st.caption(f"建议: {suggestion['suggestion']}")
            else:
                st.warning(f"🟡 {suggestion['issue']}")
                st.caption(f"建议: {suggestion['suggestion']}")
    
    # 自动优化按钮
    if st.button("🚀 应用自动优化", use_container_width=True):
        with st.spinner("正在应用优化..."):
            if optimizer.apply_automatic_optimizations():
                st.success("✅ 自动优化完成")
            else:
                st.error("❌ 自动优化失败")