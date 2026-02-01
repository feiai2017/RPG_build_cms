# Realm Rules

- 境界决定跨环连接、并行回路上限、反噬风险。
- 配置入口：`web/board_config.json` → `realm_rules[*].features`。

关键字段
- cross_count: 邻接通道数量
- allow_cross_ring: 是否允许跨环
- max_parallel_loops: 并行回路上限
- backlash_risk: 反噬风险系数

UI
- Combat 面板显示“当前境界效果”。
