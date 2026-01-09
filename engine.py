import math
import copy

class SkillNode:
    """技能链节点：用于新版递归计算"""
    def __init__(self, skill_data, modifiers=None, triggers=None):
        self.skill = skill_data
        self.modifiers = modifiers or []
        self.triggers = triggers or [] # List of {"condition": str, "node": SkillNode}

class DiabloEngine:
    def __init__(self, data_source):
        self.data = data_source
        self.stats = {}
        self.simulation_state = {"hp_percent": 1.0}

    def set_simulation_state(self, hp_percent=1.0):
        self.simulation_state["hp_percent"] = hp_percent

    def build_hero(self, model_data, talent_data):
        """初始化角色面板"""
        self.stats = copy.deepcopy(model_data.get('base_stats', {}))
        self.stats.update(model_data.get('attributes', {}))

        # 处理天赋
        if talent_data and 'dynamic_stats' in talent_data:
            for k, v in talent_data['dynamic_stats'].items():
                try:
                    self.stats[k] = self.stats.get(k, 0) + float(v)
                except:
                    pass

    def _apply_modifier_stats(self, base_stats, mods):
        """通用工具：将一组模组的属性叠加到面板"""
        temp_stats = copy.deepcopy(base_stats)
        for mod in mods:
            for k, v in mod.get('stats', {}).items():
                temp_stats[k] = temp_stats.get(k, 0) + v
        return temp_stats

    def _core_math(self, skill, current_stats):
        """核心数学公式：计算单次伤害 (不含触发)"""
        # 1. 基础伤害
        if not skill.get('damage_components'):
            return {"dps": 0, "avg_hit": 0, "aps": 1.0, "crit_rate": 0, "dmg_type": "none"}

        comp = skill['damage_components'][0]
        min_dmg = comp.get('min', 0)
        max_dmg = comp.get('max', 0)

        # 2. 属性Scaling
        scale_src = comp.get('scaling_source', 'base_atk')
        scale_coef = comp.get('scaling_coef', 1.0)
        source_val = current_stats.get(scale_src, 0)
        flat_bonus = current_stats.get(f"flat_{comp['type']}", 0)

        base_avg = (min_dmg + max_dmg) / 2 + source_val * scale_coef + flat_bonus

        # 3. 增伤区间
        inc = 1 + current_stats.get('inc_all', 0) + current_stats.get(f"inc_{comp['type']}", 0)
        more = 1 * (1 + current_stats.get('more_damage', 0))

        hit_dmg = base_avg * inc * more

        # 4. 暴击
        crit_rate = min(1.0, current_stats.get('crit_rate', 0.05))
        crit_dmg = current_stats.get('crit_dmg', 1.5)
        avg_hit = hit_dmg * (1 - crit_rate) + (hit_dmg * crit_dmg * crit_rate)

        # 5. 攻速
        aps = current_stats.get('atk_spd', 1.0)

        return {
            "dps": avg_hit * aps,
            "avg_hit": avg_hit,
            "aps": aps,
            "crit_rate": crit_rate,
            "dmg_type": comp['type']
        }

    # ============================
    # 接口 A: 旧版简单计算
    # ============================
    def calculate_skill_damage(self, skill_data, modifiers_list=None):
        """兼容旧代码：计算单一技能，无递归"""
        mods = modifiers_list or []
        # 1. 计算面板
        final_stats = self._apply_modifier_stats(self.stats, mods)
        # 2. 计算伤害
        res = self._core_math(skill_data, final_stats)
        # 3. 包装成旧版返回格式
        return {
            "DPS": res['dps'],
            "Avg_Hit": res['avg_hit'],
            "Crit_Info": {"rate": res['crit_rate'], "aps": res['aps']},
            "Trigger_Info": [] # 旧版没有触发链
        }

    # ============================
    # 接口 B: 新版递归计算
    # ============================
    def simulate_chain(self, root_node: SkillNode):
        """递归计算整条技能链"""
        logs = []
        total_dps = 0

        # 1. 计算当前节点
        node_stats = self._apply_modifier_stats(self.stats, root_node.modifiers)
        base_res = self._core_math(root_node.skill, node_stats)

        node_dps = base_res['dps']
        total_dps += node_dps

        logs.append({
            "skill": root_node.skill['name'],
            "role": "Main" if not logs else "Sub",
            "dps": int(node_dps),
            "aps": f"{base_res['aps']:.2f}",
            "info": f"基础伤害"
        })

        # 2. 递归处理触发器
        for trigger in root_node.triggers:
            child_node = trigger['node']
            condition = trigger['condition']

            # 简易频率模拟
            trigger_freq = 0.0
            if condition == "on_crit":
                trigger_freq = base_res['aps'] * base_res['crit_rate']
            elif condition == "on_hit":
                trigger_freq = base_res['aps']
            elif condition == "fixed_chance_20":
                trigger_freq = base_res['aps'] * 0.2

            if trigger_freq > 0:
                # 递归调用
                child_dps, child_logs = self.simulate_chain(child_node)

                # 修正子技能伤害：子技能原本是按它自己的aps算的，现在要强制改为触发频率
                # 修正公式：(子技能总DPS / 子技能原生APS) * 触发频率
                child_native_aps = float(child_logs[0]['aps']) if float(child_logs[0]['aps']) > 0 else 1.0
                real_child_dps = (child_dps / child_native_aps) * trigger_freq

                total_dps += real_child_dps

                logs.append({
                    "skill": f"↳ {child_node.skill['name']}",
                    "role": "Trigger",
                    "dps": int(real_child_dps),
                    "aps": f"{trigger_freq:.2f}",
                    "info": f"via {condition}"
                })

        return total_dps, logs