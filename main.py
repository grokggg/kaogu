#!/usr/bin/env python3
"""
中国历史物质文明复原研究智能体
零密钥版本 —— 由Trae自身联网能力驱动

非侵入式扩展：
- 通用模板引擎（tools/universal_template.py）
- 冲突检测器（tools/conflict_detector.py）
- 朝代参数库（config/era_configs.yaml）
使用 --enable-universal 参数启用增强模式，默认关闭，原系统完全独立可用。
"""

import os
import sys
from datetime import datetime

# ========================================
# 非侵入式扩展加载（安全try/except，不破坏原系统）
# ========================================
UNIVERSAL_AVAILABLE = False
UniversalPrompt = None
ConflictDetector = None
ConflictSeverity = None

try:
    # 将项目根目录加入路径
    _project_root = os.path.dirname(os.path.abspath(__file__))
    if _project_root not in sys.path:
        sys.path.insert(0, _project_root)
    
    from tools.universal_template import UniversalPrompt
    from tools.conflict_detector import ConflictDetector, ConflictSeverity
    UNIVERSAL_AVAILABLE = True
except ImportError as e:
    # 扩展模块不可用时静默降级，原系统正常运行
    UNIVERSAL_AVAILABLE = False


class MaterialCultureAgent:
    """历史物质文明复原研究智能体
    
    本版本不需要任何API密钥。
    运行时会生成一个任务文件，由Trae读取并执行。
    
    支持非侵入式扩展：
    - enable_universal=True 时启用通用模板引擎增强
    - 不修改原系统提示词，仅附加增强校验层
    """
    
    def __init__(self, enable_universal=False):
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.outputs_dir = os.path.join(self.project_root, 'outputs')
        self.tasks_dir = os.path.join(self.project_root, 'outputs', 'tasks')
        self.audit_dir = os.path.join(self.project_root, 'outputs', 'audit')
        os.makedirs(self.tasks_dir, exist_ok=True)
        
        # 扩展模块实例（仅在启用时创建）
        self.enable_universal = enable_universal and UNIVERSAL_AVAILABLE
        self.universal_engine = None
        self.conflict_detector = None
        if self.enable_universal:
            self.universal_engine = UniversalPrompt(self.project_root)
            os.makedirs(self.audit_dir, exist_ok=True)
    
    def run(self, dynasty, period, object_type, identity=None, scene=None):
        """
        生成研究任务文件。
        Trae读取此文件后，按照系统提示词规则执行研究并输出结果。
        """
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        task_filename = f"task_{dynasty}_{period}_{object_type}_{timestamp}.md"
        task_filename = task_filename.replace(" ", "_").replace("/", "_")
        task_filepath = os.path.join(self.tasks_dir, task_filename)
        
        # 读取系统提示词
        prompt_path = os.path.join(self.project_root, 'prompts', 'system_prompt.md')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            system_prompt = f.read()
        
        # 生成任务文件
        task_content = f"""# 历史物质文明复原研究任务

**任务生成时间**：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**任务编号**：{timestamp}
**增强模式**：{"已启用（通用模板引擎+朝代参数校验+冲突检测）" if self.enable_universal else "未启用（原系统独立运行）"}

---

## 研究参数

- **朝代**：{dynasty}
- **时期**：{period}
- **复原对象**：{object_type}
- **身份**：{identity or '不限定'}
- **场景**：{scene or '不限定'}

---

## 执行指令

请严格按照以下系统提示词中的全部规则，完成本次研究任务。
务必进行联网搜索。
输出格式必须包含所有必需章节。
{"完成研究后，请对照【通用模板引擎增强层】中的朝代参数进行校验，若有冲突在【材料冲突】章节说明。" if self.enable_universal else ""}

---

## 系统提示词

{system_prompt}

---
"""

        # ========================================
        # 非侵入式增强层：附加在原提示词之后，不覆盖原内容
        # ========================================
        if self.enable_universal:
            sandbox_prompt = self.universal_engine.generate_sandbox_prompt(
                dynasty, period, object_type, identity, scene
            )
            task_content += f"""
## 通用模板引擎增强层（附加校验规则，不覆盖原提示词）

以下为动态加载的朝代专属参数校验规则，作为原系统提示词的补充。
请在复原过程中对照这些数据进行校验，如发现与复原结果冲突，请在【材料冲突】章节标注。

{sandbox_prompt}

---
"""

        task_content += f"""
## 具体研究查询

请对以下对象进行严谨复原研究：

【研究对象】
朝代：{dynasty}
时期：{period}
复原对象：{object_type}
身份：{identity or '不限定'}
场景：{scene or '不限定'}

请严格按照上述系统提示词中的工作规范，完成完整的研究复原流程。
务必执行联网检索，并输出所有必需的章节：
1. 研究对象
2. 文献材料摘要
3. 单件复原卡（每件文物逐件输出）
4. 事实层复原
5. 推论层分析
6. 视觉复原建议
7. 依据溯源
8. 可信度评级
9. 材料冲突
10. 材料覆盖范围声明（含补全路径）
{"11. 若启用增强模式，对照朝代参数进行校验，标注偏差项" if self.enable_universal else ""}

---

## 结果保存

完成研究后，请将完整报告保存到：
`{os.path.join(self.outputs_dir, f"{dynasty}_{period}_{object_type}_{timestamp}.md")}`
{"审计日志（自动校验结果）将保存到：`" + os.path.join(self.audit_dir, f"audit_{timestamp}.json") + "`" if self.enable_universal else ""}
"""
        
        # 保存任务文件
        with open(task_filepath, 'w', encoding='utf-8') as f:
            f.write(task_content)
        
        print(f"任务文件已生成: {task_filepath}")
        print(f"请将此文件内容发送给Trae，由Trae完成研究并输出结果。")
        
        return task_filepath


# ========================================
# 命令行接口
# ========================================
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="历史物质文明复原研究智能体（零密钥版）")
    parser.add_argument("--dynasty", required=True, help="朝代，如：西汉")
    parser.add_argument("--period", required=True, help="时期，如：武帝时期")
    parser.add_argument("--object", required=True, help="复原对象，如：贵族女性服饰")
    parser.add_argument("--identity", help="身份，如：贵族女性")
    parser.add_argument("--scene", help="场景，如：日常起居")
    parser.add_argument("--enable-universal", action="store_true",
                        help="启用通用模板引擎增强模式（朝代参数校验+冲突检测）")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  中国历史物质文明复原研究智能体（零密钥版本）")
    print("=" * 60)
    print(f"  朝代：{args.dynasty}")
    print(f"  时期：{args.period}")
    print(f"  对象：{args.object}")
    print(f"  身份：{args.identity or '不限定'}")
    print(f"  场景：{args.scene or '不限定'}")
    if args.enable_universal:
        if UNIVERSAL_AVAILABLE:
            print(f"  模式：增强模式（通用模板引擎已启用）")
        else:
            print(f"  模式：增强模式请求但扩展模块加载失败，使用原系统运行")
    else:
        print(f"  模式：标准模式（原系统独立运行）")
    print("=" * 60)
    print()
    print("正在生成研究任务文件...")
    
    agent = MaterialCultureAgent(enable_universal=args.enable_universal)
    task_file = agent.run(
        dynasty=args.dynasty,
        period=args.period,
        object_type=args.object,
        identity=args.identity,
        scene=args.scene
    )
    
    print()
    print("=" * 60)
    print("下一步操作：")
    print(f"  请将以下文件的内容复制发送给Trae：")
    print(f"  {task_file}")
    print("=" * 60)
