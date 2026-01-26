# -*- coding: utf-8 -*-
"""
内置帮助和教程系统 (Built-in Help and Tutorial System)
完善内置帮助和教程系统，提供用户友好的指导
"""

import streamlit as st
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class TutorialStep:
    """教程步骤数据类"""
    title: str
    content: str
    image_url: Optional[str] = None
    action_required: bool = False
    validation_func: Optional[callable] = None


@dataclass
class HelpTopic:
    """帮助主题数据类"""
    title: str
    content: str
    category: str
    keywords: List[str]
    related_topics: List[str] = None


class HelpSystem:
    """内置帮助系统"""
    
    def __init__(self):
        self.help_topics = self._initialize_help_topics()
        self.tutorials = self._initialize_tutorials()
        self.faq = self._initialize_faq()
    
    def _initialize_help_topics(self) -> Dict[str, HelpTopic]:
        """初始化帮助主题"""
        topics = {}
        
        # 基础概念
        topics["wuxing_basics"] = HelpTopic(
            title="五行基础理论",
            content="""
            五行学说是中国古代的一种物质观，认为宇宙万物由木、火、土、金、水五种基本元素构成。
            
            **五行相生关系：**
            - 木生火：木燃烧产生火
            - 火生土：火燃烧后产生灰土
            - 土生金：土中蕴含金属
            - 金生水：金属表面凝结水珠
            - 水生木：水滋养植物生长
            
            **五行相克关系：**
            - 木克土：植物根系破坏土壤
            - 土克水：土壤吸收水分
            - 水克火：水能灭火
            - 火克金：火能熔化金属
            - 金克木：金属工具能砍伐树木
            """,
            category="基础理论",
            keywords=["五行", "相生", "相克", "木火土金水"]
        )
        
        topics["bagua_basics"] = HelpTopic(
            title="八卦基础知识",
            content="""
            八卦是中国古代的一套符号系统，由三条线组成，分为阴爻（--）和阳爻（—）。
            
            **后天八卦方位：**
            - 乾（☰）：西北，代表天、父亲
            - 兑（☱）：西，代表泽、少女
            - 离（☲）：南，代表火、中女
            - 震（☳）：东，代表雷、长男
            - 巽（☴）：东南，代表风、长女
            - 坎（☵）：北，代表水、中男
            - 艮（☶）：东北，代表山、少男
            - 坤（☷）：西南，代表地、母亲
            
            **八卦与五行对应：**
            - 乾、兑属金
            - 离属火
            - 震、巽属木
            - 坎属水
            - 艮、坤属土
            """,
            category="基础理论",
            keywords=["八卦", "乾兑离震", "巽坎艮坤", "方位"]
        )
        
        topics["bagua_calculation"] = HelpTopic(
            title="八卦加成计算详解",
            content="""
            八卦系统包含多层次的加成计算机制，理解这些能帮你最大化角色实力。
            
            **主要加成类型：**
            
            1. **五行相生相克基础加成**
               - 相生关系：每对+10%（木→火→土→金→水→木）
               - 相克关系：每对-10%（木克土，土克水，水克火，火克金，金克木）
            
            2. **卦域相生相克加成**
               - 灵石生卦位：+50%（如木灵石放在离火位）
               - 卦位生灵石：+30%（如离火位放金灵石）
               - 灵石克卦位：-20%（如水灵石放在离火位）
               - 同元素：+10%（如火灵石放在离火位）
            
            3. **卦内链路加成（内→中→外）**
               - 相生链：每段+15%
               - 相克链：每段-10%
            
            4. **环形链路加成（八卦环形）**
               - 环形相生：每段+20%
               - 环形相克：每段-15%
            
            5. **五行共鸣与平衡**
               - 平衡加成：五行接近平衡时+20%倍率
               - 共鸣加成：某元素≥3个时，1.0+(数量-2)×10%
               - 偏科弱点：过度偏向时受到惩罚
            
            6. **主灵根亲和加成**
               - 主灵根元素：+20%
               - 主灵根所生：+5%
               - 克主灵根：-5%
            
            7. **逻辑灵石特殊效果**
               - 逻辑·强化：该卦位所有五行灵石+15%
               - 逻辑·平衡：相克惩罚减半
               - 逻辑·共鸣：同元素共鸣效果+50%
            
            8. **真言核心(BIOS)系统级效果**
               - 五行逆转：火↔水、木↔金互换
               - 元素增幅：指定元素+25%
               - 平衡调节：相生+20%，相克-20%
            
            **完整伤害计算公式：**
            ```
            最终伤害 = 基础伤害 
                    × 主灵根加成 
                    × 卦域效果 
                    × 全局协同效果 
                    × 共鸣效果 
                    × 链路效果 
                    × BIOS效果
            ```
            
            **计算示例：**
            主灵根木，离火位放置木→火→土
            - 基础相生：木→火+10%，火→土+10%
            - 卦域加成：木生火+50%
            - 链路加成：木→火+15%，火→土+15%
            - 主灵根：木+20%，火+5%，土0%
            - 总倍率：约2.35倍
            
            **详细机制文档：**
            更多详细的计算机制和公式请参考项目根目录的 WUXING_SYSTEM_MECHANICS.md 文档。
            """,
            category="进阶指南",
            keywords=["八卦", "加成", "计算", "倍率", "相生相克", "机制", "公式"]
        )
        
        topics["wuxing_detailed_mechanics"] = HelpTopic(
            title="五行系统详细机制",
            content="""
            **五行系统完整机制解析**
            
            五行系统是整个RPG数值验证工具的核心，通过多个层次影响角色属性。
            
            **1. 主灵根影响机制**
            主灵根是角色的基础五行倾向，影响所有五行相关计算：
            - 同属性灵石：+20% 效果加成
            - 相生属性灵石：+5% 效果加成（如木主灵根对火系灵石）
            - 被克属性：-5% 效果减成（如木主灵根被金系灵石克制）
            
            **2. 灵石放置规则 (P1更新)**
            每个卦位有4个槽位：
            - 第1槽（逻辑位）：逻辑灵石，提供增幅效果（卦位默认激活）
            - 第2槽（内环）：五行灵石，参与环形链路计算
            - 第3槽（中环）：五行灵石，形成内→中链路
            - 第4槽（外环）：五行灵石，形成中→外链路
            
            **3. 卦域相生相克效果**
            灵石与卦位的五行关系产生不同效果：
            - 灵石生卦位：+50%（如木灵石放在离火位）
            - 卦位生灵石：+30%（如离火位放土灵石）
            - 灵石克卦位：-20%（如水灵石放在离火位）
            - 卦位克灵石：-15%（如坎水位放火灵石）
            - 同元素共鸣：+10%（如火灵石放在离火位）
            
            **4. 逻辑灵石特殊作用**
            逻辑灵石不参与五行相生相克，但提供特殊效果：
            - 逻辑·强化：该卦位所有五行灵石效果+15%
            - 逻辑·平衡：该卦位相克惩罚减半
            - 逻辑·共鸣：该卦位同元素共鸣效果+50%
            
            **5. 真言核心(BIOS)系统**
            放置在中央阵眼，提供系统级增强：
            - 五行逆转：将火↔水、木↔金互换，土不变
            - 元素增幅：指定元素的所有效果+25%
            - 平衡调节：所有相生效果+20%，相克惩罚-20%
            
            **6. 五行循环机制**
            完整的相生链可获得额外加成：
            - 五元素完整循环：+50%
            - 四元素链：+30%
            - 三元素链：+15%
            
            **7. 伤害计算完整公式**
            ```
            最终伤害 = 基础伤害 
                    × 主灵根加成(1.0-1.2) 
                    × 卦域效果(0.8-1.5) 
                    × 全局协同效果(0.5-2.0) 
                    × 共鸣效果(1.0-1.5) 
                    × 链路效果(0.8-1.4) 
                    × BIOS效果(1.0-1.25)
            ```
            
            **实战应用示例**
            火系爆发流配置：
            - 主灵根：木系（木生火+5%）
            - 离卦：放置木系灵石（木生火+50%）
            - 核心BIOS：元素增幅(火)（+25%）
            - 预期倍率：1.05 × 1.50 × 1.25 ≈ 1.97倍
            
            **详细文档参考**
            完整的计算公式和更多示例请查看项目根目录的 WUXING_SYSTEM_MECHANICS.md 文档。
            """,
            category="进阶指南",
            keywords=["五行", "机制", "详细", "计算", "公式", "主灵根", "逻辑灵石", "BIOS", "循环"]
        )
        
        topics["bagua_quick_start"] = HelpTopic(
            title="八卦系统快速入门",
            content="""
            **5分钟上手八卦系统**
            
            **第一步：了解基础布局**
            ```
            艮(土)  坎(水)  乾(金)
            震(木)  阵眼   兑(金)  
            巽(木)  离(火)  坤(土)
            ```
            
            **第二步：理解槽位规则**
            - 槽位1：🧩 逻辑灵石专用
            - 槽位2：💎 内环位（参与环形效果）
            - 槽位3：💎 中环位（参与链路效果）
            - 槽位4：💎 外环位（参与链路效果）
            
            **第三步：掌握五行关系**
            - 相生（好）：木→火→土→金→水→木
            - 相克（坏）：木克土，土克水，水克火，火克金，金克木
            
            **三种简单策略：**
            
            1. **新手平衡流**：每种元素2-3个，追求平衡
            2. **主灵根强化流**：专精主灵根元素，获得共鸣
            3. **相生链路流**：构建完整相生链，多重加成
            
            **快速判断配置好坏：**
            - 🟢 好配置：总倍率>1.5，相生多于相克
            - 🔴 差配置：总倍率<1.2，大量相克冲突
            - 🟡 需调整：总倍率1.2-1.5，可进一步优化
            
            **操作技巧：**
            1. 先选灵石，再点槽位放置
            2. 观察右侧衍算结果实时变化
            3. 不满意可重新放置调整
            4. 配置完成后进行战斗测试验证
            """,
            category="新手指南",
            keywords=["八卦", "入门", "快速", "新手", "操作"]
        )
        
        return topics
    
    def _initialize_tutorials(self) -> Dict[str, List[TutorialStep]]:
        """初始化教程"""
        tutorials = {}
        
        # 新手入门教程
        tutorials["beginner_guide"] = [
            TutorialStep(
                title="欢迎使用统一RPG系统",
                content="""
                欢迎来到统一RPG数值验证系统！这是一个基于真正道教五行八卦理论的修真游戏工具。
                
                本教程将引导您：
                1. 了解系统基本界面
                2. 创建和配置角色
                3. 学习五行八卦配置
                4. 进行战斗模拟测试
                5. 体验刷宝和流派系统
                
                点击"下一步"开始您的修真之旅！
                """
            ),
            TutorialStep(
                title="系统界面导览",
                content="""
                系统主要包含以下模块：
                
                🏠 **系统概览**：查看角色信息和系统状态
                ☯️ **五行八卦盘**：配置灵石和八卦阵法
                ⚔️ **战斗模拟**：测试BD配置的实战效果
                🎓 **流派管理**：选择和发展修真流派
                💎 **刷宝系统**：挑战敌人获取装备
                📊 **BD分析**：深度分析配置优化建议
                ⚙️ **系统设置**：管理角色和数据
                
                您可以通过左侧导航栏在不同模块间切换。
                """
            )
        ]
        
        return tutorials
    
    def _initialize_faq(self) -> List[Dict[str, str]]:
        """初始化常见问题"""
        return [
            {
                "question": "八卦系统的加成是如何计算的？",
                "answer": "八卦系统有多层加成：1）五行相生相克基础加成（相生+10%，相克-10%）；2）卦域加成（灵石与卦位元素关系，最高+50%）；3）链路加成（卦内和环形链路，最高+20%）；4）共鸣加成（元素数量≥3时获得倍率加成）；5）主灵根亲和（主灵根元素+20%）。这些加成会叠加计算。"
            },
            {
                "question": "主灵根的选择对系统有什么具体影响？",
                "answer": "主灵根是角色的核心五行属性，影响所有五行计算：1）同属性灵石获得+20%效果加成；2）相生属性灵石获得+5%加成（如木主灵根对火系灵石）；3）被克属性受到-5%减成（如木主灵根被金系灵石克制）；4）其他属性无加成。选择时要考虑你的主要灵石类型和战术风格。"
            },
            {
                "question": "灵石在不同位置放置有什么区别？",
                "answer": "每个卦位有4个槽位，作用不同：1）第1槽（逻辑位）：放置逻辑灵石提供增幅效果，卦位默认激活无需逻辑灵石；2）第2槽（内环）：参与八卦环形链路计算；3）第3槽（中环）：与内环形成内→中链路；4）第4槽（外环）：与中环形成中→外链路。链路中的相生关系会获得加成。"
            },
            {
                "question": "逻辑灵石具体有什么作用？(P1更新)",
                "answer": "逻辑灵石从'激活开关'改为'增幅器'：1）放大器：卦域效果+8%，链路上限+5%；2）路由器：链路上限+10%，支持跨卦连接；3）主动化：卦域效果+15%，触发式增强。卦位默认激活，逻辑灵石提供质变玩法而非门票税。"
            },
            {
                "question": "真言核心(BIOS)系统是如何工作的？",
                "answer": "真言核心放置在中央阵眼，提供系统级增强：1）五行逆转：将火↔水、木↔金互换，土不变，可以改变不利的五行关系；2）元素增幅：指定元素的所有效果+25%；3）平衡调节：所有相生效果+20%，相克惩罚-20%。境界越高可用的核心槽位越多（炼气1个，金丹2个，化神3个）。"
            },
            {
                "question": "五行循环是怎么形成的？有什么好处？",
                "answer": "五行循环是指按照木→火→土→金→水→木的顺序形成完整的相生链。好处：1）五元素完整循环获得+50%额外加成；2）四元素链获得+30%加成；3）三元素链获得+15%加成。要形成循环需要确保五行元素齐全，避免相克关系打断链路，合理安排灵石位置。"
            },
            {
                "question": "伤害是如何具体计算的？",
                "answer": "完整的伤害计算公式：最终伤害 = 基础伤害 × 主灵根加成(1.0-1.2) × 卦域效果(0.8-1.5) × 全局协同效果(0.5-2.0) × 共鸣效果(1.0-1.5) × 链路效果(0.8-1.4) × BIOS效果(1.0-1.25)。每个系数都有其计算规则，最终可能达到数倍的伤害提升。"
            },
            {
                "question": "什么是相生链？如何形成？",
                "answer": "相生链是指按照五行相生关系（木→火→土→金→水→木）连续放置的灵石。可以在卦内形成（内→中→外环），也可以在八卦环形中形成。相生链会获得15-20%的倍率加成，链越长加成越高。"
            },
            {
                "question": "为什么我的配置显示'配置无效'？",
                "answer": "可能的原因：1）灵石放置位置错误（逻辑灵石放错位置）；2）超出境界带宽限制；3）存在严重的相克冲突；4）八卦方位配置错误。请检查右侧衍算结果中的错误提示，并根据建议调整。"
            },
            {
                "question": "新手应该如何配置八卦？",
                "answer": "新手推荐平衡流配置：1）每种五行元素放置2-3个灵石；2）避免明显的相克组合；3）优先在对应元素的卦位放置灵石（如火灵石放离火位）；4）先填满内环位，再考虑中外环；5）观察右侧衍算结果，总倍率>1.5就是不错的配置。"
            },
            {
                "question": "什么是卦域相生相克？",
                "answer": "每个卦位都有固定的五行属性（如离火、坎水等）。当你在卦位放置灵石时，会产生卦域效果：灵石生卦位+50%（如木灵石放离火位），卦位生灵石+30%，灵石克卦位-20%，同元素+10%。这是获得高倍率的重要机制。"
            },
            {
                "question": "如何激活卦脉导通？",
                "answer": "卦脉导通需要特定的三连卦段都有内环位灵石，且三个元素间不能有强相克关系。四个导通卦段是：离→坤→兑、兑→乾→坎、坎→艮→震、震→巽→离。每个导通卦段提供+8点基础属性加成。"
            },
            {
                "question": "战斗模拟的结果如何理解？",
                "answer": "战斗结果包含DPS（每秒伤害）、生存能力评分、效率评级等。DPS越高输出越强，生存评分越高越不容易死亡，效率评级综合考虑输出和生存。还会显示战斗过程中的关键数据和优化建议。"
            },
            {
                "question": "如何保存和分享我的配置？",
                "answer": "系统会自动保存你的配置。你也可以在系统设置中使用'导出配置'功能生成配置文件，然后分享给其他玩家。其他玩家可以使用'导入配置'功能加载你的配置。还可以使用配置快照功能保存多个不同的配置方案。"
            },
            {
                "question": "火/水主灵根是否处于劣势？(P1-2更新)",
                "answer": "P1-2更新解决了火/水主灵根的结构性劣势。传统八卦中木/金/土各有2个卦位，而火/水只有1个。现在通过中宫辅灵石系统，火/水主灵根可以在中宫放置对应的辅灵石，获得额外节点参与同元素共鸣和循环链计算，并获得+8%共鸣加成，实现公平补位。"
            },
            {
                "question": "P1级别改进包含哪些内容？",
                "answer": "P1级别改进主要包含两个方面：1）逻辑灵石从'激活开关'改为'增幅器'，卦位默认激活，逻辑灵石提供放大器/路由器/主动化三类专业增强；2）中宫辅灵石系统，为火/水主灵根提供公平补位，通过中宫额外节点参与计算。这些改进消除了'门票税'和结构性不平衡问题。"
            }
        ]
    
    def search_help(self, query: str) -> List[HelpTopic]:
        """搜索帮助内容"""
        query_lower = query.lower()
        results = []
        
        for topic in self.help_topics.values():
            # 搜索标题、内容和关键词
            if (query_lower in topic.title.lower() or 
                query_lower in topic.content.lower() or 
                any(query_lower in keyword.lower() for keyword in topic.keywords)):
                results.append(topic)
        
        return results
    
    def get_topic(self, topic_id: str) -> Optional[HelpTopic]:
        """获取特定帮助主题"""
        return self.help_topics.get(topic_id)
    
    def get_tutorial(self, tutorial_id: str) -> Optional[List[TutorialStep]]:
        """获取教程"""
        return self.tutorials.get(tutorial_id)
    
    def render_help_interface(self):
        """渲染帮助界面"""
        st.title("📚 帮助中心")
        st.caption("获取系统使用指导和解答常见问题")
        
        # 搜索框
        search_query = st.text_input("🔍 搜索帮助内容", placeholder="输入关键词搜索...")
        
        if search_query:
            results = self.search_help(search_query)
            if results:
                st.subheader(f"搜索结果 ({len(results)} 条)")
                for topic in results:
                    with st.expander(f"📖 {topic.title}"):
                        st.markdown(topic.content)
                        st.caption(f"分类: {topic.category} | 关键词: {', '.join(topic.keywords)}")
            else:
                st.info("未找到相关内容，请尝试其他关键词")
        
        # 帮助分类
        st.subheader("📂 帮助分类")
        
        categories = {}
        for topic in self.help_topics.values():
            if topic.category not in categories:
                categories[topic.category] = []
            categories[topic.category].append(topic)
        
        for category, topics in categories.items():
            with st.expander(f"📁 {category}"):
                for topic in topics:
                    if st.button(f"📖 {topic.title}", key=f"help_{topic.title}"):
                        st.session_state.selected_help_topic = topic
        
        # 显示选中的帮助主题
        if hasattr(st.session_state, 'selected_help_topic'):
            topic = st.session_state.selected_help_topic
            st.subheader(f"📖 {topic.title}")
            st.markdown(topic.content)
            st.caption(f"分类: {topic.category} | 关键词: {', '.join(topic.keywords)}")
        
        # 常见问题
        st.subheader("❓ 常见问题")
        
        for i, faq in enumerate(self.faq):
            with st.expander(f"Q{i+1}: {faq['question']}"):
                st.markdown(faq['answer'])


# 全局帮助系统实例
_global_help_system: Optional[HelpSystem] = None


def get_help_system() -> HelpSystem:
    """获取全局帮助系统实例"""
    global _global_help_system
    
    if _global_help_system is None:
        _global_help_system = HelpSystem()
    
    return _global_help_system