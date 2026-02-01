# Boss Mechanics

机制数据：`web/core/boss_profiles.js`

通用机制
- port_lock: 封锁端口类型
- loop_disrupt: 回路受扰，削弱主/副回路
- overload: 提高伤害压力
- backlash: 反噬爆发
- mirror: 反制输出
- slow_drain: 压制续航

Combat 输出
- 事件日志会输出机制触发时间与影响。
- 失败原因基于输出/生存与回路状态给出提示。
