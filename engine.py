import copy
from typing import Any, Dict, List, Optional, Tuple


class SkillNode:
    """技能链节点：主技能/子技能 + 模组 + 触发器。

    triggers: List[{"condition": str, "node": SkillNode}]
    """

    def __init__(
        self,
        skill_data: Dict[str, Any],
        modifiers: Optional[List[Dict[str, Any]]] = None,
        triggers: Optional[List[Dict[str, Any]]] = None,
    ):
        self.skill = skill_data
        self.modifiers = modifiers or []
        self.triggers = triggers or []


class DiabloEngine:
    def __init__(self, data_source: Dict[str, Any]):
        self.data = data_source
        self.stats: Dict[str, float] = {}
        # 运行时状态（用于 hp_lt_30 等条件）
        self.simulation_state: Dict[str, float] = {"hp_percent": 1.0}

    # -----------------------------
    # 基础：角色面板
    # -----------------------------
    def set_simulation_state(self, hp_percent: float = 1.0):
        try:
            hp = float(hp_percent)
        except Exception:
            hp = 1.0
        self.simulation_state["hp_percent"] = max(0.0, min(1.0, hp))

    def build_hero(self, model_data: Dict[str, Any], talent_data: Optional[Dict[str, Any]] = None):
        """初始化角色面板（尽量兼容你现有 YAML 结构）"""
        self.stats = copy.deepcopy(model_data.get("base_stats", {}))
        self.stats.update(model_data.get("attributes", {}))

        # 兼容：有些模型把 base_stats/attributes 写在顶层
        for k in ("max_hp", "base_atk", "crit_rate", "crit_dmg", "atk_spd"):
            if k in model_data and k not in self.stats:
                try:
                    self.stats[k] = float(model_data[k])
                except Exception:
                    pass

        # 处理天赋（dynamic_stats：加法叠加）
        if talent_data and isinstance(talent_data, dict) and "dynamic_stats" in talent_data:
            for k, v in (talent_data.get("dynamic_stats") or {}).items():
                try:
                    self.stats[k] = float(self.stats.get(k, 0.0)) + float(v)
                except Exception:
                    pass

    def _apply_modifier_stats(self, base_stats: Dict[str, float], mods: List[Dict[str, Any]]) -> Dict[str, float]:
        temp = copy.deepcopy(base_stats)
        for mod in mods or []:
            for k, v in (mod.get("stats") or {}).items():
                try:
                    temp[k] = float(temp.get(k, 0.0)) + float(v)
                except Exception:
                    pass
        return temp

    # -----------------------------
    # 核心数值：单技能“期望”计算
    # -----------------------------
    def _normalize_aps(self, atk_spd_val: float) -> float:
        """当前版本把 atk_spd 统一视为“绝对 APS”。"""
        try:
            v = float(atk_spd_val)
        except Exception:
            return 1.0
        if v <= 0:
            return 1.0
        return v

    def _core_math(self, skill: Dict[str, Any], current_stats: Dict[str, float]) -> Dict[str, Any]:
        """核心数学：计算单技能期望（不含触发链拓展）"""
        aps = self._normalize_aps(current_stats.get("atk_spd", 1.0))

        if not skill.get("damage_components"):
            return {"avg_hit": 0.0, "aps": aps, "crit_rate": 0.0, "dps": 0.0, "dmg_type": "none"}

        comp = skill["damage_components"][0]
        dmg_type = comp.get("type", "physical")

        min_dmg = float(comp.get("min", 0.0))
        max_dmg = float(comp.get("max", 0.0))

        scale_src = comp.get("scaling_source", "base_atk")
        scale_coef = float(comp.get("scaling_coef", 1.0))
        source_val = float(current_stats.get(scale_src, 0.0))

        flat_bonus = float(current_stats.get(f"flat_{dmg_type}", 0.0))
        base_avg = (min_dmg + max_dmg) / 2.0 + source_val * scale_coef + flat_bonus

        inc_all = float(current_stats.get("inc_all", 0.0))
        inc_type = float(current_stats.get(f"inc_{dmg_type}", 0.0))
        inc = 1.0 + inc_all + inc_type

        more_damage = float(current_stats.get("more_damage", 0.0))
        more = 1.0 + more_damage

        hit = base_avg * inc * more

        crit_rate = min(1.0, max(0.0, float(current_stats.get("crit_rate", 0.05))))
        crit_dmg = float(current_stats.get("crit_dmg", 1.5))
        avg_hit = hit * (1.0 - crit_rate) + (hit * crit_dmg * crit_rate)

        return {
            "avg_hit": avg_hit,
            "aps": aps,
            "crit_rate": crit_rate,
            "dps": avg_hit * aps,
            "dmg_type": dmg_type,
        }

    # -----------------------------
    # 兼容旧接口：单技能
    # -----------------------------
    def calculate_skill_damage(self, skill_data: Dict[str, Any], modifiers_list: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        mods = modifiers_list or []
        final_stats = self._apply_modifier_stats(self.stats, mods)
        res = self._core_math(skill_data, final_stats)
        return {
            "DPS": res["dps"],
            "Avg_Hit": res["avg_hit"],
            "Crit_Info": {"rate": res["crit_rate"], "aps": res["aps"]},
            "Trigger_Info": [],
        }

    # -----------------------------
    # 触发频率
    # -----------------------------
    def _trigger_frequency(self, condition: str, parent_cps: float, parent_crit_rate: float) -> float:
        if parent_cps <= 0:
            return 0.0

        if condition == "on_hit":
            return parent_cps
        if condition == "on_crit":
            return parent_cps * max(0.0, min(1.0, parent_crit_rate))
        if condition == "fixed_chance_20":
            return parent_cps * 0.2
        if condition == "hp_lt_30":
            return parent_cps if float(self.simulation_state.get("hp_percent", 1.0)) < 0.3 else 0.0
        return 0.0

    # -----------------------------
    # 技能链（期望）计算 + 生存 profile
    # -----------------------------
    def simulate_chain(self, root_node: SkillNode) -> Tuple[float, List[Dict[str, Any]]]:
        total_dps, logs, _profile = self.simulate_chain_with_profile(root_node, max_depth=99)
        return total_dps, logs

    def simulate_chain_with_profile(
        self,
        root_node: SkillNode,
        max_depth: int = 1,
        max_triggers: Optional[int] = None,
    ) -> Tuple[float, List[Dict[str, Any]], Dict[str, Any]]:
        """递归计算技能链：返回 (total_dps, logs, profile)

        profile 用于 MVP：
        - heals_per_sec: 期望每秒治疗
        - expected_damage_taken_mult: 期望承伤倍率（<1 表示减伤）
        """

        logs: List[Dict[str, Any]] = []
        profile = {
            "heals_per_sec": 0.0,
            "expected_damage_taken_mult": 1.0,
        }

        hero_max_hp = float(self.stats.get("max_hp", 500.0))

        def apply_effects(eff: Dict[str, Any], proc_cps: float):
            if not eff or proc_cps <= 0:
                return

            # ICD 限制：每秒最多触发 1/icd 次
            icd = eff.get("icd", None)
            if icd is not None:
                try:
                    icd_v = float(icd)
                    if icd_v > 0:
                        proc_cps = min(proc_cps, 1.0 / icd_v)
                except Exception:
                    pass

            # heal
            heal_pct = eff.get("heal_percent_max_hp", 0.0)
            try:
                heal_pct = float(heal_pct)
            except Exception:
                heal_pct = 0.0

            if heal_pct > 0:
                profile["heals_per_sec"] += proc_cps * heal_pct * hero_max_hp

            # damage_taken_mult (multiplier) + duration -> uptime
            dmg_mult = eff.get("damage_taken_mult", None)
            duration = eff.get("duration", None)
            if dmg_mult is not None and duration is not None:
                try:
                    dmg_mult = float(dmg_mult)
                    duration = float(duration)
                except Exception:
                    dmg_mult = None
                    duration = None

            if dmg_mult is not None and duration and duration > 0 and dmg_mult > 0:
                uptime = min(1.0, proc_cps * duration)
                # 期望承伤倍率因子： (1-u)*1 + u*dmg_mult
                expected_factor = (1.0 - uptime) + uptime * dmg_mult
                profile["expected_damage_taken_mult"] *= expected_factor

        def walk(node: SkillNode, forced_cps: Optional[float], depth: int, via: str) -> float:
            # 1) 当前节点面板
            node_stats = self._apply_modifier_stats(self.stats, node.modifiers)
            base = self._core_math(node.skill, node_stats)

            native_cps = float(base["aps"]) if float(base["aps"]) > 0 else 1.0
            cps = float(forced_cps) if forced_cps is not None else native_cps
            cps = max(0.0, cps)

            node_dps = float(base["avg_hit"]) * cps

            logs.append(
                {
                    "skill": node.skill.get("name", node.skill.get("id", "unknown")),
                    "role": "Main" if depth == 0 else "Trigger",
                    "dps": int(node_dps),
                    "aps": f"{cps:.2f}",
                    "info": via,
                }
            )

            # 2) effects
            eff = node.skill.get("effects") or {}
            apply_effects(eff, cps)

            total = node_dps

            # 3) 触发器
            if depth >= max_depth:
                return total

            triggers = node.triggers or []
            if max_triggers is not None:
                triggers = triggers[: max(0, int(max_triggers))]

            for trig in triggers:
                child = trig.get("node")
                cond = trig.get("condition")
                if not child or not cond:
                    continue

                trig_cps = self._trigger_frequency(str(cond), cps, float(base["crit_rate"]))
                if trig_cps <= 0:
                    continue

                total += walk(child, trig_cps, depth + 1, via=f"via {cond}")

            return total

        total_dps = walk(root_node, None, 0, via="base")

        # clamp to avoid weirdness
        profile["heals_per_sec"] = max(0.0, float(profile["heals_per_sec"]))
        profile["expected_damage_taken_mult"] = max(0.05, min(5.0, float(profile["expected_damage_taken_mult"])))

        return float(total_dps), logs, profile

    # -----------------------------
    # MVP：战斗外壳（会赢/会输/会超时）
    # -----------------------------
    def _stats_damage_taken_base_mult(self) -> float:
        """兼容 stats['damage_taken_mult'] 的两种写法：
        - multiplier: 0.8 表示承伤*0.8
        - offset: -0.2 表示承伤*(1-0.2)=0.8
        """
        v = self.stats.get("damage_taken_mult", 0.0)
        try:
            v = float(v)
        except Exception:
            return 1.0

        if v == 0.0:
            return 1.0

        # multiplier 写法更常见：0 < v < 2
        if 0.0 < v < 2.0:
            return max(0.05, v)

        # offset 写法：-0.9 ~ 0.9
        if -0.9 < v < 0.9:
            return max(0.05, 1.0 + v)

        # 兜底
        return max(0.05, v)

    def simulate_mvp_fight(
        self,
        root_node: SkillNode,
        enemy_hp: float = 3000.0,
        enemy_dps: float = 30.0,
        max_time: float = 20.0,
        dt: float = 0.1,
        max_depth: int = 1,
        **kwargs,
    ) -> Dict[str, Any]:
        """最小可验证 Demo：

        - 敌人：恒定 DPS
        - 英雄：用技能链给出期望 DPS + 期望治疗/减伤
        - 输出：WIN/LOSE/TIMEOUT + 诊断 + timeline

        兼容 app.py 可能传入的额外参数：max_triggers / allowed_conditions / ...
        """

        # 兼容：有人把 max_depth 放进 kwargs
        if "max_depth" in kwargs:
            try:
                max_depth = int(kwargs["max_depth"])
            except Exception:
                pass

        max_triggers = kwargs.get("max_triggers", None)

        try:
            enemy_hp = float(enemy_hp)
            enemy_dps = float(enemy_dps)
            max_time = float(max_time)
            dt = float(dt)
        except Exception:
            enemy_hp, enemy_dps, max_time, dt = 3000.0, 30.0, 20.0, 0.1

        if dt <= 0:
            dt = 0.1

        hero_max_hp = float(self.stats.get("max_hp", 500.0))
        hero_hp = hero_max_hp

        base_taken_mult = self._stats_damage_taken_base_mult()

        t = 0.0
        timeline: List[Dict[str, Any]] = []

        total_heal = 0.0
        total_incoming = 0.0
        total_damage_done = 0.0
        last_logs: List[Dict[str, Any]] = []

        while t < max_time:
            hp_percent = hero_hp / hero_max_hp if hero_max_hp > 0 else 0.0
            self.set_simulation_state(hp_percent)

            total_dps, logs, prof = self.simulate_chain_with_profile(
                root_node,
                max_depth=max_depth,
                max_triggers=max_triggers,
            )
            last_logs = logs

            heals_per_sec = float(prof.get("heals_per_sec", 0.0))
            expected_taken_mult = float(prof.get("expected_damage_taken_mult", 1.0))

            incoming_mult = base_taken_mult * expected_taken_mult
            incoming_mult = max(0.05, min(10.0, incoming_mult))

            incoming = enemy_dps * incoming_mult * dt
            total_incoming += incoming
            hero_hp -= incoming

            heal = heals_per_sec * dt
            total_heal += heal
            hero_hp = min(hero_max_hp, hero_hp + heal)

            dmg = total_dps * dt
            total_damage_done += dmg
            enemy_hp -= dmg

            timeline.append(
                {
                    "time": round(t, 2),
                    "hero_hp": int(max(hero_hp, 0.0)),
                    "enemy_hp": int(max(enemy_hp, 0.0)),
                    "dps": int(total_dps),
                    "heal_ps": int(heals_per_sec),
                    "dmg_taken_mult": round(incoming_mult, 3),
                }
            )

            if enemy_hp <= 0:
                return {
                    "result": "WIN",
                    "time": round(t, 2),
                    "reason": "enemy_dead",
                    "summary": {
                        "hero_max_hp": int(hero_max_hp),
                        "hero_hp_left": int(max(hero_hp, 0.0)),
                        "enemy_hp_left": 0,
                        "avg_dps": int(total_damage_done / max(t + dt, 0.001)),
                        "total_heal": int(total_heal),
                        "total_incoming": int(total_incoming),
                    },
                    "chain_logs": last_logs,
                    "timeline": timeline,
                }

            if hero_hp <= 0:
                return {
                    "result": "LOSE",
                    "time": round(t, 2),
                    "reason": "hero_dead",
                    "summary": {
                        "hero_max_hp": int(hero_max_hp),
                        "hero_hp_left": 0,
                        "enemy_hp_left": int(max(enemy_hp, 0.0)),
                        "avg_dps": int(total_damage_done / max(t + dt, 0.001)),
                        "total_heal": int(total_heal),
                        "total_incoming": int(total_incoming),
                    },
                    "chain_logs": last_logs,
                    "timeline": timeline,
                }

            t += dt

        return {
            "result": "TIMEOUT",
            "time": round(max_time, 2),
            "reason": "damage_insufficient",
            "summary": {
                "hero_max_hp": int(hero_max_hp),
                "hero_hp_left": int(max(hero_hp, 0.0)),
                "enemy_hp_left": int(max(enemy_hp, 0.0)),
                "avg_dps": int(total_damage_done / max(max_time, 0.001)),
                "total_heal": int(total_heal),
                "total_incoming": int(total_incoming),
            },
            "chain_logs": last_logs,
            "timeline": timeline,
        }
