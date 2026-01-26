# RPG_build_cms（统一RPG系统）

一个基于 Python + Streamlit 的修真游戏数值验证工具，整合了五行八卦、战斗模拟、流派管理、智能刷宝与 BD 分析等模块，提供统一状态管理与配置持久化。

## 快速开始

### 环境要求

- Python 3.8+
- pip 或 conda

### 安装依赖

1) 创建并激活虚拟环境（推荐）
```bash
python -m venv .venv
source .venv/bin/activate
```

2) 安装依赖
```bash
pip install -r requirements.txt
```

项目未提供 `requirements.txt` 时，请先安装基础依赖并按运行报错补充：

```bash
pip install streamlit pyyaml pandas
```

若后续新增 `requirements.txt`，建议优先使用：

```bash
pip install -r requirements.txt
```

### 启动方式（推荐顺序）

1) 统一主应用（推荐）
```bash
python -m streamlit run unified_main_app.py
```

2) 通过原应用启用统一界面
```bash
streamlit run app.py
# 侧边栏勾选“🔄 启用统一界面”
```

3) 运行封装入口
```bash
python run.py
```

## 功能模块使用说明

### 🏠 系统概览
- 展示角色信息、系统状态和一致性检查结果。
- 支持快速操作（同步模块、保存状态、生成报告）。

### ☯️ 五行八卦盘
- 采用后天八卦方位布局，支持五行相生相克计算。
- 槽位规则：第 1 槽为逻辑灵石，第 2-4 槽为内/中/外环五行灵石；中央为核心 BIOS。
- 操作流程：选择灵石 → 点击槽位放置 → 观察衍算结果 → 调整配置。

### ⚔️ 战斗模拟
- 集成五行八卦效果的战斗计算。
- 输出 DPS、生存评分、效率评级与详细战斗记录。
- 建议在完成八卦配置与角色流派后进行模拟。

### 🎓 流派管理
- 五大流派：剑修、法修、体修、丹修、阵修。
- 支持流派技能解锁、进阶与协同效果计算。

### 💎 刷宝系统
- 基于流派特性进行智能掉落权重调整。
- 提供挑战内容、装备对比与 BD 优化建议。

### 📊 BD 分析
- 校验配置完整性、属性分布平衡与协同效果。
- 输出优化建议，并支持配置快照对比。

### ⚙️ 系统设置
- 角色信息设置与调整。
- 配置导入/导出、备份/恢复。

### 📄 传统界面
- 保留原有功能的兼容模式，便于回溯旧流程。

## 典型使用流程

1. 在“系统设置”中创建角色并设定境界、主灵根。
2. 在“流派管理”选择流派，解锁基础技能。
3. 在“五行八卦盘”完成灵石与核心 BIOS 配置。
4. 进入“战斗模拟”验证 DPS 与生存表现。
5. 使用“刷宝系统”获取装备并比较优劣。
6. 在“BD 分析”中优化配置并保存快照。

## 文档导航

- `USER_MANUAL.md`：用户手册与上手流程
- `UNIFIED_INTERFACE_README.md`：统一界面与模块说明
- `DEVELOPER_GUIDE.md`：开发者指南与架构
- `BAGUA_QUICK_START.md` / `BAGUA_CALCULATION_GUIDE.md`：八卦入门与计算
- `WUXING_SYSTEM_SUMMARY.md` / `WUXING_SYSTEM_MECHANICS.md`：五行机制说明
- `SYSTEM_DOCUMENTATION.md`：完整系统文档

## 测试（可选）

```bash
pytest
```

也可运行单项集成测试：

```bash
python test_unified_interface.py
```
