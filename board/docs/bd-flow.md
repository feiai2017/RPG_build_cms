# BD（构筑）流程与循环（Web 主路径）

本文档描述 `board/web/index.html` 作为入口时的 BD（构筑）流程、数据结构与模拟循环概览，面向开发与策划对齐认知。

## 术语与对象
- BD：构筑（Build），即一套技能/符文/联结的配置组合。
- boardState：棋盘运行时状态对象，结构为 `{ build, slots, layout }`。
- build：构筑配置对象。
  - `name`：构筑名称。
  - `skills_by_gua`：卦位 -> 技能 ID。
  - `private_runes`：卦位 -> `{ form, loop }`。
  - `edge_runes`：联结边（`A|B`） -> 联结符文 ID。
- slots：渲染与交互用槽位数组，包含 `id/kind/gua/x/y/item_id` 等。
- layout：布局参数与环半径（`size/center/skillR/runeR/edgeR/outerLabelR`）。

## 入口与模块分层
入口页面为 `board/web/index.html`，依次加载：
1. `core/solver.js`：定义 `window.BaguaSolver`（技能库、符文库、模拟器）。
2. `core/board-model.js`：定义 `window.TiandaoModel`（构筑/校验/序列化）。
3. `adapters/godot-export.js`：定义 `window.TiandaoGodotExport`（最小导出结构）。
4. `ui/board-render.js`：SVG 渲染与详情描述。
5. `ui/board-controller.js`：事件绑定、状态同步、模拟与导出。

说明：本文仅覆盖上述模块化主路径，不涉及 `web/tiandao.js` 与 `web/board.js` 的旧/旁系实现。

## 主流程（整体链路）
1. 初始化
   - `board-controller.init()` 调用 `Model.buildDefaultConfig()` + `Model.buildBoardState()` 生成 `boardState`。
   - `Model.validateBuild()` 生成构筑问题清单并更新 UI。
   - `Render.renderBoard()` 首次渲染棋盘。
   - `GodotExport.persistPayload()` 写入 `localStorage.tiandao_board`。
2. 渲染
   - `Render.renderBoard()` 输出 SVG，`Render.updateDetail()` 刷新右侧详情。
3. 交互改动
   - 选择槽位、替换物品、清空槽位。
   - 通过 `Model.applyItem()` / `Model.clearSlot()` 修改 `boardState.build` 与 `slot.item_id`。
4. 校验
   - `Model.validateBuild()` 基于联结数量与技能要求输出问题列表。
5. 重渲染与持久化
   - `refreshBoard()` 重新渲染并持久化 `tiandao_board`。
6. 导出
   - `exportBoard()` 调用 `GodotExport.buildMinimalPayload()` 生成 `tiandao_board.json`。
7. 模拟与日志
   - `runSimulation()` 调用 `Model.simulateBuild()` + `Model.simulateBoss()` 生成结果与战斗日志。
   - 结果写入 `localStorage.battle_log`，由 `battle_log.html` 读取与展示。

## 模拟循环概览（高层）
模拟器位于 `core/solver.js` 的 `simulateBuild()`：
1. Tick 更新冷却（默认 `tickSeconds = 0.5`，`maxTicks = 20`）。
2. 处理延迟队列（复施/接力等延迟触发）。
3. 选择可施放技能（按卦序扫描）。
4. 施放与入队（命中、复施、接力联结）。
5. 触发联结与反应（CD_ROUTER、REACT_DETONATOR、SUSTAIN_LINK 等）。
6. 汇总统计（伤害、续航、反应次数、空窗等）。

## 导出与日志
- `TiandaoGodotExport.persistPayload()` 将最小导出结构写入 `localStorage.tiandao_board`。
- `exportBoard()` 下载 `tiandao_board.json`（与 Godot 渲染结构一致）。
- `runSimulation()` 写入 `localStorage.battle_log`，`battle_log.html` 展示统计与事件列表。
