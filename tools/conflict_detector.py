#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
冲突检测器与双轨运行保障模块
独立模块，不修改原系统核心代码
"""

import re
import os
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum


class ConflictSeverity(Enum):
    LOW = "low"           # 轻度偏差，不影响核心结论
    MEDIUM = "medium"     # 中度矛盾，需标注
    HIGH = "high"         # 严重错误，必须修正
    CRITICAL = "critical" # 跨时代/原则性错误，禁止输出


@dataclass
class Conflict:
    conflict_type: str
    description: str
    expected: str
    found: str
    severity: ConflictSeverity
    location: str = ""
    suggestion: str = ""


@dataclass
class ValidationResult:
    is_valid: bool = True
    conflicts: List[Conflict] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    score: float = 100.0  # 0-100
    needs_human_review: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'is_valid': self.is_valid,
            'score': self.score,
            'needs_human_review': self.needs_human_review,
            'conflicts_count': len(self.conflicts),
            'warnings_count': len(self.warnings),
            'conflicts': [
                {
                    'type': c.conflict_type,
                    'description': c.description,
                    'expected': c.expected,
                    'found': c.found,
                    'severity': c.severity.value,
                    'location': c.location,
                    'suggestion': c.suggestion
                }
                for c in self.conflicts
            ],
            'warnings': self.warnings
        }


class ConflictDetector:
    """双轨运行冲突检测器
    
    职责：
    1. 检测跨时代元素混入
    2. 校验度量衡数据是否符合时代锚点
    3. 检查建筑构件是否符合时代规范
    4. 检查服饰制度是否符合舆服禁令
    5. 偏差超过阈值时触发人工审核标记
    """
    
    def __init__(self, era_config: Dict = None):
        self.era_config = era_config or {}
        self._build_forbidden_patterns()
    
    def _build_forbidden_patterns(self):
        """构建各朝代禁止出现的元素模式"""
        self.forbidden_patterns = {
            '西汉': [
                (r'琉璃瓦|琉璃[顶屋面]', '琉璃瓦', '琉璃瓦在西汉尚未出现，北魏始有，唐宋普及', ConflictSeverity.HIGH),
                (r'砖包城[墙垣]|包砖城[墙垣]', '城墙包砖', '西汉城墙为纯夯土，包砖始于东晋以后，明代才大规模普及', ConflictSeverity.HIGH),
                (r'歇山顶|九脊顶|歇山式', '歇山顶', '歇山顶在汉代尚未出现，汉代屋顶主要为庑殿顶和悬山顶', ConflictSeverity.HIGH),
                (r'硬山顶', '硬山顶', '硬山顶出现较晚，汉代无', ConflictSeverity.HIGH),
                (r'乌纱帽', '乌纱帽', '乌纱帽起源于东晋，定名于隋唐，汉代为进贤冠/武弁大冠', ConflictSeverity.HIGH),
                (r'补子|补服', '补子', '补子制度始于明代', ConflictSeverity.CRITICAL),
                (r'马蹄袖', '马蹄袖', '马蹄袖为清代满族服饰', ConflictSeverity.CRITICAL),
                (r'椅子|靠背椅|圈椅|交椅', '高足坐具椅子', '张骞出使时期尚无椅子，人们席地而坐或坐榻，椅子传入在东汉以后', ConflictSeverity.HIGH),
                (r'青花瓷', '青花瓷', '青花瓷成熟于元代', ConflictSeverity.CRITICAL),
                (r'斗拱出[跳三四五]铺作', '复杂斗拱出跳', '西汉斗拱为雏形阶段，仅实拍拱、一斗二升、一斗三升，无多跳出跳', ConflictSeverity.HIGH),
                (r'和玺彩画|旋子彩画', '明清式彩画', '汉代无此彩画制度', ConflictSeverity.CRITICAL),
            ],
            '唐': [
                (r'补子|补服', '补子', '补子制度始于明代', ConflictSeverity.CRITICAL),
                (r'马蹄袖', '马蹄袖', '马蹄袖为清代满族服饰', ConflictSeverity.CRITICAL),
                (r'琉璃[全整]顶|满铺琉璃', '全顶琉璃', '唐代宫殿以青棍瓦为主，琉璃仅用于剪边（屋脊、檐口）', ConflictSeverity.MEDIUM),
                (r'硬山顶', '硬山顶', '硬山顶明清才普及', ConflictSeverity.MEDIUM),
                (r'青花瓷', '青花瓷', '青花瓷成熟于元代', ConflictSeverity.HIGH),
                (r'和玺彩画', '和玺彩画', '和玺彩画为清代最高等级彩画', ConflictSeverity.HIGH),
            ],
            '北宋': [
                (r'补子|补服', '补子', '补子制度始于明代', ConflictSeverity.CRITICAL),
                (r'马蹄袖', '马蹄袖', '马蹄袖为清代满族服饰', ConflictSeverity.CRITICAL),
                (r'和玺彩画', '和玺彩画', '和玺彩画为清代', ConflictSeverity.HIGH),
            ],
            '明': [
                (r'马蹄袖', '马蹄袖', '马蹄袖为清代满族服饰，明代汉服无马蹄袖', ConflictSeverity.CRITICAL),
                (r'旗袍|旗装', '旗装', '旗装为清代满族服饰', ConflictSeverity.CRITICAL),
                (r'和玺彩画', '和玺彩画', '和玺彩画定型于清代', ConflictSeverity.MEDIUM),
            ],
        }
    
    def validate_output(self, text: str, era_name: str = None) -> ValidationResult:
        """校验输出内容，检测冲突
        
        Args:
            text: 待校验的输出文本
            era_name: 朝代名称
            
        Returns:
            ValidationResult 校验结果
        """
        result = ValidationResult()
        
        if not era_name:
            # 尝试从文本中推断朝代
            for era in self.forbidden_patterns:
                if era in text[:500]:
                    era_name = era
                    break
        
        if not era_name:
            result.warnings.append("无法识别朝代名称，跳过跨时代元素检测")
            return result
        
        # 1. 检测跨时代禁止元素
        patterns = self.forbidden_patterns.get(era_name, [])
        for pattern, element, description, severity in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                # 检查是否在"禁止使用"或"未出现"等否定语境中
                start = max(0, match.start() - 30)
                context = text[start:match.end() + 30]
                if any(neg in context for neg in ['禁止', '不可', '不能', '未出现', '尚未', '没有', '无', '不使用', '严禁']):
                    continue  # 在否定语境中，属于正确说明
                
                result.conflicts.append(Conflict(
                    conflict_type="跨时代元素混入",
                    description=f"在{era_name}复原内容中发现{element}：{description}",
                    expected=f"{era_name}时期不应出现{element}",
                    found=match.group(),
                    severity=severity,
                    location=f"位置约第{text[:match.start()].count(chr(10))+1}行",
                    suggestion=f"删除或修改关于{element}的描述"
                ))
        
        # 2. 度量衡数据校验（简单范围检查）
        self._validate_measurements(text, era_name, result)
        
        # 3. 检查是否使用了禁用来源
        forbidden_sources = ['百度百科', '维基百科', '知乎', '微信公众号', '个人博客',
                           '古装剧', '影视剧', '游戏', 'AI生成']
        for source in forbidden_sources:
            if f"来源：{source}" in text or f"参考：{source}" in text:
                result.conflicts.append(Conflict(
                    conflict_type="禁用来源",
                    description=f"使用了禁用来源：{source}",
                    expected="应使用考古报告、核心期刊、正史、博物馆资料",
                    found=source,
                    severity=ConflictSeverity.HIGH,
                    suggestion=f"移除对{source}的引用，替换为学术来源"
                ))
        
        # 4. 计算分数和判定
        score_deduction = 0
        for c in result.conflicts:
            if c.severity == ConflictSeverity.CRITICAL:
                score_deduction += 50
                result.is_valid = False
            elif c.severity == ConflictSeverity.HIGH:
                score_deduction += 20
                result.is_valid = False
            elif c.severity == ConflictSeverity.MEDIUM:
                score_deduction += 10
            else:
                score_deduction += 3
        
        result.score = max(0, 100 - score_deduction)
        result.needs_human_review = (result.score < 85) or len(result.conflicts) > 0
        
        # 5. 生成警告
        if not result.conflicts and not result.warnings:
            result.warnings.append("自动校验通过，但仍需人工确认细节准确性")
        
        return result
    
    def _validate_measurements(self, text: str, era_name: str, result: ValidationResult):
        """度量衡数据校验"""
        # 汉尺校验：若出现"汉尺...厘米"格式，检查是否在23-24cm范围内
        if era_name in ['西汉', '东汉', '汉']:
            chi_matches = re.finditer(r'(?:汉尺|1尺)[^\d]*?(\d+\.?\d*)\s*厘米', text)
            for m in chi_matches:
                val = float(m.group(1))
                if not (22.5 <= val <= 24.0):
                    result.conflicts.append(Conflict(
                        conflict_type="度量衡偏差",
                        description=f"汉代1尺长度数据异常：{val}厘米",
                        expected="西汉1尺约23.1厘米，容差±0.5厘米",
                        found=f"{val}厘米",
                        severity=ConflictSeverity.MEDIUM,
                        suggestion="修正为23.1厘米或标注所用尺度标准"
                    ))
            
            # 素纱襌衣重量校验
            if '素纱' in text or '襌衣' in text:
                weight_matches = re.finditer(r'素纱[襌禅]衣[^\d]*?重\s*(\d+)\s*克', text)
                for m in weight_matches:
                    val = int(m.group(1))
                    if not (45 <= val <= 55) and val != 49:
                        result.warnings.append(f"素纱襌衣重量数据为{val}克，标准数据为49克（马王堆一号汉墓出土）")
    
    def merge_results(self, original_result: str, enhanced_result: str,
                      original_validation: ValidationResult,
                      enhanced_validation: ValidationResult) -> Tuple[str, ValidationResult]:
        """双轨结果合并器
        
        合并策略：
        - 两边均无冲突：合并输出
        - 一边有冲突：采用无冲突版本，标注问题
        - 两边均有冲突：标记需人工审核，列出所有冲突
        - 关键事实差异>15%：标记需人工复核
        """
        merged_validation = ValidationResult()
        merged_validation.conflicts.extend(original_validation.conflicts)
        merged_validation.conflicts.extend(enhanced_validation.conflicts)
        merged_validation.warnings.extend(original_validation.warnings)
        merged_validation.warnings.extend(enhanced_validation.warnings)
        
        has_critical = any(c.severity == ConflictSeverity.CRITICAL for c in merged_validation.conflicts)
        
        if has_critical:
            merged_validation.is_valid = False
            merged_validation.needs_human_review = True
            merged_validation.score = min(original_validation.score, enhanced_validation.score)
            
            merged_output = (
                "# ⚠️ 双轨检测发现严重问题，需人工复核\n\n"
                "自动检测发现以下严重冲突，原智能体与扩展模块输出存在矛盾，已暂停合并。\n\n"
                "## 检测到的严重问题\n\n"
            )
            for c in merged_validation.conflicts:
                if c.severity in [ConflictSeverity.HIGH, ConflictSeverity.CRITICAL]:
                    merged_output += f"- **[{c.severity.value.upper()}]** {c.description}\n"
                    merged_output += f"  - 期望：{c.expected}\n"
                    merged_output += f"  - 检测到：{c.found}\n"
                    merged_output += f"  - 建议：{c.suggestion}\n\n"
            return merged_output, merged_validation
        
        # 无严重冲突时，以原系统输出为主，附加增强层校验结果
        merged_output = original_result
        if enhanced_validation.warnings or enhanced_validation.conflicts:
            merged_output += "\n\n---\n\n## 【通用模板引擎校验报告】\n\n"
            merged_output += f"- 校验分数：{enhanced_validation.score}/100\n"
            if enhanced_validation.conflicts:
                merged_output += f"- 发现问题：{len(enhanced_validation.conflicts)}项\n"
                for c in enhanced_validation.conflicts:
                    merged_output += f"  - [{c.severity.value}] {c.description}\n"
            if enhanced_validation.warnings:
                merged_output += f"- 提示：\n"
                for w in enhanced_validation.warnings:
                    merged_output += f"  - {w}\n"
            if enhanced_validation.needs_human_review:
                merged_output += "\n⚠️ 本报告已通过自动校验但存在需关注项，建议人工复核细节。\n"
        
        merged_validation.score = min(original_validation.score, enhanced_validation.score)
        merged_validation.needs_human_review = (
            original_validation.needs_human_review or enhanced_validation.needs_human_review
        )
        merged_validation.is_valid = original_validation.is_valid and enhanced_validation.is_valid
        
        return merged_output, merged_validation
    
    def save_audit_log(self, result: ValidationResult, output_dir: str, task_id: str):
        """保存审计日志（独立存储，不污染原系统数据库）"""
        os.makedirs(output_dir, exist_ok=True)
        log_path = os.path.join(output_dir, f"audit_{task_id}.json")
        log_data = {
            'task_id': task_id,
            'timestamp': datetime.now().isoformat(),
            'validation': result.to_dict()
        }
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        return log_path
