import math
import copy
import random
import json
import hashlib
from typing import Dict, Any, List, Tuple, Optional


def _stable_hash(obj: Any) -> str:
    """Stable hash for determinism checks (JSON with sorted keys)."""
    s = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]

class SkillNode:
    """技能链节点：用于递归计算 / MVP 战斗验证"""
    def __init__(self, skill_data: Dict[str, Any], modifiers: Optional[List[Dict[str, Any]]] = None, triggers: Optional[List[Dict[str, Any]]] = None):
        self.skill = skill_data
        self.modifiers = modifiers or []
        # triggers: List[{"condition": str, "node": SkillNode}]
        self.triggers = triggers or []

class DiabloEngine:
    def __init__(self, data_source: Dict[str, Any]):
        self.data = data_source
        self.stats: Dict[str, float] = {}
        self.simulation_state = {"hp_percent": 1.0}


    def version(self) -> str:
        return "0.2-seed-deterministic"

    def set_simulation_state(self, hp_percent: float = 1.0):
        self.simulation_state["hp_percent"] = float(hp_percent)

    def _get_rule(self, key: str, default: float = 0.0) -> float:
        try:
            return float((self.data.get("rules") or {}).get(key, default))
        except Exception:
            return float(default)

    def build_hero(self, model_data: Dict[str, Any], talent_data: Optional[Dict[str, Any]]):
        """初始化角色面板 + 最小派生（MVP 需要 max_hp / crit_rate 等）"""
        self.stats = copy.deepcopy(model_data.get('base_stats', {})) or {}
        self.stats.update(copy.deepcopy(model_data.get('attributes', {})) or {})

        # 处理天赋（直接加）
        if talent_data and 'dynamic_stats' in talent_data:
            for k, v in (talent_data.get('dynamic_stats') or {}).items():
                try:
                    self.stats[k] = self.stats.get(k, 0) + float(v)
                except Exception:
                    pass

        # === 最小派生（让 MVP “会输会赢”）===
        base_hp = self._get_rule("base_hp", 500.0)
        str_to_hp = self._get_rule("str_to_hp", 20.0)
        agi_to_crit = self._get_rule("agi_to_crit_rate", 0.002)
        int_to_ele = self._get_rule("int_to_inc_elemental", 0.02)

        str_v = float(self.stats.get("str", 0))
        agi_v = float(self.stats.get("agi", 0))
        int_v = float(self.stats.get("int", 0))

        # max_hp 由 base_hp + str 派生 + max_hp_bonus
        max_hp_bonus = float(self.stats.get("max_hp_bonus", 0))
        self.stats["max_hp"] = float(self.stats.get("max_hp", base_hp + str_v * str_to_hp + max_hp_bonus))

        # 基础暴击率 5% + 敏捷派生 + 额外加成
        self.stats["crit_rate"] = float(self.stats.get("crit_rate", 0.05 + agi_v * agi_to_crit))

        # 元素增伤（如果你后面要用）
        self.stats["inc_elemental"] = float(self.stats.get("inc_elemental", 0.0 + int_v * int_to_ele))

        # 攻速兜底
        self.stats["atk_spd"] = float(self.stats.get("atk_spd", 1.0))

        # 受伤倍率兜底（1.0 = 不减伤）
        self.stats["damage_taken_mult"] = float(self.stats.get("damage_taken_mult", 1.0))

    def _apply_modifier_stats(self, base_stats: Dict[str, float], mods: List[Dict[str, Any]]) -> Dict[str, float]:
        """将一组模组的属性叠加到面板（对 *_mult 做乘法，对其它做加法）"""
        temp = copy.deepcopy(base_stats)
        for mod in mods or []:
            for k, v in (mod.get('stats') or {}).items():
                try:
                    fv = float(v)
                except Exception:
                    continue
                if str(k).endswith("_mult"):
                    temp[k] = float(temp.get(k, 1.0)) * fv
                else:
                    temp[k] = float(temp.get(k, 0.0)) + fv
        return temp

    def _core_math(self, skill: Dict[str, Any], current_stats: Dict[str, float]) -> Dict[str, Any]:
        """计算单次平均伤害与 DPS（不含触发）"""
        comps = skill.get('damage_components') or []
        if not comps:
            return {"dps": 0.0, "avg_hit": 0.0, "aps": float(current_stats.get("atk_spd", 1.0)), "crit_rate": 0.0, "dmg_type": "none"}

        comp = comps[0]
        min_dmg = float(comp.get('min', 0))
        max_dmg = float(comp.get('max', 0))
        dtype = comp.get('type', 'physical')

        scale_src = comp.get('scaling_source', 'base_atk')
        scale_coef = float(comp.get('scaling_coef', 1.0))
        source_val = float(current_stats.get(scale_src, 0))
        flat_bonus = float(current_stats.get(f"flat_{dtype}", 0))

        base_avg = (min_dmg + max_dmg) / 2.0 + source_val * scale_coef + flat_bonus

        inc = 1.0 + float(current_stats.get('inc_all', 0)) + float(current_stats.get(f"inc_{dtype}", 0))
        # 兼容元素总增伤
        if dtype in ("fire", "cold", "lightning"):
            inc *= (1.0 + float(current_stats.get("inc_elemental", 0)))

        more = 1.0 * (1.0 + float(current_stats.get('more_damage', 0)))

        hit_dmg = base_avg * inc * more

        crit_rate = min(1.0, max(0.0, float(current_stats.get('crit_rate', 0.05))))
        crit_dmg = float(current_stats.get('crit_dmg', 1.5))
        avg_hit = hit_dmg * (1.0 - crit_rate) + (hit_dmg * crit_dmg * crit_rate)

        aps = float(current_stats.get('atk_spd', 1.0))
        return {"dps": avg_hit * aps, "avg_hit": avg_hit, "aps": aps, "crit_rate": crit_rate, "dmg_type": dtype}

    def calculate_skill_damage(self, skill_data: Dict[str, Any], modifiers_list: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        mods = modifiers_list or []
        final_stats = self._apply_modifier_stats(self.stats, mods)
        res = self._core_math(skill_data, final_stats)
        return {"DPS": res['dps'], "Avg_Hit": res['avg_hit'], "Crit_Info": {"rate": res['crit_rate'], "aps": res['aps']}, "Trigger_Info": []}

    # ====== 递归链：带 profile（治疗/减伤/触发次数）======
    def simulate_chain_with_profile(self, root_node: SkillNode, max_depth: int = 1) -> Tuple[float, List[Dict[str, Any]], Dict[str, float]]:
        logs: List[Dict[str, Any]] = []
        profile = {
            "heal_per_sec": 0.0,           # 期望每秒治疗（按最大血）
            "damage_taken_mult": 1.0,      # 期望受伤倍率（乘法叠）
            "uptime_guard": 0.0,           # 减伤 uptime（0~1）
        }

        def clamp01(x: float) -> float:
            return 0.0 if x < 0 else (1.0 if x > 1 else x)

        def merge_profile(p: Dict[str, float], child_p: Dict[str, float]):
            # 治疗可加
            p["heal_per_sec"] += child_p.get("heal_per_sec", 0.0)
            # 受伤倍率乘法叠（越小越硬）
            p["damage_taken_mult"] *= child_p.get("damage_taken_mult", 1.0)
            # uptime 取 max（用于展示）
            p["uptime_guard"] = max(p.get("uptime_guard", 0.0), child_p.get("uptime_guard", 0.0))

        def expected_proc_rate(freq: float, icd: float) -> float:
            if icd <= 0:
                return max(0.0, freq)
            return min(max(0.0, freq), 1.0 / icd)

        def walk(node: SkillNode, depth: int) -> Tuple[float, List[Dict[str, Any]], Dict[str, float]]:
            node_logs: List[Dict[str, Any]] = []
            node_profile = {"heal_per_sec": 0.0, "damage_taken_mult": 1.0, "uptime_guard": 0.0}

            node_stats = self._apply_modifier_stats(self.stats, node.modifiers)
            base_res = self._core_math(node.skill, node_stats)
            node_dps = float(base_res['dps'])

            node_logs.append({
                "skill": node.skill.get('name', node.skill.get('id')),
                "role": "Main" if depth == 0 else "Sub",
                "dps": int(node_dps),
                "aps": f"{base_res['aps']:.2f}",
                "info": "base"
            })

            # 技能 effects（期望模型）
            effects = node.skill.get("effects") or {}
            if effects:
                max_hp = float(self.stats.get("max_hp", 500.0))
                freq = float(base_res["aps"])  # 主技能每秒调用次数（近似）
                icd = float(effects.get("icd", 0.0) or 0.0)
                proc = expected_proc_rate(freq, icd)

                heal_pct = float(effects.get("heal_percent_max_hp", 0.0) or 0.0)
                if heal_pct > 0:
                    node_profile["heal_per_sec"] += proc * heal_pct * max_hp

                dmg_mult = effects.get("damage_taken_mult", None)
                duration = float(effects.get("duration", 0.0) or 0.0)
                if dmg_mult is not None and duration > 0:
                    dm = float(dmg_mult)
                    uptime = clamp01(proc * duration)
                    # 期望受伤倍率 = uptime*dm + (1-uptime)*1
                    expected_mult = uptime * dm + (1.0 - uptime) * 1.0
                    node_profile["damage_taken_mult"] *= expected_mult
                    node_profile["uptime_guard"] = max(node_profile["uptime_guard"], uptime)

            if depth >= max_depth:
                return node_dps, node_logs, node_profile

            # 触发
            for trig in (node.triggers or []):
                child = trig["node"]
                cond = trig.get("condition", "on_hit")

                trigger_freq = 0.0
                if cond == "on_crit":
                    trigger_freq = float(base_res["aps"]) * float(base_res["crit_rate"])
                elif cond == "on_hit":
                    trigger_freq = float(base_res["aps"])
                elif cond == "fixed_chance_20":
                    trigger_freq = float(base_res["aps"]) * 0.2
                elif cond == "hp_lt_30":
                    if float(self.simulation_state.get("hp_percent", 1.0)) < 0.3:
                        trigger_freq = float(base_res["aps"])
                    else:
                        trigger_freq = 0.0

                if trigger_freq <= 0:
                    continue

                child_dps, child_logs, child_profile = walk(child, depth + 1)

                # 子技能的 dps 是按它自己的 aps 计算的；触发要把频率替换成 trigger_freq
                child_native_aps = float(child_logs[0].get("aps", 1.0) or 1.0)
                if child_native_aps <= 0:
                    child_native_aps = 1.0
                real_child_dps = (child_dps / child_native_aps) * trigger_freq

                node_dps += real_child_dps

                node_logs.append({
                    "skill": f"↳ {child.skill.get('name', child.skill.get('id'))}",
                    "role": "Trigger",
                    "dps": int(real_child_dps),
                    "aps": f"{trigger_freq:.2f}",
                    "info": f"via {cond}"
                })

                merge_profile(node_profile, child_profile)

            return node_dps, node_logs, node_profile

        total_dps, logs, profile = walk(root_node, 0)
        return float(total_dps), logs, profile

    # ====== MVP 战斗外壳（带 BOSS 机制与图表数据）======
    def simulate_mvp_fight(
            self,
            root_node: SkillNode,
            enemy_hp: float = 3000.0,
            enemy_dps: float = 20.0,
            max_time: float = 20.0,
            dt: float = 0.1,
            seed: Optional[int] = None,
            max_depth: int = 1,
            **kwargs
    ) -> Dict[str, Any]:
        """
        全过程模拟：
        1. 引入时间轴 dt 循环
        2. 引入 BOSS 机制（每4秒暴击）
        3. 记录 Combat Log 和 Timeline 用于画图
        """
        hero_hp = float(self.stats.get("max_hp", 500.0))
        hero_max_hp = hero_hp


        # --- Determinism control ---
        if seed is None:
            # allow passing seed via kwargs for backward compatibility
            seed = kwargs.get("seed", 0)
        try:
            seed = int(seed)
        except Exception:
            seed = 0
        _rng = random.Random(seed)  # reserved for future RNG features

        # --- Enemy mechanics overrides (per-trial) ---
        boss_crit_interval = float(kwargs.get("boss_crit_interval", 4.0))
        boss_crit_mult = float(kwargs.get("boss_crit_mult", 2.5))

        # 初始血量记录（用于画图百分比）
        init_enemy_hp = kwargs.get("init_enemy_hp", enemy_hp)

        time = 0.0
        timeline: List[Dict[str, Any]] = []
        combat_log: List[str] = [] # 文字战报

        # --- BOSS 机制参数 ---
        # boss_crit_interval / boss_crit_mult are configurable per-trial (see kwargs)
        # boss_crit_mult configured above
        last_crit_time = -boss_crit_interval # 确保第4秒触发

        while time < max_time:
            # 1. 更新仿真状态 (用于触发条件如 hp_lt_30)
            hp_pct = max(0.0, hero_hp / max(hero_max_hp, 1.0))
            self.set_simulation_state(hp_pct)

            # 2. 计算玩家当前状态 (DPS, 期望减伤, 期望回血)
            dps, logs, profile = self.simulate_chain_with_profile(root_node, max_depth=max_depth)

            # --- 玩家输出阶段 ---
            dmg_to_enemy = float(dps) * dt
            enemy_hp -= dmg_to_enemy

            # --- BOSS 输出阶段 ---
            # 基础伤害
            incoming_dmg = float(enemy_dps) * dt
            is_boss_crit = False

            # 判定 BOSS 机制
            if time - last_crit_time >= boss_crit_interval:
                incoming_dmg *= boss_crit_mult
                is_boss_crit = True
                last_crit_time = time
                combat_log.append(f"[{time:.1f}s] ⚠️ BOSS 释放蓄力重击！({int(incoming_dmg/dt)} 伤害)")

            # 应用玩家减伤
            # 来源：装备 stats + 技能 profile (e.g. 护盾)
            final_taken_mult = float(self.stats.get("damage_taken_mult", 1.0)) * float(profile.get("damage_taken_mult", 1.0))
            # 限制硬减伤上限 (防止无敌)
            final_taken_mult = max(0.1, min(2.0, final_taken_mult))

            actual_taken = incoming_dmg * final_taken_mult
            hero_hp -= actual_taken

            # --- 玩家回血阶段 ---
            heal_amt = float(profile.get("heal_per_sec", 0.0)) * dt
            if heal_amt > 0 and hero_hp < hero_max_hp:
                # 记录一下回血关键时刻
                if hero_hp < hero_max_hp * 0.3:
                    combat_log.append(f"[{time:.1f}s] 🚑 触发紧急治疗 (+{int(heal_amt/dt)} HP/s)")
                hero_hp = min(hero_max_hp, hero_hp + heal_amt)

            # --- 记录 Timeline (用于画图) ---
            timeline.append({
                "time": round(time, 1),
                "hero_hp": int(max(hero_hp, 0)),
                "enemy_hp": int(max(enemy_hp, 0)),
                "is_crit": is_boss_crit
            })

            # --- 胜负判定 ---
            if hero_hp <= 0:
                combat_log.append(f"[{time:.1f}s] ☠️ 英雄阵亡！")
                result = {
                    "result": "LOSE",
                    "time": round(time, 2),
                    "reason": "hero_dead",
                    "timeline": timeline,
                    "logs": logs,
                    "combat_log": combat_log
                }
                # attach determinism header
                result["seed"] = seed
                result["dt"] = dt
                result["boss_crit_interval"] = boss_crit_interval
                result["boss_crit_mult"] = boss_crit_mult
                result["engine_version"] = self.version()
                result["result_hash"] = _stable_hash(result)
                return result
            if enemy_hp <= 0:
                combat_log.append(f"[{time:.1f}s] 🎉 击杀 BOSS！")
                result = {
                    "result": "WIN",
                    "time": round(time, 2),
                    "reason": "enemy_dead",
                    "timeline": timeline,
                    "logs": logs,
                    "combat_log": combat_log
                }
                # attach determinism header
                result["seed"] = seed
                result["dt"] = dt
                result["boss_crit_interval"] = boss_crit_interval
                result["boss_crit_mult"] = boss_crit_mult
                result["engine_version"] = self.version()
                result["result_hash"] = _stable_hash(result)
                return result

            time += dt

        combat_log.append(f"[{time:.1f}s] ⏳ 战斗超时，BOSS 狂暴灭团。")
        result = {
            "result": "TIMEOUT",
            "time": round(max_time, 2),
            "reason": "damage_insufficient",
            "timeline": timeline,
            "logs": logs,
            "combat_log": combat_log
        }
        # attach determinism header
        result["seed"] = seed
        result["dt"] = dt
        result["boss_crit_interval"] = boss_crit_interval
        result["boss_crit_mult"] = boss_crit_mult
        result["engine_version"] = self.version()
        result["result_hash"] = _stable_hash(result)
        return result
