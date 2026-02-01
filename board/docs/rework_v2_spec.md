# Board Rework v2 Spec

## Goals
- 将节点从数据层强制区分为 skill / mechanic / stat，避免混淆。
- 落地“主回路 + 副回路”结构，形成可解释 BD 构筑。
- UI 能清晰表达节点类型/端口/连接合法性，并提供模板驱动配置。
- 境界与卦象从数值层升级为规则层。
- Boss 从数值检测器升级为“回路破坏者”。
- 角色属性成为回路上限系统（吞吐/并行/反噬阈值）。

## Terminology
- **NodeType**: skill / mechanic / stat
- **Port**: 端口（in/out，指定兼容连接）
- **Circuit/Loop**: 从 SOURCE 出发，经 skill/mechanic 形成闭环或准闭环
- **Main Loop**: 主输出回路
- **Support Loop**: 维持/防御/资源回路
- **Realm**: 境界（功能开关 + 规则约束）
- **Trigram**: 卦象区域规则（连接/失效/反噬）
- **BossMechanic**: 对回路产生规则级干扰的机制

## Data Structures (target)
### Node
```
{
  id: string,
  name: string,
  type: 'skill' | 'mechanic' | 'stat' | 'unknown',
  element: '金'|'木'|'水'|'火'|'土',
  tags: string[],
  ports: { in: Port[], out: Port[] },
  params: Record<string, any>,
  ui: { icon?: string, shape?: string, color?: string, ring?: string, tooltip?: string }
}
```

### Template
```
{
  template_id: string,
  type: NodeType,
  default_params: Record<string, any>,
  param_schema: { field: string, type: 'number'|'enum'|'string', range?: [min,max], options?: string[] }[],
  ports: { in: Port[], out: Port[] },
  tooltip: string
}
```

### Circuit
```
{
  id: string,
  kind: 'main'|'support',
  nodes: string[],
  stable: boolean,
  reason?: string
}
```

## Acceptance Criteria (global)
- 任何节点都能归类为 skill/mechanic/stat（或标红 unknown）。
- UI 能提示“只有技能堆叠，没有回路”。
- 预设导入后能解释主/副回路，并高亮关键节点。
- 境界切换明显改变连接规则/可并行回路数。
- 卦象区域改变连接/失效规则而非纯数值。
- Boss 机制能导致回路断裂或稳定性变化，并给出原因。
- 角色属性能限制回路复杂度（带宽/并行/反噬阈值）。

## Execution Order (recommended)
1) 数据模型与迁移
2) 连接合法性 + 回路检测
3) UI 清晰化 + 模板表单
4) 预设 BD 库
5) 境界规则层
6) 卦象规则层
7) Boss 机制改造
8) 角色属性接入
9) 测试与文档

## Task 1 Status
- Node schema fields added in generator (node_type/template_id/ports/params/ui).
- Template catalog: `web/node_templates.json`.
- Migration script: `tools/migrate_board_v2.py`.
- UI detail shows node_type/template and flags unknown.

## Task 2 Status
- Port compatibility check in `buildAutoEdges` with illegal reason surfaced in edge tooltip.
- Loop detection with main/support classification and HUD hint.

## Task 3 Status
- 节点类型徽标与端口点显示。
- 模板驱动表单（detail panel + dev 模板库）。
- 连接模式增加“邻接”，默认仅显示邻近连线。
- 端口方向性接入，连线显示方向箭头。
- 模板端口方向约束生效（skill需输入、stat需输出）。

## Task 4 Status
- 预设格式升级：concept/main_loop/support_loop/counters/realm_requirement/trigram_synergy。
- 预设卡片展示与主/副回路高亮。

## Task 5 Status
- 境界规则迁移到 `realm_rules.features`，Combat 面板展示当前境界效果。
- 回路并行上限进入 BD 提示。

## Task 6 Status
- 卦象规则映射到连接合法性与乱流修正。
- 节点详情/悬浮信息包含卦象规则说明。

## Task 7 Status
- Boss 增加机制定义（port_lock/loop_disrupt/overload等）。
- 战斗日志输出机制事件与失败原因。

## Task 8 Status
- 角色基础/派生属性引入并进入回路上限与面板展示。

## Task 9 Status
- 文档：node_types/realm/trigram/bosses。\n- 最小测试脚本：`tools/test_v2.py`。
