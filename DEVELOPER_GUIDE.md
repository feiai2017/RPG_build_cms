# 统一RPG系统开发者指南

## 目录

1. [项目概述](#项目概述)
2. [架构设计](#架构设计)
3. [开发环境设置](#开发环境设置)
4. [核心模块详解](#核心模块详解)
5. [API参考](#API参考)
6. [扩展开发](#扩展开发)
7. [测试指南](#测试指南)
8. [性能优化](#性能优化)
9. [部署指南](#部署指南)
10. [贡献指南](#贡献指南)

## 项目概述

统一RPG系统是一个基于Python和Streamlit的修真游戏数值验证工具，整合了五行八卦理论、战斗模拟、流派管理等功能。

### 技术栈

- **前端框架**：Streamlit
- **后端语言**：Python 3.8+
- **数据存储**：YAML/JSON文件
- **测试框架**：pytest + Hypothesis (Property-Based Testing)
- **依赖管理**：pip/conda

### 项目结构

```
├── unified_main_app.py              # 主应用入口
├── unified_interface_modules.py     # 统一界面模块
├── unified_state_manager.py         # 统一状态管理器
├── wuxing_engine.py                 # 五行八卦计算引擎
├── enhanced_combat_engine.py        # 增强战斗引擎
├── cultivation_school_system.py     # 流派系统
├── loot_generator.py                # 智能掉落系统
├── performance_optimizer.py         # 性能优化器
├── help_system.py                   # 帮助系统
├── config_manager.py                # 配置管理器
├── module_interfaces.py             # 模块接口定义
├── test_*.py                        # 测试文件
├── USER_MANUAL.md                   # 用户手册
├── DEVELOPER_GUIDE.md               # 开发者指南
└── README.md                        # 项目说明
```

## 架构设计

### 整体架构

系统采用分层架构设计：

```
┌─────────────────────────────────────────────────────────────┐
│                    UI Layer (Streamlit)                     │
├─────────────────────────────────────────────────────────────┤
│                  Business Logic Layer                       │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐  │
│  │Five Elements│ Combat      │ Character   │ Loot        │  │
│  │Engine       │ Engine      │ Manager     │ Generator   │  │
│  └─────────────┴─────────────┴─────────────┴─────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    Data Layer                               │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐  │
│  │ State Mgmt  │ Config Mgmt │ Save/Load   │ Export/     │  │
│  │             │             │ System      │ Import      │  │
│  └─────────────┴─────────────┴─────────────┴─────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 设计原则

1. **单一职责**：每个模块负责特定功能
2. **松耦合**：模块间通过接口通信
3. **高内聚**：相关功能集中在同一模块
4. **可扩展**：支持新功能模块的添加
5. **可测试**：所有核心逻辑都有对应测试

### 核心组件

#### 统一状态管理器 (UnifiedStateManager)

负责所有模块的状态管理和数据同步：

```python
class UnifiedStateManager:
    def __init__(self):
        self.character_data: Dict[str, Any] = {}
        self.bagua_configuration: Dict[str, Any] = {}
        self.combat_settings: Dict[str, Any] = {}
        self.loot_inventory: List[Dict[str, Any]] = []
    
    def sync_modules(self) -> None:
        """同步所有模块的数据状态"""
    
    def save_state(self, filepath: str = None) -> bool:
        """保存当前状态到文件"""
    
    def load_state(self, filepath: str) -> bool:
        """从文件加载状态"""
```

#### 五行八卦引擎 (WuxingEngine)

实现五行八卦的核心计算逻辑：

```python
class WuxingEngine:
    def __init__(self):
        self.elements = ["木", "火", "土", "金", "水"]
        self.generation_cycle = {...}
        self.destruction_cycle = {...}
    
    def calculate_element_synergy(self, stones: List[Stone]) -> Dict[str, float]:
        """计算五行灵石的协同效果"""
    
    def validate_bagua_configuration(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证八卦配置的合理性"""
```

## 开发环境设置

### 环境要求

- Python 3.8 或更高版本
- pip 或 conda 包管理器
- Git 版本控制

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd unified-rpg-system
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate     # Windows
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **运行测试**
   ```bash
   pytest
   ```

5. **启动应用**
   ```bash
   streamlit run unified_main_app.py
   ```

### 开发工具推荐

- **IDE**：PyCharm, VSCode
- **调试**：Python Debugger, Streamlit Debug模式
- **代码格式化**：black, autopep8
- **类型检查**：mypy
- **文档生成**：sphinx

## 核心模块详解

### 统一状态管理器

**职责：**
- 管理所有模块的数据状态
- 提供数据同步机制
- 处理数据持久化

**关键方法：**

```python
def update_character_data(self, updates: Dict[str, Any]) -> None:
    """更新角色数据"""
    self.character_data.update(updates)
    self._mark_dirty("character")

def get_module_state(self, module_name: str) -> Dict[str, Any]:
    """获取特定模块的状态"""
    return getattr(self, f"{module_name}_data", {})

def validate_state_consistency(self) -> Tuple[bool, List[str]]:
    """验证状态一致性"""
    issues = []
    # 验证逻辑...
    return len(issues) == 0, issues
```

### 五行八卦引擎

**职责：**
- 实现五行相生相克计算
- 处理八卦方位和卦象效果
- 验证灵石配置合理性

**核心算法：**

```python
def calculate_generation_chain_bonus(self, stones: List[Stone]) -> float:
    """计算相生链加成"""
    chain_length = self._find_longest_generation_chain(stones)
    return 1.0 + (chain_length - 1) * 0.2  # 每个相生关系+20%

def calculate_destruction_penalty(self, stones: List[Stone]) -> float:
    """计算相克惩罚"""
    conflicts = self._find_element_conflicts(stones)
    return max(0.5, 1.0 - len(conflicts) * 0.1)  # 每个相克关系-10%
```

### 战斗引擎

**职责：**
- 执行战斗模拟
- 计算伤害和效果
- 生成战斗报告

**战斗流程：**

```python
def simulate_combat(self, character: Character, enemy: Enemy) -> CombatResult:
    """模拟战斗过程"""
    combat_log = []
    current_time = 0.0
    
    while not self._is_combat_over(character, enemy, current_time):
        # 确定行动顺序
        actors = self._get_action_order(character, enemy)
        
        for actor in actors:
            if self._can_act(actor, current_time):
                action = self._choose_action(actor)
                result = self._execute_action(actor, action)
                combat_log.append(result)
        
        current_time += self.time_step
    
    return self._generate_combat_result(combat_log)
```