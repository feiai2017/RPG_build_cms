import math
import copy
import json
import hashlib
import random
from typing import Dict, Any, List, Tuple, Optional


def _stable_hash(obj: Any) -> str:
    """稳定 hash：用于确定性校验（Run/Replay 是否一致）。"""
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]
    """增强的战斗引擎
    
    基于DiabloEngine扩展，集成五行八卦效果：
    - 实时战斗数据记录和分析
    - 详细的DPS报告和生存能力分析  
    - 五行八卦效果集成到战斗计算
    - 流派协同效果计算
    """
    
    def __init__(self, data_source: Dict[str, Any]):
        super().__init__(data_source)
        self.wuxing_engine = WuxingEngine()
        self.combat_records: List[CombatRecord] = []
        self.active_elemental_effects: List[ElementalEffect] = []
        self.bagua_configuration: Optional[Dict[str, Any]] = None
        self.cultivation_school: Optional[str] = None
        
        # 战斗分析数据
        self.damage_breakdown: Dict[str, float] = {}
        self.elemental_damage_log: List[Dict[str, Any]] = []
        self.survivability_events: List[Dict[str, Any]] = []
        
    def set_bagua_configuration(self, config: Dict[str, Any]) -> None:
        """设置八卦配置"""
        self.bagua_configuration = config
        
        # 验证配置
        is_valid, errors = self.wuxing_engine.validate_bagua_configuration(config)
        if not is_valid:
            print(f"警告：八卦配置存在问题: {errors}")
    
    def set_cultivation_school(self, school: str) -> None:
        """设置修真流派"""
        self.cultivation_school = school
    
    def calculate_elemental_effects(self) -> Dict[str, float]:
        """计算五行元素效果对战斗属性的影响"""
        if not self.bagua_configuration:
            return {}
        
        # 计算八卦配置的综合效果
        comprehensive_effects = self.wuxing_engine.calculate_comprehensive_effects(
            self.bagua_configuration
        )
        
        elemental_bonuses = {}
        
        # 全局协同效果
        global_synergy = comprehensive_effects.get("global_synergy", {})
        total_multiplier = global_synergy.get("total_multiplier", 1.0)
        
        # 应用到战斗属性
        elemental_bonuses["damage_multiplier"] = total_multiplier
        elemental_bonuses["generation_bonus"] = global_synergy.get("generation_bonus", 0.0)
        elemental_bonuses["destruction_penalty"] = global_synergy.get("destruction_penalty", 0.0)
        
        # 卦位效果
        trigram_effects = comprehensive_effects.get("trigram_effects", {})
        for trigram, effects in trigram_effects.items():
            final_mult = effects.get("final_multiplier", 1.0)
            trigram_name = self.wuxing_engine.trigrams[trigram]["name"]
            elemental_bonuses[f"{trigram_name}_multiplier"] = final_mult
        
        # 共鸣效果
        resonance_effects = comprehensive_effects.get("resonance_effects", {})
        resonance_mult = resonance_effects.get("resonance_multiplier", 1.0)
        elemental_bonuses["resonance_multiplier"] = resonance_mult
        
        # 稳定性加成
        stability_bonus = resonance_effects.get("stability_bonus", 0.0)
        elemental_bonuses["stability_bonus"] = stability_bonus
        
        return elemental_bonuses
    
    def apply_elemental_effects_to_stats(self, base_stats: Dict[str, float]) -> Dict[str, float]:
        """将五行效果应用到角色属性"""
        enhanced_stats = copy.deepcopy(base_stats)
        elemental_effects = self.calculate_elemental_effects()
        
        if not elemental_effects:
            return enhanced_stats
        
        # 应用伤害倍率
        damage_mult = elemental_effects.get("damage_multiplier", 1.0)
        for key in enhanced_stats:
            if "atk" in key or "damage" in key:
                enhanced_stats[key] *= damage_mult
        
        # 应用共鸣倍率
        resonance_mult = elemental_effects.get("resonance_multiplier", 1.0)
        enhanced_stats["crit_dmg"] = enhanced_stats.get("crit_dmg", 1.5) * resonance_mult
        
        # 应用稳定性加成（转化为减伤）
        stability_bonus = elemental_effects.get("stability_bonus", 0.0)
        if stability_bonus > 0:
            damage_reduction = min(0.3, stability_bonus * 0.01)  # 最多30%减伤
            enhanced_stats["damage_taken_mult"] = enhanced_stats.get("damage_taken_mult", 1.0) * (1.0 - damage_reduction)
        
        return enhanced_stats
    
    def build_hero_with_wuxing(self, model_data: Dict[str, Any], talent_data: Optional[Dict[str, Any]] = None):
        """构建角色，集成五行八卦效果"""
        # 先用基础方法构建角色
        self.build_hero(model_data, talent_data)
        
        # 应用五行八卦效果
        self.stats = self.apply_elemental_effects_to_stats(self.stats)
        
        # 记录五行效果到战斗日志
        elemental_effects = self.calculate_elemental_effects()
        if elemental_effects:
            self.elemental_damage_log.append({
                "timestamp": datetime.now(),
                "event": "wuxing_effects_applied",
                "effects": elemental_effects
            })
    
    def simulate_enhanced_fight(
        self,
        root_node: SkillNode,
        enemy_hp: float = 3000.0,
        enemy_dps: float = 20.0,
        enemy_type: str = "boss",
        max_time: float = 20.0,
        dt: float = 0.1,
        seed: int = 0,
        **kwargs
    ) -> Dict[str, Any]:
        """增强的战斗模拟，包含详细的数据记录和分析"""
        
        # 记录战斗开始时间
        fight_start = datetime.now()
        
        # 创建角色快照
        character_snapshot = {
            "stats": copy.deepcopy(self.stats),
            "bagua_config": copy.deepcopy(self.bagua_configuration),
            "cultivation_school": self.cultivation_school,
            "elemental_effects": self.calculate_elemental_effects()
        }
        
        # 重置战斗数据
        self.damage_breakdown = {}
        self.elemental_damage_log = []
        self.survivability_events = []
        
        # 执行基础战斗模拟
        base_result = self.simulate_mvp_fight(
            root_node, enemy_hp, enemy_dps, max_time, dt, seed, **kwargs
        )
        
        # 计算战斗统计
        fight_duration = base_result.get("time", 0.0)
        total_damage_dealt = self._calculate_total_damage_dealt(base_result)
        total_damage_taken = self._calculate_total_damage_taken(base_result)
        
        # 生成DPS分析报告
        dps_analysis = self._generate_dps_analysis(base_result, total_damage_dealt, fight_duration)
        
        # 计算生存能力评分
        survivability_score = self._calculate_survivability_score(base_result, total_damage_taken)
        
        # 计算效率评级
        efficiency_rating = self._calculate_efficiency_rating(dps_analysis, survivability_score, fight_duration)
        
        # 创建战斗记录
        combat_record = CombatRecord(
            timestamp=fight_start,
            character_snapshot=character_snapshot,
            enemy_type=enemy_type,
            duration=fight_duration,
            result=base_result.get("result", "unknown"),
            damage_dealt=total_damage_dealt,
            damage_taken=total_damage_taken,
            skills_used=self._extract_skills_used(base_result),
            critical_moments=self._identify_critical_moments(base_result),
            dps_analysis=dps_analysis,
            survivability_score=survivability_score,
            efficiency_rating=efficiency_rating
        )
        
        # 保存战斗记录
        self.combat_records.append(combat_record)
        
        # 增强结果数据
        enhanced_result = copy.deepcopy(base_result)
        enhanced_result.update({
            "combat_record": combat_record,
            "dps_analysis": dps_analysis,
            "survivability_analysis": {
                "score": survivability_score,
                "events": self.survivability_events
            },
            "elemental_effects_log": self.elemental_damage_log,
            "damage_breakdown": self.damage_breakdown,
            "efficiency_rating": efficiency_rating,
            "wuxing_contributions": self._analyze_wuxing_contributions()
        })
        
        return enhanced_result
    
    def _calculate_total_damage_dealt(self, fight_result: Dict[str, Any]) -> float:
        """计算总伤害输出"""
        timeline = fight_result.get("timeline", [])
        if not timeline:
            return 0.0
        
        initial_enemy_hp = timeline[0].get("enemy_hp", 0.0) if timeline else 0.0
        final_enemy_hp = timeline[-1].get("enemy_hp", 0.0) if timeline else 0.0
        
        return max(0.0, initial_enemy_hp - final_enemy_hp)
    
    def _calculate_total_damage_taken(self, fight_result: Dict[str, Any]) -> float:
        """计算总承受伤害"""
        timeline = fight_result.get("timeline", [])
        if not timeline:
            return 0.0
        
        initial_hero_hp = timeline[0].get("hero_hp", 0.0) if timeline else 0.0
        final_hero_hp = timeline[-1].get("hero_hp", 0.0) if timeline else 0.0
        
        return max(0.0, initial_hero_hp - final_hero_hp)
    
    def _generate_dps_analysis(self, fight_result: Dict[str, Any], total_damage: float, duration: float) -> Dict[str, float]:
        """生成DPS分析报告"""
        if duration <= 0:
            return {"average_dps": 0.0, "peak_dps": 0.0, "sustained_dps": 0.0}
        
        average_dps = total_damage / duration
        
        # 从日志中提取DPS信息
        logs = fight_result.get("logs", [])
        dps_values = []
        for log in logs:
            if isinstance(log.get("dps"), (int, float)):
                dps_values.append(float(log["dps"]))
        
        peak_dps = max(dps_values) if dps_values else average_dps
        sustained_dps = sum(dps_values) / len(dps_values) if dps_values else average_dps
        
        return {
            "average_dps": average_dps,
            "peak_dps": peak_dps,
            "sustained_dps": sustained_dps,
            "total_damage": total_damage,
            "fight_duration": duration
        }
    
    def _calculate_survivability_score(self, fight_result: Dict[str, Any], total_damage_taken: float) -> float:
        """计算生存能力评分（0-100）"""
        result = fight_result.get("result", "unknown")
        duration = fight_result.get("time", 0.0)
        
        # 基础分数
        base_score = 50.0
        
        # 结果加成
        if result == "WIN":
            base_score += 30.0
        elif result == "TIMEOUT":
            base_score += 10.0
        # LOSE 不加分
        
        # 持续时间加成
        if duration > 15.0:
            base_score += 15.0
        elif duration > 10.0:
            base_score += 10.0
        elif duration > 5.0:
            base_score += 5.0
        
        # 承受伤害惩罚
        max_hp = self.stats.get("max_hp", 500.0)
        if max_hp > 0:
            damage_ratio = total_damage_taken / max_hp
            if damage_ratio > 0.8:
                base_score -= 20.0
            elif damage_ratio > 0.5:
                base_score -= 10.0
        
        return max(0.0, min(100.0, base_score))
    
    def _calculate_efficiency_rating(self, dps_analysis: Dict[str, float], survivability_score: float, duration: float) -> float:
        """计算效率评级（0-100）"""
        # DPS效率（40%权重）
        average_dps = dps_analysis.get("average_dps", 0.0)
        dps_efficiency = min(100.0, (average_dps / 200.0) * 100.0)  # 假设200 DPS为满分
        
        # 生存效率（40%权重）
        survival_efficiency = survivability_score
        
        # 时间效率（20%权重）
        time_efficiency = max(0.0, min(100.0, (20.0 - duration) * 5.0))  # 20秒内完成为满分
        
        total_efficiency = (dps_efficiency * 0.4 + survival_efficiency * 0.4 + time_efficiency * 0.2)
        return round(total_efficiency, 1)
    
    def _extract_skills_used(self, fight_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取使用的技能信息"""
        logs = fight_result.get("logs", [])
        skills_used = []
        
        for log in logs:
            if isinstance(log, dict) and "skill" in log:
                skills_used.append({
                    "skill_name": log.get("skill", "unknown"),
                    "role": log.get("role", "unknown"),
                    "dps": log.get("dps", 0),
                    "info": log.get("info", "")
                })
        
        return skills_used
    
    def _identify_critical_moments(self, fight_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别战斗中的关键时刻"""
        timeline = fight_result.get("timeline", [])
        critical_moments = []
        
        for i, frame in enumerate(timeline):
            hero_hp = frame.get("hero_hp", 0)
            is_crit = frame.get("is_crit", False)
            time = frame.get("time", 0.0)
            
            # 低血量警告
            max_hp = self.stats.get("max_hp", 500.0)
            if hero_hp < max_hp * 0.3:
                critical_moments.append({
                    "time": time,
                    "type": "low_health",
                    "description": f"生命值降至{hero_hp}/{max_hp}",
                    "severity": "high"
                })
            
            # BOSS暴击
            if is_crit:
                critical_moments.append({
                    "time": time,
                    "type": "boss_crit",
                    "description": "BOSS释放暴击攻击",
                    "severity": "medium"
                })
        
        return critical_moments
    
    def _analyze_wuxing_contributions(self) -> Dict[str, Any]:
        """分析五行八卦对战斗的贡献"""
        if not self.bagua_configuration:
            return {"enabled": False}
        
        elemental_effects = self.calculate_elemental_effects()
        comprehensive_effects = self.wuxing_engine.calculate_comprehensive_effects(
            self.bagua_configuration
        )
        
        return {
            "enabled": True,
            "damage_multiplier": elemental_effects.get("damage_multiplier", 1.0),
            "resonance_type": comprehensive_effects.get("resonance_effects", {}).get("resonance_type", "none"),
            "active_circuits": comprehensive_effects.get("circuit_effects", {}).get("active_circuits", []),
            "element_distribution": comprehensive_effects.get("element_counts", {}),
            "validation_status": comprehensive_effects.get("is_valid_configuration", False)
        }
    
    def generate_combat_report(self, record: CombatRecord) -> str:
        """生成战斗报告"""
        report = []
        report.append("=" * 50)
        report.append("战斗报告")
        report.append("=" * 50)
        report.append(f"时间: {record.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"敌人类型: {record.enemy_type}")
        report.append(f"战斗结果: {record.result}")
        report.append(f"持续时间: {record.duration:.2f}秒")
        report.append("")
        
        report.append("伤害统计:")
        report.append(f"  总伤害输出: {record.damage_dealt:.0f}")
        report.append(f"  总承受伤害: {record.damage_taken:.0f}")
        report.append(f"  平均DPS: {record.dps_analysis.get('average_dps', 0):.1f}")
        report.append(f"  峰值DPS: {record.dps_analysis.get('peak_dps', 0):.1f}")
        report.append("")
        
        report.append("评分:")
        report.append(f"  生存能力: {record.survivability_score:.1f}/100")
        report.append(f"  效率评级: {record.efficiency_rating:.1f}/100")
        report.append("")
        
        if record.critical_moments:
            report.append("关键时刻:")
            for moment in record.critical_moments[:5]:  # 只显示前5个
                report.append(f"  [{moment['time']:.1f}s] {moment['description']}")
            report.append("")
        
        return "\n".join(report)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能总结"""
        if not self.combat_records:
            return {"total_fights": 0}
        
        total_fights = len(self.combat_records)
        wins = sum(1 for r in self.combat_records if r.result == "WIN")
        avg_duration = sum(r.duration for r in self.combat_records) / total_fights
        avg_dps = sum(r.dps_analysis.get('average_dps', 0) for r in self.combat_records) / total_fights
        avg_survivability = sum(r.survivability_score for r in self.combat_records) / total_fights
        avg_efficiency = sum(r.efficiency_rating for r in self.combat_records) / total_fights
        
        return {
            "total_fights": total_fights,
            "win_rate": (wins / total_fights) * 100,
            "average_duration": avg_duration,
            "average_dps": avg_dps,
            "average_survivability": avg_survivability,
            "average_efficiency": avg_efficiency,
            "latest_record": self.combat_records[-1] if self.combat_records else None
        }

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
        return "engine-2026-01-16"

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
            seed: int = 0,
            boss_crit_interval: float = 4.0,
            boss_crit_mult: float = 2.5,
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

        # 初始血量记录（用于画图百分比）
        init_enemy_hp = float(kwargs.get("init_enemy_hp", enemy_hp))

        time = 0.0
        timeline: List[Dict[str, Any]] = []
        combat_log: List[str] = [] # 文字战报

        rng = random.Random(int(seed))

        # --- BOSS 机制参数（由试炼用例配置）---
        boss_crit_interval = float(boss_crit_interval)
        boss_crit_mult = float(boss_crit_mult)
        last_crit_time = -boss_crit_interval # 确保第4秒触发

        # 保底初始化，防止极端情况下（比如 max_time=0）变量未定义
        logs: List[Dict[str, Any]] = []

        def _pack(result: str, reason: str, t_end: float) -> Dict[str, Any]:
            payload = {
                "result": result,
                "time": round(float(t_end), 2),
                "reason": reason,
                "seed": int(seed),
                "dt": float(dt),
                "boss_crit_interval": float(boss_crit_interval),
                "boss_crit_mult": float(boss_crit_mult),
                "timeline": timeline,
                "logs": logs,
                "combat_log": combat_log,
            }
            # result_hash：用关键字段 + timeline/log 的 hash 组合，确保 Run/Replay 稳定
            key_obj = {
                "result": payload["result"],
                "time": payload["time"],
                "reason": payload["reason"],
                "seed": payload["seed"],
                "dt": payload["dt"],
                "boss_crit_interval": payload["boss_crit_interval"],
                "boss_crit_mult": payload["boss_crit_mult"],
                "final_hero_hp": int(max(hero_hp, 0)),
                "final_enemy_hp": int(max(enemy_hp, 0)),
                "timeline_hash": _stable_hash(timeline),
                "logs_hash": _stable_hash(logs),
                "combat_log_hash": _stable_hash(combat_log),
            }
            payload["result_hash"] = _stable_hash(key_obj)
            return payload

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
                return _pack("LOSE", "hero_dead", time)
            if enemy_hp <= 0:
                combat_log.append(f"[{time:.1f}s] 🎉 击杀 BOSS！")
                return _pack("WIN", "enemy_dead", time)

            time += dt

        # 如果循环结束但没有返回，说明超时了
        combat_log.append(f"[{time:.1f}s] ⏳ 战斗超时，BOSS 狂暴灭团。")
        return _pack("TIMEOUT", "damage_insufficient", max_time)


def _stable_hash(obj: Any) -> str:
    """稳定 hash：用于确定性校验（Run/Replay 是否一致）。"""
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


# 保持原有的DiabloEngine类以确保向后兼容
# （EnhancedCombatEngine继承自DiabloEngine）