# 五行同心环棋盘 · Web/JSON/Godot 最小工程

## 目录结构
```
board/
  tools/
    gen_board.py
  web/
    index.html
    board.js
    style.css
    board.json
  godot/
    BoardView.gd
    board.json
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

## Godot 使用
- 打开 Godot 4.x，新建项目并指向 `board/godot/`。
- 新建场景，根节点选择 `Node2D`，挂载 `BoardView.gd`。
- 确保 `board.json` 与脚本在同目录。
- 运行即可看到棋盘结构渲染（含 hover 高亮）。

## 说明
- 生成器严格使用极坐标布局，不含随机扰动。
- Web/Godot 读取同一份 `board.json` 渲染，布局完全一致。
- Web 端支持参数面板实时调参、节点 hover 和搜索高亮、滚轮缩放/拖拽。
