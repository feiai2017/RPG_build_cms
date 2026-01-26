# -*- coding: utf-8 -*-
"""
模块间通信接口和数据同步机制
定义各模块间的标准化通信协议和数据交换格式
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import threading
import time


class ModuleType(Enum):
    """模块类型枚举"""
    FIVE_ELEMENTS = "five_elements"
    COMBAT = "combat"
    CHARACTER = "character"
    LOOT = "loot"
    UI = "ui"


class EventType(Enum):
    """事件类型枚举"""
    CHARACTER_UPDATED = "character_updated"
    BAGUA_CHANGED = "bagua_changed"
    COMBAT_RESULT = "combat_result"
    SKILL_UNLOCKED = "skill_unlocked"
    ITEM_OBTAINED = "item_obtained"
    STATE_SYNC_REQUIRED = "state_sync_required"


@dataclass
class ModuleEvent:
    """模块事件数据结构"""
    event_type: EventType
    source_module: ModuleType
    target_modules: List[ModuleType]
    data: Dict[str, Any]
    timestamp: float
    event_id: str


class IModuleInterface(ABC):
    """模块接口基类"""
    
    @abstractmethod
    def get_module_type(self) -> ModuleType:
        """获取模块类型"""
        pass
    
    @abstractmethod
    def initialize(self, state_manager) -> bool:
        """初始化模块"""
        pass
    
    @abstractmethod
    def update_state(self, state_data: Dict[str, Any]) -> bool:
        """更新模块状态"""
        pass
    
    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """获取模块当前状态"""
        pass
    
    @abstractmethod
    def handle_event(self, event: ModuleEvent) -> bool:
        """处理模块事件"""
        pass
    
    @abstractmethod
    def validate_data(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """验证数据有效性"""
        pass


class EventBus:
    """事件总线 - 负责模块间事件传递"""
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._event_history: List[ModuleEvent] = []
        self._lock = threading.Lock()
    
    def subscribe(self, event_type: EventType, callback: Callable[[ModuleEvent], None]) -> None:
        """订阅事件"""
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: EventType, callback: Callable) -> None:
        """取消订阅"""
        with self._lock:
            if event_type in self._subscribers:
                try:
                    self._subscribers[event_type].remove(callback)
                except ValueError:
                    pass
    
    def publish(self, event: ModuleEvent) -> None:
        """发布事件"""
        with self._lock:
            self._event_history.append(event)
            # 保持历史记录在合理范围内
            if len(self._event_history) > 1000:
                self._event_history = self._event_history[-500:]
        
        # 通知订阅者
        subscribers = self._subscribers.get(event.event_type, [])
        for callback in subscribers:
            try:
                callback(event)
            except Exception as e:
                print(f"事件处理错误: {e}")
    
    def get_event_history(self, event_type: Optional[EventType] = None, 
                         limit: int = 100) -> List[ModuleEvent]:
        """获取事件历史"""
        with self._lock:
            if event_type:
                filtered = [e for e in self._event_history if e.event_type == event_type]
                return filtered[-limit:]
            return self._event_history[-limit:]


class ModuleCommunicationHub:
    """模块通信中心"""
    
    def __init__(self):
        self._modules: Dict[ModuleType, IModuleInterface] = {}
        self._event_bus = EventBus()
        self._sync_callbacks: List[Callable] = []
    
    def register_module(self, module: IModuleInterface) -> bool:
        """注册模块"""
        try:
            module_type = module.get_module_type()
            self._modules[module_type] = module
            
            # 订阅相关事件
            self._setup_module_subscriptions(module)
            
            return True
        except Exception as e:
            print(f"模块注册失败: {e}")
            return False
    
    def _setup_module_subscriptions(self, module: IModuleInterface) -> None:
        """设置模块事件订阅"""
        module_type = module.get_module_type()
        
        # 根据模块类型设置不同的事件订阅
        if module_type == ModuleType.FIVE_ELEMENTS:
            self._event_bus.subscribe(EventType.CHARACTER_UPDATED, 
                                    lambda e: self._handle_character_update_for_five_elements(e))
        
        elif module_type == ModuleType.COMBAT:
            self._event_bus.subscribe(EventType.BAGUA_CHANGED,
                                    lambda e: self._handle_bagua_change_for_combat(e))
            self._event_bus.subscribe(EventType.CHARACTER_UPDATED,
                                    lambda e: self._handle_character_update_for_combat(e))
        
        elif module_type == ModuleType.CHARACTER:
            self._event_bus.subscribe(EventType.COMBAT_RESULT,
                                    lambda e: self._handle_combat_result_for_character(e))
            self._event_bus.subscribe(EventType.SKILL_UNLOCKED,
                                    lambda e: self._handle_skill_unlock_for_character(e))
        
        elif module_type == ModuleType.LOOT:
            self._event_bus.subscribe(EventType.COMBAT_RESULT,
                                    lambda e: self._handle_combat_result_for_loot(e))
        
        elif module_type == ModuleType.UI:
            # UI模块监听所有事件以更新界面
            for event_type in EventType:
                self._event_bus.subscribe(event_type,
                                        lambda e: self._handle_ui_update(e))
    
    def _handle_character_update_for_five_elements(self, event: ModuleEvent) -> None:
        """处理角色更新对五行模块的影响"""
        if ModuleType.FIVE_ELEMENTS in self._modules:
            module = self._modules[ModuleType.FIVE_ELEMENTS]
            module.handle_event(event)
    
    def _handle_bagua_change_for_combat(self, event: ModuleEvent) -> None:
        """处理八卦变化对战斗模块的影响"""
        if ModuleType.COMBAT in self._modules:
            module = self._modules[ModuleType.COMBAT]
            module.handle_event(event)
    
    def _handle_character_update_for_combat(self, event: ModuleEvent) -> None:
        """处理角色更新对战斗模块的影响"""
        if ModuleType.COMBAT in self._modules:
            module = self._modules[ModuleType.COMBAT]
            module.handle_event(event)
    
    def _handle_combat_result_for_character(self, event: ModuleEvent) -> None:
        """处理战斗结果对角色的影响"""
        if ModuleType.CHARACTER in self._modules:
            module = self._modules[ModuleType.CHARACTER]
            module.handle_event(event)
    
    def _handle_skill_unlock_for_character(self, event: ModuleEvent) -> None:
        """处理技能解锁对角色的影响"""
        if ModuleType.CHARACTER in self._modules:
            module = self._modules[ModuleType.CHARACTER]
            module.handle_event(event)
    
    def _handle_combat_result_for_loot(self, event: ModuleEvent) -> None:
        """处理战斗结果对掉落系统的影响"""
        if ModuleType.LOOT in self._modules:
            module = self._modules[ModuleType.LOOT]
            module.handle_event(event)
    
    def _handle_ui_update(self, event: ModuleEvent) -> None:
        """处理UI更新"""
        if ModuleType.UI in self._modules:
            module = self._modules[ModuleType.UI]
            module.handle_event(event)
    
    def broadcast_event(self, event: ModuleEvent) -> None:
        """广播事件到所有相关模块"""
        self._event_bus.publish(event)
    
    def sync_all_modules(self, state_manager) -> bool:
        """同步所有模块状态"""
        try:
            # 触发状态管理器同步
            state_manager.sync_modules()
            
            # 更新各模块状态
            for module_type, module in self._modules.items():
                module_state = state_manager.get_module_state(module_type.value)
                module.update_state(module_state)
            
            # 通知同步完成
            for callback in self._sync_callbacks:
                callback()
            
            return True
        except Exception as e:
            print(f"模块同步失败: {e}")
            return False
    
    def add_sync_callback(self, callback: Callable) -> None:
        """添加同步完成回调"""
        self._sync_callbacks.append(callback)
    
    def get_module(self, module_type: ModuleType) -> Optional[IModuleInterface]:
        """获取指定模块"""
        return self._modules.get(module_type)
    
    def get_all_modules_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有模块状态"""
        status = {}
        for module_type, module in self._modules.items():
            try:
                status[module_type.value] = {
                    "state": module.get_state(),
                    "type": module_type.value,
                    "active": True
                }
            except Exception as e:
                status[module_type.value] = {
                    "error": str(e),
                    "active": False
                }
        return status


class DataSyncProtocol:
    """数据同步协议"""
    
    @staticmethod
    def create_character_update_event(source_module: ModuleType, 
                                    character_data: Dict[str, Any]) -> ModuleEvent:
        """创建角色更新事件"""
        return ModuleEvent(
            event_type=EventType.CHARACTER_UPDATED,
            source_module=source_module,
            target_modules=[ModuleType.FIVE_ELEMENTS, ModuleType.COMBAT, ModuleType.UI],
            data={"character": character_data},
            timestamp=time.time(),
            event_id=f"char_update_{int(time.time() * 1000)}"
        )
    
    @staticmethod
    def create_bagua_change_event(source_module: ModuleType,
                                bagua_config: Dict[str, Any]) -> ModuleEvent:
        """创建八卦配置变更事件"""
        return ModuleEvent(
            event_type=EventType.BAGUA_CHANGED,
            source_module=source_module,
            target_modules=[ModuleType.COMBAT, ModuleType.CHARACTER, ModuleType.UI],
            data={"bagua": bagua_config},
            timestamp=time.time(),
            event_id=f"bagua_change_{int(time.time() * 1000)}"
        )
    
    @staticmethod
    def create_combat_result_event(source_module: ModuleType,
                                 combat_result: Dict[str, Any]) -> ModuleEvent:
        """创建战斗结果事件"""
        return ModuleEvent(
            event_type=EventType.COMBAT_RESULT,
            source_module=source_module,
            target_modules=[ModuleType.CHARACTER, ModuleType.LOOT, ModuleType.UI],
            data={"result": combat_result},
            timestamp=time.time(),
            event_id=f"combat_result_{int(time.time() * 1000)}"
        )
    
    @staticmethod
    def create_skill_unlock_event(source_module: ModuleType,
                                skill_data: Dict[str, Any]) -> ModuleEvent:
        """创建技能解锁事件"""
        return ModuleEvent(
            event_type=EventType.SKILL_UNLOCKED,
            source_module=source_module,
            target_modules=[ModuleType.CHARACTER, ModuleType.UI],
            data={"skill": skill_data},
            timestamp=time.time(),
            event_id=f"skill_unlock_{int(time.time() * 1000)}"
        )
    
    @staticmethod
    def create_item_obtained_event(source_module: ModuleType,
                                 item_data: Dict[str, Any]) -> ModuleEvent:
        """创建物品获得事件"""
        return ModuleEvent(
            event_type=EventType.ITEM_OBTAINED,
            source_module=source_module,
            target_modules=[ModuleType.CHARACTER, ModuleType.UI],
            data={"item": item_data},
            timestamp=time.time(),
            event_id=f"item_obtained_{int(time.time() * 1000)}"
        )


# 全局通信中心实例
_global_communication_hub: Optional[ModuleCommunicationHub] = None


def get_communication_hub() -> ModuleCommunicationHub:
    """获取全局通信中心实例"""
    global _global_communication_hub
    if _global_communication_hub is None:
        _global_communication_hub = ModuleCommunicationHub()
    return _global_communication_hub


def initialize_module_communication() -> ModuleCommunicationHub:
    """初始化模块通信系统"""
    global _global_communication_hub
    _global_communication_hub = ModuleCommunicationHub()
    return _global_communication_hub