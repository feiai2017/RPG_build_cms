import math

class DiabloEngine:
    def __init__(self, config):
        self.config = config
        self.stats = {}
        self.modifiers = []
        self.conversions = []
        self.simulation_context = {"hp_percent": 1.0}

    def set_simulation_state(self, hp_percent):
        self.simulation_context['hp_percent'] = hp_percent

    def build_hero(self, model_data, talent_data):
        self.modifiers = []
        self.conversions = []

        attrs = model_data['attributes']
        base = model_data['base_stats']
        rules = self.config['rules']

        # 计算基础面板
        max_hp = (attrs['str'] * rules['str_to_hp']) + base.get('max_hp_bonus', 0)

        self.stats = {
            # 1. 核心三维
            "str": attrs['str'], "agi": attrs['agi'], "int": attrs['int'],

            # 2. 生存面板
            "max_hp": max_hp,
            "current_hp": max_hp * self.simulation_context['hp_percent'],

            # 3. 攻击面板
            "base_atk": base['base_atk'],
            "crit_rate": attrs['agi'] * rules['agi_to_crit_rate'],
            "crit_dmg": base['crit_dmg'],
            "atk_spd": 100,

            # 4. 属性衍生加成 (Inc)
            "inc_fire": attrs['int'] * rules.get('int_to_inc_elemental', 0.0),
            "inc_cold": attrs['int'] * rules.get('int_to_inc_elemental', 0.0),
            "inc_lightning": attrs['int'] * rules.get('int_to_inc_elemental', 0.0),

            # 5. 全局点伤池 (Flat Damage Pool) - [修复点]
            # 装备提供的 "flat_physical", "flat_fire" 等会汇总到这里
            "flat_physical": 0, "flat_fire": 0, "flat_cold": 0, "flat_lightning": 0,
            "flat_chaos": 0, "flat_poison": 0, "flat_dark": 0,

            # 6. 增伤池
            "inc_physical": 0.0, "inc_elemental": 0.0, "inc_all": 0.0, "more_damage": 1.0
        }

        self.apply_dynamic_modifier(talent_data)

    def apply_modifier(self, mod_data):
        self.modifiers.append(mod_data)

        if 'stats' in mod_data:
            for k, v in mod_data['stats'].items():
                self.stats[k] = self.stats.get(k, 0) + v

        if 'conversions' in mod_data:
            for conv in mod_data['conversions']:
                self.conversions.append(conv)

        if 'dynamic_stats' in mod_data:
            self.apply_dynamic_modifier(mod_data)

    def apply_dynamic_modifier(self, mod_data):
        if 'dynamic_stats' in mod_data:
            ctx = {
                "stats": self.stats,
                "max_hp": self.stats['max_hp'],
                "current_hp": self.stats['current_hp'],
                "missing_hp_pct": 1.0 - self.simulation_context['hp_percent']
            }
            for k, formula in mod_data['dynamic_stats'].items():
                try:
                    val = eval(str(formula), {}, ctx)
                    self.stats[k] = self.stats.get(k, 0) + val
                except: pass

    def calculate_skill_damage(self, skill_data):
        """
        严谨伤害管线 (The Damage Pipeline)
        Stage 1: Base (Global Flat + Skill Base)
        Stage 2: Conversion
        Stage 3: Additive (Inc)
        Stage 4: Multiplicative (More)
        Stage 5: Crit & DPS
        """
        damage_packet = {}
        skill_tags = set(skill_data.get('tags', []))
        base_explanations = []

        # ====================================================
        # Stage 1: 构建基础伤害池 (Base Construction)
        # ====================================================
        # 1.1 先把装备提供的 "Global Flat Damage" 倒进去
        # 比如戒指提供了 +10 flat_physical，这甚至能让法术附带物理伤
        for k, v in self.stats.items():
            if k.startswith("flat_") and v > 0:
                dtype = k.replace("flat_", "")
                damage_packet[dtype] = damage_packet.get(dtype, 0) + v
                if v > 0:
                    base_explanations.append(f"全局点伤({dtype}): {v}")

        # 1.2 叠加技能本身的伤害
        for comp in skill_data['damage_components']:
            dtype = comp['type']
            base_val = (comp['min'] + comp['max']) / 2

            explain_parts = [f"技能{base_val:.0f}"]

            # 武器系数 (Weapon Damage)
            if 'weapon_scale' in comp:
                w_dmg = self.stats['base_atk'] * comp['weapon_scale']
                base_val += w_dmg
                explain_parts.append(f"武器({self.stats['base_atk']}x{comp['weapon_scale']})")

            # 属性系数 (Stat Scaling)
            if 'scaling_source' in comp:
                attr = comp['scaling_source']
                attr_val = self.stats.get(attr, 0)
                s_dmg = attr_val * comp.get('scaling_coef', 1.0)
                base_val += s_dmg
                explain_parts.append(f"{attr}({attr_val}x{comp['scaling_coef']})")

            damage_packet[dtype] = damage_packet.get(dtype, 0) + base_val

            # 记录日志
            base_explanations.append(f"{dtype.title()}组件: {' + '.join(explain_parts)} = {base_val:.1f}")

        # ====================================================
        # Stage 2: 伤害转化 (Conversion)
        # ====================================================
        # 物理 -> 火 -> 混沌 (按优先级或顺序，这里简化为单次遍历)
        temp_packet = damage_packet.copy()
        for conv in self.conversions:
            src, dest, ratio = conv['from'], conv['to'], conv['ratio']
            if damage_packet.get(src, 0) > 0:
                amount = damage_packet[src] * ratio
                temp_packet[src] -= amount
                temp_packet[dest] = temp_packet.get(dest, 0) + amount
                # 这里可以加个log记录转化
        damage_packet = temp_packet

        # ====================================================
        # Stage 3 & 4: 增伤乘区 (Buckets)
        # ====================================================
        final_dmg = 0
        process_logs = []

        for dtype, value in damage_packet.items():
            if value <= 0: continue

            # --- Stage 3: Additive (Inc) ---
            # 基础 Inc = 全局Inc + 类型Inc (如 inc_fire)
            inc_sum = self.stats['inc_all'] + self.stats.get(f"inc_{dtype}", 0)

            # 元素通用 Inc
            if dtype in ['fire', 'cold', 'lightning']:
                inc_sum += self.stats.get('inc_elemental', 0)

            # Tag 匹配 (从装备里找 Tag 匹配的 Inc)
            matched_buffs = []
            for mod in self.modifiers:
                if 'stats' not in mod: continue
                for k, v in mod['stats'].items():
                    if k.startswith("inc_"):
                        tag = k.replace("inc_", "")
                        # 规则: 属性匹配 OR 技能Tag匹配
                        if tag == dtype or tag in skill_tags:
                            inc_sum += v
                            matched_buffs.append(f"{mod['name']}(+{v:.0%})")

            # --- Stage 4: Multiplicative (More) ---
            more_prod = self.stats['more_damage']
            more_prod *= (1 + self.stats.get(f"more_{dtype}", 0)) # 类型独立

            if dtype in ['fire', 'cold', 'lightning']:
                more_prod *= (1 + self.stats.get('more_elemental', 0))

            # 单项结算
            inc_mult = 1 + inc_sum
            type_dmg = value * inc_mult * more_prod
            final_dmg += type_dmg

            process_logs.append({
                "type": dtype,
                "base": value,
                "inc_sum": inc_sum,
                "inc_mult": inc_mult,
                "more_mult": more_prod,
                "final": type_dmg,
                "matched_buffs": matched_buffs
            })

        # ====================================================
        # Stage 5: 暴击与期望 (Crit & DPS)
        # ====================================================
        crit_rate = min(1.0, max(0.0, self.stats['crit_rate']))
        crit_dmg = self.stats['crit_dmg']
        avg_hit = final_dmg * (1 + (crit_rate * (crit_dmg - 1)))

        aps = max(0.1, self.stats['atk_spd'] / 100.0)
        dps = avg_hit * aps

        return {
            "DPS": dps,
            "Avg_Hit": avg_hit,
            "Packet": damage_packet,
            "Process": process_logs,
            "Base_Explain": base_explanations,
            "Crit_Info": {"rate": crit_rate, "dmg": crit_dmg, "aps": aps}
        }