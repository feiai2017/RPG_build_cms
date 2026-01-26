# -*- coding: utf-8 -*-
"""
平衡性调整系统 (Balance Adjustment System)
进行最终的平衡性调整和bug修复
"""

import streamlit as st
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from unified_state_manager import get_state_manager
from wuxing_engine import WuxingEngine
from enhanced_combat_engine import EnhancedCombatEngine


@dataclass
class BalanceIssue:
    """平衡性问题数据类"""
    category: str  # "overpowered", "underpowered", "bug", "inconsistency"
    severity: str  # "critical", "major", "minor"
    description: str
    affected_components: List[str]
    suggested_fix: str
    priority: int  # 1-10, 10最高


class BalanceSystem:
    """平衡性调整系统"""
    
    def __init__(self):
        self.balance_config = self._load_balance_config()
        self.known_issues = self._initialize_known_issues()
        self.adjustment_history = []
    
    def _load_balance_config(self) -> Dict[str, Any]:
        """加载平衡性配置"""
        return {
            # 五行相生相克倍率
            "element_generation_bonus": 0.2,  # 相生加成20%
            "element_destruction_bonus": 0.5,  # 相克加成50%
            "element_conflict_penalty": 0.3,   # 被克惩罚30%
            
            # 流派平衡参数
            "school_balance": {
                "sword_cultivator": {"attack_mult": 1.2, "defense_mult": 0.9},
                "spell_cultivator": {"attack_mult": 1.1, "defense_mult": 0.8},
                "body_cultivator": {"attack_mult": 0.8, "defense_mult": 1.3},
                "pill_cultivator": {"attack_mult": 0.9, "defense_mult": 1.0},
                "formation_cultivator": {"attack_mult": 1.0, "defense_mult": 1.1}
            },
            
            # 战斗平衡参数
            "combat_balance": {
                "max_combat_time": 60.0,  # 最大战斗时间
                "dps_target_range": (100, 300),  # 目标DPS范围
                "survivability_target": 0.7,  # 目标生存率
                "crit_rate_cap": 0.8,  # 暴击率上限
                "crit_damage_cap": 3.0   # 暴击伤害上限
            },
            
            # 掉落平衡参数
            "loot_balance": {
                "rarity_weights": {
                    "common": 0.6,
                    "rare": 0.25,
                    "epic": 0.12,
                    "legendary": 0.03
                },
                "school_affinity_bonus": 0.5,  # 流派匹配掉落加成
                "level_range_tolerance": 5     # 等级范围容忍度
            }
        }
    
    def _initialize_known_issues(self) -> List[BalanceIssue]:
        """初始化已知的平衡性问题"""
        return [
            BalanceIssue(
                category="overpowered",
                severity="major",
                description="法修流派在高等级时伤害过高",
                affected_components=["spell_cultivator", "combat_engine"],
                suggested_fix="降低法修的法术强度倍率从1.5到1.3",
                priority=8
            ),
            BalanceIssue(
                category="underpowered",
                severity="minor",
                description="体修流派的输出能力偏低",
                affected_components=["body_cultivator", "combat_engine"],
                suggested_fix="增加体修的基础攻击力倍率",
                priority=5
            ),
            BalanceIssue(
                category="bug",
                severity="critical",
                description="五行相生链在特定配置下计算错误",
                affected_components=["wuxing_engine"],
                suggested_fix="修复相生链长度计算算法",
                priority=10
            ),
            BalanceIssue(
                category="inconsistency",
                severity="major",
                description="不同模块间的属性计算存在差异",
                affected_components=["state_manager", "combat_engine"],
                suggested_fix="统一属性计算接口和标准",
                priority=7
            )
        ]
    
    def analyze_current_balance(self) -> Dict[str, Any]:
        """分析当前系统的平衡性"""
        state_manager = get_state_manager()
        wuxing_engine = WuxingEngine()
        
        analysis = {
            "overall_score": 0.0,
            "issues_found": [],
            "recommendations": [],
            "detailed_analysis": {}
        }
        
        # 分析五行平衡性
        element_analysis = self._analyze_element_balance(wuxing_engine)
        analysis["detailed_analysis"]["elements"] = element_analysis
        
        # 分析流派平衡性
        school_analysis = self._analyze_school_balance(state_manager)
        analysis["detailed_analysis"]["schools"] = school_analysis
        
        # 分析战斗平衡性
        combat_analysis = self._analyze_combat_balance(state_manager)
        analysis["detailed_analysis"]["combat"] = combat_analysis
        
        # 计算总体评分
        scores = [
            element_analysis.get("balance_score", 0),
            school_analysis.get("balance_score", 0),
            combat_analysis.get("balance_score", 0)
        ]
        analysis["overall_score"] = sum(scores) / len(scores)
        
        # 生成建议
        analysis["recommendations"] = self._generate_balance_recommendations(analysis)
        
        return analysis
    
    def _analyze_element_balance(self, wuxing_engine: WuxingEngine) -> Dict[str, Any]:
        """分析五行平衡性"""
        analysis = {
            "balance_score": 0.8,  # 基础评分
            "issues": [],
            "strengths": []
        }
        
        # 检查相生相克倍率是否合理
        gen_bonus = self.balance_config["element_generation_bonus"]
        dest_bonus = self.balance_config["element_destruction_bonus"]
        
        if gen_bonus < 0.1 or gen_bonus > 0.5:
            analysis["issues"].append("相生加成倍率可能不合理")
            analysis["balance_score"] -= 0.1
        
        if dest_bonus < 0.3 or dest_bonus > 0.8:
            analysis["issues"].append("相克加成倍率可能过高或过低")
            analysis["balance_score"] -= 0.1
        
        # 检查五行元素的使用频率
        element_usage = self._get_element_usage_stats()
        usage_variance = self._calculate_variance(list(element_usage.values()))
        
        if usage_variance > 0.2:
            analysis["issues"].append("五行元素使用不平衡")
            analysis["balance_score"] -= 0.2
        else:
            analysis["strengths"].append("五行元素使用相对平衡")
        
        return analysis
    
    def _analyze_school_balance(self, state_manager) -> Dict[str, Any]:
        """分析流派平衡性"""
        analysis = {
            "balance_score": 0.7,
            "issues": [],
            "strengths": []
        }
        
        school_config = self.balance_config["school_balance"]
        
        # 检查各流派的倍率分布
        attack_mults = [config["attack_mult"] for config in school_config.values()]
        defense_mults = [config["defense_mult"] for config in school_config.values()]
        
        attack_variance = self._calculate_variance(attack_mults)
        defense_variance = self._calculate_variance(defense_mults)
        
        if attack_variance > 0.3:
            analysis["issues"].append("流派攻击力差异过大")
            analysis["balance_score"] -= 0.15
        
        if defense_variance > 0.3:
            analysis["issues"].append("流派防御力差异过大")
            analysis["balance_score"] -= 0.15
        
        # 检查是否有明显的强势或弱势流派
        total_power = [(a + d) / 2 for a, d in zip(attack_mults, defense_mults)]
        max_power = max(total_power)
        min_power = min(total_power)
        
        if max_power - min_power > 0.4:
            analysis["issues"].append("存在明显的强势或弱势流派")
            analysis["balance_score"] -= 0.2
        
        return analysis
    
    def _analyze_combat_balance(self, state_manager) -> Dict[str, Any]:
        """分析战斗平衡性"""
        analysis = {
            "balance_score": 0.75,
            "issues": [],
            "strengths": []
        }
        
        combat_config = self.balance_config["combat_balance"]
        
        # 模拟一些战斗来分析平衡性
        try:
            test_results = self._run_balance_test_combats()
            
            # 分析DPS分布
            dps_values = [result["dps"] for result in test_results]
            target_min, target_max = combat_config["dps_target_range"]
            
            out_of_range = sum(1 for dps in dps_values 
                             if dps < target_min or dps > target_max)
            
            if out_of_range > len(dps_values) * 0.3:
                analysis["issues"].append("DPS分布超出目标范围")
                analysis["balance_score"] -= 0.2
            
            # 分析生存率
            survival_rates = [result["survival_rate"] for result in test_results]
            avg_survival = sum(survival_rates) / len(survival_rates)
            target_survival = combat_config["survivability_target"]
            
            if abs(avg_survival - target_survival) > 0.2:
                analysis["issues"].append("平均生存率偏离目标值")
                analysis["balance_score"] -= 0.15
            
        except Exception as e:
            analysis["issues"].append(f"战斗平衡性测试失败: {str(e)}")
            analysis["balance_score"] -= 0.3
        
        return analysis
    
    def _run_balance_test_combats(self) -> List[Dict[str, Any]]:
        """运行平衡性测试战斗"""
        # 这里应该运行一系列标准化的战斗测试
        # 返回模拟结果用于分析
        return [
            {"dps": 150, "survival_rate": 0.8, "combat_time": 30},
            {"dps": 200, "survival_rate": 0.7, "combat_time": 25},
            {"dps": 180, "survival_rate": 0.75, "combat_time": 28}
        ]
    
    def _calculate_variance(self, values: List[float]) -> float:
        """计算方差"""
        if not values:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5  # 返回标准差
    
    def _get_element_usage_stats(self) -> Dict[str, float]:
        """获取五行元素使用统计"""
        # 这里应该从实际使用数据中统计
        # 现在返回模拟数据
        return {
            "木": 0.22,
            "火": 0.18,
            "土": 0.20,
            "金": 0.19,
            "水": 0.21
        }
    
    def _generate_balance_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """生成平衡性建议"""
        recommendations = []
        
        if analysis["overall_score"] < 0.6:
            recommendations.append("系统整体平衡性需要重大调整")
        elif analysis["overall_score"] < 0.8:
            recommendations.append("系统平衡性需要适度调整")
        
        # 基于具体分析结果生成建议
        for category, details in analysis["detailed_analysis"].items():
            if details["balance_score"] < 0.7:
                recommendations.append(f"{category}模块需要平衡性调整")
            
            for issue in details.get("issues", []):
                recommendations.append(f"建议修复: {issue}")
        
        return recommendations
    
    def apply_balance_adjustments(self, adjustments: List[Dict[str, Any]]) -> bool:
        """应用平衡性调整"""
        try:
            for adjustment in adjustments:
                self._apply_single_adjustment(adjustment)
                self.adjustment_history.append(adjustment)
            
            return True
        except Exception as e:
            st.error(f"应用平衡性调整失败: {str(e)}")
            return False
    
    def _apply_single_adjustment(self, adjustment: Dict[str, Any]):
        """应用单个平衡性调整"""
        category = adjustment.get("category")
        target = adjustment.get("target")
        value = adjustment.get("value")
        
        if category == "element_balance":
            self.balance_config[target] = value
        elif category == "school_balance":
            school = adjustment.get("school")
            self.balance_config["school_balance"][school][target] = value
        elif category == "combat_balance":
            self.balance_config["combat_balance"][target] = value
    
    def get_balance_report(self) -> Dict[str, Any]:
        """获取平衡性报告"""
        analysis = self.analyze_current_balance()
        
        return {
            "timestamp": st.session_state.get("current_time", "unknown"),
            "overall_score": analysis["overall_score"],
            "grade": self._score_to_grade(analysis["overall_score"]),
            "critical_issues": [
                issue for issue in self.known_issues 
                if issue.severity == "critical"
            ],
            "recommendations": analysis["recommendations"],
            "detailed_analysis": analysis["detailed_analysis"]
        }
    
    def _score_to_grade(self, score: float) -> str:
        """将评分转换为等级"""
        if score >= 0.9:
            return "A+"
        elif score >= 0.8:
            return "A"
        elif score >= 0.7:
            return "B"
        elif score >= 0.6:
            return "C"
        else:
            return "D"
    
    def render_balance_interface(self):
        """渲染平衡性调整界面"""
        st.title("⚖️ 系统平衡性调整")
        st.caption("分析和调整系统的平衡性，修复已知问题")
        
        # 平衡性分析
        with st.container(border=True):
            st.subheader("📊 平衡性分析")
            
            if st.button("🔍 分析当前平衡性", use_container_width=True):
                with st.spinner("正在分析系统平衡性..."):
                    report = self.get_balance_report()
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("总体评分", f"{report['overall_score']:.2f}")
                
                with col2:
                    st.metric("平衡等级", report["grade"])
                
                with col3:
                    critical_count = len(report["critical_issues"])
                    st.metric("严重问题", critical_count)
                
                # 显示详细分析
                if report["detailed_analysis"]:
                    st.subheader("详细分析结果")
                    
                    for category, details in report["detailed_analysis"].items():
                        with st.expander(f"📈 {category.title()} 模块"):
                            st.metric("模块评分", f"{details['balance_score']:.2f}")
                            
                            if details.get("issues"):
                                st.write("**发现的问题：**")
                                for issue in details["issues"]:
                                    st.error(f"• {issue}")
                            
                            if details.get("strengths"):
                                st.write("**优势方面：**")
                                for strength in details["strengths"]:
                                    st.success(f"• {strength}")
                
                # 显示建议
                if report["recommendations"]:
                    st.subheader("🔧 改进建议")
                    for rec in report["recommendations"]:
                        st.info(f"💡 {rec}")
        
        # 已知问题管理
        with st.container(border=True):
            st.subheader("🐛 已知问题管理")
            
            # 按严重程度分组显示
            critical_issues = [i for i in self.known_issues if i.severity == "critical"]
            major_issues = [i for i in self.known_issues if i.severity == "major"]
            minor_issues = [i for i in self.known_issues if i.severity == "minor"]
            
            if critical_issues:
                st.write("**🔴 严重问题**")
                for issue in critical_issues:
                    with st.expander(f"P{issue.priority}: {issue.description}"):
                        st.write(f"**类别**: {issue.category}")
                        st.write(f"**影响组件**: {', '.join(issue.affected_components)}")
                        st.write(f"**建议修复**: {issue.suggested_fix}")
            
            if major_issues:
                st.write("**🟡 重要问题**")
                for issue in major_issues:
                    with st.expander(f"P{issue.priority}: {issue.description}"):
                        st.write(f"**类别**: {issue.category}")
                        st.write(f"**影响组件**: {', '.join(issue.affected_components)}")
                        st.write(f"**建议修复**: {issue.suggested_fix}")
            
            if minor_issues:
                st.write("**🟢 次要问题**")
                for issue in minor_issues:
                    with st.expander(f"P{issue.priority}: {issue.description}"):
                        st.write(f"**类别**: {issue.category}")
                        st.write(f"**影响组件**: {', '.join(issue.affected_components)}")
                        st.write(f"**建议修复**: {issue.suggested_fix}")
        
        # 快速修复
        with st.container(border=True):
            st.subheader("🚀 快速修复")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔧 应用推荐修复", use_container_width=True):
                    # 应用一些预定义的修复
                    adjustments = [
                        {
                            "category": "element_balance",
                            "target": "element_generation_bonus",
                            "value": 0.25,
                            "description": "调整相生加成为25%"
                        }
                    ]
                    
                    if self.apply_balance_adjustments(adjustments):
                        st.success("✅ 推荐修复已应用")
                    else:
                        st.error("❌ 修复应用失败")
            
            with col2:
                if st.button("🔄 重置平衡配置", use_container_width=True):
                    self.balance_config = self._load_balance_config()
                    st.success("✅ 平衡配置已重置")


# 全局平衡系统实例
_global_balance_system: Optional[BalanceSystem] = None


def get_balance_system() -> BalanceSystem:
    """获取全局平衡系统实例"""
    global _global_balance_system
    
    if _global_balance_system is None:
        _global_balance_system = BalanceSystem()
    
    return _global_balance_system