# -*- coding: utf-8 -*-
"""BD评测跑批器：机制有效 vs 数值虚高"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

try:
    import pandas as pd
except Exception:  # pragma: no cover - pandas may be absent in some environments
    pd = None

from engine import DiabloEngine, SkillNode

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_EVAL_DIR = ROOT_DIR / "configs" / "eval"
DEFAULT_DATA_PATH = ROOT_DIR / "data.yaml"


def load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_eval_configs(base_dir: Path = DEFAULT_EVAL_DIR) -> Dict[str, Any]:
    return {
        "bosses": load_yaml(base_dir / "bosses.yaml"),
        "builds": load_yaml(base_dir / "builds.yaml"),
        "nerfs": load_yaml(base_dir / "nerf_profiles.yaml"),
    }


def list_build_ids(configs: Dict[str, Any]) -> List[str]:
    return [b.get("build_id") for b in (configs.get("builds", {}) or {}).get("builds", [])]


def list_boss_suite_ids(configs: Dict[str, Any]) -> List[str]:
    suites = (configs.get("bosses", {}) or {}).get("suites", {}) or {}
    return list(suites.keys())


def compute_pass_flag(ttk: float, survival_margin: float, thresholds: Dict[str, Any]) -> bool:
    return (ttk <= float(thresholds.get("max_ttk", 9999))) and (
        survival_margin >= float(thresholds.get("min_survival_margin", 0.0))
    )


def _find_build(configs: Dict[str, Any], build_id: str) -> Dict[str, Any]:
    for b in (configs.get("builds", {}) or {}).get("builds", []):
        if b.get("build_id") == build_id:
            return b
    raise KeyError(f"build_id not found: {build_id}")


def _collect_bosses(configs: Dict[str, Any], suite_id: str) -> List[Dict[str, Any]]:
    suites = (configs.get("bosses", {}) or {}).get("suites", {}) or {}
    bosses: List[Dict[str, Any]] = []
    if suite_id == "all":
        for sid, suite in suites.items():
            for boss in suite.get("bosses", []) or []:
                row = dict(boss)
                row["suite_id"] = sid
                row["suite_name"] = suite.get("name", sid)
                bosses.append(row)
        return bosses

    if suite_id not in suites:
        raise KeyError(f"boss_suite not found: {suite_id}")
    suite = suites[suite_id]
    for boss in suite.get("bosses", []) or []:
        row = dict(boss)
        row["suite_id"] = suite_id
        row["suite_name"] = suite.get("name", suite_id)
        bosses.append(row)
    return bosses


def _normalize_nerf_profiles(configs: Dict[str, Any], nerf_profiles: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    if nerf_profiles is not None:
        return nerf_profiles
    return (configs.get("nerfs", {}) or {}).get("profiles", []) or []


def _normalize_mechanism_modes(build: Dict[str, Any], mechanism_modes: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    defaults = build.get("feature_flags_default") or {}
    if mechanism_modes is not None:
        return mechanism_modes
    on_flags = dict(defaults)
    off_flags = {k: False for k in defaults}
    return [
        {"id": "on", "name": "on", "flags": on_flags},
        {"id": "off", "name": "off", "flags": off_flags},
    ]


def _build_skill_node(data: Dict[str, Any], skill_set: Dict[str, Any]) -> SkillNode:
    skills_list = data.get("skills", []) or []
    mods_list = data.get("modifiers", []) or []

    def get_skill(sid: str) -> Dict[str, Any]:
        return next(s for s in skills_list if s["id"] == sid)

    def get_mod(mid: str) -> Dict[str, Any]:
        return next(m for m in mods_list if m["id"] == mid)

    root = SkillNode(get_skill(skill_set["main_skill"]), [get_mod(m) for m in (skill_set.get("main_mods") or [])])
    root.triggers = []
    for trig in skill_set.get("triggers", []) or []:
        if not trig.get("enabled", True):
            continue
        child = SkillNode(get_skill(trig["skill"]), [get_mod(m) for m in (trig.get("mods") or [])])
        child.triggers = []
        root.triggers.append({"condition": trig.get("condition", "on_hit"), "node": child})
    return root


def _extract_final_hp(result: Dict[str, Any]) -> Tuple[float, float]:
    hero_max_hp = float(result.get("hero_max_hp", 0.0) or 0.0)
    timeline = result.get("timeline", []) or []
    if timeline:
        final_hero = float(timeline[-1].get("hero_hp", 0.0))
    else:
        final_hero = 0.0
    return hero_max_hp, final_hero


def _effective_dps(result: Dict[str, Any], enemy_max_hp: float) -> float:
    timeline = result.get("timeline", []) or []
    if not timeline:
        return 0.0
    final_enemy_hp = float(timeline[-1].get("enemy_hp", 0.0))
    time = float(result.get("time", 0.0) or 0.0)
    if time <= 0:
        return 0.0
    dealt = max(0.0, enemy_max_hp - final_enemy_hp)
    return dealt / time


def _variance(values: List[float]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return sum((v - mean) ** 2 for v in values) / len(values)


def _linear_slope(xs: List[float], ys: List[float]) -> float:
    if len(xs) < 2:
        return 0.0
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    denom = sum((x - mean_x) ** 2 for x in xs)
    if denom == 0:
        return 0.0
    return sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / denom


def run_evaluation(
    build_id: str,
    boss_suite: str = "all",
    seeds: Optional[List[int]] = None,
    nerf_profiles: Optional[List[Dict[str, Any]]] = None,
    mechanism_modes: Optional[List[Dict[str, Any]]] = None,
    base_dir: Path = DEFAULT_EVAL_DIR,
    data_path: Path = DEFAULT_DATA_PATH,
    return_df: bool = True,
) -> Dict[str, Any]:
    configs = load_eval_configs(base_dir)
    build = _find_build(configs, build_id)
    bosses = _collect_bosses(configs, boss_suite)
    nerfs = _normalize_nerf_profiles(configs, nerf_profiles)
    mech_modes = _normalize_mechanism_modes(build, mechanism_modes)

    if seeds is None:
        seeds = [101, 102, 103]

    data = load_yaml(data_path)

    model_id = build.get("model_id") or "model_human"
    talent_id = build.get("talent_id")
    model_obj = next(m for m in (data.get("models", []) or []) if m.get("id") == model_id)
    talent_obj = next((t for t in (data.get("talents", []) or []) if t.get("id") == talent_id), None) if talent_id else None

    skill_set = build.get("skill_set") or {}
    max_depth = int(skill_set.get("max_depth", 1))
    root_node = _build_skill_node(data, skill_set)

    rows: List[Dict[str, Any]] = []

    for boss in bosses:
        dps_profile = boss.get("dps_profile") or {}
        enemy_hp = float(boss.get("base_hp", 3000))
        enemy_dps = float(dps_profile.get("base_dps", 20))
        max_time = float(dps_profile.get("max_time", 20))
        boss_crit_interval = float(dps_profile.get("boss_crit_interval", 4.0))
        boss_crit_mult = float(dps_profile.get("boss_crit_mult", 2.5))
        thresholds = boss.get("thresholds") or {}

        for nerf in nerfs:
            nerf_id = nerf.get("id", "custom")
            damage_mul = float(nerf.get("damage_mul", 1.0))
            heal_mul = float(nerf.get("heal_mul", 1.0))
            shield_mul = float(nerf.get("shield_mul", 1.0))

            for mode in mech_modes:
                flags = mode.get("flags") or {}
                mode_id = mode.get("id", mode.get("name", "mode"))

                seed_metrics = []
                for seed in seeds:
                    eng = DiabloEngine(data)
                    eng.build_hero(model_obj, talent_obj)
                    result = eng.simulate_mvp_fight(
                        root_node,
                        enemy_hp=enemy_hp,
                        init_enemy_hp=enemy_hp,
                        enemy_dps=enemy_dps,
                        max_time=max_time,
                        dt=float(dps_profile.get("dt", 0.1)),
                        seed=int(seed),
                        boss_crit_interval=boss_crit_interval,
                        boss_crit_mult=boss_crit_mult,
                        max_depth=max_depth,
                        nerf_profile=nerf,
                        damage_mul=damage_mul,
                        heal_mul=heal_mul,
                        shield_mul=shield_mul,
                        mechanism_flags=flags,
                        mechanism_params=build.get("mechanism_params") or {},
                        mechanism_disable_strategy=build.get("mechanism_disable_strategy") or {},
                    )

                    hero_max_hp, final_hero_hp = _extract_final_hp(result)
                    survival_margin = (final_hero_hp / hero_max_hp) if hero_max_hp > 0 else 0.0
                    ttk = float(result.get("time", 0.0) or 0.0)
                    effective_dps = _effective_dps(result, enemy_hp)

                    seed_metrics.append({
                        "effective_dps": effective_dps,
                        "ttk": ttk,
                        "survival_margin": survival_margin,
                        "pass_flag": compute_pass_flag(ttk, survival_margin, thresholds),
                    })

                avg_dps = sum(m["effective_dps"] for m in seed_metrics) / len(seed_metrics)
                avg_ttk = sum(m["ttk"] for m in seed_metrics) / len(seed_metrics)
                avg_margin = sum(m["survival_margin"] for m in seed_metrics) / len(seed_metrics)
                pass_flag = compute_pass_flag(avg_ttk, avg_margin, thresholds)

                rows.append({
                    "build_id": build_id,
                    "boss_suite": boss.get("suite_id"),
                    "boss_name": boss.get("name"),
                    "boss_id": boss.get("boss_id"),
                    "nerf_id": nerf_id,
                    "damage_mul": damage_mul,
                    "heal_mul": heal_mul,
                    "shield_mul": shield_mul,
                    "mechanism_mode": mode_id,
                    "effective_dps": round(avg_dps, 3),
                    "ttk": round(avg_ttk, 3),
                    "survival_margin": round(avg_margin, 4),
                    "pass_flag": bool(pass_flag),
                    "seed_count": len(seed_metrics),
                })

    # --- 汇总指标 ---
    baseline_nerf = next((n for n in nerfs if float(n.get("damage_mul", 1.0)) == 1.0 and float(n.get("heal_mul", 1.0)) == 1.0 and float(n.get("shield_mul", 1.0)) == 1.0), nerfs[0])
    baseline_id = baseline_nerf.get("id", "baseline")

    rows_on = [r for r in rows if r["mechanism_mode"] == "on"]
    rows_off = [r for r in rows if r["mechanism_mode"] == "off"]

    robust_pass_rate = 0.0
    if rows_on:
        robust_pass_rate = sum(1 for r in rows_on if r["pass_flag"]) / len(rows_on)

    # sensitivity: ttk vs damage_mul (on mode)
    dmg_points = {}
    for r in rows_on:
        dmg_points.setdefault(r["damage_mul"], []).append(r["ttk"])
    xs = sorted(dmg_points.keys())
    ys = [sum(dmg_points[x]) / len(dmg_points[x]) for x in xs]
    sensitivity_ttk_damage = _linear_slope(xs, ys)

    # mechanism deltas (baseline nerf only)
    on_base = [r for r in rows_on if r["nerf_id"] == baseline_id]
    off_base = [r for r in rows_off if r["nerf_id"] == baseline_id]
    on_ttk = sum(r["ttk"] for r in on_base) / len(on_base) if on_base else 0.0
    off_ttk = sum(r["ttk"] for r in off_base) / len(off_base) if off_base else 0.0
    on_margin = sum(r["survival_margin"] for r in on_base) / len(on_base) if on_base else 0.0
    off_margin = sum(r["survival_margin"] for r in off_base) / len(off_base) if off_base else 0.0
    mechanism_delta_ttk = (off_ttk / on_ttk) if on_ttk > 0 else 0.0
    mechanism_delta_survival = on_margin - off_margin

    # specialization score (baseline + on)
    per_suite = {}
    for r in on_base:
        per_suite.setdefault(r["boss_suite"], {"ttk": [], "margin": []})
        per_suite[r["boss_suite"]]["ttk"].append(r["ttk"])
        per_suite[r["boss_suite"]]["margin"].append(r["survival_margin"])
    suite_ttks = [sum(v["ttk"]) / len(v["ttk"]) for v in per_suite.values() if v["ttk"]]
    suite_margins = [sum(v["margin"]) / len(v["margin"]) for v in per_suite.values() if v["margin"]]
    specialization_score = _variance(suite_ttks) + _variance(suite_margins)

    if robust_pass_rate >= 0.6 and mechanism_delta_ttk >= 1.3:
        final_label = "mechanism_driven"
    elif robust_pass_rate < 0.4 and mechanism_delta_ttk < 1.15:
        final_label = "stat_driven"
    else:
        final_label = "mixed"

    summary = {
        "build_id": build_id,
        "robust_pass_rate": round(robust_pass_rate, 3),
        "sensitivity_ttk_damage": round(sensitivity_ttk_damage, 4),
        "mechanism_delta_ttk": round(mechanism_delta_ttk, 3),
        "mechanism_delta_survival": round(mechanism_delta_survival, 4),
        "specialization_score": round(specialization_score, 4),
        "final_label": final_label,
        "baseline_nerf_id": baseline_id,
    }

    result = {
        "rows": rows,
        "summary": summary,
        "meta": {
            "build_name": build.get("name"),
            "boss_suite": boss_suite,
            "seeds": list(seeds),
            "nerf_profiles": nerfs,
            "mechanism_modes": mech_modes,
        },
    }

    if return_df and pd is not None:
        result["df"] = pd.DataFrame(rows)

    return result


def export_report_bytes(report: Dict[str, Any]) -> Dict[str, bytes]:
    rows = report.get("rows", [])
    df = None
    if pd is not None:
        df = pd.DataFrame(rows)
    if df is None:
        csv_text = "\n".join([json.dumps(r, ensure_ascii=False) for r in rows])
    else:
        csv_text = df.to_csv(index=False)
    csv_bytes = ("\ufeff" + csv_text).encode("utf-8")
    json_bytes = ("\ufeff" + json.dumps(report, ensure_ascii=False, indent=2)).encode("utf-8")
    return {"csv": csv_bytes, "json": json_bytes}
