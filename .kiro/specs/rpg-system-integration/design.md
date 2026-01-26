# Design Document: RPG System Integration

## Overview

本设计文档描述了如何将现有的分散RPG数值验证系统整合为一个统一的、具有真正五行八卦感觉的单机BD刷宝游戏系统。系统将基于现有的app.py和app_five_elements.py代码，进行深度整合和优化，创造一个可实际运行和验证玩法的成熟工具。

核心设计理念：
- **真实性**: 基于真正的道教五行八卦理论，不是简单的游戏化包装
- **实用性**: 从概念验证转向实际可用的游戏工具
- **整合性**: 统一的系统架构，避免功能分散
- **可扩展性**: 支持后续移植到游戏引擎的架构设计

## Architecture

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Unified RPG System                       │
├─────────────────────────────────────────────────────────────┤
│  UI Layer (Streamlit)                                      │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐  │
│  │ Bagua Panel │ Combat Sim  │ Character   │ Loot System │  │
│  │             │             │ Builder     │             │  │
│  └─────────────┴─────────────┴─────────────┴─────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  Business Logic Layer                                       │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐  │
│  │Five Elements│ Combat      │ Character   │ Loot        │  │
│  │Engine       │ Engine      │ Manager     │ Generator   │  │
│  └─────────────┴─────────────┴─────────────┴─────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  Data Layer                                                 │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐  │
│  │ YAML Config │ Save/Load   │ State Mgmt  │ Export/     │  │
│  │ Manager     │ System      │             │ Import      │  │
│  └─────────────┴─────────────┴─────────────┴─────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 核心模块设计

#### 1. Five Elements Engine (五行引擎)
负责所有五行八卦相关的计算和逻辑：
- 五行相生相克计算
- 八卦方位和卦象效果
- 灵石配置验证
- 属性加成计算

#### 2. Combat Engine (战斗引擎)
基于现有engine.py扩展：
- 实时战斗模拟
- DPS计算和分析
- 技能链执行
- 战斗数据记录

#### 3. Character Manager (角色管理器)
统一的角色数据管理：
- 流派系统
- 属性计算
- BD配置管理
- 进度追踪

#### 4. Loot Generator (掉落生成器)
智能的装备和灵石生成：
- 基于流派的掉落权重
- 随机属性生成
- 稀有度控制
- 平衡性保证

## Components and Interfaces

### 1. 统一状态管理器 (UnifiedStateManager)

```python
class UnifiedStateManager:
    def __init__(self):
        self.character_data: Dict[str, Any] = {}
        self.bagua_configuration: Dict[str, Any] = {}
        self.combat_settings: Dict[str, Any] = {}
        self.loot_inventory: List[Dict[str, Any]] = []
        
    def sync_modules(self) -> None:
        """同步所有模块的数据状态"""
        
    def save_state(self, filepath: str) -> bool:
        """保存当前状态到文件"""
        
    def load_state(self, filepath: str) -> bool:
        """从文件加载状态"""
```

### 2. 五行八卦计算引擎 (WuxingEngine)

```python
class WuxingEngine:
    def __init__(self):
        self.elements = ["木", "火", "土", "金", "水"]
        self.generation_cycle = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
        self.destruction_cycle = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
        
    def calculate_element_synergy(self, stones: List[Stone]) -> Dict[str, float]:
        """计算五行灵石的协同效果"""
        
    def validate_bagua_configuration(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证八卦配置的合理性"""
        
    def get_trigram_effects(self, trigram: str, stones: List[Stone]) -> Dict[str, float]:
        """获取特定卦位的效果加成"""
```

### 3. 流派系统 (CultivationSchoolSystem)

```python
class CultivationSchool:
    def __init__(self, school_id: str, name: str, element_affinity: str):
        self.school_id = school_id
        self.name = name
        self.element_affinity = element_affinity
        self.skill_tree: Dict[str, Any] = {}
        self.equipment_preferences: List[str] = []
        
    def get_attribute_bonuses(self, level: int) -> Dict[str, float]:
        """获取流派属性加成"""
        
    def unlock_skills(self, character_level: int) -> List[str]:
        """解锁可用技能"""

class SchoolManager:
    def __init__(self):
        self.schools = {
            "sword_cultivator": CultivationSchool("sword", "剑修", "金"),
            "spell_cultivator": CultivationSchool("spell", "法修", "火"),
            "body_cultivator": CultivationSchool("body", "体修", "土"),
            "pill_cultivator": CultivationSchool("pill", "丹修", "木"),
            "formation_cultivator": CultivationSchool("formation", "阵修", "水")
        }
```

### 4. 智能掉落系统 (IntelligentLootSystem)

```python
class LootGenerator:
    def __init__(self, wuxing_engine: WuxingEngine):
        self.wuxing_engine = wuxing_engine
        self.rarity_weights = {"common": 0.6, "rare": 0.25, "epic": 0.12, "legendary": 0.03}
        
    def generate_stone(self, player_school: str, enemy_type: str) -> Stone:
        """根据玩家流派和敌人类型生成灵石"""
        
    def generate_equipment(self, player_level: int, school: str) -> Dict[str, Any]:
        """生成适合的装备"""
        
    def calculate_drop_probability(self, school_affinity: str, stone_element: str) -> float:
        """计算掉落概率"""
```

## Data Models

### 1. 统一角色数据模型

```python
@dataclass
class UnifiedCharacter:
    # 基础信息
    name: str
    level: int
    school: str
    realm: str
    
    # 属性
    base_attributes: Dict[str, float]
    derived_attributes: Dict[str, float]
    
    # 五行八卦配置
    bagua_stones: Dict[str, Dict[int, Optional[str]]]  # 八卦位置 -> 槽位 -> 灵石ID
    core_bios: Dict[int, Optional[str]]  # 核心槽位
    
    # 装备和物品
    equipment: Dict[str, Optional[str]]
    inventory: List[str]
    
    # 进度数据
    unlocked_skills: List[str]
    completed_challenges: List[str]
    cultivation_progress: Dict[str, float]
```

### 2. 增强的灵石数据模型

```python
@dataclass
class EnhancedStone(Stone):
    # 继承原有Stone属性
    
    # 新增属性
    school_affinity: List[str]  # 适合的流派
    synergy_bonus: Dict[str, float]  # 协同加成
    unlock_requirements: Dict[str, Any]  # 解锁条件
    lore_description: str  # 背景描述
    
    def calculate_effectiveness(self, character: UnifiedCharacter) -> float:
        """计算对特定角色的有效性"""
        
    def get_visual_effects(self) -> Dict[str, str]:
        """获取视觉效果配置"""
```

### 3. 战斗记录数据模型

```python
@dataclass
class CombatRecord:
    timestamp: datetime
    character_snapshot: UnifiedCharacter
    enemy_type: str
    duration: float
    result: str  # "win", "lose", "timeout"
    
    # 详细数据
    damage_dealt: float
    damage_taken: float
    skills_used: List[Dict[str, Any]]
    critical_moments: List[Dict[str, Any]]
    
    # 分析结果
    dps_analysis: Dict[str, float]
    survivability_score: float
    efficiency_rating: float
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

基于prework分析，以下是系统的核心正确性属性：

### Property 1: 五行相生相克计算正确性
*For any* 五行灵石配置，当形成相生关系时，系统计算的属性加成应该为正值；当形成相克关系时，应该应用负面效果或警告
**Validates: Requirements 1.2, 1.3, 1.4**

### Property 2: 八卦方位布局一致性
*For any* 八卦盘界面渲染，所有卦位应该严格按照后天八卦方位排列（乾西北、兑西、离南、震东、巽东南、坎北、艮东北、坤西南）
**Validates: Requirements 1.1**

### Property 3: 模块数据同步一致性
*For any* 用户在任意模块中的配置修改，所有相关模块的数据状态应该保持一致，不存在数据不同步的情况
**Validates: Requirements 3.2, 3.3, 3.4**

### Property 4: BD配置实时计算准确性
*For any* BD配置变更，系统应该立即重新计算所有相关属性，并在所有显示界面中反映最新的计算结果
**Validates: Requirements 2.2, 3.4**

### Property 5: 战斗模拟数据完整性
*For any* 战斗模拟执行，系统应该记录完整的战斗过程数据，包括伤害、技能使用、状态变化等所有关键信息
**Validates: Requirements 2.3, 2.4, 6.2, 6.3**

### Property 6: 流派系统解锁逻辑正确性
*For any* 角色流派选择，系统应该解锁对应的技能、装备类型和属性加成，不同流派之间不应该有错误的交叉解锁
**Validates: Requirements 4.1, 5.2, 5.3**

### Property 7: 掉落系统流派关联性
*For any* 刷宝活动，掉落的装备和灵石应该与玩家当前流派有合理的关联性，符合流派特色和需求
**Validates: Requirements 4.2, 4.5**

### Property 8: 数据持久化完整性
*For any* 用户配置保存操作，保存的数据应该能够完整恢复，包括角色属性、八卦配置、装备等所有状态信息
**Validates: Requirements 2.5, 7.1, 7.2, 7.3, 7.4**

### Property 9: 配置验证和冲突处理
*For any* 外部配置导入或内部配置冲突，系统应该能够正确识别问题并提供合理的解决方案
**Validates: Requirements 7.4, 7.5**

### Property 10: 系统状态统一性
*For any* 系统运行状态，所有模块应该使用统一的数据存储和配置管理，不存在数据孤岛或不一致的状态
**Validates: Requirements 3.5**

## Error Handling

### 1. 五行配置错误处理
- **无效灵石组合**: 当用户尝试放置不兼容的灵石时，显示详细的冲突说明和建议
- **八卦方位错误**: 自动纠正错误的卦位配置，并提供教育性提示
- **属性计算溢出**: 处理极端配置导致的数值溢出，设置合理的上下限

### 2. 战斗模拟错误处理
- **配置不完整**: 在战斗开始前验证角色配置的完整性
- **计算异常**: 捕获战斗计算中的异常，提供降级处理
- **性能问题**: 监控战斗模拟的性能，超时时提供简化计算

### 3. 数据持久化错误处理
- **文件损坏**: 检测配置文件的完整性，提供修复或重置选项
- **版本兼容**: 处理不同版本配置文件的兼容性问题
- **权限问题**: 优雅处理文件读写权限不足的情况

### 4. 用户界面错误处理
- **状态不一致**: 定期检查UI状态与数据状态的一致性
- **操作冲突**: 防止用户同时进行冲突的操作
- **资源加载失败**: 提供备用的UI元素和提示信息

## Testing Strategy

### 单元测试策略
- **五行计算模块**: 测试各种五行组合的计算结果
- **八卦布局模块**: 验证卦位排列和效果计算
- **流派系统**: 测试流派解锁和属性加成逻辑
- **数据持久化**: 测试保存/加载功能的正确性

### 属性测试策略
使用property-based testing验证系统的通用属性：
- **配置最少100次迭代**以确保充分的随机测试覆盖
- **每个属性测试必须引用对应的设计文档属性**
- **标签格式**: **Feature: rpg-system-integration, Property {number}: {property_text}**

### 集成测试策略
- **模块间通信**: 测试不同模块之间的数据传递
- **端到端流程**: 测试完整的用户操作流程
- **性能测试**: 验证系统在各种负载下的表现
- **兼容性测试**: 确保与现有数据格式的兼容性

### 用户验收测试
- **真实场景模拟**: 使用实际的游戏场景进行测试
- **用户体验评估**: 收集用户对界面和功能的反馈
- **平衡性验证**: 确保游戏机制的平衡性和趣味性