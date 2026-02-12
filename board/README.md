# 五行同心环棋盘 · Web/JSON/Godot 最小工程

## 目录结构
```
board/
  tools/
    gen_board.py
  web/
    index.html
    tiandao.js
    adapters/
      godot-export.js
    core/
      board-model.js
      solver.js
    ui/
      board-controller.js
      board-render.js
    board.js
    style.css
    board.json
  godot/
    BoardView.gd
    board.json
  docs/
    bd-flow.md
  README.md
```

## 生成 board.json
在 `board/` 目录下运行：
```
python tools/gen_board.py
```
会生成：
- `web/board.json`
- `godot/board.json`

## 运行 Web 渲染器
方式一：直接双击打开 `web/index.html`

方式二（推荐）：
```
cd web
python -m http.server 8000
```
浏览器访问 `http://localhost:8000`。

## Tiandao 构筑（当前主路径）
- 入口：`web/index.html`（加载 `core/solver.js` + `core/board-model.js` + `ui/*` + `adapters/godot-export.js`）。
- 分层约定：
  - `web/core/board-model.js`：构筑/验证/序列化等纯逻辑。
  - `web/ui/board-render.js`：SVG 渲染与详情视图。
  - `web/ui/board-controller.js`：事件绑定与状态同步。
  - `web/adapters/godot-export.js`：最小导出结构适配层。

## BD 流程与循环
详见 `docs/bd-flow.md`，涵盖入口加载、构筑数据结构、交互与校验链路、模拟循环概览，以及导出/日志路径说明，可用于快速对齐系统流转与调参语境。

## Tiandao 最小导出清单（无版本号）
导出 `tiandao_board.json` 仅包含以下字段：
- `meta.elements`
- `rings[]`
- `nodes[]`
- `edges[]`
- `build.slots[]`

## 交互操作
- 拖拽棋盘：旋转当前选中环（松手带惯性，2~4 秒内停止）。
- 滚轮：微调当前选中环（键盘不需要按 Shift）。
- 快捷键：`Q/E` 或 `A/D` 旋转当前选中环。
- 吸附开关：HUD 里的“吸附”勾选后，旋转停止时会吸附到最近节点角度。
- 断线规则：同环相邻节点可连；跨环仅允许配置的 `bridge_pairs` + `bridge_slots`，且角度差小于阈值（可在 Dev 面板调整）。
- Debug Overlay：Dev 面板打开后可查看每环角度、节点坐标、FPS 与连接数量。

## Godot 使用
- 打开 Godot 4.x，新建项目并指向 `board/godot/`。
- 新建场景，根节点选择 `Node2D`，挂载 `BoardView.gd`。
- 确保 `board.json` 与脚本在同目录。
- 运行即可看到棋盘结构渲染（含 hover 高亮）。

## 说明
- 生成器严格使用极坐标布局，不含随机扰动。
- Web/Godot 读取同一份 `board.json` 渲染，布局完全一致。
- Web 端支持参数面板实时调参、节点 hover 和搜索高亮、滚轮缩放/拖拽。

## 玩法与操作（Web）
- 点击核心开始通电，只能点亮与通电路径相邻的节点。
- 左键点亮/取消，右键撤销。
- R 旋转中环触发生克加成，HUD 显示当前加成状态。
- 滚轮缩放，拖拽平移，右侧面板实时显示属性汇总。
