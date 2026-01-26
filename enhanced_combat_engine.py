# -*- coding: utf-8 -*-
"""
增强的战斗引擎 (Enhanced Combat Engine)
基于现有engine.py扩展，集成五行八卦效果到战斗计算中
实现实时战斗数据记录和分析，添加详细的DPS报告和生存能力分析
"""

import math
import copy
import json
import hashlib
import random
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime

# 导入基础引擎和五行八卦引擎
from engine import DiabloEngine, SkillNode
from wuxing_engine import WuxingEngine, Stone


@dataclass
class CombatRecord:
    """战斗记录数据模型"""
    timestamp: datetime
    character_snapshot: Dict[str, Any]
    enemy_type: str
    duration: float
    result: str  # "win", "lose", "timeout"
    
    # 详细数据
    damage_dealt: float
    damage_taken: float
    skills_used: List[Dict[str, Any]] = field(default_factory=list)
    critical_moments: List[Dict[str, Any]] = field(default_factory=list)
    
    # 分析结果
    dps_analysis: Dict[str, float] = field(default_factory=dict)
    survivability_score: float = 0.0
    efficiency_rating: float = 0.0


@dataclass
class ElementalEffect:
    """五行元素效果"""
    element: str
    effect_type: str  # "damage", "resistance", "buff", "debuff"
    magnitude: float
    duration: float
    source: str


class EnhancedCombatEngine(DiabloEngine):
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
            return {
                "average_dps": 0.0, 
                "peak_dps": 0.0, 
                "sustained_dps": 0.0,
                "total_damage": total_damage,
                "fight_duration": duration
            }
        
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