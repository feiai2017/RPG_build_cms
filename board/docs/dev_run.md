# Dev Run

## Demo paths
- `web/index.html` (棋盘)
- `web/combat.html` (战斗与面板)

## Local run (static server)
```sh
cd /Users/wangpengfei/go/src/github.com/RPG_build_cms/RPG_build_cms/board/web
python3 -m http.server 8000
```

Open in browser:
- http://localhost:8000/index.html
- http://localhost:8000/combat.html

## Notes
- Both pages are static and use local JSON/JS assets.
- If loading snapshot data, open `index.html` first and click `Open Combat Panel`.
