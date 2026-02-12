# -*- coding: utf-8 -*-

import json

from core.eval import eval_runner


def test_eval_determinism():
    report1 = eval_runner.run_evaluation(
        build_id="dot_core",
        boss_suite="low_pressure_high_hp",
        seeds=[123],
        nerf_profiles=[{"id": "baseline", "damage_mul": 1.0, "heal_mul": 1.0, "shield_mul": 1.0}],
        mechanism_modes=None,
        return_df=False,
    )
    report2 = eval_runner.run_evaluation(
        build_id="dot_core",
        boss_suite="low_pressure_high_hp",
        seeds=[123],
        nerf_profiles=[{"id": "baseline", "damage_mul": 1.0, "heal_mul": 1.0, "shield_mul": 1.0}],
        mechanism_modes=None,
        return_df=False,
    )

    dump1 = json.dumps(report1["rows"], ensure_ascii=False, sort_keys=True)
    dump2 = json.dumps(report2["rows"], ensure_ascii=False, sort_keys=True)
    assert dump1 == dump2


def test_pass_flag_logic():
    thresholds = {"max_ttk": 12, "min_survival_margin": 0.4}
    assert eval_runner.compute_pass_flag(10, 0.5, thresholds) is True
    assert eval_runner.compute_pass_flag(13, 0.5, thresholds) is False
    assert eval_runner.compute_pass_flag(10, 0.2, thresholds) is False
