# -*- coding: utf-8 -*-
"""五行棋盘规则评估的最小测试"""

from wuxing_board import generate_wuxing_board
from wuxing_rules import evaluate_wuxing_rules, example_builds


def test_generation_loop_detection():
    layout = generate_wuxing_board()
    builds = example_builds(layout)
    chain_build = builds[0]
    result = evaluate_wuxing_rules(layout, set(chain_build["selected_nodes"]))
    assert result.loop_unlocked is True
    assert result.generation_links


def test_destruction_rule_rewrite_detection():
    layout = generate_wuxing_board()
    builds = example_builds(layout)
    convert_build = builds[1]
    result = evaluate_wuxing_rules(layout, set(convert_build["selected_nodes"]), realm="金丹")
    assert result.destruction_effects
