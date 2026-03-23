"""
Report Agent服务
使用LangChain + Zep实现ReACT模式的模拟报告生成

功能：
1. 根据模拟需求和Zep图谱信息生成报告
2. 先规划目录结构，然后分段生成
3. 每段采用ReACT多轮思考与反思模式
4. 支持与用户对话，在对话中自主调用检索工具
"""

import os
import json
import time
import re
import copy
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..config import Config
from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger
from ..utils.locale import get_language_name, get_output_language_instruction, normalize_locale
from .report_ui import build_llm_response_ui_payload, build_section_source_bundle, build_section_ui_payload, extract_final_answer, has_final_answer_marker, normalize_log_entry_for_ui, normalize_section_entry_for_ui, normalize_tool_result_for_ui
from .zep_tools import (
    ZepToolsService, 
    SearchResult, 
    InsightForgeResult, 
    PanoramaResult,
    InterviewResult
)

logger = get_logger('mirofish.report_agent')


REPORT_TEXT = {
    "en": {
        "report_started": "Report generation started",
        "planning_started": "Started planning the report outline",
        "planning_context": "Retrieved simulation context",
        "planning_complete": "Outline planning complete",
        "section_start": "Started generating section: {section_title}",
        "react_thought": "ReACT reasoning round {iteration}",
        "tool_call": "Calling tool: {tool_name}",
        "tool_result": "Tool {tool_name} returned a result",
        "llm_response": "LLM response (tool calls: {has_tool_calls}, final answer: {has_final_answer})",
        "section_content_done": "Section content finished: {section_title}",
        "section_complete": "Section complete: {section_title}",
        "report_complete": "Report generation complete",
        "error": "Error: {error_message}",
        "available_tools": "Available tools:",
        "parameters_label": "Parameters",
        "unknown_tool": "Unknown tool: {tool_name}. Use one of: insight_forge, panorama_search, quick_search, interview_agents",
        "tool_execution_failed": "Tool execution failed: {error}",
        "analyzing_requirement": "Analyzing the simulation requirement...",
        "generating_outline": "Generating the report outline...",
        "parsing_outline": "Parsing the outline structure...",
        "outline_done": "Outline planning complete",
        "default_report_title": "Simulation Analysis Report",
        "default_future_report_title": "Future Forecast Report",
        "default_future_report_summary": "Trend and risk analysis based on simulation forecasts",
        "default_section_1": "Prediction Scenario and Core Findings",
        "default_section_2": "Behavioral Forecast Analysis",
        "default_section_3": "Trends Outlook and Risk Signals",
        "initializing_report": "Initializing the report...",
        "planning_report": "Starting report outline planning...",
        "outline_complete_count": "Outline planning finished with {count} sections",
        "generating_section": "Generating section: {title} ({current}/{total})",
        "section_done": "Section complete: {title}",
        "assembling_report": "Assembling the full report...",
        "report_done": "Report generation complete",
        "report_failed": "Report generation failed: {error}",
        "step_enter": "Entered Step {step}: {label}",
        "step_back": "Returned to Step {step}: {label}",
        "custom_rounds": "Custom simulation rounds: {count}",
        "auto_rounds": "Using automatically configured simulation rounds",
        "report_content_truncated": "... [report content truncated] ...",
        "no_report": "(No report available yet)",
        "insight_desc": "Perform deep multi-hop retrieval, automatically break the problem into sub-questions, gather facts, entities, and relationship chains, and return a synthesis suitable for report writing.",
        "insight_param_query": "The question or topic to analyze in depth",
        "insight_param_context": "Optional context from the current report section to sharpen sub-question generation",
        "panorama_desc": "Retrieve a broad panorama of the simulated world, including active information and historical or expired facts, to understand evolution and overall context.",
        "panorama_param_query": "The search query used for relevance ranking",
        "panorama_param_expired": "Whether to include expired or historical facts (default: true)",
        "quick_desc": "Run a fast, lightweight retrieval for directly relevant facts when you only need the top matches.",
        "quick_param_query": "Search query string",
        "quick_param_limit": "Maximum number of results to return (optional, default: 10)",
        "interview_desc": "Interview active simulated agents to collect multiple viewpoints from the simulated world and summarize their responses.",
        "interview_param_topic": "Interview topic or requirement description",
        "interview_param_max_agents": "Maximum number of agents to interview (optional, default: 5, max: 10)",
    },
    "ar": {
        "report_started": "تم بدء توليد التقرير",
        "planning_started": "بدأ تخطيط مخطط التقرير",
        "planning_context": "تم جلب سياق المحاكاة",
        "planning_complete": "اكتمل تخطيط المخطط",
        "section_start": "بدأ توليد القسم: {section_title}",
        "react_thought": "جولة التفكير ReACT رقم {iteration}",
        "tool_call": "جارٍ استدعاء الأداة: {tool_name}",
        "tool_result": "أعادت الأداة {tool_name} نتيجة",
        "llm_response": "استجابة النموذج (استدعاءات الأدوات: {has_tool_calls}، إجابة نهائية: {has_final_answer})",
        "section_content_done": "اكتمل محتوى القسم: {section_title}",
        "section_complete": "اكتمل القسم: {section_title}",
        "report_complete": "اكتمل توليد التقرير",
        "error": "خطأ: {error_message}",
        "available_tools": "الأدوات المتاحة:",
        "parameters_label": "المعلمات",
        "unknown_tool": "أداة غير معروفة: {tool_name}. استخدم إحدى الأدوات التالية: insight_forge أو panorama_search أو quick_search أو interview_agents",
        "tool_execution_failed": "فشل تنفيذ الأداة: {error}",
        "analyzing_requirement": "جارٍ تحليل متطلب المحاكاة...",
        "generating_outline": "جارٍ توليد مخطط التقرير...",
        "parsing_outline": "جارٍ تحليل بنية المخطط...",
        "outline_done": "اكتمل تخطيط المخطط",
        "default_report_title": "تقرير تحليل المحاكاة",
        "default_future_report_title": "تقرير توقعات مستقبلية",
        "default_future_report_summary": "تحليل الاتجاهات والمخاطر استناداً إلى توقعات المحاكاة",
        "default_section_1": "سيناريو التنبؤ والنتائج الأساسية",
        "default_section_2": "تحليل التنبؤات السلوكية",
        "default_section_3": "اتجاهات المستقبل وإشارات المخاطر",
        "initializing_report": "جارٍ تهيئة التقرير...",
        "planning_report": "جارٍ بدء تخطيط مخطط التقرير...",
        "outline_complete_count": "اكتمل تخطيط المخطط مع {count} أقسام",
        "generating_section": "جارٍ توليد القسم: {title} ({current}/{total})",
        "section_done": "اكتمل القسم: {title}",
        "assembling_report": "جارٍ تجميع التقرير الكامل...",
        "report_done": "اكتمل توليد التقرير",
        "report_failed": "فشل توليد التقرير: {error}",
        "step_enter": "تم الدخول إلى الخطوة {step}: {label}",
        "step_back": "تمت العودة إلى الخطوة {step}: {label}",
        "custom_rounds": "عدد جولات المحاكاة المخصص: {count}",
        "auto_rounds": "جارٍ استخدام عدد الجولات المُعد تلقائياً",
        "report_content_truncated": "... [تم اقتطاع محتوى التقرير] ...",
        "no_report": "(لا يوجد تقرير بعد)",
        "insight_desc": "نفّذ استرجاعاً عميقاً متعدد القفزات، وقسّم السؤال إلى أسئلة فرعية، واجمع الحقائق والكيانات وسلاسل العلاقات، ثم أعد خلاصة مناسبة لكتابة التقرير.",
        "insight_param_query": "السؤال أو الموضوع المطلوب تحليله بعمق",
        "insight_param_context": "سياق اختياري من قسم التقرير الحالي لتحسين توليد الأسئلة الفرعية",
        "panorama_desc": "استرجع صورة بانورامية واسعة للعالم المُحاكى، بما في ذلك المعلومات النشطة والحقائق التاريخية أو المنتهية، لفهم التطور والسياق العام.",
        "panorama_param_query": "استعلام البحث المستخدم لترتيب الصلة",
        "panorama_param_expired": "هل تُضمَّن الحقائق المنتهية أو التاريخية؟ (الافتراضي: نعم)",
        "quick_desc": "نفّذ استرجاعاً سريعاً وخفيفاً للحقائق الأكثر صلة عندما تحتاج فقط إلى أفضل النتائج المباشرة.",
        "quick_param_query": "نص استعلام البحث",
        "quick_param_limit": "الحد الأقصى لعدد النتائج المعادة (اختياري، الافتراضي: 10)",
        "interview_desc": "أجرِ مقابلات مع الوكلاء النشطين في المحاكاة لجمع وجهات نظر متعددة من العالم المُحاكى وتلخيص ردودهم.",
        "interview_param_topic": "موضوع المقابلة أو وصف الطلب",
        "interview_param_max_agents": "الحد الأقصى لعدد الوكلاء الذين ستُجرى معهم المقابلات (اختياري، الافتراضي: 5، الحد الأقصى: 10)",
    },
    "zh": {
        "report_started": "报告生成任务开始",
        "planning_started": "开始规划报告大纲",
        "planning_context": "获取模拟上下文信息",
        "planning_complete": "大纲规划完成",
        "section_start": "开始生成章节: {section_title}",
        "react_thought": "ReACT 第{iteration}轮思考",
        "tool_call": "调用工具: {tool_name}",
        "tool_result": "工具 {tool_name} 返回结果",
        "llm_response": "LLM 响应 (工具调用: {has_tool_calls}, 最终答案: {has_final_answer})",
        "section_content_done": "章节 {section_title} 内容生成完成",
        "section_complete": "章节 {section_title} 生成完成",
        "report_complete": "报告生成完成",
        "error": "发生错误: {error_message}",
        "available_tools": "可用工具：",
        "parameters_label": "参数",
        "unknown_tool": "未知工具: {tool_name}。请使用以下工具之一: insight_forge, panorama_search, quick_search, interview_agents",
        "tool_execution_failed": "工具执行失败: {error}",
        "analyzing_requirement": "正在分析模拟需求...",
        "generating_outline": "正在生成报告大纲...",
        "parsing_outline": "正在解析大纲结构...",
        "outline_done": "大纲规划完成",
        "default_report_title": "模拟分析报告",
        "default_future_report_title": "未来预测报告",
        "default_future_report_summary": "基于模拟预测的未来趋势与风险分析",
        "default_section_1": "预测场景与核心发现",
        "default_section_2": "人群行为预测分析",
        "default_section_3": "趋势展望与风险提示",
        "initializing_report": "初始化报告...",
        "planning_report": "开始规划报告大纲...",
        "outline_complete_count": "大纲规划完成，共{count}个章节",
        "generating_section": "正在生成章节: {title} ({current}/{total})",
        "section_done": "章节 {title} 已完成",
        "assembling_report": "正在组装完整报告...",
        "report_done": "报告生成完成",
        "report_failed": "报告生成失败: {error}",
        "step_enter": "进入 Step {step}: {label}",
        "step_back": "返回 Step {step}: {label}",
        "custom_rounds": "自定义模拟轮数: {count}",
        "auto_rounds": "使用自动配置的模拟轮数",
        "report_content_truncated": "... [报告内容已截断] ...",
        "no_report": "（暂无报告）",
        "insight_desc": "执行深度多跳检索，自动拆解子问题，收集事实、实体与关系链，并输出适合写入报告的综合分析。",
        "insight_param_query": "你想深入分析的问题或话题",
        "insight_param_context": "当前报告章节的上下文（可选，有助于生成更精准的子问题）",
        "panorama_desc": "获取模拟世界的广度全景，包括当前有效信息与历史/过期事实，用于理解事件演变和整体背景。",
        "panorama_param_query": "搜索查询，用于相关性排序",
        "panorama_param_expired": "是否包含过期/历史内容（默认True）",
        "quick_desc": "快速检索最相关的事实，适合只需要高匹配结果的轻量场景。",
        "quick_param_query": "搜索查询字符串",
        "quick_param_limit": "返回结果数量（可选，默认10）",
        "interview_desc": "采访正在运行的模拟Agent，从模拟世界收集多视角观点并总结回答。",
        "interview_param_topic": "采访主题或需求描述",
        "interview_param_max_agents": "最多采访的Agent数量（可选，默认5，最大10）",
    },
}

REPORT_TEXT_EXTRA = {
    "en": {
        "deep_search_writing": "Deep retrieval and drafting ({current}/{max})",
        "first_section_placeholder": "(This is the first section)",
        "empty_response_marker": "(empty response)",
        "please_continue": "Please continue generating the section.",
        "conflict_retry_message": "Your previous reply contained both a tool call and `Final Answer:`. Reply again and do exactly one of them: either a single `<tool_call>` block with no final answer, or `Final Answer:` with no tool call.",
        "unused_tools_recommendation": "(These tools are still unused and worth trying: {tools})",
        "section_generation_failed_empty": "(This section could not be generated because the model returned an empty response. Please try again later.)",
        "report_context_template": "Section title: {section_title}\nSimulation requirement: {simulation_requirement}",
        "tool_result_block_label": "[{tool} result]",
    },
    "ar": {
        "deep_search_writing": "استرجاع عميق وصياغة القسم ({current}/{max})",
        "first_section_placeholder": "(هذا هو القسم الأول)",
        "empty_response_marker": "(استجابة فارغة)",
        "please_continue": "يرجى متابعة توليد القسم.",
        "conflict_retry_message": "احتوت إجابتك السابقة على استدعاء أداة و `Final Answer:` معاً. أعد المحاولة ونفّذ واحداً فقط: إمّا كتلة `<tool_call>` واحدة دون إجابة نهائية، أو `Final Answer:` دون أي استدعاء أداة.",
        "unused_tools_recommendation": "(هذه الأدوات لم تُستخدم بعد ويُستحسن تجربتها: {tools})",
        "section_generation_failed_empty": "(تعذّر توليد هذا القسم لأن النموذج أعاد استجابة فارغة. يرجى المحاولة مرة أخرى لاحقاً.)",
        "report_context_template": "عنوان القسم: {section_title}\nمتطلب المحاكاة: {simulation_requirement}",
        "tool_result_block_label": "[نتيجة {tool}]",
    },
    "zh": {
        "deep_search_writing": "深度检索与撰写中 ({current}/{max})",
        "first_section_placeholder": "（这是第一个章节）",
        "empty_response_marker": "（响应为空）",
        "please_continue": "请继续生成内容。",
        "conflict_retry_message": "你上一条回复同时包含了工具调用和 `Final Answer:`。请重新回复，并且只做其中一件事：要么仅输出一个 `<tool_call>` 块，不要写 Final Answer；要么仅输出 `Final Answer:`，不要包含工具调用。",
        "unused_tools_recommendation": "（这些工具还未使用，推荐尝试: {tools}）",
        "section_generation_failed_empty": "（本章节生成失败：LLM 返回空响应，请稍后重试）",
        "report_context_template": "章节标题: {section_title}\n模拟需求: {simulation_requirement}",
        "tool_result_block_label": "[{tool}结果]",
    },
}

for _locale, _values in REPORT_TEXT_EXTRA.items():
    REPORT_TEXT.setdefault(_locale, {}).update(_values)


PROMPT_TEXT = {
    "en": {
        "plan_system_prompt": """You are writing a forward-looking simulation report from an observer's view over a simulated world. Treat the simulation as a rehearsal of possible future developments rather than a commentary on present-day reality.

Your job is to design a concise report outline that explains:
1. what future state emerges under the simulation requirement,
2. how different agents or groups react and behave,
3. which future trends, risks, and opportunities are worth watching.

Constraints:
- Return JSON only.
- Use 2 to 5 sections.
- Do not create subsections.
- Keep the section structure focused on predictive findings.

Return JSON in this shape:
{
  "title": "Report title",
  "summary": "One-sentence summary",
  "sections": [
    {"title": "Section title", "description": "What this section covers"}
  ]
}

{language_instruction}""",
        "plan_user_prompt": """Simulation setup:
{simulation_requirement}

Observed scale of the simulated world:
- participating entities: {total_nodes}
- relationships formed: {total_edges}
- entity types: {entity_types}
- active agents: {total_entities}

Sample future facts retrieved from the simulation:
{related_facts_json}

From an observer's view, identify the most useful predictive report structure for this scenario. Keep it concise, focused, and limited to 2-5 sections.

{language_instruction}""",
        "section_system_prompt": """You are writing one section of a forward-looking simulation report.

Report title: {report_title}
Report summary: {report_summary}
Simulation requirement: {simulation_requirement}
Current section: {section_title}

Core rule: the simulated world is your evidence base. Use only information returned from the tools. Do not rely on outside knowledge.

Mandatory rules:
1. Call tools 3 to 5 times before you finalize the section.
2. Mix tools when useful; do not overuse a single tool.
3. Use agent statements and simulation observations as evidence.
4. Write the entire section in {target_language_name}. If tool results contain another language, translate them naturally before quoting them.
5. Do not add markdown headings. The system will add the section title. Use paragraphs, bold emphasis, lists, and blockquotes only.
6. Avoid repeating material that already appears in completed sections.

Available tools:
{tools_description}

Per reply you may do exactly one of these:
A) Call one tool using:
<tool_call>
{"name": "tool_name", "parameters": {"key": "value"}}
</tool_call>

B) Finish the section by starting your reply with `Final Answer:`.

Never include a tool call and `Final Answer:` in the same reply.

{language_instruction}""",
        "section_user_prompt": """Previously completed sections (read carefully and avoid repetition):
{previous_content}

Current task: write the section titled "{section_title}".

Before writing, you must first call a tool and gather enough simulation evidence. Once you have enough evidence, reply with `Final Answer:` followed by body text only, with no headings.

{language_instruction}""",
        "react_observation": """Observation (retrieval result):

=== Tool {tool_name} output ===
{result}

Tool calls used: {tool_calls_count}/{max_tool_calls} (used: {used_tools_str}){unused_hint}
- If the evidence is sufficient, start your next reply with `Final Answer:` and write the section.
- If you still need evidence, call one more tool.
""",
        "react_insufficient": "You have used only {tool_calls_count} tool calls. Use at least {min_tool_calls} before replying with `Final Answer:`. {unused_hint}",
        "react_insufficient_alt": "You have used {tool_calls_count} tool calls so far. Use at least {min_tool_calls} before finalizing the section. {unused_hint}",
        "react_tool_limit": "The tool-call limit has been reached ({tool_calls_count}/{max_tool_calls}). Do not call more tools. Reply immediately with `Final Answer:` and write the section.",
        "react_unused_tools_hint": "\nSuggestion: you have not used these tools yet: {unused_list}",
        "react_force_final": "The iteration or tool limit has been reached. Reply now with `Final Answer:` and write the section content.",
        "chat_system_prompt": """You are a concise simulation-report assistant.

Background condition:
{simulation_requirement}

Existing report content:
{report_content}

Rules:
1. Answer from the existing report first.
2. Only call tools if the report is insufficient.
3. Keep answers direct, clear, and structured.
4. Prefer a conclusion first, then short quoted evidence when useful.

Available tools (use only when necessary, at most 1-2 calls):
{tools_description}

Tool format:
<tool_call>
{"name": "tool_name", "parameters": {"key": "value"}}
</tool_call>

{language_instruction}""",
        "chat_observation_suffix": "\n\nPlease answer the question concisely.",
    },
    "ar": {
        "plan_system_prompt": """أنت تكتب تقريراً استشرافياً مبنياً على عالم مُحاكى تُشاهده من منظور المراقب. اعتبر المحاكاة تمريناً لما قد يحدث مستقبلاً، لا تعليقاً على الواقع الحالي.

مهمتك هي تصميم مخطط تقرير موجز يوضح:
1. ما الحالة المستقبلية التي تظهر تحت شرط المحاكاة،
2. كيف تتفاعل الفئات والوكلاء المختلفون ويتصرفون،
3. ما الاتجاهات والمخاطر والفرص المستقبلية الجديرة بالمتابعة.

القيود:
- أعد JSON فقط.
- استخدم من قسمين إلى خمسة أقسام.
- لا تُنشئ أقساماً فرعية.
- اجعل البنية مركزة على النتائج التنبؤية.

أعد JSON بهذا الشكل:
{
  "title": "عنوان التقرير",
  "summary": "ملخص من جملة واحدة",
  "sections": [
    {"title": "عنوان القسم", "description": "ما الذي يغطيه هذا القسم"}
  ]
}

{language_instruction}""",
        "plan_user_prompt": """إعداد المحاكاة:
{simulation_requirement}

حجم العالم المُحاكى المرصود:
- عدد الكيانات المشاركة: {total_nodes}
- عدد العلاقات المتشكلة: {total_edges}
- أنواع الكيانات: {entity_types}
- عدد الوكلاء النشطين: {total_entities}

عينات من الحقائق المستقبلية المسترجعة من المحاكاة:
{related_facts_json}

من منظور المراقب، صمّم البنية الأنسب لتقرير تنبؤي موجز لهذه الحالة، على أن تكون مركزة ومحدودة بين 2 و5 أقسام.

{language_instruction}""",
        "section_system_prompt": """أنت تكتب قسماً واحداً من تقرير استشرافي مبني على المحاكاة.

عنوان التقرير: {report_title}
ملخص التقرير: {report_summary}
متطلب المحاكاة: {simulation_requirement}
القسم الحالي: {section_title}

القاعدة الأساسية: العالم المُحاكى هو مصدر الأدلة. استخدم فقط المعلومات التي تعيدها الأدوات، ولا تعتمد على معرفة خارجية.

قواعد إلزامية:
1. استدعِ الأدوات من 3 إلى 5 مرات قبل إنهاء القسم.
2. نوّع بين الأدوات عند الحاجة، ولا تعتمد على أداة واحدة فقط.
3. استخدم أقوال الوكلاء ومشاهدات المحاكاة كأدلة.
4. اكتب القسم كاملاً باللغة {target_language_name}. وإذا احتوت نتائج الأدوات على لغة أخرى، فترجمها ترجمة طبيعية قبل الاقتباس.
5. لا تضف عناوين Markdown. سيضيف النظام عنوان القسم تلقائياً. استخدم الفقرات، والتأكيد الغامق، والقوائم، والاقتباسات فقط.
6. تجنب تكرار ما ورد في الأقسام المكتملة سابقاً.

الأدوات المتاحة:
{tools_description}

في كل رد يمكنك القيام بشيء واحد فقط:
أ) استدعاء أداة واحدة بهذا الشكل:
<tool_call>
{"name": "tool_name", "parameters": {"key": "value"}}
</tool_call>

ب) إنهاء القسم ببدء الرد بالبادئة `Final Answer:`.

يُمنع الجمع بين استدعاء أداة و `Final Answer:` في الرد نفسه.

{language_instruction}""",
        "section_user_prompt": """الأقسام المكتملة سابقاً (اقرأها بعناية وتجنب التكرار):
{previous_content}

المهمة الحالية: اكتب القسم المعنون "{section_title}".

قبل الكتابة، يجب أن تستدعي أداة أولاً وتجمع أدلة كافية من المحاكاة. وعندما تصبح الأدلة كافية، أعد الرد بالبادئة `Final Answer:` ثم نص القسم مباشرة من دون أي عناوين.

{language_instruction}""",
        "react_observation": """الملاحظة (نتيجة الاسترجاع):

=== مخرجات الأداة {tool_name} ===
{result}

تم استخدام {tool_calls_count}/{max_tool_calls} من استدعاءات الأدوات (المستخدَم: {used_tools_str}){unused_hint}
- إذا أصبحت الأدلة كافية، فابدأ الرد التالي بالبادئة `Final Answer:` ثم اكتب القسم.
- إذا كنت بحاجة إلى أدلة إضافية، فاستدعِ أداة أخرى واحدة.
""",
        "react_insufficient": "لقد استخدمت {tool_calls_count} استدعاءات أدوات فقط. استخدم {min_tool_calls} على الأقل قبل الرد بـ `Final Answer:`. {unused_hint}",
        "react_insufficient_alt": "لقد استخدمت حتى الآن {tool_calls_count} استدعاءات أدوات. استخدم {min_tool_calls} على الأقل قبل إنهاء القسم. {unused_hint}",
        "react_tool_limit": "تم الوصول إلى الحد الأقصى لاستدعاءات الأدوات ({tool_calls_count}/{max_tool_calls}). لا تستدعِ أدوات إضافية. أعد الرد فوراً بالبادئة `Final Answer:` واكتب القسم.",
        "react_unused_tools_hint": "\nاقتراح: لم تستخدم هذه الأدوات بعد: {unused_list}",
        "react_force_final": "تم الوصول إلى حد التكرار أو الأدوات. أعد الرد الآن بالبادئة `Final Answer:` واكتب محتوى القسم.",
        "chat_system_prompt": """أنت مساعد موجز خاص بتقارير المحاكاة.

شرط الخلفية:
{simulation_requirement}

محتوى التقرير الحالي:
{report_content}

القواعد:
1. أجب أولاً بالاعتماد على التقرير الحالي.
2. لا تستدعِ الأدوات إلا إذا كان التقرير غير كافٍ.
3. اجعل الإجابات مباشرة وواضحة ومنظمة.
4. قدّم الخلاصة أولاً، ثم أدلة مقتبسة قصيرة عند الحاجة.

الأدوات المتاحة (استخدمها فقط عند الضرورة، وبحد أقصى 1-2 استدعاء):
{tools_description}

صيغة استدعاء الأداة:
<tool_call>
{"name": "tool_name", "parameters": {"key": "value"}}
</tool_call>

{language_instruction}""",
        "chat_observation_suffix": "\n\nأجب عن السؤال بإيجاز ووضوح.",
    },
    "zh": {},
}


def pt(locale: str, key: str, **params) -> str:
    normalized = normalize_locale(locale)
    template = PROMPT_TEXT.get(normalized, PROMPT_TEXT['en']).get(key, PROMPT_TEXT['en'].get(key, key))
    for k, v in params.items():
        template = template.replace('{' + k + '}', str(v))
    return template





def rt(locale: str, key: str, **params) -> str:
    normalized = normalize_locale(locale)
    template = REPORT_TEXT.get(normalized, REPORT_TEXT['en']).get(key, REPORT_TEXT['en'].get(key, key))
    for k, v in params.items():
        template = template.replace('{' + k + '}', str(v))
    return template


class ReportLogger:
    """
    Report Agent 详细日志记录器
    
    在报告文件夹中生成 agent_log.jsonl 文件，记录每一步详细动作。
    每行是一个完整的 JSON 对象，包含时间戳、动作类型、详细内容等。
    """
    
    def __init__(self, report_id: str, locale: str = "en"):
        """
        初始化日志记录器
        
        Args:
            report_id: 报告ID，用于确定日志文件路径
        """
        self.report_id = report_id
        self.locale = normalize_locale(locale)
        self.log_file_path = os.path.join(
            Config.UPLOAD_FOLDER, 'reports', report_id, 'agent_log.jsonl'
        )
        self.start_time = datetime.now()
        self._ensure_log_file()
    
    def _ensure_log_file(self):
        """确保日志文件所在目录存在"""
        log_dir = os.path.dirname(self.log_file_path)
        os.makedirs(log_dir, exist_ok=True)
    
    def _get_elapsed_time(self) -> float:
        """获取从开始到现在的耗时（秒）"""
        return (datetime.now() - self.start_time).total_seconds()
    
    def log(
        self, 
        action: str, 
        stage: str,
        details: Dict[str, Any],
        section_title: str = None,
        section_index: int = None
    ):
        """
        记录一条日志
        
        Args:
            action: 动作类型，如 'start', 'tool_call', 'llm_response', 'section_complete' 等
            stage: 当前阶段，如 'planning', 'generating', 'completed'
            details: 详细内容字典，不截断
            section_title: 当前章节标题（可选）
            section_index: 当前章节索引（可选）
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": round(self._get_elapsed_time(), 2),
            "report_id": self.report_id,
            "action": action,
            "stage": stage,
            "section_title": section_title,
            "section_index": section_index,
            "details": details
        }
        
        # 追加写入 JSONL 文件
        with open(self.log_file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    def log_start(self, simulation_id: str, graph_id: str, simulation_requirement: str):
        """记录报告生成开始"""
        self.log(
            action="report_start",
            stage="pending",
            details={
                "simulation_id": simulation_id,
                "graph_id": graph_id,
                "simulation_requirement": simulation_requirement,
                "message": rt(self.locale, "report_started")
            }
        )
    
    def log_planning_start(self):
        """记录大纲规划开始"""
        self.log(
            action="planning_start",
            stage="planning",
            details={"message": rt(self.locale, "planning_started")}
        )
    
    def log_planning_context(self, context: Dict[str, Any]):
        """记录规划时获取的上下文信息"""
        self.log(
            action="planning_context",
            stage="planning",
            details={
                "message": rt(self.locale, "planning_context"),
                "context": context
            }
        )
    
    def log_planning_complete(self, outline_dict: Dict[str, Any]):
        """记录大纲规划完成"""
        self.log(
            action="planning_complete",
            stage="planning",
            details={
                "message": rt(self.locale, "planning_complete"),
                "outline": outline_dict
            }
        )
    
    def log_section_start(self, section_title: str, section_index: int):
        """记录章节生成开始"""
        self.log(
            action="section_start",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={"message": rt(self.locale, "section_start", section_title=section_title)}
        )
    
    def log_react_thought(self, section_title: str, section_index: int, iteration: int, thought: str):
        """记录 ReACT 思考过程"""
        self.log(
            action="react_thought",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "iteration": iteration,
                "thought": thought,
                "message": rt(self.locale, "react_thought", iteration=iteration)
            }
        )
    
    def log_tool_call(
        self, 
        section_title: str, 
        section_index: int,
        tool_name: str, 
        parameters: Dict[str, Any],
        iteration: int
    ):
        """记录工具调用"""
        self.log(
            action="tool_call",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "iteration": iteration,
                "tool_name": tool_name,
                "parameters": parameters,
                "message": rt(self.locale, "tool_call", tool_name=tool_name)
            }
        )
    
    def log_tool_result(
        self,
        section_title: str,
        section_index: int,
        tool_name: str,
        result: str,
        iteration: int,
        structured_result: Optional[Any] = None,
        ui_payload: Optional[Dict[str, Any]] = None,
    ):
        """记录工具调用结果（完整内容，不截断）"""
        self.log(
            action="tool_result",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "iteration": iteration,
                "tool_name": tool_name,
                "result": result,  # 完整结果，不截断
                "result_length": len(result),
                "result_structured": structured_result,
                "ui_payload": ui_payload,
                "message": rt(self.locale, "tool_result", tool_name=tool_name)
            }
        )
    
    def log_llm_response(
        self,
        section_title: str,
        section_index: int,
        response: str,
        iteration: int,
        has_tool_calls: bool,
        has_final_answer: bool,
        ui_payload: Optional[Dict[str, Any]] = None,
        evidence_context: Optional[Dict[str, Any]] = None,
    ):
        """记录 LLM 响应（完整内容，不截断）"""
        self.log(
            action="llm_response",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "iteration": iteration,
                "response": response,  # 完整响应，不截断
                "response_length": len(response),
                "has_tool_calls": has_tool_calls,
                "has_final_answer": has_final_answer,
                "ui_payload": ui_payload,
                "evidence_context": evidence_context,
                "message": rt(self.locale, "llm_response", has_tool_calls=has_tool_calls, has_final_answer=has_final_answer)
            }
        )
    
    def log_section_content(
        self,
        section_title: str,
        section_index: int,
        content: str,
        tool_calls_count: int
    ):
        """记录章节内容生成完成（仅记录内容，不代表整个章节完成）"""
        self.log(
            action="section_content",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "content": content,  # 完整内容，不截断
                "content_length": len(content),
                "tool_calls_count": tool_calls_count,
                "message": rt(self.locale, "section_content_done", section_title=section_title)
            }
        )
    
    def log_section_full_complete(
        self,
        section_title: str,
        section_index: int,
        full_content: str
    ):
        """
        记录章节生成完成

        前端应监听此日志来判断一个章节是否真正完成，并获取完整内容
        """
        self.log(
            action="section_complete",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "content": full_content,
                "content_length": len(full_content),
                "message": rt(self.locale, "section_complete", section_title=section_title)
            }
        )
    
    def log_report_complete(self, total_sections: int, total_time_seconds: float):
        """记录报告生成完成"""
        self.log(
            action="report_complete",
            stage="completed",
            details={
                "total_sections": total_sections,
                "total_time_seconds": round(total_time_seconds, 2),
                "message": rt(self.locale, "report_complete")
            }
        )
    
    def log_error(self, error_message: str, stage: str, section_title: str = None):
        """记录错误"""
        self.log(
            action="error",
            stage=stage,
            section_title=section_title,
            section_index=None,
            details={
                "error": error_message,
                "message": rt(self.locale, "error", error_message=error_message)
            }
        )


class ReportConsoleLogger:
    """
    Report Agent 控制台日志记录器
    
    将控制台风格的日志（INFO、WARNING等）写入报告文件夹中的 console_log.txt 文件。
    这些日志与 agent_log.jsonl 不同，是纯文本格式的控制台输出。
    """
    
    def __init__(self, report_id: str, locale: str = "en"):
        """
        初始化控制台日志记录器
        
        Args:
            report_id: 报告ID，用于确定日志文件路径
        """
        self.report_id = report_id
        self.locale = normalize_locale(locale)
        self.log_file_path = os.path.join(
            Config.UPLOAD_FOLDER, 'reports', report_id, 'console_log.txt'
        )
        self._ensure_log_file()
        self._file_handler = None
        self._setup_file_handler()
    
    def _ensure_log_file(self):
        """确保日志文件所在目录存在"""
        log_dir = os.path.dirname(self.log_file_path)
        os.makedirs(log_dir, exist_ok=True)
    
    def _setup_file_handler(self):
        """设置文件处理器，将日志同时写入文件"""
        import logging
        
        # 创建文件处理器
        self._file_handler = logging.FileHandler(
            self.log_file_path,
            mode='a',
            encoding='utf-8'
        )
        self._file_handler.setLevel(logging.INFO)
        
        # 使用与控制台相同的简洁格式
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        self._file_handler.setFormatter(formatter)
        
        # 添加到 report_agent 相关的 logger
        loggers_to_attach = [
            'mirofish.report_agent',
            'mirofish.zep_tools',
        ]
        
        for logger_name in loggers_to_attach:
            target_logger = logging.getLogger(logger_name)
            # 避免重复添加
            if self._file_handler not in target_logger.handlers:
                target_logger.addHandler(self._file_handler)
    
    def close(self):
        """关闭文件处理器并从 logger 中移除"""
        import logging
        
        if self._file_handler:
            loggers_to_detach = [
                'mirofish.report_agent',
                'mirofish.zep_tools',
            ]
            
            for logger_name in loggers_to_detach:
                target_logger = logging.getLogger(logger_name)
                if self._file_handler in target_logger.handlers:
                    target_logger.removeHandler(self._file_handler)
            
            self._file_handler.close()
            self._file_handler = None
    
    def __del__(self):
        """析构时确保关闭文件处理器"""
        self.close()


class ReportStatus(str, Enum):
    """报告状态"""
    PENDING = "pending"
    PLANNING = "planning"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ReportSection:
    """报告章节"""
    title: str
    content: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content
        }

    def to_markdown(self, level: int = 2) -> str:
        """转换为Markdown格式"""
        md = f"{'#' * level} {self.title}\n\n"
        if self.content:
            md += f"{self.content}\n\n"
        return md


@dataclass
class ReportOutline:
    """报告大纲"""
    title: str
    summary: str
    sections: List[ReportSection]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "summary": self.summary,
            "sections": [s.to_dict() for s in self.sections]
        }
    
    def to_markdown(self) -> str:
        """转换为Markdown格式"""
        md = f"# {self.title}\n\n"
        md += f"> {self.summary}\n\n"
        for section in self.sections:
            md += section.to_markdown()
        return md


@dataclass
class Report:
    """完整报告"""
    report_id: str
    simulation_id: str
    graph_id: str
    simulation_requirement: str
    status: ReportStatus
    outline: Optional[ReportOutline] = None
    markdown_content: str = ""
    created_at: str = ""
    completed_at: str = ""
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "simulation_id": self.simulation_id,
            "graph_id": self.graph_id,
            "simulation_requirement": self.simulation_requirement,
            "status": self.status.value,
            "outline": self.outline.to_dict() if self.outline else None,
            "markdown_content": self.markdown_content,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "error": self.error
        }


# ═══════════════════════════════════════════════════════════════
# Prompt 模板常量
# ═══════════════════════════════════════════════════════════════

# ── 工具描述 ──

TOOL_DESC_INSIGHT_FORGE = """\
【深度洞察检索 - 强大的检索工具】
这是我们强大的检索函数，专为深度分析设计。它会：
1. 自动将你的问题分解为多个子问题
2. 从多个维度检索模拟图谱中的信息
3. 整合语义搜索、实体分析、关系链追踪的结果
4. 返回最全面、最深度的检索内容

【使用场景】
- 需要深入分析某个话题
- 需要了解事件的多个方面
- 需要获取支撑报告章节的丰富素材

【返回内容】
- 相关事实原文（可直接引用）
- 核心实体洞察
- 关系链分析"""

TOOL_DESC_PANORAMA_SEARCH = """\
【广度搜索 - 获取全貌视图】
这个工具用于获取模拟结果的完整全貌，特别适合了解事件演变过程。它会：
1. 获取所有相关节点和关系
2. 区分当前有效的事实和历史/过期的事实
3. 帮助你了解舆情是如何演变的

【使用场景】
- 需要了解事件的完整发展脉络
- 需要对比不同阶段的舆情变化
- 需要获取全面的实体和关系信息

【返回内容】
- 当前有效事实（模拟最新结果）
- 历史/过期事实（演变记录）
- 所有涉及的实体"""

TOOL_DESC_QUICK_SEARCH = """\
【简单搜索 - 快速检索】
轻量级的快速检索工具，适合简单、直接的信息查询。

【使用场景】
- 需要快速查找某个具体信息
- 需要验证某个事实
- 简单的信息检索

【返回内容】
- 与查询最相关的事实列表"""

TOOL_DESC_INTERVIEW_AGENTS = """\
【深度采访 - 真实Agent采访（双平台）】
调用OASIS模拟环境的采访API，对正在运行的模拟Agent进行真实采访！
这不是LLM模拟，而是调用真实的采访接口获取模拟Agent的原始回答。
默认在Twitter和Reddit两个平台同时采访，获取更全面的观点。

功能流程：
1. 自动读取人设文件，了解所有模拟Agent
2. 智能选择与采访主题最相关的Agent（如学生、媒体、官方等）
3. 自动生成采访问题
4. 调用 /api/simulation/interview/batch 接口在双平台进行真实采访
5. 整合所有采访结果，提供多视角分析

【使用场景】
- 需要从不同角色视角了解事件看法（学生怎么看？媒体怎么看？官方怎么说？）
- 需要收集多方意见和立场
- 需要获取模拟Agent的真实回答（来自OASIS模拟环境）
- 想让报告更生动，包含"采访实录"

【返回内容】
- 被采访Agent的身份信息
- 各Agent在Twitter和Reddit两个平台的采访回答
- 关键引言（可直接引用）
- 采访摘要和观点对比

【重要】需要OASIS模拟环境正在运行才能使用此功能！"""

# ── 大纲规划 prompt ──

PLAN_SYSTEM_PROMPT = """\
你是一个「未来预测报告」的撰写专家，拥有对模拟世界的「上帝视角」——你可以洞察模拟中每一位Agent的行为、言论和互动。

【核心理念】
我们构建了一个模拟世界，并向其中注入了特定的「模拟需求」作为变量。模拟世界的演化结果，就是对未来可能发生情况的预测。你正在观察的不是"实验数据"，而是"未来的预演"。

【你的任务】
撰写一份「未来预测报告」，回答：
1. 在我们设定的条件下，未来发生了什么？
2. 各类Agent（人群）是如何反应和行动？
3. 这个模拟揭示了哪些值得关注的未来趋势和风险？

【报告定位】
- ✅ 这是一份基于模拟的未来预测报告，揭示"如果这样，未来会怎样"
- ✅ 聚焦于预测结果：事件走向、群体反应、涌现现象、潜在风险
- ✅ 模拟世界中的Agent言行就是对未来人群行为的预测
- ❌ 不是对现实世界现状的分析
- ❌ 不是泛泛而谈的舆情综述

【章节数量限制】
- 最少2个章节，最多5个章节
- 不需要子章节，每个章节直接撰写完整内容
- 内容要精炼，聚焦于核心预测发现
- 章节结构由你根据预测结果自主设计

请输出JSON格式的报告大纲，格式如下：
{
    "title": "报告标题",
    "summary": "报告摘要（一句话概括核心预测发现）",
    "sections": [
        {
            "title": "章节标题",
            "description": "章节内容描述"
        }
    ]
}

注意：sections数组最少2个，最多5个元素！

{language_instruction}"""

PLAN_USER_PROMPT_TEMPLATE = """\
【预测场景设定】
我们向模拟世界注入的变量（模拟需求）：{simulation_requirement}

【模拟世界规模】
- 参与模拟的实体数量: {total_nodes}
- 实体间产生的关系数量: {total_edges}
- 实体类型分布: {entity_types}
- 活跃Agent数量: {total_entities}

【模拟预测到的部分未来事实样本】
{related_facts_json}

请以「上帝视角」审视这个未来预演：
1. 在我们设定的条件下，未来呈现出了什么样的状态？
2. 各类人群（Agent）是如何反应和行动的？
3. 这个模拟揭示了哪些值得关注的未来趋势？

根据预测结果，设计最合适的报告章节结构。

【再次提醒】报告章节数量：最少2个，最多5个，内容要精炼聚焦于核心预测发现。

{language_instruction}"""

# ── 章节生成 prompt ──

SECTION_SYSTEM_PROMPT_TEMPLATE = """\
你是一个「未来预测报告」的撰写专家，正在撰写报告的一个章节。

报告标题: {report_title}
报告摘要: {report_summary}
预测场景（模拟需求）: {simulation_requirement}

当前要撰写的章节: {section_title}

═══════════════════════════════════════════════════════════════
【核心理念】
═══════════════════════════════════════════════════════════════

模拟世界是对未来的预演。我们向模拟世界注入了特定条件（模拟需求），
模拟中Agent的行为和互动，就是对未来人群行为的预测。

你的任务是：
- 揭示在设定条件下，未来发生了什么
- 预测各类人群（Agent）是如何反应和行动的
- 发现值得关注的未来趋势、风险和机会

❌ 不要写成对现实世界现状的分析
✅ 要聚焦于"未来会怎样"——模拟结果就是预测的未来

═══════════════════════════════════════════════════════════════
【最重要的规则 - 必须遵守】
═══════════════════════════════════════════════════════════════

1. 【必须调用工具观察模拟世界】
   - 你正在以「上帝视角」观察未来的预演
   - 所有内容必须来自模拟世界中发生的事件和Agent言行
   - 禁止使用你自己的知识来编写报告内容
   - 每个章节至少调用3次工具（最多5次）来观察模拟的世界，它代表了未来

2. 【必须引用Agent的原始言行】
   - Agent的发言和行为是对未来人群行为的预测
   - 在报告中使用引用格式展示这些预测，例如：
     > "某类人群会表示：原文内容..."
   - 这些引用是模拟预测的核心证据

3. 【语言一致性 - 引用内容必须翻译为报告语言】
   - 工具返回的内容可能包含中文、英文或多语言混杂的表述
   - 本次报告必须完整使用 {target_language_name} 撰写
   - 当你引用工具返回的其他语言内容时，必须先翻译成自然流畅的 {target_language_name} 再写入报告
   - 翻译时保持原意不变，确保表述自然通顺
   - 这一规则同时适用于正文和引用块（> 格式）中的内容

4. 【忠实呈现预测结果】
   - 报告内容必须反映模拟世界中的代表未来的模拟结果
   - 不要添加模拟中不存在的信息
   - 如果某方面信息不足，如实说明

═══════════════════════════════════════════════════════════════
【⚠️ 格式规范 - 极其重要！】
═══════════════════════════════════════════════════════════════

【一个章节 = 最小内容单位】
- 每个章节是报告的最小分块单位
- ❌ 禁止在章节内使用任何 Markdown 标题（#、##、###、#### 等）
- ❌ 禁止在内容开头添加章节主标题
- ✅ 章节标题由系统自动添加，你只需撰写纯正文内容
- ✅ 使用**粗体**、段落分隔、引用、列表来组织内容，但不要用标题

【正确示例】
```
本章节分析了事件的舆论传播态势。通过对模拟数据的深入分析，我们发现...

**首发引爆阶段**

微博作为舆情的第一现场，承担了信息首发的核心功能：

> "微博贡献了68%的首发声量..."

**情绪放大阶段**

抖音平台进一步放大了事件影响力：

- 视觉冲击力强
- 情绪共鸣度高
```

【错误示例】
```
## 执行摘要          ← 错误！不要添加任何标题
### 一、首发阶段     ← 错误！不要用###分小节
#### 1.1 详细分析   ← 错误！不要用####细分

本章节分析了...
```

═══════════════════════════════════════════════════════════════
【可用检索工具】（每章节调用3-5次）
═══════════════════════════════════════════════════════════════

{tools_description}

【工具使用建议 - 请混合使用不同工具，不要只用一种】
- insight_forge: 深度洞察分析，自动分解问题并多维度检索事实和关系
- panorama_search: 广角全景搜索，了解事件全貌、时间线和演变过程
- quick_search: 快速验证某个具体信息点
- interview_agents: 采访模拟Agent，获取不同角色的第一人称观点和真实反应

═══════════════════════════════════════════════════════════════
【工作流程】
═══════════════════════════════════════════════════════════════

每次回复你只能做以下两件事之一（不可同时做）：

选项A - 调用工具：
输出你的思考，然后用以下格式调用一个工具：
<tool_call>
{{"name": "工具名称", "parameters": {{"参数名": "参数值"}}}}
</tool_call>
系统会执行工具并把结果返回给你。你不需要也不能自己编写工具返回结果。

选项B - 输出最终内容：
当你已通过工具获取了足够信息，以 "Final Answer:" 开头输出章节内容。

⚠️ 严格禁止：
- 禁止在一次回复中同时包含工具调用和 Final Answer
- 禁止自己编造工具返回结果（Observation），所有工具结果由系统注入
- 每次回复最多调用一个工具

═══════════════════════════════════════════════════════════════
【章节内容要求】
═══════════════════════════════════════════════════════════════

1. 内容必须基于工具检索到的模拟数据
2. 大量引用原文来展示模拟效果
3. 使用Markdown格式（但禁止使用标题）：
   - 使用 **粗体文字** 标记重点（代替子标题）
   - 使用列表（-或1.2.3.）组织要点
   - 使用空行分隔不同段落
   - ❌ 禁止使用 #、##、###、#### 等任何标题语法
4. 【引用格式规范 - 必须单独成段】
   引用必须独立成段，前后各有一个空行，不能混在段落中：

   ✅ 正确格式：
   ```
   校方的回应被认为缺乏实质内容。

   > "校方的应对模式在瞬息万变的社交媒体环境中显得僵化和迟缓。"

   这一评价反映了公众的普遍不满。
   ```

   ❌ 错误格式：
   ```
   校方的回应被认为缺乏实质内容。> "校方的应对模式..." 这一评价反映了...
   ```
5. 保持与其他章节的逻辑连贯性
6. 【避免重复】仔细阅读下方已完成的章节内容，不要重复描述相同的信息
7. 【再次强调】不要添加任何标题！用**粗体**代替小节标题

{language_instruction}"""

SECTION_USER_PROMPT_TEMPLATE = """\
已完成的章节内容（请仔细阅读，避免重复）：
{previous_content}

═══════════════════════════════════════════════════════════════
【当前任务】撰写章节: {section_title}
═══════════════════════════════════════════════════════════════

【重要提醒】
1. 仔细阅读上方已完成的章节，避免重复相同的内容！
2. 开始前必须先调用工具获取模拟数据
3. 请混合使用不同工具，不要只用一种
4. 报告内容必须来自检索结果，不要使用自己的知识

【⚠️ 格式警告 - 必须遵守】
- ❌ 不要写任何标题（#、##、###、####都不行）
- ❌ 不要写"{section_title}"作为开头
- ✅ 章节标题由系统自动添加
- ✅ 直接写正文，用**粗体**代替小节标题

请开始：
1. 首先思考（Thought）这个章节需要什么信息
2. 然后调用工具（Action）获取模拟数据
3. 收集足够信息后输出 Final Answer（纯正文，无任何标题）

{language_instruction}"""

# ── ReACT 循环内消息模板 ──

REACT_OBSERVATION_TEMPLATE = """\
Observation（检索结果）:

═══ 工具 {tool_name} 返回 ═══
{result}

═══════════════════════════════════════════════════════════════
已调用工具 {tool_calls_count}/{max_tool_calls} 次（已用: {used_tools_str}）{unused_hint}
- 如果信息充分：以 "Final Answer:" 开头输出章节内容（必须引用上述原文）
- 如果需要更多信息：调用一个工具继续检索
═══════════════════════════════════════════════════════════════"""

REACT_INSUFFICIENT_TOOLS_MSG = (
    "【注意】你只调用了{tool_calls_count}次工具，至少需要{min_tool_calls}次。"
    "请再调用工具获取更多模拟数据，然后再输出 Final Answer。{unused_hint}"
)

REACT_INSUFFICIENT_TOOLS_MSG_ALT = (
    "当前只调用了 {tool_calls_count} 次工具，至少需要 {min_tool_calls} 次。"
    "请调用工具获取模拟数据。{unused_hint}"
)

REACT_TOOL_LIMIT_MSG = (
    "工具调用次数已达上限（{tool_calls_count}/{max_tool_calls}），不能再调用工具。"
    '请立即基于已获取的信息，以 "Final Answer:" 开头输出章节内容。'
)

REACT_UNUSED_TOOLS_HINT = "\n💡 你还没有使用过: {unused_list}，建议尝试不同工具获取多角度信息"

REACT_FORCE_FINAL_MSG = "已达到工具调用限制，请直接输出 Final Answer: 并生成章节内容。"

# ── Chat prompt ──

CHAT_SYSTEM_PROMPT_TEMPLATE = """\
你是一个简洁高效的模拟预测助手。

【背景】
预测条件: {simulation_requirement}

【已生成的分析报告】
{report_content}

【规则】
1. 优先基于上述报告内容回答问题
2. 直接回答问题，避免冗长的思考论述
3. 仅在报告内容不足以回答时，才调用工具检索更多数据
4. 回答要简洁、清晰、有条理

【可用工具】（仅在需要时使用，最多调用1-2次）
{tools_description}

【工具调用格式】
<tool_call>
{{"name": "工具名称", "parameters": {{"参数名": "参数值"}}}}
</tool_call>

【回答风格】
- 简洁直接，不要长篇大论
- 使用 > 格式引用关键内容
- 优先给出结论，再解释原因

{language_instruction}"""

CHAT_OBSERVATION_SUFFIX = "\n\n请简洁回答问题。"

PROMPT_TEXT.setdefault("zh", {}).update({
    "plan_system_prompt": PLAN_SYSTEM_PROMPT,
    "plan_user_prompt": PLAN_USER_PROMPT_TEMPLATE,
    "section_system_prompt": SECTION_SYSTEM_PROMPT_TEMPLATE,
    "section_user_prompt": SECTION_USER_PROMPT_TEMPLATE,
    "react_observation": REACT_OBSERVATION_TEMPLATE,
    "react_insufficient": REACT_INSUFFICIENT_TOOLS_MSG,
    "react_insufficient_alt": REACT_INSUFFICIENT_TOOLS_MSG_ALT,
    "react_tool_limit": REACT_TOOL_LIMIT_MSG,
    "react_unused_tools_hint": REACT_UNUSED_TOOLS_HINT,
    "react_force_final": REACT_FORCE_FINAL_MSG,
    "chat_system_prompt": CHAT_SYSTEM_PROMPT_TEMPLATE,
    "chat_observation_suffix": CHAT_OBSERVATION_SUFFIX,
})


# ═══════════════════════════════════════════════════════════════
# ReportAgent 主类
# ═══════════════════════════════════════════════════════════════


class ReportAgent:
    """
    Report Agent - 模拟报告生成Agent

    采用ReACT（Reasoning + Acting）模式：
    1. 规划阶段：分析模拟需求，规划报告目录结构
    2. 生成阶段：逐章节生成内容，每章节可多次调用工具获取信息
    3. 反思阶段：检查内容完整性和准确性
    """
    
    # 最大工具调用次数（每个章节）
    MAX_TOOL_CALLS_PER_SECTION = 5
    
    # 最大反思轮数
    MAX_REFLECTION_ROUNDS = 3
    
    # 对话中的最大工具调用次数
    MAX_TOOL_CALLS_PER_CHAT = 2
    
    def __init__(
        self, 
        graph_id: str,
        simulation_id: str,
        simulation_requirement: str,
        llm_client: Optional[LLMClient] = None,
        zep_tools: Optional[ZepToolsService] = None,
        locale: str = "en"
    ):
        """
        初始化Report Agent
        
        Args:
            graph_id: 图谱ID
            simulation_id: 模拟ID
            simulation_requirement: 模拟需求描述
            llm_client: LLM客户端（可选）
            zep_tools: Zep工具服务（可选）
        """
        self.graph_id = graph_id
        self.simulation_id = simulation_id
        self.simulation_requirement = simulation_requirement
        self.locale = normalize_locale(locale)
        self.language_name = get_language_name(self.locale)
        self.language_instruction = get_output_language_instruction(self.locale)
        
        self.llm = llm_client or LLMClient()
        self.zep_tools = zep_tools or ZepToolsService(locale=self.locale)
        
        # 工具定义
        self.tools = self._define_tools()
        
        # 日志记录器（在 generate_report 中初始化）
        self.report_logger: Optional[ReportLogger] = None
        # 控制台日志记录器（在 generate_report 中初始化）
        self.console_logger: Optional[ReportConsoleLogger] = None
        
        logger.info(f"ReportAgent initialized: graph_id={graph_id}, simulation_id={simulation_id}, locale={self.locale}")

    def _build_language_context(self) -> Dict[str, str]:
        return {
            "language_instruction": self.language_instruction,
            "target_language_name": self.language_name,
        }

    def _define_tools(self) -> Dict[str, Dict[str, Any]]:
        """Define localized tool metadata."""
        return {
            "insight_forge": {
                "name": "insight_forge",
                "description": rt(self.locale, "insight_desc"),
                "parameters": {
                    "query": rt(self.locale, "insight_param_query"),
                    "report_context": rt(self.locale, "insight_param_context"),
                }
            },
            "panorama_search": {
                "name": "panorama_search",
                "description": rt(self.locale, "panorama_desc"),
                "parameters": {
                    "query": rt(self.locale, "panorama_param_query"),
                    "include_expired": rt(self.locale, "panorama_param_expired"),
                }
            },
            "quick_search": {
                "name": "quick_search",
                "description": rt(self.locale, "quick_desc"),
                "parameters": {
                    "query": rt(self.locale, "quick_param_query"),
                    "limit": rt(self.locale, "quick_param_limit"),
                }
            },
            "interview_agents": {
                "name": "interview_agents",
                "description": rt(self.locale, "interview_desc"),
                "parameters": {
                    "interview_topic": rt(self.locale, "interview_param_topic"),
                    "max_agents": rt(self.locale, "interview_param_max_agents"),
                }
            }
        }

    def _serialize_tool_result(self, result: Any) -> Optional[Any]:
        if hasattr(result, "to_dict"):
            try:
                return result.to_dict()
            except Exception:
                return None
        if isinstance(result, (dict, list)):
            return result
        return None

    def _execute_tool_with_metadata(self, tool_name: str, parameters: Dict[str, Any], report_context: str = "") -> Dict[str, Any]:
        """执行工具调用并返回文本结果与结构化负载。"""
        logger.info(f"Executing tool: {tool_name}, parameters: {parameters}")

        try:
            result_obj = None
            if tool_name == "insight_forge":
                query = parameters.get("query", "")
                ctx = parameters.get("report_context", "") or report_context
                result_obj = self.zep_tools.insight_forge(
                    graph_id=self.graph_id,
                    query=query,
                    simulation_requirement=self.simulation_requirement,
                    report_context=ctx
                )

            elif tool_name == "panorama_search":
                query = parameters.get("query", "")
                include_expired = parameters.get("include_expired", True)
                if isinstance(include_expired, str):
                    include_expired = include_expired.lower() in ['true', '1', 'yes']
                result_obj = self.zep_tools.panorama_search(
                    graph_id=self.graph_id,
                    query=query,
                    include_expired=include_expired
                )

            elif tool_name == "quick_search":
                query = parameters.get("query", "")
                limit = parameters.get("limit", 10)
                if isinstance(limit, str):
                    limit = int(limit)
                result_obj = self.zep_tools.quick_search(
                    graph_id=self.graph_id,
                    query=query,
                    limit=limit
                )

            elif tool_name == "interview_agents":
                interview_topic = parameters.get("interview_topic", parameters.get("query", ""))
                max_agents = parameters.get("max_agents", 5)
                if isinstance(max_agents, str):
                    max_agents = int(max_agents)
                max_agents = min(max_agents, 10)
                result_obj = self.zep_tools.interview_agents(
                    simulation_id=self.simulation_id,
                    interview_requirement=interview_topic,
                    simulation_requirement=self.simulation_requirement,
                    max_agents=max_agents
                )

            elif tool_name == "search_graph":
                logger.info("search_graph redirected to quick_search")
                return self._execute_tool_with_metadata("quick_search", parameters, report_context)

            elif tool_name == "get_graph_statistics":
                result_obj = self.zep_tools.get_graph_statistics(self.graph_id)

            elif tool_name == "get_entity_summary":
                entity_name = parameters.get("entity_name", "")
                result_obj = self.zep_tools.get_entity_summary(
                    graph_id=self.graph_id,
                    entity_name=entity_name
                )

            elif tool_name == "get_simulation_context":
                logger.info("get_simulation_context redirected to insight_forge")
                query = parameters.get("query", self.simulation_requirement)
                return self._execute_tool_with_metadata("insight_forge", {"query": query}, report_context)

            elif tool_name == "get_entities_by_type":
                entity_type = parameters.get("entity_type", "")
                nodes = self.zep_tools.get_entities_by_type(
                    graph_id=self.graph_id,
                    entity_type=entity_type
                )
                result_obj = [n.to_dict() for n in nodes]

            else:
                return {
                    "text": rt(self.locale, "unknown_tool", tool_name=tool_name),
                    "structured_result": None,
                    "ui_payload": normalize_tool_result_for_ui(tool_name, {"error": rt(self.locale, "unknown_tool", tool_name=tool_name)}, locale=self.locale),
                }

            structured_result = self._serialize_tool_result(result_obj)
            ui_payload = normalize_tool_result_for_ui(tool_name, structured_result if structured_result is not None else result_obj, locale=self.locale)
            if hasattr(result_obj, "to_text"):
                text_result = result_obj.to_text(locale=self.locale)
            elif isinstance(result_obj, (dict, list)):
                text_result = json.dumps(result_obj, ensure_ascii=False, indent=2)
            else:
                text_result = str(result_obj)

            return {
                "text": text_result,
                "structured_result": structured_result,
                "ui_payload": ui_payload,
            }

        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name}, error: {str(e)}")
            error_text = rt(self.locale, "tool_execution_failed", error=str(e))
            return {
                "text": error_text,
                "structured_result": {"error": error_text},
                "ui_payload": normalize_tool_result_for_ui(tool_name, {"error": error_text}, locale=self.locale),
            }

    def _execute_tool(self, tool_name: str, parameters: Dict[str, Any], report_context: str = "") -> str:
        return self._execute_tool_with_metadata(tool_name, parameters, report_context=report_context)["text"]

    # 合法的工具名称集合，用于裸 JSON 兜底解析时校验
    VALID_TOOL_NAMES = {"insight_forge", "panorama_search", "quick_search", "interview_agents"}

    def _parse_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """
        从LLM响应中解析工具调用

        支持的格式（按优先级）：
        1. <tool_call>{"name": "tool_name", "parameters": {...}}</tool_call>
        2. 裸 JSON（响应整体或单行就是一个工具调用 JSON）
        """
        tool_calls = []

        # 格式1: XML风格（标准格式）
        xml_pattern = r'<tool_call>\s*(\{.*?\})\s*</tool_call>'
        for match in re.finditer(xml_pattern, response, re.DOTALL):
            try:
                call_data = json.loads(match.group(1))
                tool_calls.append(call_data)
            except json.JSONDecodeError:
                pass

        if tool_calls:
            return tool_calls

        # 格式2: 兜底 - LLM 直接输出裸 JSON（没包 <tool_call> 标签）
        # 只在格式1未匹配时尝试，避免误匹配正文中的 JSON
        stripped = response.strip()
        if stripped.startswith('{') and stripped.endswith('}'):
            try:
                call_data = json.loads(stripped)
                if self._is_valid_tool_call(call_data):
                    tool_calls.append(call_data)
                    return tool_calls
            except json.JSONDecodeError:
                pass

        # 响应可能包含思考文字 + 裸 JSON，尝试提取最后一个 JSON 对象
        json_pattern = r'(\{"(?:name|tool)"\s*:.*?\})\s*$'
        match = re.search(json_pattern, stripped, re.DOTALL)
        if match:
            try:
                call_data = json.loads(match.group(1))
                if self._is_valid_tool_call(call_data):
                    tool_calls.append(call_data)
            except json.JSONDecodeError:
                pass

        return tool_calls

    def _is_valid_tool_call(self, data: dict) -> bool:
        """校验解析出的 JSON 是否是合法的工具调用"""
        # 支持 {"name": ..., "parameters": ...} 和 {"tool": ..., "params": ...} 两种键名
        tool_name = data.get("name") or data.get("tool")
        if tool_name and tool_name in self.VALID_TOOL_NAMES:
            # 统一键名为 name / parameters
            if "tool" in data:
                data["name"] = data.pop("tool")
            if "params" in data and "parameters" not in data:
                data["parameters"] = data.pop("params")
            return True
        return False
    
    def _get_tools_description(self) -> str:
        """生成工具描述文本"""
        desc_parts = [rt(self.locale, "available_tools")]
        for name, tool in self.tools.items():
            params_desc = ", ".join([f"{k}: {v}" for k, v in tool["parameters"].items()])
            desc_parts.append(f"- {name}: {tool['description']}")
            if params_desc:
                desc_parts.append(f"  {rt(self.locale, 'parameters_label')}: {params_desc}")
        return "\n".join(desc_parts)
    
    def plan_outline(
        self, 
        progress_callback: Optional[Callable] = None
    ) -> ReportOutline:
        """
        规划报告大纲
        
        使用LLM分析模拟需求，规划报告的目录结构
        
        Args:
            progress_callback: 进度回调函数
            
        Returns:
            ReportOutline: 报告大纲
        """
        logger.info("Starting report outline planning...")
        
        if progress_callback:
            progress_callback("planning", 0, rt(self.locale, "analyzing_requirement"))
        
        # 首先获取模拟上下文
        context = self.zep_tools.get_simulation_context(
            graph_id=self.graph_id,
            simulation_requirement=self.simulation_requirement
        )
        
        if progress_callback:
            progress_callback("planning", 30, rt(self.locale, "generating_outline"))
        
        language_context = self._build_language_context()
        system_prompt = pt(self.locale, "plan_system_prompt", **language_context)
        user_prompt = pt(self.locale, "plan_user_prompt",
            simulation_requirement=self.simulation_requirement,
            total_nodes=context.get('graph_statistics', {}).get('total_nodes', 0),
            total_edges=context.get('graph_statistics', {}).get('total_edges', 0),
            entity_types=list(context.get('graph_statistics', {}).get('entity_types', {}).keys()),
            total_entities=context.get('total_entities', 0),
            related_facts_json=json.dumps(context.get('related_facts', [])[:10], ensure_ascii=False, indent=2),
            **language_context,
        )

        try:
            response = self.llm.chat_json(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            if progress_callback:
                progress_callback("planning", 80, rt(self.locale, "parsing_outline"))
            
            # 解析大纲
            sections = []
            for section_data in response.get("sections", []):
                sections.append(ReportSection(
                    title=section_data.get("title", ""),
                    content=""
                ))
            
            outline = ReportOutline(
                title=response.get("title", rt(self.locale, "default_report_title")),
                summary=response.get("summary", ""),
                sections=sections
            )
            
            if progress_callback:
                progress_callback("planning", 100, rt(self.locale, "outline_done"))
            
            logger.info(f"Outline planning complete: {len(sections)} sections")
            return outline
            
        except Exception as e:
            logger.error(f"Outline planning failed: {str(e)}")
            # 返回默认大纲（3个章节，作为fallback）
            return ReportOutline(
                title=rt(self.locale, "default_future_report_title"),
                summary=rt(self.locale, "default_future_report_summary"),
                sections=[
                    ReportSection(title=rt(self.locale, "default_section_1")),
                    ReportSection(title=rt(self.locale, "default_section_2")),
                    ReportSection(title=rt(self.locale, "default_section_3"))
                ]
            )
    
    def _generate_section_react(
        self, 
        section: ReportSection,
        outline: ReportOutline,
        previous_sections: List[str],
        progress_callback: Optional[Callable] = None,
        section_index: int = 0
    ) -> str:
        """
        使用ReACT模式生成单个章节内容
        
        ReACT循环：
        1. Thought（思考）- 分析需要什么信息
        2. Action（行动）- 调用工具获取信息
        3. Observation（观察）- 分析工具返回结果
        4. 重复直到信息足够或达到最大次数
        5. Final Answer（最终回答）- 生成章节内容
        
        Args:
            section: 要生成的章节
            outline: 完整大纲
            previous_sections: 之前章节的内容（用于保持连贯性）
            progress_callback: 进度回调
            section_index: 章节索引（用于日志记录）
            
        Returns:
            章节内容（Markdown格式）
        """
        logger.info(f"Generating section with ReACT: {section.title}")
        
        # 记录章节开始日志
        if self.report_logger:
            self.report_logger.log_section_start(section.title, section_index)
        
        language_context = self._build_language_context()
        system_prompt = pt(self.locale, "section_system_prompt",
            report_title=outline.title,
            report_summary=outline.summary,
            simulation_requirement=self.simulation_requirement,
            section_title=section.title,
            tools_description=self._get_tools_description(),
            **language_context,
        )

        # 构建用户prompt - 每个已完成章节各传入最大4000字
        if previous_sections:
            previous_parts = []
            for sec in previous_sections:
                # 每个章节最多4000字
                truncated = sec[:4000] + "..." if len(sec) > 4000 else sec
                previous_parts.append(truncated)
            previous_content = "\n\n---\n\n".join(previous_parts)
        else:
            previous_content = rt(self.locale, "first_section_placeholder")
        
        user_prompt = pt(self.locale, "section_user_prompt",
            previous_content=previous_content,
            section_title=section.title,
            **language_context,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # ReACT循环
        tool_calls_count = 0
        max_iterations = 5  # 最大迭代轮数
        min_tool_calls = 3  # 最少工具调用次数
        conflict_retries = 0  # 工具调用与Final Answer同时出现的连续冲突次数
        used_tools = set()  # 记录已调用过的工具名
        all_tools = {"insight_forge", "panorama_search", "quick_search", "interview_agents"}
        section_tool_events: List[Dict[str, Any]] = []

        # 报告上下文，用于InsightForge的子问题生成
        report_context = rt(
            self.locale,
            "report_context_template",
            section_title=section.title,
            simulation_requirement=self.simulation_requirement,
        )
        
        for iteration in range(max_iterations):
            if progress_callback:
                progress_callback(
                    "generating", 
                    int((iteration / max_iterations) * 100),
                    rt(self.locale, "deep_search_writing", current=tool_calls_count, max=self.MAX_TOOL_CALLS_PER_SECTION)
                )
            
            # 调用LLM
            response = self.llm.chat(
                messages=messages,
                temperature=0.5,
                max_tokens=4096
            )

            # 检查 LLM 返回是否为 None（API 异常或内容为空）
            if response is None:
                logger.warning(f"Section {section.title}, iteration {iteration + 1}: LLM returned None")
                # 如果还有迭代次数，添加消息并重试
                if iteration < max_iterations - 1:
                    messages.append({"role": "assistant", "content": rt(self.locale, "empty_response_marker")})
                    messages.append({"role": "user", "content": rt(self.locale, "please_continue")})
                    continue
                # 最后一次迭代也返回 None，跳出循环进入强制收尾
                break

            logger.debug(f"LLM response: {response[:200]}...")

            # 解析一次，复用结果
            tool_calls = self._parse_tool_calls(response)
            has_tool_calls = bool(tool_calls)
            parsed_final_answer = extract_final_answer(response)
            has_final_answer = bool(parsed_final_answer or has_final_answer_marker(response))

            # ── 冲突处理：LLM 同时输出了工具调用和 Final Answer ──
            if has_tool_calls and has_final_answer:
                conflict_retries += 1
                logger.warning(
                    f"章节 {section.title} 第 {iteration+1} 轮: "
                    f"LLM 同时输出工具调用和 Final Answer（第 {conflict_retries} 次冲突）"
                )

                if conflict_retries <= 2:
                    # 前两次：丢弃本次响应，要求 LLM 重新回复
                    messages.append({"role": "assistant", "content": response})
                    messages.append({
                        "role": "user",
                        "content": rt(self.locale, "conflict_retry_message"),
                    })
                    continue
                else:
                    # 第三次：降级处理，截断到第一个工具调用，强制执行
                    logger.warning(
                        f"章节 {section.title}: 连续 {conflict_retries} 次冲突，"
                        "降级为截断执行第一个工具调用"
                    )
                    first_tool_end = response.find('</tool_call>')
                    if first_tool_end != -1:
                        response = response[:first_tool_end + len('</tool_call>')]
                        tool_calls = self._parse_tool_calls(response)
                        has_tool_calls = bool(tool_calls)
                    has_final_answer = False
                    conflict_retries = 0

            # 记录 LLM 响应日志
            evidence_context = build_section_source_bundle(section_tool_events, locale=self.locale) if section_tool_events else None
            if self.report_logger:
                self.report_logger.log_llm_response(
                    section_title=section.title,
                    section_index=section_index,
                    response=response,
                    iteration=iteration + 1,
                    has_tool_calls=has_tool_calls,
                    has_final_answer=has_final_answer,
                    ui_payload=build_llm_response_ui_payload(
                        response,
                        locale=self.locale,
                        has_final_answer=has_final_answer,
                        evidence_context=evidence_context,
                    ),
                    evidence_context=evidence_context,
                )

            # ── 情况1：LLM 输出了 Final Answer ──
            if has_final_answer:
                # 工具调用次数不足，拒绝并要求继续调工具
                if tool_calls_count < min_tool_calls:
                    messages.append({"role": "assistant", "content": response})
                    unused_tools = all_tools - used_tools
                    unused_hint = rt(self.locale, "unused_tools_recommendation", tools=", ".join(unused_tools)) if unused_tools else ""
                    messages.append({
                        "role": "user",
                        "content": pt(self.locale, "react_insufficient",
                            tool_calls_count=tool_calls_count,
                            min_tool_calls=min_tool_calls,
                            unused_hint=unused_hint,
                        ),
                    })
                    continue

                # 正常结束
                final_answer = (parsed_final_answer or response).strip()
                logger.info(f"Section {section.title} completed (tool calls: {tool_calls_count})")

                if self.report_logger:
                    self.report_logger.log_section_content(
                        section_title=section.title,
                        section_index=section_index,
                        content=final_answer,
                        tool_calls_count=tool_calls_count
                    )
                return final_answer

            # ── 情况2：LLM 尝试调用工具 ──
            if has_tool_calls:
                # 工具额度已耗尽 → 明确告知，要求输出 Final Answer
                if tool_calls_count >= self.MAX_TOOL_CALLS_PER_SECTION:
                    messages.append({"role": "assistant", "content": response})
                    messages.append({
                        "role": "user",
                        "content": pt(self.locale, "react_tool_limit",
                            tool_calls_count=tool_calls_count,
                            max_tool_calls=self.MAX_TOOL_CALLS_PER_SECTION,
                        ),
                    })
                    continue

                # 只执行第一个工具调用
                call = tool_calls[0]
                if len(tool_calls) > 1:
                    logger.info(f"LLM attempted {len(tool_calls)} tool calls; executing only the first: {call['name']}")

                if self.report_logger:
                    self.report_logger.log_tool_call(
                        section_title=section.title,
                        section_index=section_index,
                        tool_name=call["name"],
                        parameters=call.get("parameters", {}),
                        iteration=iteration + 1
                    )

                tool_execution = self._execute_tool_with_metadata(
                    call["name"],
                    call.get("parameters", {}),
                    report_context=report_context
                )
                result = tool_execution["text"]

                if self.report_logger:
                    self.report_logger.log_tool_result(
                        section_title=section.title,
                        section_index=section_index,
                        tool_name=call["name"],
                        result=result,
                        iteration=iteration + 1,
                        structured_result=tool_execution.get("structured_result"),
                        ui_payload=tool_execution.get("ui_payload"),
                    )

                section_tool_events.append({
                    "toolName": call["name"],
                    "iteration": iteration + 1,
                    "parameters": copy.deepcopy(call.get("parameters", {})),
                    "ui_payload": copy.deepcopy(tool_execution.get("ui_payload") if isinstance(tool_execution.get("ui_payload"), dict) else {}),
                })

                tool_calls_count += 1
                used_tools.add(call['name'])

                # 构建未使用工具提示
                unused_tools = all_tools - used_tools
                unused_hint = ""
                if unused_tools and tool_calls_count < self.MAX_TOOL_CALLS_PER_SECTION:
                    unused_hint = pt(self.locale, "react_unused_tools_hint", unused_list=", ".join(unused_tools))

                messages.append({"role": "assistant", "content": response})
                messages.append({
                    "role": "user",
                    "content": pt(self.locale, "react_observation",
                        tool_name=call["name"],
                        result=result,
                        tool_calls_count=tool_calls_count,
                        max_tool_calls=self.MAX_TOOL_CALLS_PER_SECTION,
                        used_tools_str=", ".join(used_tools),
                        unused_hint=unused_hint,
                    ),
                })
                continue

            # ── 情况3：既没有工具调用，也没有 Final Answer ──
            messages.append({"role": "assistant", "content": response})

            if tool_calls_count < min_tool_calls:
                # 工具调用次数不足，推荐未用过的工具
                unused_tools = all_tools - used_tools
                unused_hint = rt(self.locale, "unused_tools_recommendation", tools=", ".join(unused_tools)) if unused_tools else ""

                messages.append({
                    "role": "user",
                    "content": pt(self.locale, "react_insufficient_alt",
                        tool_calls_count=tool_calls_count,
                        min_tool_calls=min_tool_calls,
                        unused_hint=unused_hint,
                    ),
                })
                continue

            # 工具调用已足够，LLM 输出了内容但没带 "Final Answer:" 前缀
            # 直接将这段内容作为最终答案，不再空转
            logger.info(f"Section {section.title}: no Final Answer prefix detected; accepting raw LLM output as final content (tool calls: {tool_calls_count})")
            final_answer = response.strip()

            if self.report_logger:
                self.report_logger.log_section_content(
                    section_title=section.title,
                    section_index=section_index,
                    content=final_answer,
                    tool_calls_count=tool_calls_count
                )
            return final_answer
        
        # 达到最大迭代次数，强制生成内容
        logger.warning(f"Section {section.title} reached the maximum iteration count; forcing final generation")
        messages.append({"role": "user", "content": pt(self.locale, "react_force_final")})
        
        response = self.llm.chat(
            messages=messages,
            temperature=0.5,
            max_tokens=4096
        )

        forced_evidence_context = build_section_source_bundle(section_tool_events, locale=self.locale) if section_tool_events else None
        if response is not None and self.report_logger:
            forced_final_answer = bool(extract_final_answer(response) or has_final_answer_marker(response))
            self.report_logger.log_llm_response(
                section_title=section.title,
                section_index=section_index,
                response=response,
                iteration=max_iterations + 1,
                has_tool_calls=bool(self._parse_tool_calls(response)),
                has_final_answer=forced_final_answer,
                ui_payload=build_llm_response_ui_payload(
                    response,
                    locale=self.locale,
                    has_final_answer=forced_final_answer,
                    evidence_context=forced_evidence_context,
                ),
                evidence_context=forced_evidence_context,
            )

        # 检查强制收尾时 LLM 返回是否为 None
        if response is None:
            logger.error(f"Section {section.title}: LLM returned None during forced finalization; using fallback error text")
            final_answer = rt(self.locale, "section_generation_failed_empty")
        elif extract_final_answer(response):
            final_answer = extract_final_answer(response).strip()
        else:
            final_answer = response
        
        # 记录章节内容生成完成日志
        if self.report_logger:
            self.report_logger.log_section_content(
                section_title=section.title,
                section_index=section_index,
                content=final_answer,
                tool_calls_count=tool_calls_count
            )
        
        return final_answer
    
    def generate_report(
        self, 
        progress_callback: Optional[Callable[[str, int, str], None]] = None,
        report_id: Optional[str] = None
    ) -> Report:
        """
        生成完整报告（分章节实时输出）
        
        每个章节生成完成后立即保存到文件夹，不需要等待整个报告完成。
        文件结构：
        reports/{report_id}/
            meta.json       - 报告元信息
            outline.json    - 报告大纲
            progress.json   - 生成进度
            section_01.md   - 第1章节
            section_02.md   - 第2章节
            ...
            full_report.md  - 完整报告
        
        Args:
            progress_callback: 进度回调函数 (stage, progress, message)
            report_id: 报告ID（可选，如果不传则自动生成）
            
        Returns:
            Report: 完整报告
        """
        import uuid
        
        # 如果没有传入 report_id，则自动生成
        if not report_id:
            report_id = f"report_{uuid.uuid4().hex[:12]}"
        start_time = datetime.now()
        
        report = Report(
            report_id=report_id,
            simulation_id=self.simulation_id,
            graph_id=self.graph_id,
            simulation_requirement=self.simulation_requirement,
            status=ReportStatus.PENDING,
            created_at=datetime.now().isoformat()
        )
        
        # 已完成的章节标题列表（用于进度追踪）
        completed_section_titles = []
        
        try:
            # 初始化：创建报告文件夹并保存初始状态
            ReportManager._ensure_report_folder(report_id)
            
            # 初始化日志记录器（结构化日志 agent_log.jsonl）
            self.report_logger = ReportLogger(report_id, locale=self.locale)
            self.report_logger.log_start(
                simulation_id=self.simulation_id,
                graph_id=self.graph_id,
                simulation_requirement=self.simulation_requirement
            )
            
            # 初始化控制台日志记录器（console_log.txt）
            self.console_logger = ReportConsoleLogger(report_id)
            
            ReportManager.update_progress(
                report_id, "pending", 0, rt(self.locale, "initializing_report"),
                completed_sections=[]
            )
            ReportManager.save_report(report)
            
            # 阶段1: 规划大纲
            report.status = ReportStatus.PLANNING
            ReportManager.update_progress(
                report_id, "planning", 5, rt(self.locale, "planning_report"),
                completed_sections=[]
            )
            
            # 记录规划开始日志
            self.report_logger.log_planning_start()
            
            if progress_callback:
                progress_callback("planning", 0, rt(self.locale, "planning_report"))
            
            outline = self.plan_outline(
                progress_callback=lambda stage, prog, msg: 
                    progress_callback(stage, prog // 5, msg) if progress_callback else None
            )
            report.outline = outline
            
            # 记录规划完成日志
            self.report_logger.log_planning_complete(outline.to_dict())
            
            # 保存大纲到文件
            ReportManager.save_outline(report_id, outline)
            ReportManager.update_progress(
                report_id, "planning", 15, rt(self.locale, "outline_complete_count", count=len(outline.sections)),
                completed_sections=[]
            )
            ReportManager.save_report(report)
            
            logger.info(f"Outline saved to file: {report_id}/outline.json")
            
            # 阶段2: 逐章节生成（分章节保存）
            report.status = ReportStatus.GENERATING
            
            total_sections = len(outline.sections)
            generated_sections = []  # 保存内容用于上下文
            
            for i, section in enumerate(outline.sections):
                section_num = i + 1
                base_progress = 20 + int((i / total_sections) * 70)
                
                # 更新进度
                ReportManager.update_progress(
                    report_id, "generating", base_progress,
                    rt(self.locale, "generating_section", title=section.title, current=section_num, total=total_sections),
                    current_section=section.title,
                    completed_sections=completed_section_titles
                )
                
                if progress_callback:
                    progress_callback(
                        "generating", 
                        base_progress, 
                        rt(self.locale, "generating_section", title=section.title, current=section_num, total=total_sections)
                    )
                
                # 生成主章节内容
                section_content = self._generate_section_react(
                    section=section,
                    outline=outline,
                    previous_sections=generated_sections,
                    progress_callback=lambda stage, prog, msg:
                        progress_callback(
                            stage, 
                            base_progress + int(prog * 0.7 / total_sections),
                            msg
                        ) if progress_callback else None,
                    section_index=section_num
                )
                
                section.content = section_content
                generated_sections.append(f"## {section.title}\n\n{section_content}")

                # 保存章节
                ReportManager.save_section(report_id, section_num, section, locale=self.locale)
                completed_section_titles.append(section.title)

                # 记录章节完成日志
                full_section_content = f"## {section.title}\n\n{section_content}"

                if self.report_logger:
                    self.report_logger.log_section_full_complete(
                        section_title=section.title,
                        section_index=section_num,
                        full_content=full_section_content.strip()
                    )

                logger.info(f"Section saved: {report_id}/section_{section_num:02d}.md")
                
                # 更新进度
                ReportManager.update_progress(
                    report_id, "generating", 
                    base_progress + int(70 / total_sections),
                    rt(self.locale, "section_done", title=section.title),
                    current_section=None,
                    completed_sections=completed_section_titles
                )
            
            # 阶段3: 组装完整报告
            if progress_callback:
                progress_callback("generating", 95, rt(self.locale, "assembling_report"))
            
            ReportManager.update_progress(
                report_id, "generating", 95, rt(self.locale, "assembling_report"),
                completed_sections=completed_section_titles
            )
            
            # 使用ReportManager组装完整报告
            report.markdown_content = ReportManager.assemble_full_report(report_id, outline)
            report.status = ReportStatus.COMPLETED
            report.completed_at = datetime.now().isoformat()
            
            # 计算总耗时
            total_time_seconds = (datetime.now() - start_time).total_seconds()
            
            # 记录报告完成日志
            if self.report_logger:
                self.report_logger.log_report_complete(
                    total_sections=total_sections,
                    total_time_seconds=total_time_seconds
                )
            
            # 保存最终报告
            ReportManager.save_report(report)
            ReportManager.update_progress(
                report_id, "completed", 100, rt(self.locale, "report_done"),
                completed_sections=completed_section_titles
            )
            
            if progress_callback:
                progress_callback("completed", 100, rt(self.locale, "report_done"))
            
            logger.info(f"Report generation complete: {report_id}")
            
            # 关闭控制台日志记录器
            if self.console_logger:
                self.console_logger.close()
                self.console_logger = None
            
            return report
            
        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}")
            report.status = ReportStatus.FAILED
            report.error = str(e)
            
            # 记录错误日志
            if self.report_logger:
                self.report_logger.log_error(str(e), "failed")
            
            # 保存失败状态
            try:
                ReportManager.save_report(report)
                ReportManager.update_progress(
                    report_id, "failed", -1, rt(self.locale, "report_failed", error=str(e)),
                    completed_sections=completed_section_titles
                )
            except Exception:
                pass  # 忽略保存失败的错误
            
            # 关闭控制台日志记录器
            if self.console_logger:
                self.console_logger.close()
                self.console_logger = None
            
            return report
    
    def chat(
        self, 
        message: str,
        chat_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        与Report Agent对话
        
        在对话中Agent可以自主调用检索工具来回答问题
        
        Args:
            message: 用户消息
            chat_history: 对话历史
            
        Returns:
            {
                "response": "Agent回复",
                "tool_calls": [调用的工具列表],
                "sources": [信息来源]
            }
        """
        logger.info(f"Report Agent chat: {message[:50]}...")
        
        chat_history = chat_history or []
        
        # 获取已生成的报告内容
        report_content = ""
        try:
            report = ReportManager.get_report_by_simulation(self.simulation_id)
            if report and report.markdown_content:
                # 限制报告长度，避免上下文过长
                report_content = report.markdown_content[:15000]
                if len(report.markdown_content) > 15000:
                    report_content += "\n\n" + rt(self.locale, "report_content_truncated")
        except Exception as e:
            logger.warning(f"Failed to fetch report content: {e}")
        
        language_context = self._build_language_context()
        system_prompt = pt(self.locale, "chat_system_prompt",
            simulation_requirement=self.simulation_requirement,
            report_content=report_content if report_content else rt(self.locale, "no_report"),
            tools_description=self._get_tools_description(),
            **language_context,
        )

        # 构建消息
        messages = [{"role": "system", "content": system_prompt}]
        
        # 添加历史对话
        for h in chat_history[-10:]:  # 限制历史长度
            messages.append(h)
        
        # 添加用户消息
        messages.append({
            "role": "user", 
            "content": message
        })
        
        # ReACT循环（简化版）
        tool_calls_made = []
        max_iterations = 2  # 减少迭代轮数
        
        for iteration in range(max_iterations):
            response = self.llm.chat(
                messages=messages,
                temperature=0.5
            )
            
            # 解析工具调用
            tool_calls = self._parse_tool_calls(response)
            
            if not tool_calls:
                # 没有工具调用，直接返回响应
                clean_response = re.sub(r'<tool_call>.*?</tool_call>', '', response, flags=re.DOTALL)
                clean_response = re.sub(r'\[TOOL_CALL\].*?\)', '', clean_response)
                
                return {
                    "response": clean_response.strip(),
                    "tool_calls": tool_calls_made,
                    "sources": [tc.get("parameters", {}).get("query", "") for tc in tool_calls_made]
                }
            
            # 执行工具调用（限制数量）
            tool_results = []
            for call in tool_calls[:1]:  # 每轮最多执行1次工具调用
                if len(tool_calls_made) >= self.MAX_TOOL_CALLS_PER_CHAT:
                    break
                result = self._execute_tool(call["name"], call.get("parameters", {}))
                tool_results.append({
                    "tool": call["name"],
                    "result": result[:1500]  # 限制结果长度
                })
                tool_calls_made.append(call)
            
            # 将结果添加到消息
            messages.append({"role": "assistant", "content": response})
            observation = "\n".join([f"{rt(self.locale, 'tool_result_block_label', tool=r['tool'])}\n{r['result']}" for r in tool_results])
            messages.append({
                "role": "user",
                "content": observation + pt(self.locale, "chat_observation_suffix")
            })
        
        # 达到最大迭代，获取最终响应
        final_response = self.llm.chat(
            messages=messages,
            temperature=0.5
        )
        
        # 清理响应
        clean_response = re.sub(r'<tool_call>.*?</tool_call>', '', final_response, flags=re.DOTALL)
        clean_response = re.sub(r'\[TOOL_CALL\].*?\)', '', clean_response)
        
        return {
            "response": clean_response.strip(),
            "tool_calls": tool_calls_made,
            "sources": [tc.get("parameters", {}).get("query", "") for tc in tool_calls_made]
        }


class ReportManager:
    """
    报告管理器
    
    负责报告的持久化存储和检索
    
    文件结构（分章节输出）：
    reports/
      {report_id}/
        meta.json          - 报告元信息和状态
        outline.json       - 报告大纲
        progress.json      - 生成进度
        section_01.md      - 第1章节
        section_02.md      - 第2章节
        ...
        full_report.md     - 完整报告
    """
    
    # 报告存储目录
    REPORTS_DIR = os.path.join(Config.UPLOAD_FOLDER, 'reports')
    
    @classmethod
    def _ensure_reports_dir(cls):
        """确保报告根目录存在"""
        os.makedirs(cls.REPORTS_DIR, exist_ok=True)
    
    @classmethod
    def _get_report_folder(cls, report_id: str) -> str:
        """获取报告文件夹路径"""
        return os.path.join(cls.REPORTS_DIR, report_id)
    
    @classmethod
    def _ensure_report_folder(cls, report_id: str) -> str:
        """确保报告文件夹存在并返回路径"""
        folder = cls._get_report_folder(report_id)
        os.makedirs(folder, exist_ok=True)
        return folder
    
    @classmethod
    def _get_report_path(cls, report_id: str) -> str:
        """获取报告元信息文件路径"""
        return os.path.join(cls._get_report_folder(report_id), "meta.json")
    
    @classmethod
    def _get_report_markdown_path(cls, report_id: str) -> str:
        """获取完整报告Markdown文件路径"""
        return os.path.join(cls._get_report_folder(report_id), "full_report.md")
    
    @classmethod
    def _get_outline_path(cls, report_id: str) -> str:
        """获取大纲文件路径"""
        return os.path.join(cls._get_report_folder(report_id), "outline.json")
    
    @classmethod
    def _get_progress_path(cls, report_id: str) -> str:
        """获取进度文件路径"""
        return os.path.join(cls._get_report_folder(report_id), "progress.json")
    
    @classmethod
    def _get_section_path(cls, report_id: str, section_index: int) -> str:
        """获取章节Markdown文件路径"""
        return os.path.join(cls._get_report_folder(report_id), f"section_{section_index:02d}.md")

    @classmethod
    def _get_section_meta_path(cls, report_id: str, section_index: int) -> str:
        """获取章节元数据文件路径"""
        return os.path.join(cls._get_report_folder(report_id), f"section_{section_index:02d}.json")

    @classmethod
    def _extract_section_title_from_markdown(cls, markdown_content: str, default: str = "") -> str:
        """从章节 Markdown 中提取一级章节标题。"""
        value = str(markdown_content or "").strip()
        if not value:
            return default
        match = re.search(r"^##\s+(.+)$", value, flags=re.MULTILINE)
        if match:
            return match.group(1).strip()
        return default

    @classmethod
    def _titles_match(cls, left: str, right: str) -> bool:
        def normalize(value: str) -> str:
            return re.sub(r"\s+", "", str(value or "")).strip().lower()
        return bool(normalize(left) and normalize(left) == normalize(right))

    @classmethod
    def load_outline(cls, report_id: str) -> Optional[ReportOutline]:
        """加载报告大纲文件。"""
        path = cls._get_outline_path(report_id)
        if not os.path.exists(path):
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            sections = []
            for section in data.get('sections', []) or []:
                if not isinstance(section, dict):
                    continue
                sections.append(
                    ReportSection(
                        title=str(section.get('title') or ''),
                        content=str(section.get('content') or '')
                    )
                )
            return ReportOutline(
                title=str(data.get('title') or ''),
                summary=str(data.get('summary') or ''),
                sections=sections
            )
        except Exception as exc:
            logger.warning(f"Failed to load outline for {report_id}: {exc}")
            return None

    @classmethod
    def _load_section_metadata(cls, report_id: str, section_index: int) -> Dict[str, Any]:
        """读取章节元数据文件；若不存在则返回空字典。"""
        path = cls._get_section_meta_path(report_id, section_index)
        if not os.path.exists(path):
            return {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception as exc:
            logger.warning(f"Failed to read section metadata for {report_id}/section_{section_index:02d}: {exc}")
            return {}

    @classmethod
    def _build_section_entry(
        cls,
        report_id: str,
        section_index: int,
        locale: str = "en",
        include_content: bool = True,
        fallback_title: str = "",
        fallback_status: str = "pending",
    ) -> Dict[str, Any]:
        """构建统一的章节条目结构，优先使用 JSON 元数据。"""
        file_path = cls._get_section_path(report_id, section_index)
        file_exists = os.path.exists(file_path)
        metadata = cls._load_section_metadata(report_id, section_index)
        content = ''
        if include_content and file_exists:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

        title = str(
            metadata.get('title')
            or cls._extract_section_title_from_markdown(content, default=fallback_title)
            or fallback_title
            or f'Section {section_index:02d}'
        )
        status = str(metadata.get('status') or ('completed' if file_exists else fallback_status or 'pending'))
        generated_at = metadata.get('generated_at')
        if not generated_at and file_exists:
            generated_at = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()

        entry = {
            'filename': f'section_{section_index:02d}.md',
            'metadata_filename': f'section_{section_index:02d}.json',
            'section_index': section_index,
            'title': title,
            'status': status,
            'generated_at': generated_at or '',
            'locale': metadata.get('locale') or normalize_locale(locale),
            'content_format': metadata.get('content_format') or 'markdown',
            'has_content': bool(file_exists),
            'content': content if include_content and file_exists else '',
            'ui_payload': metadata.get('ui_payload'),
            'provenance': metadata.get('provenance') or cls._aggregate_section_provenance(report_id, section_index),
            'source_bundle': metadata.get('source_bundle') or cls._aggregate_section_source_bundle(report_id, section_index, locale=locale),
        }
        return normalize_section_entry_for_ui(entry, locale=locale)

    @classmethod
    def _get_agent_log_path(cls, report_id: str) -> str:
        """获取 Agent 日志文件路径"""
        return os.path.join(cls._get_report_folder(report_id), "agent_log.jsonl")
    
    @classmethod
    def _get_console_log_path(cls, report_id: str) -> str:
        """获取控制台日志文件路径"""
        return os.path.join(cls._get_report_folder(report_id), "console_log.txt")
    
    @classmethod
    def get_console_log(cls, report_id: str, from_line: int = 0) -> Dict[str, Any]:
        """
        获取控制台日志内容
        
        这是报告生成过程中的控制台输出日志（INFO、WARNING等），
        与 agent_log.jsonl 的结构化日志不同。
        
        Args:
            report_id: 报告ID
            from_line: 从第几行开始读取（用于增量获取，0 表示从头开始）
            
        Returns:
            {
                "logs": [日志行列表],
                "total_lines": 总行数,
                "from_line": 起始行号,
                "has_more": 是否还有更多日志
            }
        """
        log_path = cls._get_console_log_path(report_id)
        
        if not os.path.exists(log_path):
            return {
                "logs": [],
                "total_lines": 0,
                "from_line": 0,
                "has_more": False
            }
        
        logs = []
        total_lines = 0
        
        with open(log_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                total_lines = i + 1
                if i >= from_line:
                    # 保留原始日志行，去掉末尾换行符
                    logs.append(line.rstrip('\n\r'))
        
        return {
            "logs": logs,
            "total_lines": total_lines,
            "from_line": from_line,
            "has_more": False  # 已读取到末尾
        }
    
    @classmethod
    def get_console_log_stream(cls, report_id: str) -> List[str]:
        """
        获取完整的控制台日志（一次性获取全部）
        
        Args:
            report_id: 报告ID
            
        Returns:
            日志行列表
        """
        result = cls.get_console_log(report_id, from_line=0)
        return result["logs"]
    
    @classmethod
    def get_agent_log(cls, report_id: str, from_line: int = 0, locale: str = "en") -> Dict[str, Any]:
        """
        获取 Agent 日志内容
        
        Args:
            report_id: 报告ID
            from_line: 从第几行开始读取（用于增量获取，0 表示从头开始）
            
        Returns:
            {
                "logs": [日志条目列表],
                "total_lines": 总行数,
                "from_line": 起始行号,
                "has_more": 是否还有更多日志
            }
        """
        log_path = cls._get_agent_log_path(report_id)
        
        if not os.path.exists(log_path):
            return {
                "logs": [],
                "total_lines": 0,
                "from_line": 0,
                "has_more": False
            }
        
        logs = []
        total_lines = 0
        
        with open(log_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                total_lines = i + 1
                if i >= from_line:
                    try:
                        log_entry = json.loads(line.strip())
                        logs.append(normalize_log_entry_for_ui(log_entry, locale=locale))
                    except json.JSONDecodeError:
                        # 跳过解析失败的行
                        continue
        
        return {
            "logs": logs,
            "total_lines": total_lines,
            "from_line": from_line,
            "has_more": False  # 已读取到末尾
        }
    
    @classmethod
    def get_agent_log_stream(cls, report_id: str, locale: str = "en") -> List[Dict[str, Any]]:
        """
        获取完整的 Agent 日志（用于一次性获取全部）
        
        Args:
            report_id: 报告ID
            
        Returns:
            日志条目列表
        """
        result = cls.get_agent_log(report_id, from_line=0, locale=locale)
        return result["logs"]
    
    @classmethod
    def save_outline(cls, report_id: str, outline: ReportOutline) -> None:
        """
        保存报告大纲
        
        在规划阶段完成后立即调用
        """
        cls._ensure_report_folder(report_id)
        
        with open(cls._get_outline_path(report_id), 'w', encoding='utf-8') as f:
            json.dump(outline.to_dict(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"Outline saved: {report_id}")
    
    @classmethod
    def _iter_agent_log_entries(cls, report_id: str) -> List[Dict[str, Any]]:
        """Read structured agent log lines for report-level aggregation."""
        log_path = cls._get_agent_log_path(report_id)
        entries: List[Dict[str, Any]] = []
        if not os.path.exists(log_path):
            return entries
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                for raw in f:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        parsed = json.loads(raw)
                    except Exception:
                        continue
                    if isinstance(parsed, dict):
                        entries.append(parsed)
        except Exception as exc:
            logger.warning(f"Failed to aggregate agent log for {report_id}: {exc}")
        return entries

    @classmethod
    def _aggregate_section_provenance(cls, report_id: str, section_index: int) -> Dict[str, Any]:
        """Summarize tool usage and evidence for one generated section."""
        tool_names: List[str] = []
        tool_call_count = 0
        tool_result_count = 0
        llm_response_count = 0
        quote_count = 0
        evidence_counts = {
            'facts': 0,
            'entities': 0,
            'relationships': 0,
            'interviews': 0,
            'questions': 0,
            'citations': 0,
        }
        final_answer_count = 0
        previews: List[str] = []

        for entry in cls._iter_agent_log_entries(report_id):
            if int(entry.get('section_index') or 0) != int(section_index):
                continue
            action = str(entry.get('action') or '')
            details = entry.get('details') if isinstance(entry.get('details'), dict) else {}
            if action == 'tool_call':
                tool_call_count += 1
                name = str(details.get('tool_name') or '')
                if name:
                    tool_names.append(name)
            elif action == 'tool_result':
                tool_result_count += 1
                payload = details.get('ui_payload') if isinstance(details.get('ui_payload'), dict) else {}
                kind = str(payload.get('kind') or '')
                if kind == 'quick_search':
                    evidence_counts['facts'] += int(payload.get('count') or len(payload.get('facts') or []))
                    evidence_counts['relationships'] += len(payload.get('edges') or [])
                    evidence_counts['entities'] += len(payload.get('nodes') or [])
                elif kind == 'insight_forge':
                    stats = payload.get('stats') if isinstance(payload.get('stats'), dict) else {}
                    evidence_counts['facts'] += int(stats.get('facts') or len(payload.get('facts') or []))
                    evidence_counts['entities'] += int(stats.get('entities') or len(payload.get('entities') or []))
                    evidence_counts['relationships'] += int(stats.get('relationships') or len(payload.get('relations') or []))
                elif kind == 'panorama_search':
                    stats = payload.get('stats') if isinstance(payload.get('stats'), dict) else {}
                    evidence_counts['facts'] += int(stats.get('activeFacts') or len(payload.get('activeFacts') or []))
                    evidence_counts['facts'] += int(stats.get('historicalFacts') or len(payload.get('historicalFacts') or []))
                    evidence_counts['entities'] += int(stats.get('nodes') or len(payload.get('entities') or []))
                    evidence_counts['relationships'] += int(stats.get('edges') or len(payload.get('edges') or []))
                elif kind == 'interview_agents':
                    evidence_counts['interviews'] += int(payload.get('successCount') or len(payload.get('interviews') or []))
                    evidence_counts['questions'] += int(payload.get('questionCount') or 0)
                    quote_count += int(payload.get('quoteCount') or 0)

                evidence_counts['citations'] += int(payload.get('citationCount') or 0)
                preview = str(payload.get('summary') or payload.get('summaryPreview') or '').strip()
                if preview and preview not in previews:
                    previews.append(preview)
            elif action == 'llm_response':
                llm_response_count += 1
                payload = details.get('ui_payload') if isinstance(details.get('ui_payload'), dict) else {}
                if payload.get('hasFinalAnswer'):
                    final_answer_count += 1
                evidence_counts['facts'] += int(payload.get('factLikeCount') or 0)
                evidence_counts['citations'] += int(payload.get('citationCount') or 0)
                quote_count += int(payload.get('quoteCount') or 0)
                preview = str(payload.get('finalAnswerPreview') or payload.get('responsePreview') or '').strip()
                if preview and preview not in previews:
                    previews.append(preview)

        unique_tools: List[str] = []
        seen = set()
        for tool in tool_names:
            if tool and tool not in seen:
                unique_tools.append(tool)
                seen.add(tool)

        return {
            'toolCalls': int(tool_call_count),
            'toolResults': int(tool_result_count),
            'llmResponses': int(llm_response_count),
            'finalAnswers': int(final_answer_count),
            'toolsUsed': unique_tools,
            'quoteCount': int(quote_count),
            'evidence': evidence_counts,
            'previewSnippets': previews[:4],
        }

    @classmethod
    def _aggregate_section_source_bundle(cls, report_id: str, section_index: int, locale: str = "en") -> Dict[str, Any]:
        """Build a frontend-stable research bundle from structured tool logs."""
        call_lookup: Dict[tuple, Dict[str, Any]] = {}
        tool_events: List[Dict[str, Any]] = []

        for entry in cls._iter_agent_log_entries(report_id):
            if int(entry.get('section_index') or 0) != int(section_index):
                continue
            action = str(entry.get('action') or '')
            details = entry.get('details') if isinstance(entry.get('details'), dict) else {}
            tool_name = str(details.get('tool_name') or '')
            iteration = int(details.get('iteration') or 0)

            if action == 'tool_call':
                if tool_name:
                    call_lookup[(iteration, tool_name)] = {
                        'parameters': copy.deepcopy(details.get('parameters') if isinstance(details.get('parameters'), dict) else {}),
                        'iteration': iteration,
                        'toolName': tool_name,
                    }
                continue

            if action != 'tool_result':
                continue

            payload = details.get('ui_payload') if isinstance(details.get('ui_payload'), dict) else normalize_tool_result_for_ui(
                tool_name,
                details.get('result_structured') if details.get('result_structured') is not None else details.get('result'),
                locale=locale,
            )
            if not isinstance(payload, dict):
                continue

            lookup = call_lookup.get((iteration, tool_name), {})
            tool_events.append({
                'toolName': tool_name,
                'iteration': iteration,
                'parameters': copy.deepcopy(lookup.get('parameters') or {}),
                'payload': payload,
                'ui_payload': payload,
            })

        return build_section_source_bundle(tool_events, locale=locale)

    @classmethod
    def save_section(
        cls,
        report_id: str,
        section_index: int,
        section: ReportSection,
        locale: str = "en"
    ) -> str:
        """
        保存单个章节

        在每个章节生成完成后立即调用，实现分章节输出

        Args:
            report_id: 报告ID
            section_index: 章节索引（从1开始）
            section: 章节对象
            locale: 当前输出语言

        Returns:
            保存的文件路径
        """
        cls._ensure_report_folder(report_id)

        # 构建章节Markdown内容 - 清理可能存在的重复标题
        cleaned_content = cls._clean_section_content(section.content, section.title)
        md_content = f"## {section.title}\n\n"
        if cleaned_content:
            md_content += f"{cleaned_content}\n\n"

        # 保存 Markdown 文件
        file_suffix = f"section_{section_index:02d}.md"
        file_path = os.path.join(cls._get_report_folder(report_id), file_suffix)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        generated_at = datetime.now().isoformat()
        provenance = cls._aggregate_section_provenance(report_id, section_index)
        source_bundle = cls._aggregate_section_source_bundle(report_id, section_index, locale=locale)
        section_ui_payload = build_section_ui_payload(
            title=section.title,
            content=md_content,
            section_index=section_index,
            locale=locale,
            status="completed",
            generated_at=generated_at,
            source_bundle=source_bundle,
        )
        claim_bundle = section_ui_payload.get("claimBundle") if isinstance(section_ui_payload.get("claimBundle"), dict) else None
        section_meta = {
            "filename": file_suffix,
            "metadata_filename": f"section_{section_index:02d}.json",
            "section_index": section_index,
            "title": section.title,
            "status": "completed",
            "generated_at": generated_at,
            "locale": normalize_locale(locale),
            "content_format": "markdown",
            "has_content": True,
            "provenance": provenance,
            "source_bundle": source_bundle,
            "claim_bundle": claim_bundle,
            "ui_payload": section_ui_payload,
        }
        meta_path = cls._get_section_meta_path(report_id, section_index)
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(section_meta, f, ensure_ascii=False, indent=2)

        logger.info(f"Section saved: {report_id}/{file_suffix}")
        return file_path

    @classmethod
    def _clean_section_content(cls, content: str, section_title: str) -> str:
        """
        清理章节内容
        
        1. 移除内容开头与章节标题重复的Markdown标题行
        2. 将所有 ### 及以下级别的标题转换为粗体文本
        
        Args:
            content: 原始内容
            section_title: 章节标题
            
        Returns:
            清理后的内容
        """
        import re
        
        if not content:
            return content
        
        content = content.strip()
        lines = content.split('\n')
        cleaned_lines = []
        skip_next_empty = False
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # 检查是否是Markdown标题行
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
            
            if heading_match:
                level = len(heading_match.group(1))
                title_text = heading_match.group(2).strip()
                
                # 检查是否是与章节标题重复的标题（跳过前5行内的重复）
                if i < 5:
                    if title_text == section_title or title_text.replace(' ', '') == section_title.replace(' ', ''):
                        skip_next_empty = True
                        continue
                
                # 将所有级别的标题（#, ##, ###, ####等）转换为粗体
                # 因为章节标题由系统添加，内容中不应有任何标题
                cleaned_lines.append(f"**{title_text}**")
                cleaned_lines.append("")  # 添加空行
                continue
            
            # 如果上一行是被跳过的标题，且当前行为空，也跳过
            if skip_next_empty and stripped == '':
                skip_next_empty = False
                continue
            
            skip_next_empty = False
            cleaned_lines.append(line)
        
        # 移除开头的空行
        while cleaned_lines and cleaned_lines[0].strip() == '':
            cleaned_lines.pop(0)
        
        # 移除开头的分隔线
        while cleaned_lines and cleaned_lines[0].strip() in ['---', '***', '___']:
            cleaned_lines.pop(0)
            # 同时移除分隔线后的空行
            while cleaned_lines and cleaned_lines[0].strip() == '':
                cleaned_lines.pop(0)
        
        return '\n'.join(cleaned_lines)
    
    @classmethod
    def update_progress(
        cls, 
        report_id: str, 
        status: str, 
        progress: int, 
        message: str,
        current_section: str = None,
        completed_sections: List[str] = None
    ) -> None:
        """
        更新报告生成进度
        
        前端可以通过读取progress.json获取实时进度
        """
        cls._ensure_report_folder(report_id)
        
        progress_data = {
            "status": status,
            "progress": progress,
            "message": message,
            "current_section": current_section,
            "completed_sections": completed_sections or [],
            "updated_at": datetime.now().isoformat()
        }
        
        with open(cls._get_progress_path(report_id), 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def get_progress(cls, report_id: str) -> Optional[Dict[str, Any]]:
        """获取报告生成进度"""
        path = cls._get_progress_path(report_id)
        
        if not os.path.exists(path):
            return None
        
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @classmethod
    def get_generated_sections(
        cls,
        report_id: str,
        locale: str = "en",
        include_pending: bool = False,
        include_content: bool = True
    ) -> List[Dict[str, Any]]:
        """
        获取章节列表。

        默认返回已生成章节；当 include_pending=True 时，会结合 outline/progress
        返回完整的章节清单（completed/current/pending）。
        """
        folder = cls._get_report_folder(report_id)
        outline = cls.load_outline(report_id)
        progress = cls.get_progress(report_id) or {}

        if not os.path.exists(folder) and not outline:
            return []

        completed_by_index: Dict[int, Dict[str, Any]] = {}
        if os.path.exists(folder):
            for filename in sorted(os.listdir(folder)):
                if not (filename.startswith('section_') and filename.endswith('.md')):
                    continue
                try:
                    section_index = int(filename.replace('.md', '').split('_')[1])
                except (IndexError, ValueError):
                    continue
                completed_by_index[section_index] = cls._build_section_entry(
                    report_id=report_id,
                    section_index=section_index,
                    locale=locale,
                    include_content=include_content,
                    fallback_status='completed',
                )

        if not include_pending:
            return [completed_by_index[idx] for idx in sorted(completed_by_index.keys())]

        planned_sections = outline.sections if outline else []
        highest_index = max(completed_by_index.keys(), default=0)
        total_sections = max(len(planned_sections), highest_index)
        current_section_title = str(progress.get('current_section') or '')
        completed_titles = [str(item or '') for item in (progress.get('completed_sections') or [])]

        sections: List[Dict[str, Any]] = []
        for idx in range(1, total_sections + 1):
            planned_title = planned_sections[idx - 1].title if idx <= len(planned_sections) else ''
            if idx in completed_by_index:
                entry = completed_by_index[idx]
                if planned_title and not entry.get('title'):
                    entry['title'] = planned_title
                entry['status'] = 'completed'
                entry = normalize_section_entry_for_ui(entry, locale=locale)
                sections.append(entry)
                continue

            fallback_status = 'pending'
            if planned_title and cls._titles_match(current_section_title, planned_title):
                fallback_status = 'current'
            elif planned_title and any(cls._titles_match(planned_title, item) for item in completed_titles):
                fallback_status = 'completed'

            entry = cls._build_section_entry(
                report_id=report_id,
                section_index=idx,
                locale=locale,
                include_content=include_content,
                fallback_title=planned_title,
                fallback_status=fallback_status,
            )
            if planned_title and not entry.get('title'):
                entry['title'] = planned_title
            entry['status'] = fallback_status if not entry.get('has_content') else 'completed'
            entry = normalize_section_entry_for_ui(entry, locale=locale)
            sections.append(entry)

        return sections

    @classmethod
    def assemble_full_report(cls, report_id: str, outline: ReportOutline) -> str:
        """
        组装完整报告
        
        从已保存的章节文件组装完整报告，并进行标题清理
        """
        folder = cls._get_report_folder(report_id)
        
        # 构建报告头部
        md_content = f"# {outline.title}\n\n"
        md_content += f"> {outline.summary}\n\n"
        md_content += f"---\n\n"
        
        # 按顺序读取所有章节文件
        sections = cls.get_generated_sections(report_id)
        for section_info in sections:
            md_content += section_info["content"]
        
        # 后处理：清理整个报告的标题问题
        md_content = cls._post_process_report(md_content, outline)
        
        # 保存完整报告
        full_path = cls._get_report_markdown_path(report_id)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        logger.info(f"Full report assembled: {report_id}")
        return md_content
    
    @classmethod
    def _post_process_report(cls, content: str, outline: ReportOutline) -> str:
        """
        后处理报告内容
        
        1. 移除重复的标题
        2. 保留报告主标题(#)和章节标题(##)，移除其他级别的标题(###, ####等)
        3. 清理多余的空行和分隔线
        
        Args:
            content: 原始报告内容
            outline: 报告大纲
            
        Returns:
            处理后的内容
        """
        import re
        
        lines = content.split('\n')
        processed_lines = []
        prev_was_heading = False
        
        # 收集大纲中的所有章节标题
        section_titles = set()
        for section in outline.sections:
            section_titles.add(section.title)
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # 检查是否是标题行
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
            
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                
                # 检查是否是重复标题（在连续5行内出现相同内容的标题）
                is_duplicate = False
                for j in range(max(0, len(processed_lines) - 5), len(processed_lines)):
                    prev_line = processed_lines[j].strip()
                    prev_match = re.match(r'^(#{1,6})\s+(.+)$', prev_line)
                    if prev_match:
                        prev_title = prev_match.group(2).strip()
                        if prev_title == title:
                            is_duplicate = True
                            break
                
                if is_duplicate:
                    # 跳过重复标题及其后的空行
                    i += 1
                    while i < len(lines) and lines[i].strip() == '':
                        i += 1
                    continue
                
                # 标题层级处理：
                # - # (level=1) 只保留报告主标题
                # - ## (level=2) 保留章节标题
                # - ### 及以下 (level>=3) 转换为粗体文本
                
                if level == 1:
                    if title == outline.title:
                        # 保留报告主标题
                        processed_lines.append(line)
                        prev_was_heading = True
                    elif title in section_titles:
                        # 章节标题错误使用了#，修正为##
                        processed_lines.append(f"## {title}")
                        prev_was_heading = True
                    else:
                        # 其他一级标题转为粗体
                        processed_lines.append(f"**{title}**")
                        processed_lines.append("")
                        prev_was_heading = False
                elif level == 2:
                    if title in section_titles or title == outline.title:
                        # 保留章节标题
                        processed_lines.append(line)
                        prev_was_heading = True
                    else:
                        # 非章节的二级标题转为粗体
                        processed_lines.append(f"**{title}**")
                        processed_lines.append("")
                        prev_was_heading = False
                else:
                    # ### 及以下级别的标题转换为粗体文本
                    processed_lines.append(f"**{title}**")
                    processed_lines.append("")
                    prev_was_heading = False
                
                i += 1
                continue
            
            elif stripped == '---' and prev_was_heading:
                # 跳过标题后紧跟的分隔线
                i += 1
                continue
            
            elif stripped == '' and prev_was_heading:
                # 标题后只保留一个空行
                if processed_lines and processed_lines[-1].strip() != '':
                    processed_lines.append(line)
                prev_was_heading = False
            
            else:
                processed_lines.append(line)
                prev_was_heading = False
            
            i += 1
        
        # 清理连续的多个空行（保留最多2个）
        result_lines = []
        empty_count = 0
        for line in processed_lines:
            if line.strip() == '':
                empty_count += 1
                if empty_count <= 2:
                    result_lines.append(line)
            else:
                empty_count = 0
                result_lines.append(line)
        
        return '\n'.join(result_lines)
    
    @classmethod
    def save_report(cls, report: Report) -> None:
        """保存报告元信息和完整报告"""
        cls._ensure_report_folder(report.report_id)
        
        # 保存元信息JSON
        with open(cls._get_report_path(report.report_id), 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        
        # 保存大纲
        if report.outline:
            cls.save_outline(report.report_id, report.outline)
        
        # 保存完整Markdown报告
        if report.markdown_content:
            with open(cls._get_report_markdown_path(report.report_id), 'w', encoding='utf-8') as f:
                f.write(report.markdown_content)
        
        logger.info(f"Report saved: {report.report_id}")
    
    @classmethod
    def get_report(cls, report_id: str) -> Optional[Report]:
        """获取报告"""
        path = cls._get_report_path(report_id)
        
        if not os.path.exists(path):
            # 兼容旧格式：检查直接存储在reports目录下的文件
            old_path = os.path.join(cls.REPORTS_DIR, f"{report_id}.json")
            if os.path.exists(old_path):
                path = old_path
            else:
                return None
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 重建Report对象
        outline = None
        if data.get('outline'):
            outline_data = data['outline']
            sections = []
            for s in outline_data.get('sections', []):
                sections.append(ReportSection(
                    title=s['title'],
                    content=s.get('content', '')
                ))
            outline = ReportOutline(
                title=outline_data['title'],
                summary=outline_data['summary'],
                sections=sections
            )
        
        # 如果markdown_content为空，尝试从full_report.md读取
        markdown_content = data.get('markdown_content', '')
        if not markdown_content:
            full_report_path = cls._get_report_markdown_path(report_id)
            if os.path.exists(full_report_path):
                with open(full_report_path, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()
        
        return Report(
            report_id=data['report_id'],
            simulation_id=data['simulation_id'],
            graph_id=data['graph_id'],
            simulation_requirement=data['simulation_requirement'],
            status=ReportStatus(data['status']),
            outline=outline,
            markdown_content=markdown_content,
            created_at=data.get('created_at', ''),
            completed_at=data.get('completed_at', ''),
            error=data.get('error')
        )
    
    @classmethod
    def get_report_by_simulation(cls, simulation_id: str) -> Optional[Report]:
        """根据模拟ID获取报告"""
        cls._ensure_reports_dir()
        
        for item in os.listdir(cls.REPORTS_DIR):
            item_path = os.path.join(cls.REPORTS_DIR, item)
            # 新格式：文件夹
            if os.path.isdir(item_path):
                report = cls.get_report(item)
                if report and report.simulation_id == simulation_id:
                    return report
            # 兼容旧格式：JSON文件
            elif item.endswith('.json'):
                report_id = item[:-5]
                report = cls.get_report(report_id)
                if report and report.simulation_id == simulation_id:
                    return report
        
        return None
    
    @classmethod
    def list_reports(cls, simulation_id: Optional[str] = None, limit: int = 50) -> List[Report]:
        """列出报告"""
        cls._ensure_reports_dir()
        
        reports = []
        for item in os.listdir(cls.REPORTS_DIR):
            item_path = os.path.join(cls.REPORTS_DIR, item)
            # 新格式：文件夹
            if os.path.isdir(item_path):
                report = cls.get_report(item)
                if report:
                    if simulation_id is None or report.simulation_id == simulation_id:
                        reports.append(report)
            # 兼容旧格式：JSON文件
            elif item.endswith('.json'):
                report_id = item[:-5]
                report = cls.get_report(report_id)
                if report:
                    if simulation_id is None or report.simulation_id == simulation_id:
                        reports.append(report)
        
        # 按创建时间倒序
        reports.sort(key=lambda r: r.created_at, reverse=True)
        
        return reports[:limit]
    
    @classmethod
    def delete_report(cls, report_id: str) -> bool:
        """删除报告（整个文件夹）"""
        import shutil
        
        folder_path = cls._get_report_folder(report_id)
        
        # 新格式：删除整个文件夹
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            shutil.rmtree(folder_path)
            logger.info(f"Report folder deleted: {report_id}")
            return True
        
        # 兼容旧格式：删除单独的文件
        deleted = False
        old_json_path = os.path.join(cls.REPORTS_DIR, f"{report_id}.json")
        old_md_path = os.path.join(cls.REPORTS_DIR, f"{report_id}.md")
        
        if os.path.exists(old_json_path):
            os.remove(old_json_path)
            deleted = True
        if os.path.exists(old_md_path):
            os.remove(old_md_path)
            deleted = True
        
        return deleted
