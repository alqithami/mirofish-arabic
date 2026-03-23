"""Locale helpers for request handling and multilingual generation."""

from __future__ import annotations

from flask import request

SUPPORTED_LOCALES = ("ar", "en", "zh")
DEFAULT_LOCALE = "ar"

LANGUAGE_NAMES = {
    "ar": "Arabic",
    "en": "English",
    "zh": "Chinese",
}

OUTPUT_LANGUAGE_INSTRUCTIONS = {
    "ar": (
        "【لغة الإخراج】يجب أن يكون هذا الإخراج كله باللغة العربية. "
        "العناوين والملخصات والنصوص والقوائم والاقتباسات المعاد صياغتها والخلاصات وإجابات الدردشة يجب أن تكون عربية طبيعية. "
        "إذا أعادت الأدوات محتوى صينياً أو إنجليزياً، فترجم النص المعروض للمستخدم إلى العربية مع الحفاظ على المعنى. "
        "إذا طُلب JSON فاحتفظ بالمفاتيح كما هي، لكن اجعل كل القيم النصية الموجّهة للمستخدم بالعربية."
    ),
    "en": (
        "【Output language】This output must be fully written in English. "
        "Titles, summaries, body text, lists, quoted paraphrases, conclusions, and chat answers must all be natural English. "
        "If tools return Chinese or mixed-language content, translate user-facing text into English while preserving meaning. "
        "If JSON is required, keep the JSON keys intact but write all user-facing string values in English."
    ),
    "zh": (
        "【输出语言】本次输出必须全部使用中文撰写。标题、摘要、正文、列表、引用转述、结论与对话回答都必须是自然流畅的中文。"
        "若工具返回英文或中英混杂内容，请在写入报告或回答时翻译成中文；必要时可保留专有名词原文并加括注。"
        "若需要输出JSON，则JSON结构键保持原样，但所有面向用户的字符串值都必须使用中文。"
    ),
}

INTERVIEW_PROMPT_PREFIXES = {
    "ar": "اعتمد على شخصيتك وجميع ذكرياتك وأفعالك السابقة، وأجبني مباشرةً نصيًا من دون استدعاء أي أدوات: ",
    "en": "Based on your persona and all of your prior memories and actions, reply directly in plain text without calling any tools: ",
    "zh": "结合你的人设、所有的过往记忆与行动，不调用任何工具直接用文本回复我：",
}

PROFILE_LANGUAGE_HINTS = {
    "ar": "اجعل الحقول الموجهة للمستخدم مثل name وbio وpersona وprofession وinterested_topics بالعربية قدر الإمكان، مع الإبقاء على الأسماء العلم عند الحاجة.",
    "en": "Write user-facing fields such as name, bio, persona, profession, and interested_topics in English unless a proper noun should stay in its original language.",
    "zh": "所有面向用户的字段（name、bio、persona、profession、interested_topics）优先使用中文；必要时可保留专有名词原文。",
}

CONFIG_LANGUAGE_HINTS = {
    "ar": "اجعل الحقول النصية الموجهة للمستخدم مثل السرد والموضوعات الساخنة ومحتوى المنشور الأولي وتفسير التوليد بالعربية. لا تفترض سياقاً صينياً ما لم تفرضه المواد نفسها.",
    "en": "Write user-facing string fields such as the narrative direction, hot topics, initial post content, and generation reasoning in English. Do not assume a China-specific context unless the scenario clearly requires it.",
    "zh": "面向用户的字符串字段（如叙事方向、热点话题、初始帖子内容、生成推理）请使用中文。除非场景明确指向中国，否则不要机械套用中国语境，应优先依据材料中的地区与人群特征生成合理作息。",
}

API_MESSAGES = {
    "report_task_started": {
        "ar": "تم بدء مهمة توليد التقرير. استخدم ‎/api/report/generate/status‎ لمتابعة التقدم.",
        "en": "The report generation task has started. Use /api/report/generate/status to check progress.",
        "zh": "报告生成任务已启动，请通过 /api/report/generate/status 查询进度",
    },
    "report_exists": {
        "ar": "التقرير موجود بالفعل.",
        "en": "The report already exists.",
        "zh": "报告已存在",
    },
    "report_generated": {
        "ar": "تم توليد التقرير.",
        "en": "The report has been generated.",
        "zh": "报告已生成",
    },
    "provide_simulation_id": {
        "ar": "يرجى توفير simulation_id.",
        "en": "Please provide simulation_id.",
        "zh": "请提供 simulation_id",
    },
    "provide_message": {
        "ar": "يرجى توفير message.",
        "en": "Please provide message.",
        "zh": "请提供 message",
    },
    "missing_graph_id": {
        "ar": "معرّف الرسم المعرفي مفقود. تأكد من بناء الرسم أولاً.",
        "en": "Graph ID is missing. Make sure the graph has been built first.",
        "zh": "缺少图谱ID，请确保已构建图谱",
    },
    "missing_simulation_requirement": {
        "ar": "وصف متطلب المحاكاة مفقود.",
        "en": "Simulation requirement is missing.",
        "zh": "缺少模拟需求描述",
    },
    "initializing_report_agent": {
        "ar": "جارٍ تهيئة Report Agent...",
        "en": "Initializing Report Agent...",
        "zh": "初始化Report Agent...",
    },
    "simulation_not_found": {
        "ar": "المحاكاة غير موجودة: {simulation_id}",
        "en": "Simulation not found: {simulation_id}",
        "zh": "模拟不存在: {simulation_id}",
    },
    "project_not_found": {
        "ar": "المشروع غير موجود: {project_id}",
        "en": "Project not found: {project_id}",
        "zh": "项目不存在: {project_id}",
    },
    "provide_task_or_simulation_id": {
        "ar": "يرجى توفير task_id أو simulation_id.",
        "en": "Please provide task_id or simulation_id.",
        "zh": "请提供 task_id 或 simulation_id",
    },
    "task_not_found": {
        "ar": "المهمة غير موجودة: {task_id}",
        "en": "Task not found: {task_id}",
        "zh": "任务不存在: {task_id}",
    },
    "report_not_found": {
        "ar": "التقرير غير موجود: {report_id}",
        "en": "Report not found: {report_id}",
        "zh": "报告不存在: {report_id}",
    },
    "no_report_for_simulation": {
        "ar": "لا يوجد تقرير لهذه المحاكاة: {simulation_id}",
        "en": "No report exists for this simulation: {simulation_id}",
        "zh": "该模拟暂无报告: {simulation_id}",
    },
    "report_deleted": {
        "ar": "تم حذف التقرير: {report_id}",
        "en": "Report deleted: {report_id}",
        "zh": "报告已删除: {report_id}",
    },
    "report_or_progress_missing": {
        "ar": "التقرير غير موجود أو أن معلومات التقدم غير متاحة: {report_id}",
        "en": "Report not found or progress data unavailable: {report_id}",
        "zh": "报告不存在或进度信息不可用: {report_id}",
    },
    "section_not_found": {
        "ar": "القسم غير موجود: section_{section_index}",
        "en": "Section not found: section_{section_index}",
        "zh": "章节不存在: section_{section_index}",
    },
    "provide_graph_id_and_query": {
        "ar": "يرجى توفير graph_id و query.",
        "en": "Please provide graph_id and query.",
        "zh": "请提供 graph_id 和 query",
    },
    "provide_graph_id": {
        "ar": "يرجى توفير graph_id.",
        "en": "Please provide graph_id.",
        "zh": "请提供 graph_id",
    },
}


def normalize_locale(candidate: str | None, default: str = DEFAULT_LOCALE) -> str:
    if not candidate or not isinstance(candidate, str):
        return default
    base = candidate.split(',')[0].split(';')[0].strip().lower().split('-')[0]
    return base if base in SUPPORTED_LOCALES else default


def parse_accept_language(header_value: str | None, default: str = DEFAULT_LOCALE) -> str:
    if not header_value:
        return default
    for part in header_value.split(','):
        base = normalize_locale(part, default=None)
        if base:
            return base
    return default


def get_request_locale(default: str = DEFAULT_LOCALE) -> str:
    try:
        header_value = request.headers.get('Accept-Language')
    except RuntimeError:
        return default
    return parse_accept_language(header_value, default=default)


def get_language_name(locale: str) -> str:
    return LANGUAGE_NAMES.get(normalize_locale(locale), LANGUAGE_NAMES[DEFAULT_LOCALE])


def get_output_language_instruction(locale: str) -> str:
    return OUTPUT_LANGUAGE_INSTRUCTIONS.get(normalize_locale(locale), OUTPUT_LANGUAGE_INSTRUCTIONS[DEFAULT_LOCALE])


def get_interview_prompt_prefix(locale: str) -> str:
    return INTERVIEW_PROMPT_PREFIXES.get(normalize_locale(locale), INTERVIEW_PROMPT_PREFIXES[DEFAULT_LOCALE])


def get_profile_language_hint(locale: str) -> str:
    return PROFILE_LANGUAGE_HINTS.get(normalize_locale(locale), PROFILE_LANGUAGE_HINTS[DEFAULT_LOCALE])


def get_config_language_hint(locale: str) -> str:
    return CONFIG_LANGUAGE_HINTS.get(normalize_locale(locale), CONFIG_LANGUAGE_HINTS[DEFAULT_LOCALE])


def localize_text(key: str, locale: str, **params) -> str:
    entry = API_MESSAGES.get(key, {})
    text = entry.get(normalize_locale(locale), entry.get(DEFAULT_LOCALE, key))
    for k, v in params.items():
        text = text.replace('{' + k + '}', str(v))
    return text
