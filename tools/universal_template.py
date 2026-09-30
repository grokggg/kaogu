#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用提示词模板引擎 - 非侵入式扩展模块
本模块独立于原智能体核心代码，通过动态加载机制实现即插即用
不修改原有system_prompt.md和main.py核心逻辑
"""

import os
import yaml
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple


class UniversalPrompt:
    """通用提示词模板引擎 - 非侵入式扩展
    
    核心设计原则：
    1. 不修改原智能体的system_prompt字段
    2. 通过动态加载朝代参数库扩展能力
    3. 内置冲突检测，发现矛盾时触发人工审核标记
    4. 独立沙盒运行，不共享原系统数据库连接
    """
    
    # 不可变底层核心规则（硬编码，不可被外部配置覆盖）
    CORE_RULES = [
        "严格遵循谭其骧《中国历史地图集》历史地理考证体系",
        "优先采用考古实证数据而非文献孤证",
        "拒绝任何跨时代元素混入",
        "所有度量衡数据必须有出土实物锚点",
        "建筑构件形制必须符合对应朝代《营缮令》或工程规范",
        "服饰色彩/纹样必须符合当时舆服制度禁令"
    ]
    
    def __init__(self, project_root: str = None):
        if project_root is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.project_root = project_root
        self.era_configs = self._load_era_configs()
        self.conflict_log: List[Dict] = []
        self.audit_trail: List[Dict] = []
        
    def _load_era_configs(self) -> Dict:
        """加载朝代专属参数库（支持YAML/JSON两种格式）"""
        config_path = os.path.join(self.project_root, 'config', 'era_configs.yaml')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return self._get_builtin_era_configs()
    
    def _get_builtin_era_configs(self) -> Dict:
        """内置朝代参数库（当配置文件不存在时使用）"""
        return {
            '西汉': {
                '度量衡锚点': {
                    '1尺': '23.1厘米',
                    '1升': '200毫升',
                    '1斤': '250克',
                    '基准器': '上林共府铜斛，容积2000ml'
                },
                '车舆制度': {
                    '轺车辐条数': '最多12根（六百石以下）/30根（帝王）',
                    '车盖颜色': '二百石以下白布盖，三百石以上皂布盖，千石以上皂缯覆盖',
                    '马车类型': '轺车（轻便）、轩车（藩屏）、辎车（帷幔）、栈车（役车）'
                },
                '建筑规范': {
                    '城墙夯层': '7-12厘米/层',
                    '瓦当直径': '15-20厘米',
                    '斗拱形制': '实拍拱、一斗二升、一斗三升（雏形阶段）',
                    '屋顶类型': '庑殿顶、悬山顶（歇山顶尚未出现）'
                },
                '服饰禁忌': {
                    '商人': '不得穿丝织品（汉高祖禁令）',
                    '庶人': '不得穿彩色，只能穿本色麻布衣',
                    '冠制': '官员进贤冠梁数：公侯三梁，中二千石以下至博士两梁'
                },
                '地图精度': {
                    '长安城尺寸容差': '±50米',
                    '城墙周长': '25.7公里',
                    '面积': '约36平方公里'
                },
                '典型器物': {
                    '素纱襌衣': '马王堆一号汉墓出土，重49克',
                    '长信宫灯': '满城汉墓出土，高48厘米',
                    '铜奔马': '武威雷台汉墓出土，高34.5厘米'
                }
            },
            '唐': {
                '度量衡锚点': {
                    '1尺': '30厘米（大尺）/24.5厘米（小尺）',
                    '1升': '600毫升',
                    '1斤': '660克'
                },
                '建筑规范': {
                    '等级制度': '《营缮令》规定',
                    '斗拱': '出跳可达4-5铺作，雄大有力，约占柱高1/2',
                    '鸱尾': '高耸，无鱼尾分叉（中唐以前）',
                    '屋顶坡度': '举高1/5-1/6，平缓深远',
                    '柱础': '覆盆式'
                },
                '服饰禁忌': {
                    '帝王专用色': '赭黄色（武德令规定）',
                    '官员常服色': '三品以上紫，五品以上绯，六品七品绿，八品九品青',
                    '鱼袋制度': '五品以上佩鱼袋'
                },
                '地图精度': {
                    '长安城东西宽': '9721米±50米',
                    '南北长': '8651米±50米',
                    '面积': '约84平方公里'
                }
            },
            '北宋': {
                '建筑规范': {
                    '官书': '《营造法式》（李诫，元符三年1100年编成）',
                    '材分制度': '八等材，模数制设计',
                    '斗拱': '精巧化，出现假昂',
                    '格子门': '普及',
                    '虹桥': '木构虹梁，无柱，跨径约20米，见于《清明上河图》'
                },
                '度量衡锚点': {
                    '1尺': '31.4厘米',
                    '1升': '660毫升',
                    '1斤': '640克'
                }
            },
            '明': {
                '度量衡锚点': {
                    '1尺': '32厘米（裁衣尺）/32.7厘米（量地尺）',
                    '1升': '1035毫升',
                    '1斤': '590克'
                },
                '建筑规范': {
                    '官书': '《鲁班经》《工部厂库须知》',
                    '城墙': '全面包砖',
                    '斗拱': '装饰化，结构功能减弱',
                    '彩画': '旋子彩画成熟，和玺彩画出现'
                },
                '服饰制度': {
                    '补子': '洪武二十六年定，文官禽、武官兽',
                    '乌纱帽': '文武官员常服冠',
                    '四方平定巾': '士人便服'
                }
            },
            '清': {
                '建筑规范': {
                    '官书': '《工程做法则例》（雍正十二年1734年）',
                    '斗拱': '完全装饰化，比例极小',
                    '彩画': '和玺彩画（最高等级）、旋子彩画、苏式彩画'
                }
            }
        }
    
    def detect_task_type(self, user_query: str) -> str:
        """判断任务类型"""
        keywords = {
            'architecture': ['建筑', '宫殿', '民居', '城墙', '桥梁', '寺庙', '斗拱', '屋顶', '台基'],
            'clothing': ['服饰', '衣裳', '冠帽', '鞋履', '发型', '妆容', '深衣', '袍', '襦裙'],
            'transport': ['车', '马', '舆', '舟', '船', '出行', '驿站'],
            'military': ['兵器', '甲胄', '军阵', '城防'],
            'ritual': ['礼器', '祭祀', '丧葬', '礼乐'],
            'urban': ['长安城', '洛阳城', '汴梁', '城市', '坊市', '平面图', '地形图'],
            'food': ['饮食', '食器', '烹饪', '茶器', '酒器']
        }
        for task_type, words in keywords.items():
            if any(w in user_query for w in words):
                return task_type
        return 'general'
    
    def load_era_config(self, era_name: str) -> Dict:
        """动态加载朝代专属参数库
        
        Args:
            era_name: 朝代名称，如"西汉"、"唐"、"北宋"
            
        Returns:
            朝代配置字典，若不存在返回空字典
        """
        # 支持模糊匹配
        for key in self.era_configs:
            if key in era_name or era_name in key:
                config = self.era_configs[key].copy()
                config['_era_name'] = key
                return config
        return {}
    
    def generate_sandbox_prompt(self, dynasty: str, period: str, object_type: str,
                                 identity: str = None, scene: str = None) -> str:
        """生成沙盒环境下的扩展提示词
        
        不覆盖原system_prompt，而是作为附加增强层注入
        """
        era_config = self.load_era_config(dynasty)
        task_type = self.detect_task_type(object_type)
        
        prompt_parts = [
            "【通用模板引擎增强层 - 非侵入式加载】",
            "",
            "## 底层铁则（不可违反）",
        ]
        for i, rule in enumerate(self.CORE_RULES, 1):
            prompt_parts.append(f"{i}. {rule}")
        
        if era_config:
            prompt_parts.append("")
            prompt_parts.append(f"## {era_config.get('_era_name', dynasty)}专属参数校验规则")
            prompt_parts.append("以下数据为学术锚点，复原结果必须符合：")
            prompt_parts.append("")
            
            for category, params in era_config.items():
                if category.startswith('_'):
                    continue
                prompt_parts.append(f"### {category}")
                if isinstance(params, dict):
                    for key, value in params.items():
                        prompt_parts.append(f"- {key}：{value}")
                else:
                    prompt_parts.append(f"- {params}")
                prompt_parts.append("")
        
        prompt_parts.append("## 任务类型识别")
        prompt_parts.append(f"当前任务类型：{task_type}")
        prompt_parts.append("")
        prompt_parts.append("## 校验要求")
        prompt_parts.append("输出前请对照以上参数逐条校验，若发现不符合项：")
        prompt_parts.append("1. 在【材料冲突】章节明确标注")
        prompt_parts.append("2. 说明差异程度（轻度偏差/严重矛盾）")
        prompt_parts.append("3. 若偏差超过15%，标注【需人工复核】")
        prompt_parts.append("")
        
        self.audit_trail.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'sandbox_prompt_generated',
            'dynasty': dynasty,
            'period': period,
            'object_type': object_type,
            'task_type': task_type,
            'era_config_loaded': bool(era_config)
        })
        
        return "\n".join(prompt_parts)
    
    def detect_conflicts(self, original_output: str, enhanced_output: str) -> Tuple[bool, List[Dict]]:
        """双轨运行冲突检测器
        
        Args:
            original_output: 原智能体输出
            enhanced_output: 增强模块输出
            
        Returns:
            (是否有风险, 冲突列表)
        """
        conflicts = []
        
        # 检查是否有跨时代元素混入
        era_markers = {
            '西汉': ['琉璃瓦', '斗拱出跳', '歇山顶', '补子', '马蹄袖', '砖包城墙', '乌纱帽', '椅子'],
            '唐': ['补子', '马蹄袖', '和玺彩画', '椅子（盛唐前）', '青花瓷'],
            '宋': ['补子', '马蹄袖', '琉璃瓦全顶', '硬山顶'],
            '明': ['马蹄袖', '和玺彩画（清式）'],
        }
        
        # 检查度量衡异常
        measure_checks = [
            ('汉尺', '23.1厘米', ['29.6', '30', '32']),
        ]
        
        # 简单冲突检测逻辑（可扩展）
        for era, forbidden in era_markers.items():
            if era in str(original_output)[:100]:
                for item in forbidden:
                    if item in original_output:
                        conflicts.append({
                            'type': '跨时代元素混入',
                            'element': item,
                            'era': era,
                            'severity': 'high',
                            'location': 'original_output'
                        })
        
        self.conflict_log.extend(conflicts)
        
        has_risk = len(conflicts) > 0
        return has_risk, conflicts
    
    def get_audit_report(self) -> str:
        """生成审计追踪报告"""
        report = [
            "# 通用模板引擎审计报告",
            "",
            f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"记录条目数：{len(self.audit_trail)}",
            f"冲突检测数：{len(self.conflict_log)}",
            "",
            "## 操作记录",
        ]
        for entry in self.audit_trail:
            report.append(f"- [{entry['timestamp']}] {entry['action']} | "
                        f"{entry.get('dynasty','')}-{entry.get('period','')} "
                        f"对象:{entry.get('object_type','')} "
                        f"类型:{entry.get('task_type','')} "
                        f"朝代配置已加载:{entry.get('era_config_loaded', False)}")
        
        if self.conflict_log:
            report.append("")
            report.append("## 冲突记录")
            for c in self.conflict_log:
                report.append(f"- [{c['severity']}] {c['type']}: {c['element']} "
                            f"(时代:{c['era']}, 位置:{c['location']})")
        
        return "\n".join(report)


# ========================================
# 独立命令行接口（可单独运行测试）
# ========================================
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="通用提示词模板引擎测试")
    parser.add_argument("--dynasty", required=True, help="朝代")
    parser.add_argument("--period", default="", help="时期")
    parser.add_argument("--object", required=True, help="复原对象")
    
    args = parser.parse_args()
    
    engine = UniversalPrompt()
    prompt = engine.generate_sandbox_prompt(args.dynasty, args.period, args.object)
    print(prompt)
    print("\n" + "="*60)
    print(engine.get_audit_report())
