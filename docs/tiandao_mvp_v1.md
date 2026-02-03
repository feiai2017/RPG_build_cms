# 天道盘 MVP V1（自动循环 build）

## 目标
- 8 卦位：乾 兑 离 震 巽 坎 艮 坤
- 每卦 1 技能槽（共 8 技能：5 输出 + 3 辅助）
- 每技能 2 私有符文槽：Form / Loop
- 相邻卦之间 1 联结槽（Edge Rune，共用）
- V1 不做：五维气向量、相生相克比例、残渣/乱流断线、带宽阻断、虚线多含义
- 线/连接只表达联结槽是否启用
- 保留 tick 日志，新增字段仅放 payload/extra

## 卦位映射
顺时针顺序：
乾 兑 离 震 巽 坎 艮 坤

卦位 → (元素, 动词)：
- 乾 = 金 / 贯
- 兑 = 金 / 回
- 离 = 火 / 燃
- 震 = 木 / 连
- 巽 = 木 / 散
- 坎 = 水 / 控
- 艮 = 土 / 镇
- 坤 = 土 / 护

## 槽位结构
- 每卦 1 技能槽（中心）
- 每技能 2 私有符文槽（Form / Loop，私有不共享）
- 每相邻卦 1 联结槽（Edge Rune，共用）

硬约束：
- 全盘最多启用 3 条联结槽（edge_enabled_cap = 3）
- 单技能最多参与 2 条联结（per_skill_edge_cap = 2）

## 私有符文
Form Runes：spread / aoe / chain / channel / melee / mark

Loop Runes：cd_down / charge / auto_recast / cond_accel / hit_energy / crit_energy

目标：更换符文显著改变施放次数/形态/节奏。

## 联结符文（Edge Rune）
1) RELAY
- A 施放后延迟 N tick，自动施放 B 的弱化版（立即队列，优先于常规扫描）

2) CD_ROUTER
- A 命中时，为 B 减少“当前剩余冷却”的 10%

3) REACT_DETONATOR
- A 挂印记后，B 下次命中该目标强制触发一次反应

4) SUSTAIN_LINK
- A 造成伤害的 5% 转为 B 的护盾/治疗/资源（量化用于指标）

## 元素印记与反应（6 个）
印记规则：
- 输出技能命中目标挂印记，持续固定时长
- 不同元素命中触发反应，消耗旧印记
- 辅助技能默认不挂印记

反应表：
- FIRE + WATER = STEAM
- WATER + METAL = FROST
- WOOD + FIRE = BURN_SPREAD
- WOOD + EARTH = ROOT
- METAL + EARTH = SHATTER
- FIRE + EARTH = LAVA_FIELD

## 自动循环（Auto Loop）
- 卦位顺时针扫描，ready 即施放
- 每 tick 最多施放 1 个
- 立即队列优先（来自联结触发）

## Tick 日志（增量扩展）
新增事件放 payload/extra：
- SKILL_CAST
- HIT
- MARK_APPLIED
- REACTION_TRIGGERED
- EDGE_RUNE_TRIGGERED
- COOLDOWN_CHANGED
- SUSTAIN_GAINED

## 10 秒木桩与指标
- casts_per_skill
- reaction_counts
- downtime_ticks
- sustain_total

## 预置 build（configs/tiandao/）
- preset_1_reaction_loop：离(火) + 坎(水) + REACT_DETONATOR
- preset_2_relay_chain：连续三卦 RELAY 链
- preset_3_sustain_steady：SUSTAIN_LINK + CD_ROUTER
