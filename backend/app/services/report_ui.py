"""Helpers to normalize report-agent outputs into frontend-stable UI payloads."""

from __future__ import annotations

import copy
import hashlib
import re
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ..utils.locale import normalize_locale
UI_TEXT = {
    "en": {
        "no_response": "[No response]",
        "tool_error": "Tool execution failed",
    },
    "ar": {
        "no_response": "[لا توجد إجابة]",
        "tool_error": "فشل تنفيذ الأداة",
    },
    "zh": {
        "no_response": "[无回复]",
        "tool_error": "工具执行失败",
    },
}

TWITTER_HEADERS = [
    "【Twitter response】",
    "【Twitter platform response】",
    "【Twitter平台回答】",
    "【Twitter 回答】",
    "【إجابة منصة تويتر】",
    "Twitter response:",
    "Twitter Response:",
    "Twitter:",
    "تويتر:",
]

REDDIT_HEADERS = [
    "【Reddit response】",
    "【Reddit platform response】",
    "【Reddit平台回答】",
    "【Reddit 回答】",
    "【إجابة منصة ريديت】",
    "Reddit response:",
    "Reddit Response:",
    "Reddit:",
    "ريديت:",
]

NO_PLATFORM_PLACEHOLDERS = {
    "[No response]",
    "(No response)",
    "(No response from this platform)",
    "[无回复]",
    "（该平台未获得回复）",
    "(该平台未获得回复)",
    "[لا توجد إجابة]",
    "(لا توجد إجابة)",
    "(لم تصل أي إجابة من هذه المنصة)",
}


def _t(locale: str, key: str, **params: Any) -> str:
    normalized = normalize_locale(locale)
    template = UI_TEXT.get(normalized, UI_TEXT["en"]).get(key, UI_TEXT["en"].get(key, key))
    for name, value in params.items():
        template = template.replace("{" + name + "}", str(value))
    return template



def _coerce_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []



def _first_nonempty(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return ""



def _truncate(value: str, max_len: int = 280) -> str:
    if not value:
        return ""
    value = str(value)
    return value if len(value) <= max_len else value[: max_len - 3].rstrip() + "..."



def _stable_short_id(prefix: str, *parts: Any, length: int = 12) -> str:
    seed = "||".join(str(part or "").strip() for part in parts)
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:length]
    normalized_prefix = re.sub(r"[^a-z0-9]+", "_", str(prefix or "item").lower()).strip("_") or "item"
    return f"{normalized_prefix}_{digest}"



def _build_tool_run_id(tool_name: Any, iteration: Any, query: Any = "", summary: Any = "") -> str:
    return _stable_short_id("run", tool_name, iteration, query, summary)



def _normalize_entity_type(entity: Dict[str, Any]) -> str:
    if not isinstance(entity, dict):
        return ""
    entity_type = entity.get("type")
    if entity_type:
        return str(entity_type)
    labels = entity.get("labels")
    if isinstance(labels, list):
        for label in labels:
            if label not in {"Entity", "Node"}:
                return str(label)
        if labels:
            return str(labels[0])
    return ""



def _normalize_node(node: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(node, dict):
        return None
    name = _first_nonempty(node.get("name"), node.get("realname"), node.get("username"))
    if not name:
        return None
    return {
        "name": str(name),
        "type": _normalize_entity_type(node),
        "summary": str(node.get("summary") or ""),
    }



def _normalize_edge(edge: Any) -> Optional[Dict[str, Any]]:
    if isinstance(edge, str):
        return _parse_relation_chain_text(edge)
    if not isinstance(edge, dict):
        return None
    source = _first_nonempty(edge.get("source_node_name"), edge.get("source"), edge.get("source_node_uuid"))
    relation = _first_nonempty(edge.get("name"), edge.get("relation"), edge.get("label"))
    target = _first_nonempty(edge.get("target_node_name"), edge.get("target"), edge.get("target_node_uuid"))
    fact = str(edge.get("fact") or "")
    normalized = {
        "source": str(source or ""),
        "relation": str(relation or ""),
        "target": str(target or ""),
        "fact": fact,
        "validAt": edge.get("valid_at") or edge.get("validAt") or "",
        "invalidAt": edge.get("invalid_at") or edge.get("invalidAt") or "",
        "expiredAt": edge.get("expired_at") or edge.get("expiredAt") or "",
    }
    if any(normalized.values()):
        return normalized
    return None



def _parse_relation_chain_text(chain: str) -> Optional[Dict[str, Any]]:
    if not isinstance(chain, str):
        return None
    text = chain.strip()
    if not text:
        return None
    match = re.match(r"(.+?)\s*--\[(.+?)\]-->\s*(.+)", text)
    if match:
        return {
            "source": match.group(1).strip(),
            "relation": match.group(2).strip(),
            "target": match.group(3).strip(),
            "fact": "",
            "validAt": "",
            "invalidAt": "",
            "expiredAt": "",
        }
    return {
        "source": text,
        "relation": "",
        "target": "",
        "fact": "",
        "validAt": "",
        "invalidAt": "",
        "expiredAt": "",
    }



def _serialize_result(result: Any) -> Any:
    if result is None:
        return None
    if isinstance(result, (dict, list, str, int, float, bool)):
        return result
    if hasattr(result, "to_dict"):
        try:
            return result.to_dict()
        except Exception:
            return None
    return None



def _find_header(text: str, headers: List[str]) -> Optional[Tuple[int, str]]:
    best: Optional[Tuple[int, str]] = None
    for header in headers:
        idx = text.find(header)
        if idx == -1:
            continue
        if best is None or idx < best[0]:
            best = (idx, header)
    return best



def _clean_platform_text(text: str) -> str:
    if not text:
        return ""
    return text.strip().strip("\n\r ")



def is_placeholder_text(text: Any) -> bool:
    if text is None:
        return True
    return str(text).strip() in NO_PLATFORM_PLACEHOLDERS



def split_platform_responses(response_text: str, locale: str = "en") -> Dict[str, Any]:
    text = str(response_text or "").strip()
    if not text:
        return {
            "twitter": _t(locale, "no_response"),
            "reddit": _t(locale, "no_response"),
            "platforms": [],
            "isDualPlatform": False,
        }

    twitter_header = _find_header(text, TWITTER_HEADERS)
    reddit_header = _find_header(text, REDDIT_HEADERS)

    twitter_text = ""
    reddit_text = ""

    if twitter_header and reddit_header:
        if twitter_header[0] < reddit_header[0]:
            twitter_text = text[twitter_header[0] + len(twitter_header[1]) : reddit_header[0]]
            reddit_text = text[reddit_header[0] + len(reddit_header[1]) :]
        else:
            reddit_text = text[reddit_header[0] + len(reddit_header[1]) : twitter_header[0]]
            twitter_text = text[twitter_header[0] + len(twitter_header[1]) :]
    elif twitter_header:
        twitter_text = text[twitter_header[0] + len(twitter_header[1]) :]
    elif reddit_header:
        reddit_text = text[reddit_header[0] + len(reddit_header[1]) :]
    else:
        twitter_text = text

    twitter_text = _clean_platform_text(twitter_text)
    reddit_text = _clean_platform_text(reddit_text)

    if not twitter_text:
        twitter_text = _t(locale, "no_response")
    if not reddit_text:
        reddit_text = _t(locale, "no_response")

    platforms: List[str] = []
    if twitter_text and not is_placeholder_text(twitter_text):
        platforms.append("twitter")
    if reddit_text and not is_placeholder_text(reddit_text):
        platforms.append("reddit")

    return {
        "twitter": twitter_text,
        "reddit": reddit_text,
        "platforms": platforms,
        "isDualPlatform": len(platforms) > 1,
    }



def normalize_search_result_for_ui(result: Any, locale: str = "en") -> Optional[Dict[str, Any]]:
    data = _serialize_result(result)
    if not isinstance(data, dict):
        return None

    facts = [str(item).strip() for item in _coerce_list(data.get("facts")) if str(item).strip()]
    edges = [edge for edge in (_normalize_edge(item) for item in _coerce_list(data.get("edges"))) if edge]
    nodes = [node for node in (_normalize_node(item) for item in _coerce_list(data.get("nodes"))) if node]
    count = data.get("total_count") or data.get("count") or len(facts) or len(edges) or len(nodes)
    fact_cards = [{"text": fact, "preview": _truncate(fact, 160), "direction": _detect_text_direction(fact, locale=locale)} for fact in facts[:6]]
    edge_cards = [
        {
            "source": str(edge.get("source") or ""),
            "relation": str(edge.get("relation") or ""),
            "target": str(edge.get("target") or ""),
            "preview": _truncate(" → ".join([part for part in [str(edge.get("source") or ""), str(edge.get("relation") or ""), str(edge.get("target") or "")] if part]), 160),
        }
        for edge in edges[:6]
    ]
    entity_cards = [
        {
            "name": str(node.get("name") or ""),
            "type": str(node.get("type") or ""),
            "summary": str(node.get("summary") or ""),
            "preview": _truncate(str(node.get("summary") or node.get("name") or ""), 140),
        }
        for node in nodes[:6]
    ]

    return {
        "kind": "quick_search",
        "version": 1,
        "query": str(data.get("query") or ""),
        "count": int(count or 0),
        "facts": facts,
        "edges": edges,
        "nodes": nodes,
        "factCards": fact_cards,
        "edgeCards": edge_cards,
        "entityCards": entity_cards,
        "summary": _truncate("; ".join(facts[:2]) or str(data.get("query") or "")),
    }



def normalize_insight_result_for_ui(result: Any, locale: str = "en") -> Optional[Dict[str, Any]]:
    data = _serialize_result(result)
    if not isinstance(data, dict):
        return None

    facts = [str(item).strip() for item in _coerce_list(data.get("semantic_facts") or data.get("facts")) if str(item).strip()]

    entities: List[Dict[str, Any]] = []
    for entity in _coerce_list(data.get("entity_insights") or data.get("entities")):
        if not isinstance(entity, dict):
            continue
        related_facts = _coerce_list(entity.get("related_facts") or entity.get("relatedFacts"))
        normalized = {
            "name": str(_first_nonempty(entity.get("name"), entity.get("entity_name")) or ""),
            "type": _normalize_entity_type(entity),
            "summary": str(entity.get("summary") or entity.get("description") or ""),
            "relatedFacts": [str(item).strip() for item in related_facts if str(item).strip()],
            "relatedFactsCount": int(entity.get("relatedFactsCount") or len(related_facts) or 0),
        }
        if normalized["name"]:
            entities.append(normalized)

    relations = [
        relation
        for relation in (
            _normalize_edge(item) for item in _coerce_list(data.get("relationship_chains") or data.get("relations"))
        )
        if relation
    ]

    stats = {
        "facts": int(data.get("total_facts") or len(facts) or 0),
        "entities": int(data.get("total_entities") or len(entities) or 0),
        "relationships": int(data.get("total_relationships") or len(relations) or 0),
    }

    return {
        "kind": "insight_forge",
        "version": 1,
        "query": str(data.get("query") or ""),
        "simulationRequirement": str(
            data.get("simulation_requirement") or data.get("simulationRequirement") or ""
        ),
        "subQueries": [
            str(item).strip() for item in _coerce_list(data.get("sub_queries") or data.get("subQueries")) if str(item).strip()
        ],
        "facts": facts,
        "entities": entities,
        "relations": relations,
        "factCards": [{"text": fact, "preview": _truncate(fact, 160), "direction": _detect_text_direction(fact, locale=locale)} for fact in facts[:6]],
        "entityCards": [
            {
                "name": str(entity.get("name") or ""),
                "type": str(entity.get("type") or ""),
                "summary": str(entity.get("summary") or ""),
                "relatedFactsCount": int(entity.get("relatedFactsCount") or 0),
                "preview": _truncate(str(entity.get("summary") or entity.get("name") or ""), 140),
            }
            for entity in entities[:6]
        ],
        "relationCards": [
            {
                "source": str(relation.get("source") or ""),
                "relation": str(relation.get("relation") or ""),
                "target": str(relation.get("target") or ""),
                "preview": _truncate(" → ".join([part for part in [str(relation.get("source") or ""), str(relation.get("relation") or ""), str(relation.get("target") or "")] if part]), 160),
            }
            for relation in relations[:6]
        ],
        "stats": stats,
        "summary": _truncate("; ".join(facts[:2]) or str(data.get("query") or "")),
    }



def normalize_panorama_result_for_ui(result: Any, locale: str = "en") -> Optional[Dict[str, Any]]:
    data = _serialize_result(result)
    if not isinstance(data, dict):
        return None

    active_facts = [str(item).strip() for item in _coerce_list(data.get("active_facts") or data.get("activeFacts")) if str(item).strip()]
    historical_facts = [
        str(item).strip() for item in _coerce_list(data.get("historical_facts") or data.get("historicalFacts")) if str(item).strip()
    ]
    entities = [node for node in (_normalize_node(item) for item in _coerce_list(data.get("all_nodes") or data.get("nodes"))) if node]
    edges = [edge for edge in (_normalize_edge(item) for item in _coerce_list(data.get("all_edges") or data.get("edges"))) if edge]

    return {
        "kind": "panorama_search",
        "version": 1,
        "query": str(data.get("query") or ""),
        "activeFacts": active_facts,
        "historicalFacts": historical_facts,
        "entities": entities,
        "edges": edges,
        "factCards": [
            {
                "text": fact,
                "preview": _truncate(fact, 160),
                "kind": "active",
                "direction": _detect_text_direction(fact, locale=locale),
            }
            for fact in active_facts[:4]
        ] + [
            {
                "text": fact,
                "preview": _truncate(fact, 160),
                "kind": "historical",
                "direction": _detect_text_direction(fact, locale=locale),
            }
            for fact in historical_facts[:2]
        ],
        "stats": {
            "nodes": int(data.get("total_nodes") or len(entities) or 0),
            "edges": int(data.get("total_edges") or len(edges) or 0),
            "activeFacts": int(data.get("active_count") or len(active_facts) or 0),
            "historicalFacts": int(data.get("historical_count") or len(historical_facts) or 0),
        },
        "summary": _truncate("; ".join(active_facts[:2]) or str(data.get("query") or "")),
    }



def normalize_interview_result_for_ui(result: Any, locale: str = "en") -> Optional[Dict[str, Any]]:
    data = _serialize_result(result)
    if not isinstance(data, dict):
        return None

    shared_questions = [
        str(item).strip() for item in _coerce_list(data.get("interview_questions") or data.get("questions")) if str(item).strip()
    ]
    selection_reason = str(data.get("selection_reasoning") or data.get("selectionReason") or "")
    summary = str(data.get("summary") or "")

    interviews: List[Dict[str, Any]] = []
    for index, interview in enumerate(_coerce_list(data.get("interviews"))):
        if not isinstance(interview, dict):
            continue

        split = split_platform_responses(str(interview.get("response") or ""), locale=locale)
        explicit_questions = _coerce_list(interview.get("questions"))
        questions = [
            str(item).strip()
            for item in (explicit_questions or shared_questions or [interview.get("question")])
            if str(item or "").strip()
        ]
        explicit_answers = [str(item).strip() for item in _coerce_list(interview.get("answers")) if str(item).strip()]
        qa_pairs = [
            {
                "question": str(pair.get("question") or "").strip(),
                "twitterAnswer": str(pair.get("twitterAnswer") or pair.get("twitter_answer") or split["twitter"]),
                "redditAnswer": str(pair.get("redditAnswer") or pair.get("reddit_answer") or split["reddit"]),
                "platforms": [str(item) for item in _coerce_list(pair.get("platforms")) if str(item)],
                "isDualPlatform": bool(pair.get("isDualPlatform")),
                "answerPreview": _truncate(str(pair.get("answerPreview") or pair.get("twitterAnswer") or pair.get("redditAnswer") or ""), 180),
                "direction": _detect_text_direction(str(pair.get("question") or "") + "\n" + str(pair.get("twitterAnswer") or "") + "\n" + str(pair.get("redditAnswer") or ""), locale=locale),
            }
            for pair in _coerce_list(interview.get("qa_pairs") or interview.get("qaPairs"))
            if isinstance(pair, dict)
        ]
        if not qa_pairs and questions and explicit_answers and len(explicit_answers) == len(questions):
            qa_pairs = [
                {
                    "question": question,
                    "twitterAnswer": answer,
                    "redditAnswer": _t(locale, "no_response"),
                    "platforms": ["twitter"] if answer and not is_placeholder_text(answer) else [],
                    "isDualPlatform": False,
                    "answerPreview": _truncate(answer or _t(locale, "no_response"), 180),
                    "direction": _detect_text_direction(f"{question}\n{answer}", locale=locale),
                }
                for question, answer in zip(questions, explicit_answers)
            ]
        if not qa_pairs:
            qa_pairs = _build_interview_qa_pairs(questions, split["twitter"], split["reddit"], locale=locale)

        quotes = [str(item).strip() for item in _coerce_list(interview.get("key_quotes") or interview.get("quotes")) if str(item).strip()]
        platforms = sorted({platform for pair in qa_pairs for platform in _coerce_list(pair.get("platforms"))})
        answer_preview_source = next(
            (
                str(pair.get("answerPreview") or "")
                for pair in qa_pairs
                if str(pair.get("answerPreview") or "").strip()
            ),
            str(split["twitter"] if not is_placeholder_text(split["twitter"]) else split["reddit"])
        )

        normalized = {
            "name": str(interview.get("agent_name") or interview.get("name") or f"Agent {index + 1}"),
            "role": str(interview.get("agent_role") or interview.get("role") or ""),
            "bio": str(interview.get("agent_bio") or interview.get("bio") or ""),
            "questions": questions,
            "answers": [item for item in explicit_answers if item] or [item for item in [split["twitter"], split["reddit"]] if item and not is_placeholder_text(item)] or [
                str(interview.get("response") or _t(locale, "no_response"))
            ],
            "twitterAnswer": split["twitter"],
            "redditAnswer": split["reddit"],
            "quotes": quotes,
            "quoteCards": [{"text": quote, "preview": _truncate(quote, 160), "direction": _detect_text_direction(quote, locale=locale)} for quote in quotes[:4]],
            "platforms": platforms or split["platforms"],
            "isDualPlatform": bool(any(bool(pair.get("isDualPlatform")) for pair in qa_pairs) or split["isDualPlatform"]),
            "qaPairs": qa_pairs,
            "answerPreview": _truncate(answer_preview_source or _t(locale, "no_response"), 180),
            "direction": _detect_text_direction(f"{interview.get('agent_name') or interview.get('name') or ''}\n{answer_preview_source}", locale=locale),
            "selectionReason": selection_reason,
        }
        interviews.append(normalized)

    success_count = int(data.get("interviewed_count") or len(interviews) or 0)
    total_count = int(data.get("total_agents") or len(_coerce_list(data.get("selected_agents"))) or success_count)

    total_quotes = sum(len(item.get("quotes") or []) for item in interviews)
    total_questions = sum(len(item.get("questions") or []) for item in interviews)
    platforms = sorted({platform for item in interviews for platform in (item.get("platforms") or [])})
    summary_bullets = _extract_summary_bullets(summary, max_items=4)
    participants = [
        {
            "name": str(item.get("name") or ""),
            "role": str(item.get("role") or ""),
            "bio": str(item.get("bio") or ""),
            "platforms": item.get("platforms") or [],
            "answerPreview": str(item.get("answerPreview") or ""),
        }
        for item in interviews
    ]

    return {
        "kind": "interview_agents",
        "version": 1,
        "topic": str(data.get("interview_topic") or data.get("topic") or ""),
        "successCount": success_count,
        "totalCount": total_count,
        "agentCount": f"{success_count} / {total_count}" if total_count else str(success_count),
        "selectionReason": selection_reason,
        "interviews": interviews,
        "participants": participants,
        "summary": summary,
        "summaryPreview": _truncate(summary, 240),
        "summaryBullets": summary_bullets,
        "quoteCount": int(total_quotes),
        "questionCount": int(total_questions),
        "platforms": platforms,
        "interviewCards": [
            {
                "name": str(item.get("name") or ""),
                "role": str(item.get("role") or ""),
                "preview": str(item.get("answerPreview") or ""),
                "platforms": item.get("platforms") or [],
                "quoteCount": len(item.get("quotes") or []),
            }
            for item in interviews[:6]
        ],
    }



def normalize_generic_result_for_ui(tool_name: str, result: Any, locale: str = "en") -> Optional[Dict[str, Any]]:
    serialized = _serialize_result(result)
    if serialized is None:
        return None
    if isinstance(serialized, dict) and "error" in serialized:
        message = str(serialized.get("error") or _t(locale, "tool_error"))
        return {
            "kind": "error",
            "version": 1,
            "tool": tool_name,
            "message": message,
            "summary": _truncate(message),
        }
    if isinstance(serialized, list):
        return {
            "kind": "list",
            "version": 1,
            "tool": tool_name,
            "items": serialized,
            "summary": _truncate(str(serialized[:3])),
        }
    if isinstance(serialized, dict):
        stats = {
            key: value
            for key, value in serialized.items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        }
        return {
            "kind": "dict",
            "version": 1,
            "tool": tool_name,
            "data": serialized,
            "stats": stats,
            "summary": _truncate(str(stats or serialized)),
        }
    return {
        "kind": "text",
        "version": 1,
        "tool": tool_name,
        "text": str(serialized),
        "summary": _truncate(str(serialized)),
    }



def normalize_tool_result_for_ui(tool_name: str, result: Any, locale: str = "en") -> Optional[Dict[str, Any]]:
    normalized_tool = str(tool_name or "").strip()
    if normalized_tool == "insight_forge":
        return normalize_insight_result_for_ui(result, locale=locale)
    if normalized_tool == "panorama_search":
        return normalize_panorama_result_for_ui(result, locale=locale)
    if normalized_tool == "quick_search":
        return normalize_search_result_for_ui(result, locale=locale)
    if normalized_tool == "interview_agents":
        return normalize_interview_result_for_ui(result, locale=locale)
    return normalize_generic_result_for_ui(normalized_tool, result, locale=locale)



FINAL_ANSWER_PATTERNS = [
    r"<final_answer>([\s\S]*?)</final_answer>",
    r"Final\s*Answer[:：]?\s*\n*([\s\S]*)$",
    r"(?:Final\s*Response|Answer)[:：]\s*\n*([\s\S]*)$",
    r"最终答案[:：]\s*\n*([\s\S]*)$",
    r"(?:الإجابة\s*النهائية|الجواب\s*النهائي|النتيجة\s*النهائية)[:：]?\s*\n*([\s\S]*)$",
]


def has_final_answer_marker(response: str) -> bool:
    text = str(response or "").strip()
    if not text:
        return False
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in FINAL_ANSWER_PATTERNS[1:])


def extract_final_answer(response: str) -> Optional[str]:
    text = str(response or "").strip()
    if not text:
        return None

    for pattern in FINAL_ANSWER_PATTERNS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip() or None

    stripped = re.sub(r"<tool_call>[\s\S]*?</tool_call>", "", text, flags=re.IGNORECASE).strip()
    if stripped.startswith(("#", ">")):
        return stripped

    if len(stripped) > 300 and ("**" in stripped or ">" in stripped):
        thought_match = re.match(r"^(?:Thought|تفكير|思考)[:：][\s\S]*?(?=\n\n[^Tتف思]|\n\n$)", stripped, flags=re.IGNORECASE)
        if thought_match:
            candidate = stripped[len(thought_match.group(0)):].strip()
            if len(candidate) > 100:
                return candidate

    return None


def build_llm_response_ui_payload(
    response: str,
    locale: str = "en",
    has_final_answer: bool = False,
    evidence_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    raw_response = str(response or "")
    final_answer = extract_final_answer(raw_response) if raw_response else None
    content_source = final_answer if final_answer else raw_response
    summary_bullets = _extract_summary_bullets(content_source, max_items=4)
    headings = [match.group(1).strip() for match in _MARKDOWN_HEADING_RE.finditer(str(content_source or "")) if match.group(1).strip()]
    citation_count = len(_extract_markdown_links(content_source))
    quote_count = _extract_callout_count(content_source)
    fact_like_count = _extract_numbered_fact_count(content_source)
    tool_call_count = len(re.findall(r"<tool_call>[\s\S]*?</tool_call>", raw_response, flags=re.IGNORECASE))
    preview_source = final_answer if final_answer else raw_response
    fact_cards = _extract_fact_cards(content_source, locale=locale, max_items=6)
    citation_cards = _extract_markdown_link_cards(content_source, max_items=5)
    quote_cards = _extract_quote_cards(content_source, locale=locale, max_items=4)
    claim_bundle = build_claim_bundle(
        content_source,
        evidence_context=evidence_context,
        locale=locale,
        max_items=4,
    )
    return {
        "kind": "llm_response",
        "version": 4,
        "finalAnswer": final_answer,
        "finalAnswerPreview": _truncate(final_answer or "", 240),
        "responsePreview": _truncate(preview_source or "", 240),
        "summaryBullets": summary_bullets,
        "keywords": _extract_keywords(content_source, locale=locale, max_items=6),
        "headings": headings[:6],
        "factCards": fact_cards,
        "citationCards": citation_cards,
        "quoteCards": quote_cards,
        "claimBundle": claim_bundle,
        "claimCards": copy.deepcopy(claim_bundle.get("claimCards") or []),
        "direction": _detect_text_direction(content_source, locale=locale),
        "citationCount": int(citation_count),
        "quoteCount": int(quote_count),
        "factLikeCount": int(fact_like_count),
        "toolCallCount": int(tool_call_count),
        "responseLength": len(_strip_markdown(content_source)),
        "hasFinalAnswer": bool(has_final_answer or final_answer),
    }


def _ensure_evidence_card_identity(
    card: Dict[str, Any],
    evidence_type: str,
    source_tool: str,
    run_id: str = "",
    source_query: str = "",
    locale: str = "en",
) -> Dict[str, Any]:
    normalized = copy.deepcopy(card or {})
    preview_source = _card_text(normalized)
    preview = str(normalized.get("preview") or _truncate(preview_source, 160) if preview_source else "")
    normalized["preview"] = preview
    normalized["evidenceType"] = str(normalized.get("evidenceType") or evidence_type or "fact")
    normalized["sourceTool"] = str(normalized.get("sourceTool") or source_tool or "")
    normalized["runId"] = str(normalized.get("runId") or run_id or "")
    normalized["sourceQuery"] = str(normalized.get("sourceQuery") or source_query or "")
    normalized["direction"] = str(normalized.get("direction") or _detect_text_direction(preview_source or preview, locale=locale))
    evidence_id = str(normalized.get("evidenceId") or normalized.get("id") or "").strip()
    if not evidence_id:
        evidence_id = _stable_short_id(
            evidence_type,
            normalized.get("sourceTool"),
            normalized.get("runId"),
            normalized.get("sourceQuery"),
            normalized.get("text"),
            normalized.get("name"),
            normalized.get("label"),
            normalized.get("url"),
            normalized.get("source"),
            normalized.get("relation"),
            normalized.get("target"),
            preview,
        )
    normalized["evidenceId"] = evidence_id
    return normalized



def _build_evidence_ref(card: Any, fallback_type: str = "fact") -> Optional[Dict[str, Any]]:
    if not isinstance(card, dict):
        return None
    preview_source = _card_text(card)
    preview = str(card.get("preview") or _truncate(preview_source, 160) if preview_source else "")
    label = str(card.get("label") or "").strip()
    evidence_id = str(card.get("evidenceId") or "").strip()
    if not evidence_id and not preview and not label:
        return None
    return {
        "evidenceId": evidence_id,
        "evidenceType": str(card.get("evidenceType") or fallback_type or "fact"),
        "preview": preview,
        "label": label,
        "url": str(card.get("url") or ""),
        "sourceTool": str(card.get("sourceTool") or ""),
        "runId": str(card.get("runId") or ""),
        "sourceQuery": str(card.get("sourceQuery") or ""),
        "direction": str(card.get("direction") or ""),
    }



def _dedupe_evidence_refs(refs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    deduped: List[Dict[str, Any]] = []
    seen = set()
    for ref in refs:
        if not isinstance(ref, dict):
            continue
        key = (str(ref.get("evidenceId") or ""), str(ref.get("preview") or "").casefold(), str(ref.get("url") or ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(ref)
    return deduped



def build_section_source_bundle(tool_events: List[Dict[str, Any]], locale: str = "en") -> Dict[str, Any]:
    """Build a section-level research bundle directly from structured tool outputs.

    This bundle is meant to be stable for the frontend and avoids re-parsing the
    final markdown whenever possible. Each `tool_event` can contain:
      - toolName / tool_name
      - iteration
      - parameters
      - payload / ui_payload
    """

    normalized_locale = normalize_locale(locale)
    tool_runs: List[Dict[str, Any]] = []
    fact_cards: List[Dict[str, Any]] = []
    citation_cards: List[Dict[str, Any]] = []
    quote_cards: List[Dict[str, Any]] = []
    entity_cards: List[Dict[str, Any]] = []
    relation_cards: List[Dict[str, Any]] = []
    interview_cards: List[Dict[str, Any]] = []
    question_cards: List[Dict[str, Any]] = []
    queries: List[str] = []
    platforms: List[str] = []
    tools_used: List[str] = []
    summary_bullets: List[str] = []
    direction_sources: List[str] = []

    counts = {
        "toolResults": 0,
        "facts": 0,
        "citations": 0,
        "quotes": 0,
        "entities": 0,
        "relations": 0,
        "interviews": 0,
        "questions": 0,
        "evidenceItems": 0,
    }

    def _append_summary(text: Any) -> None:
        value = str(text or "").strip()
        if not value:
            return
        preview = _truncate(value, 180)
        if preview not in summary_bullets:
            summary_bullets.append(preview)

    def _append_tool(tool_name: Any) -> str:
        value = str(tool_name or "").strip()
        if value and value not in tools_used:
            tools_used.append(value)
        return value

    def _append_query(value: Any) -> str:
        query = str(value or "").strip()
        if query and query not in queries:
            queries.append(query)
        return query

    def _append_platforms(values: Any) -> None:
        for platform in _coerce_list(values):
            value = str(platform or "").strip().lower()
            if value and value not in platforms:
                platforms.append(value)

    def _append_direction(value: Any) -> None:
        text_value = str(value or "").strip()
        if text_value:
            direction_sources.append(text_value)

    def _append_fact_card(card: Any, source_tool: str, run_id: str = "", source_query: str = "") -> None:
        if isinstance(card, str):
            text_value = card.strip()
            if not text_value:
                return
            normalized = {
                "text": text_value,
                "preview": _truncate(text_value, 160),
            }
        elif isinstance(card, dict):
            text_value = str(card.get("text") or card.get("preview") or "").strip()
            if not text_value:
                return
            normalized = {
                **copy.deepcopy(card),
                "text": text_value,
                "preview": str(card.get("preview") or _truncate(text_value, 160)),
            }
        else:
            return
        normalized = _ensure_evidence_card_identity(
            normalized,
            evidence_type="fact",
            source_tool=source_tool,
            run_id=run_id,
            source_query=source_query,
            locale=normalized_locale,
        )
        key = normalized["text"].casefold()
        if any(str(existing.get("text") or "").casefold() == key for existing in fact_cards):
            return
        fact_cards.append(normalized)

    def _append_citation_card(card: Any, source_tool: str, run_id: str = "", source_query: str = "") -> None:
        if not isinstance(card, dict):
            return
        url = str(card.get("url") or "").strip()
        label = str(card.get("label") or card.get("preview") or url).strip()
        if not url and not label:
            return
        normalized = {
            **copy.deepcopy(card),
            "label": label or url,
            "url": url,
            "preview": str(card.get("preview") or _truncate(label or url, 120)),
        }
        normalized = _ensure_evidence_card_identity(
            normalized,
            evidence_type="citation",
            source_tool=source_tool,
            run_id=run_id,
            source_query=source_query,
            locale=normalized_locale,
        )
        key = (normalized["label"].casefold(), normalized["url"])
        if any((str(existing.get("label") or "").casefold(), str(existing.get("url") or "")) == key for existing in citation_cards):
            return
        citation_cards.append(normalized)

    def _append_quote_card(card: Any, source_tool: str, run_id: str = "", source_query: str = "") -> None:
        if isinstance(card, str):
            text_value = card.strip()
            if not text_value:
                return
            normalized = {
                "text": text_value,
                "preview": _truncate(text_value, 160),
            }
        elif isinstance(card, dict):
            text_value = str(card.get("text") or card.get("preview") or "").strip()
            if not text_value:
                return
            normalized = {
                **copy.deepcopy(card),
                "text": text_value,
                "preview": str(card.get("preview") or _truncate(text_value, 160)),
            }
        else:
            return
        normalized = _ensure_evidence_card_identity(
            normalized,
            evidence_type="quote",
            source_tool=source_tool,
            run_id=run_id,
            source_query=source_query,
            locale=normalized_locale,
        )
        key = normalized["text"].casefold()
        if any(str(existing.get("text") or "").casefold() == key for existing in quote_cards):
            return
        quote_cards.append(normalized)

    def _append_entity_card(card: Any, source_tool: str, run_id: str = "", source_query: str = "") -> None:
        if not isinstance(card, dict):
            return
        name = str(card.get("name") or "").strip()
        summary = str(card.get("summary") or card.get("preview") or name).strip()
        if not name and not summary:
            return
        normalized = {
            **copy.deepcopy(card),
            "name": name,
            "type": str(card.get("type") or ""),
            "summary": str(card.get("summary") or ""),
            "preview": str(card.get("preview") or _truncate(summary or name, 140)),
        }
        normalized = _ensure_evidence_card_identity(
            normalized,
            evidence_type="entity",
            source_tool=source_tool,
            run_id=run_id,
            source_query=source_query,
            locale=normalized_locale,
        )
        key = (normalized["name"].casefold(), normalized["type"].casefold())
        if any((str(existing.get("name") or "").casefold(), str(existing.get("type") or "").casefold()) == key for existing in entity_cards):
            return
        entity_cards.append(normalized)

    def _append_relation_card(card: Any, source_tool: str, run_id: str = "", source_query: str = "") -> None:
        if not isinstance(card, dict):
            return
        source = str(card.get("source") or "").strip()
        relation = str(card.get("relation") or "").strip()
        target = str(card.get("target") or "").strip()
        preview = str(card.get("preview") or " → ".join([part for part in [source, relation, target] if part])).strip()
        if not preview:
            return
        normalized = {
            **copy.deepcopy(card),
            "source": source,
            "relation": relation,
            "target": target,
            "preview": _truncate(preview, 160),
        }
        normalized = _ensure_evidence_card_identity(
            normalized,
            evidence_type="relation",
            source_tool=source_tool,
            run_id=run_id,
            source_query=source_query,
            locale=normalized_locale,
        )
        key = (normalized["source"].casefold(), normalized["relation"].casefold(), normalized["target"].casefold())
        if any((str(existing.get("source") or "").casefold(), str(existing.get("relation") or "").casefold(), str(existing.get("target") or "").casefold()) == key for existing in relation_cards):
            return
        relation_cards.append(normalized)

    def _append_interview_card(card: Any, source_tool: str, run_id: str = "", source_query: str = "") -> None:
        if not isinstance(card, dict):
            return
        name = str(card.get("name") or "").strip()
        preview = str(card.get("preview") or card.get("answerPreview") or "").strip()
        if not name and not preview:
            return
        normalized = {
            **copy.deepcopy(card),
            "name": name,
            "role": str(card.get("role") or ""),
            "preview": _truncate(preview or name, 180),
            "platforms": [str(item) for item in _coerce_list(card.get("platforms")) if str(item)],
            "quoteCount": int(card.get("quoteCount") or 0),
        }
        normalized = _ensure_evidence_card_identity(
            normalized,
            evidence_type="interview",
            source_tool=source_tool,
            run_id=run_id,
            source_query=source_query,
            locale=normalized_locale,
        )
        key = (normalized["name"].casefold(), normalized["role"].casefold())
        if any((str(existing.get("name") or "").casefold(), str(existing.get("role") or "").casefold()) == key for existing in interview_cards):
            return
        interview_cards.append(normalized)

    def _append_question_card(question: Any, source_tool: str, run_id: str = "", source_query: str = "") -> None:
        text_value = str(question or "").strip()
        if not text_value:
            return
        normalized = {
            "text": text_value,
            "preview": _truncate(text_value, 160),
        }
        normalized = _ensure_evidence_card_identity(
            normalized,
            evidence_type="question",
            source_tool=source_tool,
            run_id=run_id,
            source_query=source_query,
            locale=normalized_locale,
        )
        key = normalized["text"].casefold()
        if any(str(existing.get("text") or "").casefold() == key for existing in question_cards):
            return
        question_cards.append(normalized)

    for raw_event in _coerce_list(tool_events):
        if not isinstance(raw_event, dict):
            continue
        payload = raw_event.get("ui_payload") if isinstance(raw_event.get("ui_payload"), dict) else raw_event.get("payload")
        if not isinstance(payload, dict):
            continue

        counts["toolResults"] += 1
        tool_name = _append_tool(raw_event.get("toolName") or raw_event.get("tool_name") or payload.get("kind") or "")
        parameters = raw_event.get("parameters") if isinstance(raw_event.get("parameters"), dict) else {}
        query = _append_query(payload.get("query") or payload.get("topic") or payload.get("simulationRequirement") or parameters.get("query") or parameters.get("interview_topic"))
        _append_platforms(payload.get("platforms"))
        _append_summary(payload.get("summary") or payload.get("summaryPreview") or query)
        _append_direction(payload.get("summary") or payload.get("summaryPreview") or query)

        kind = str(payload.get("kind") or "")
        stats = payload.get("stats") if isinstance(payload.get("stats"), dict) else {}
        run_summary = str(payload.get("summaryPreview") or payload.get("summary") or query or "").strip()
        run_id = _build_tool_run_id(tool_name, raw_event.get("iteration"), query, run_summary or kind)

        if kind == "quick_search":
            counts["facts"] += int(payload.get("count") or len(payload.get("facts") or []) or 0)
            counts["entities"] += len(payload.get("nodes") or [])
            counts["relations"] += len(payload.get("edges") or [])
        elif kind == "insight_forge":
            counts["facts"] += int(stats.get("facts") or len(payload.get("facts") or []) or 0)
            counts["entities"] += int(stats.get("entities") or len(payload.get("entities") or []) or 0)
            counts["relations"] += int(stats.get("relationships") or len(payload.get("relations") or []) or 0)
        elif kind == "panorama_search":
            counts["facts"] += int(stats.get("activeFacts") or len(payload.get("activeFacts") or []) or 0)
            counts["facts"] += int(stats.get("historicalFacts") or len(payload.get("historicalFacts") or []) or 0)
            counts["entities"] += int(stats.get("nodes") or len(payload.get("entities") or []) or 0)
            counts["relations"] += int(stats.get("edges") or len(payload.get("edges") or []) or 0)
        elif kind == "interview_agents":
            counts["interviews"] += int(payload.get("successCount") or len(payload.get("interviews") or []) or 0)
            counts["questions"] += int(payload.get("questionCount") or 0)
            counts["quotes"] += int(payload.get("quoteCount") or 0)

        counts["citations"] += int(payload.get("citationCount") or len(payload.get("citationCards") or []) or 0)

        for card in _coerce_list(payload.get("factCards")) + _coerce_list(payload.get("activeFactCards")) + _coerce_list(payload.get("historicalFactCards")):
            _append_fact_card(card, tool_name, run_id=run_id, source_query=query)
        for card in _coerce_list(payload.get("citationCards")):
            _append_citation_card(card, tool_name, run_id=run_id, source_query=query)
        for card in _coerce_list(payload.get("quoteCards")):
            _append_quote_card(card, tool_name, run_id=run_id, source_query=query)
        for card in _coerce_list(payload.get("entityCards")):
            _append_entity_card(card, tool_name, run_id=run_id, source_query=query)
        for card in _coerce_list(payload.get("relationCards")) + _coerce_list(payload.get("edgeCards")):
            _append_relation_card(card, tool_name, run_id=run_id, source_query=query)
        for card in _coerce_list(payload.get("interviewCards")) + _coerce_list(payload.get("participants")):
            _append_interview_card(card, tool_name, run_id=run_id, source_query=query)

        for interview in _coerce_list(payload.get("interviews")):
            if not isinstance(interview, dict):
                continue
            _append_platforms(interview.get("platforms"))
            for quote in _coerce_list(interview.get("quoteCards")) + _coerce_list(interview.get("quotes")):
                _append_quote_card(quote, tool_name, run_id=run_id, source_query=query)
            for question in _coerce_list(interview.get("questions")):
                _append_question_card(question, tool_name, run_id=run_id, source_query=query)
            for pair in _coerce_list(interview.get("qaPairs") or interview.get("qa_pairs")):
                if not isinstance(pair, dict):
                    continue
                _append_question_card(pair.get("question"), tool_name, run_id=run_id, source_query=query)
                _append_platforms(pair.get("platforms"))

        tool_runs.append({
            "runId": run_id,
            "toolName": tool_name,
            "resultKind": kind or tool_name,
            "iteration": int(raw_event.get("iteration") or 0),
            "query": str(query or ""),
            "summary": _truncate(run_summary or tool_name, 180),
            "platforms": [str(item) for item in _coerce_list(payload.get("platforms")) if str(item)],
            "direction": str(payload.get("direction") or _detect_text_direction(run_summary or query or tool_name, locale=normalized_locale)),
        })

    if not counts["quotes"]:
        counts["quotes"] = len(quote_cards)
    if not counts["questions"]:
        counts["questions"] = len(question_cards)

    evidence_index: List[Dict[str, Any]] = []
    for fallback_type, cards in (
        ("fact", fact_cards),
        ("citation", citation_cards),
        ("quote", quote_cards),
        ("entity", entity_cards),
        ("relation", relation_cards),
        ("interview", interview_cards),
        ("question", question_cards),
    ):
        for card in cards:
            ref = _build_evidence_ref(card, fallback_type=fallback_type)
            if ref:
                evidence_index.append(ref)
    evidence_index = _dedupe_evidence_refs(evidence_index)
    counts["evidenceItems"] = len(evidence_index)

    display_counts = {
        "facts": len(fact_cards),
        "citations": len(citation_cards),
        "quotes": len(quote_cards),
        "entities": len(entity_cards),
        "relations": len(relation_cards),
        "interviews": len(interview_cards),
        "questions": len(question_cards),
        "toolResults": len(tool_runs),
        "evidenceItems": len(evidence_index),
    }

    direction_text = "\n".join(direction_sources[:4])
    direction = _detect_text_direction(direction_text, locale=normalized_locale) if direction_text else ("rtl" if normalized_locale == "ar" else "ltr")

    return {
        "kind": "section_source_bundle",
        "version": 2,
        "toolsUsed": tools_used,
        "toolSequence": [str(run.get("toolName") or "") for run in tool_runs if str(run.get("toolName") or "")],
        "queries": queries,
        "platforms": platforms,
        "summaryBullets": summary_bullets[:6],
        "factCards": fact_cards[:8],
        "citationCards": citation_cards[:8],
        "quoteCards": quote_cards[:6],
        "entityCards": entity_cards[:6],
        "relationCards": relation_cards[:6],
        "interviewCards": interview_cards[:6],
        "questionCards": question_cards[:8],
        "counts": counts,
        "displayCounts": display_counts,
        "toolRuns": tool_runs[:8],
        "evidenceIndex": evidence_index[:24],
        "direction": direction,
    }


_ARABIC_CHAR_RE = re.compile(r"[\u0600-\u06FF]")
_MARKDOWN_LINK_RE = re.compile(r"(?<!\!)\[([^\]]+)\]\(([^)]+)\)")
_MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
_MARKDOWN_CODE_BLOCK_RE = re.compile(r"```[\s\S]*?```")
_MARKDOWN_INLINE_CODE_RE = re.compile(r"`([^`]*)`")
_MARKDOWN_HEADING_RE = re.compile(r"^\s*#{1,6}\s+(.+)$", flags=re.MULTILINE)


def _strip_markdown(text: str) -> str:
    value = str(text or "")
    if not value:
        return ""
    value = _MARKDOWN_CODE_BLOCK_RE.sub(" ", value)
    value = _MARKDOWN_INLINE_CODE_RE.sub(r"\1", value)
    value = _MARKDOWN_IMAGE_RE.sub(" ", value)
    value = _MARKDOWN_LINK_RE.sub(r"\1", value)
    value = re.sub(r"^\s{0,3}#{1,6}\s*", "", value, flags=re.MULTILINE)
    value = re.sub(r"^\s*>\s?", "", value, flags=re.MULTILINE)
    value = re.sub(r"^\s*[-*+]\s+", "", value, flags=re.MULTILINE)
    value = re.sub(r"^\s*\d+\.\s+", "", value, flags=re.MULTILINE)
    value = value.replace("**", "").replace("__", "")
    value = re.sub(r"(?<!\*)\*(?!\*)", "", value)
    value = re.sub(r"(?<!_)_(?!_)", "", value)
    value = re.sub(r"[ \t]+\n", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def _count_words(text: str) -> int:
    plain = _strip_markdown(text)
    if not plain:
        return 0
    return len(re.findall(r"\S+", plain))


_LATIN_TOKEN_RE = re.compile(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9'_-]{1,}")
_ARABIC_TOKEN_RE = re.compile(r"[\u0600-\u06FF]{2,}")
_CJK_TOKEN_RE = re.compile(r"[\u4E00-\u9FFF]{2,}")

_STOPWORDS = {
    "en": {
        "the", "and", "that", "with", "from", "this", "have", "were", "will", "into", "their",
        "about", "there", "which", "after", "before", "while", "under", "been", "than", "then",
        "they", "them", "also", "more", "most", "such", "through", "across", "because", "where",
        "when", "what", "your", "using", "used", "only", "into", "over", "within", "between",
    },
    "ar": {
        "هذا", "هذه", "ذلك", "تلك", "على", "إلى", "من", "في", "عن", "مع", "كان", "كانت", "يكون", "تكون",
        "هناك", "هنا", "التي", "الذي", "الذين", "اللاتي", "كما", "لكن", "وقد", "ثم", "بعد", "قبل", "عند",
        "ضمن", "حول", "بسبب", "أكثر", "أقل", "فقط", "جداً", "أو", "أي", "كل", "بعض", "تم", "جار", "مما",
    },
    "zh": {"我们", "他们", "以及", "因为", "一个", "已经", "进行", "通过", "对于", "没有", "可以", "需要", "当前", "相关", "情况", "问题", "方面"},
}


def _clean_summary_line(value: str) -> str:
    text = str(value or "")
    text = re.sub(r"^\s{0,3}(?:[-*+]\s+|\d+[.)]\s+|>\s*)", "", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s+", "", text)
    text = text.strip()
    text = text.replace("**", "").replace("__", "")
    text = re.sub(r"(?<!\*)\*(?!\*)", "", text)
    text = re.sub(r"(?<!_)_(?!_)", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _extract_summary_bullets(markdown: str, max_items: int = 3) -> List[str]:
    text = str(markdown or "")
    if not text:
        return []

    candidates: List[str] = []
    lines = text.splitlines()
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^\s{0,3}(?:[-*+]\s+|\d+[.)]\s+|>\s*)", line):
            candidates.append(stripped)

    plain = _strip_markdown(text)
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", plain) if part.strip()]
    for para in paragraphs:
        if len(candidates) >= max_items * 3:
            break
        sentence_split = [item.strip() for item in re.split(r"(?<=[.!?؟。！？])\s+", para) if item.strip()]
        candidates.extend(sentence_split[:2] if sentence_split else [para])

    cleaned: List[str] = []
    seen = set()
    for item in candidates:
        normalized = _clean_summary_line(item)
        if len(normalized) < 12:
            continue
        key = normalized.casefold()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(_truncate(normalized, 140))
        if len(cleaned) >= max_items:
            break
    return cleaned


def _extract_keywords(text: str, locale: str = "en", max_items: int = 6) -> List[str]:
    plain = _strip_markdown(text)
    if not plain:
        return []

    normalized_locale = normalize_locale(locale)
    tokens: List[str] = []
    tokens.extend(_LATIN_TOKEN_RE.findall(plain))
    tokens.extend(_ARABIC_TOKEN_RE.findall(plain))
    if normalized_locale == "zh" and not tokens:
        tokens.extend(_CJK_TOKEN_RE.findall(plain))

    stopwords = _STOPWORDS.get(normalized_locale, set())
    counts: Counter[str] = Counter()
    first_seen: Dict[str, int] = {}

    for index, token in enumerate(tokens):
        normalized = token.strip().casefold()
        normalized = normalized.strip("'\"“”‘’.,;:!?()[]{}<>«»")
        if len(normalized) < 2 or normalized.isdigit():
            continue
        if normalized in stopwords:
            continue
        counts[normalized] += 1
        first_seen.setdefault(normalized, index)

    ranked = sorted(counts.keys(), key=lambda item: (-counts[item], first_seen[item], item))
    return [item for item in ranked[:max_items]]


def _count_markdown_blocks(markdown: str) -> Dict[str, int]:
    text = str(markdown or "")
    lines = text.splitlines()
    list_count = sum(1 for line in lines if re.match(r"^\s{0,3}(?:[-*+]\s+|\d+[.)]\s+)", line))
    quote_count = sum(1 for line in lines if re.match(r"^\s{0,3}>\s*", line))
    plain = _strip_markdown(text)
    paragraph_count = len([part for part in re.split(r"\n\s*\n", plain) if part.strip()])
    return {
        "listCount": int(list_count),
        "quoteCount": int(quote_count),
        "paragraphCount": int(paragraph_count),
    }


def _parse_dt(value: Any) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def _pick_latest_iso(values: List[Any]) -> str:
    candidates = [(_parse_dt(value), str(value)) for value in values if value]
    candidates = [(dt, raw) for dt, raw in candidates if dt is not None]
    if not candidates:
        return ""
    return max(candidates, key=lambda item: item[0])[1]


def _detect_text_direction(text: str, locale: str = "en") -> str:
    plain = _strip_markdown(text)
    normalized = normalize_locale(locale)
    arabic_count = len(_ARABIC_CHAR_RE.findall(plain))
    if normalized == "ar" or arabic_count > 0:
        return "rtl"
    return "ltr"


def _extract_markdown_links(markdown: str) -> List[str]:
    return [match.group(1).strip() for match in _MARKDOWN_LINK_RE.finditer(str(markdown or "")) if match.group(1).strip()]


def _extract_markdown_link_cards(markdown: str, max_items: int = 4) -> List[Dict[str, str]]:
    cards: List[Dict[str, str]] = []
    seen = set()
    for match in _MARKDOWN_LINK_RE.finditer(str(markdown or "")):
        label = str(match.group(1) or "").strip()
        url = str(match.group(2) or "").strip()
        if not label and not url:
            continue
        key = (label.casefold(), url)
        if key in seen:
            continue
        seen.add(key)
        cards.append({
            "label": label or url,
            "url": url,
            "preview": _truncate(label or url, 120),
        })
        if len(cards) >= max_items:
            break
    return cards


def _extract_quote_cards(text: str, locale: str = "en", max_items: int = 4) -> List[Dict[str, Any]]:
    cards: List[Dict[str, Any]] = []
    seen = set()
    for raw_line in str(text or "").splitlines():
        line = raw_line.strip()
        if not line.startswith(">"):
            continue
        quote = re.sub(r"^>+\s*", "", line).strip().strip('"“”')
        if len(quote) < 8:
            continue
        key = quote.casefold()
        if key in seen:
            continue
        seen.add(key)
        cards.append({
            "text": quote,
            "preview": _truncate(quote, 160),
            "direction": _detect_text_direction(quote, locale=locale),
        })
        if len(cards) >= max_items:
            break
    return cards


def _extract_fact_cards(text: str, locale: str = "en", max_items: int = 6) -> List[Dict[str, Any]]:
    candidates: List[Tuple[str, str]] = []
    for raw_line in str(text or "").splitlines():
        if not re.match(r"^\s{0,3}(?:[-*+]\s+|\d+[.)]\s+)", raw_line):
            continue
        cleaned = _clean_summary_line(raw_line)
        if len(cleaned) >= 10:
            candidates.append((cleaned, "list"))

    if not candidates:
        candidates.extend((item, "summary") for item in _extract_summary_bullets(text, max_items=max_items * 2))

    cards: List[Dict[str, Any]] = []
    seen = set()
    for cleaned, source in candidates:
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        cards.append({
            "text": cleaned,
            "preview": _truncate(cleaned, 160),
            "source": source,
            "direction": _detect_text_direction(cleaned, locale=locale),
        })
        if len(cards) >= max_items:
            break
    return cards


def _card_text(card: Any) -> str:
    if isinstance(card, str):
        return card.strip()
    if not isinstance(card, dict):
        return ""
    return " ".join(
        part
        for part in [
            str(card.get("text") or "").strip(),
            str(card.get("preview") or "").strip(),
            str(card.get("name") or "").strip(),
            str(card.get("summary") or "").strip(),
            str(card.get("label") or "").strip(),
            str(card.get("source") or "").strip(),
            str(card.get("relation") or "").strip(),
            str(card.get("target") or "").strip(),
        ]
        if part
    ).strip()


def _normalize_structured_cards(cards: Any) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for card in _coerce_list(cards):
        if isinstance(card, str):
            text = card.strip()
            if text:
                normalized.append({
                    "text": text,
                    "preview": _truncate(text, 160),
                    "direction": _detect_text_direction(text),
                })
            continue
        if not isinstance(card, dict):
            continue
        cloned = copy.deepcopy(card)
        if not cloned.get("preview"):
            preview_source = _card_text(cloned)
            cloned["preview"] = _truncate(preview_source, 160) if preview_source else ""
        normalized.append(cloned)
    return normalized


def _keyword_overlap_score(left: str, right: str, locale: str = "en") -> int:
    left_tokens = set(_extract_keywords(left, locale=locale, max_items=12))
    right_tokens = set(_extract_keywords(right, locale=locale, max_items=12))
    if not left_tokens or not right_tokens:
        return 0
    return len(left_tokens & right_tokens)


def _select_matching_cards(
    claim_text: str,
    cards: Any,
    locale: str = "en",
    limit: int = 2,
) -> List[Dict[str, Any]]:
    normalized_cards = _normalize_structured_cards(cards)
    scored: List[Tuple[int, int, int, Dict[str, Any]]] = []
    for idx, card in enumerate(normalized_cards):
        card_text = _card_text(card)
        score = _keyword_overlap_score(claim_text, card_text, locale=locale)
        if score <= 0:
            continue
        scored.append((score, len(card_text), idx, copy.deepcopy(card)))

    if not scored:
        return []

    scored.sort(key=lambda item: (-item[0], -item[1], item[2]))
    return [card for _, _, _, card in scored[: max(0, int(limit or 0))]]


def _support_level_from_count(evidence_count: int) -> str:
    if evidence_count >= 4:
        return "strong"
    if evidence_count >= 2:
        return "supported"
    if evidence_count >= 1:
        return "light"
    return "unbacked"



def _build_claim_support_refs(
    matched_facts: List[Dict[str, Any]],
    matched_quotes: List[Dict[str, Any]],
    matched_citations: List[Dict[str, Any]],
    matched_entities: List[Dict[str, Any]],
    matched_relations: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    refs: List[Dict[str, Any]] = []
    for fallback_type, cards in (
        ("fact", matched_facts),
        ("quote", matched_quotes),
        ("citation", matched_citations),
        ("entity", matched_entities),
        ("relation", matched_relations),
    ):
        for card in cards:
            ref = _build_evidence_ref(card, fallback_type=fallback_type)
            if ref:
                refs.append(ref)
    return _dedupe_evidence_refs(refs)



def build_claim_bundle(
    text: str,
    evidence_context: Optional[Dict[str, Any]] = None,
    locale: str = "en",
    max_items: int = 4,
) -> Dict[str, Any]:
    normalized_locale = normalize_locale(locale)
    claim_candidates = _extract_fact_cards(text, locale=normalized_locale, max_items=max_items)
    if not claim_candidates:
        claim_candidates = [
            {
                "text": item,
                "preview": _truncate(item, 160),
                "direction": _detect_text_direction(item, locale=normalized_locale),
            }
            for item in _extract_summary_bullets(text, max_items=max_items)
        ]

    context = evidence_context if isinstance(evidence_context, dict) else {}
    context_fact_cards = _normalize_structured_cards(context.get("factCards"))
    context_quote_cards = _normalize_structured_cards(context.get("quoteCards"))
    context_citation_cards = _normalize_structured_cards(context.get("citationCards"))
    context_entity_cards = _normalize_structured_cards(context.get("entityCards"))
    context_relation_cards = _normalize_structured_cards(context.get("relationCards"))
    context_tools = [str(item) for item in _coerce_list(context.get("toolsUsed")) if str(item)]
    context_queries = [str(item) for item in _coerce_list(context.get("queries")) if str(item)]

    claim_cards: List[Dict[str, Any]] = []
    claims_with_evidence = 0
    seen_claims = set()
    all_support_ref_ids = set()

    for index, claim in enumerate(claim_candidates[: max_items]):
        claim_text = str(claim.get("text") or claim.get("preview") or "").strip()
        if len(claim_text) < 8:
            continue
        claim_key = claim_text.casefold()
        if claim_key in seen_claims:
            continue
        seen_claims.add(claim_key)

        matched_facts = _select_matching_cards(claim_text, context_fact_cards, locale=normalized_locale, limit=2)
        matched_quotes = _select_matching_cards(claim_text, context_quote_cards, locale=normalized_locale, limit=1)
        matched_entities = _select_matching_cards(claim_text, context_entity_cards, locale=normalized_locale, limit=2)
        matched_relations = _select_matching_cards(claim_text, context_relation_cards, locale=normalized_locale, limit=1)

        evidence_tool_names: List[str] = []
        for card in matched_facts + matched_quotes + matched_entities + matched_relations:
            tool_name = str(card.get("sourceTool") or "").strip()
            if tool_name and tool_name not in evidence_tool_names:
                evidence_tool_names.append(tool_name)

        matched_citations: List[Dict[str, Any]] = []
        for card in context_citation_cards:
            citation_tool = str(card.get("sourceTool") or "").strip()
            if evidence_tool_names and citation_tool and citation_tool not in evidence_tool_names:
                continue
            matched_citations.append(copy.deepcopy(card))
            if len(matched_citations) >= 2:
                break

        if not matched_citations and context_citation_cards and (evidence_tool_names or len(claim_candidates) == 1):
            matched_citations = [copy.deepcopy(card) for card in context_citation_cards[:2]]

        support_refs = _build_claim_support_refs(
            matched_facts,
            matched_quotes,
            matched_citations,
            matched_entities,
            matched_relations,
        )
        support_ref_ids = [str(ref.get("evidenceId") or "") for ref in support_refs if str(ref.get("evidenceId") or "")]
        all_support_ref_ids.update(support_ref_ids)

        evidence_count = len(matched_facts) + len(matched_quotes) + len(matched_citations)
        if evidence_count:
            claims_with_evidence += 1

        claim_id = _stable_short_id(
            "claim",
            index + 1,
            claim_text,
            "|".join(support_ref_ids[:4]),
            "|".join(context_queries[:2]),
        )

        claim_cards.append({
            "claimId": claim_id,
            "claim": claim_text,
            "preview": str(claim.get("preview") or _truncate(claim_text, 180)),
            "direction": str(claim.get("direction") or _detect_text_direction(claim_text, locale=normalized_locale)),
            "position": int(index + 1),
            "supportingFacts": matched_facts,
            "supportingQuotes": matched_quotes,
            "supportingCitations": matched_citations,
            "supportingEntities": matched_entities,
            "supportingRelations": matched_relations,
            "supportingRefs": support_refs,
            "supportingRefIds": support_ref_ids,
            "supportRefCount": int(len(support_ref_ids)),
            "supportLevel": _support_level_from_count(evidence_count),
            "sourceTools": evidence_tool_names or context_tools[:2],
            "queries": context_queries[:2],
            "factCount": int(len(matched_facts)),
            "quoteCount": int(len(matched_quotes)),
            "citationCount": int(len(matched_citations)),
            "evidenceCount": int(evidence_count),
            "hasEvidence": bool(evidence_count),
        })

    return {
        "kind": "claim_bundle",
        "version": 2,
        "claimCards": claim_cards,
        "claimCount": int(len(claim_cards)),
        "claimsWithEvidence": int(claims_with_evidence),
        "evidenceRefCount": int(len(all_support_ref_ids)),
        "direction": _detect_text_direction(text or "", locale=normalized_locale),
        "toolsUsed": context_tools,
        "queries": context_queries,
    }


def _split_answer_by_questions(answer_text: str, question_count: int) -> List[str]:
    text = str(answer_text or "")
    if not text or question_count <= 0:
        return [text] if text else []
    if is_placeholder_text(text):
        return [""]

    matches: List[Tuple[int, int]] = []
    for pattern in (
        re.compile(r"(?:^|[\r\n]+)(?:问题|Question|السؤال)\s*(\d+)[：:]\s*", flags=re.IGNORECASE),
        re.compile(r"(?:^|[\r\n]+)(\d+)\.\s+"),
    ):
        matches = [(match.start(), match.end()) for match in pattern.finditer(text)]
        if matches:
            break

    if len(matches) <= 1:
        cleaned = re.sub(r"^(?:问题|Question|السؤال)\s*\d+[：:]\s*", "", text, flags=re.IGNORECASE)
        cleaned = re.sub(r"^\d+\.\s+", "", cleaned)
        cleaned = cleaned.strip()
        return [cleaned or text]

    parts: List[str] = []
    for idx, (_, end) in enumerate(matches):
        next_start = matches[idx + 1][0] if idx + 1 < len(matches) else len(text)
        segment = text[end:next_start].strip()
        segment = re.sub(r"[\r\n]+$", "", segment).strip()
        parts.append(segment)

    if any(parts):
        return parts
    return [text]


def _build_interview_qa_pairs(
    questions: List[str],
    twitter_answer: str,
    reddit_answer: str,
    locale: str = "en",
) -> List[Dict[str, Any]]:
    normalized_questions = [str(item).strip() for item in questions if str(item).strip()]
    if not normalized_questions:
        normalized_questions = [""]

    twitter_parts = _split_answer_by_questions(twitter_answer, len(normalized_questions))
    reddit_parts = _split_answer_by_questions(reddit_answer, len(normalized_questions))

    qa_pairs: List[Dict[str, Any]] = []
    for idx, question in enumerate(normalized_questions):
        twitter_part = twitter_parts[idx] if idx < len(twitter_parts) else (twitter_parts[0] if len(normalized_questions) == 1 and twitter_parts else "")
        reddit_part = reddit_parts[idx] if idx < len(reddit_parts) else (reddit_parts[0] if len(normalized_questions) == 1 and reddit_parts else "")
        has_twitter = bool(twitter_part and not is_placeholder_text(twitter_part))
        has_reddit = bool(reddit_part and not is_placeholder_text(reddit_part))
        preview_source = twitter_part if has_twitter else (reddit_part if has_reddit else _t(locale, "no_response"))
        qa_pairs.append({
            "question": question,
            "twitterAnswer": twitter_part or _t(locale, "no_response"),
            "redditAnswer": reddit_part or _t(locale, "no_response"),
            "platforms": [platform for platform, has_value in (("twitter", has_twitter), ("reddit", has_reddit)) if has_value],
            "isDualPlatform": bool(has_twitter and has_reddit and twitter_part != reddit_part),
            "answerPreview": _truncate(preview_source, 180),
            "direction": _detect_text_direction(f"{question}\n{twitter_part}\n{reddit_part}", locale=locale),
        })
    return qa_pairs


def _count_sentences(text: str) -> int:
    plain = _strip_markdown(text)
    if not plain:
        return 0
    return len([item.strip() for item in re.split(r"(?<=[.!?؟。！？])\s+", plain) if item.strip()])


def _extract_callout_count(markdown: str) -> int:
    return sum(1 for line in str(markdown or "").splitlines() if re.match(r"^\s{0,3}>\s*", line))


def _extract_numbered_fact_count(markdown: str) -> int:
    return sum(1 for line in str(markdown or "").splitlines() if re.match(r"^\s{0,3}(?:[-*+]\s+|\d+[.)]\s+)", line))


def build_section_ui_payload(
    title: str,
    content: str,
    section_index: int,
    locale: str = "en",
    status: str = "completed",
    generated_at: Optional[str] = None,
    source_bundle: Optional[Dict[str, Any]] = None,
    claim_bundle: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    markdown = str(content or "")
    plain = _strip_markdown(markdown)
    word_count = _count_words(markdown)
    char_count = len(plain)
    heading_count = len(_MARKDOWN_HEADING_RE.findall(markdown))
    estimated_read_minutes = (word_count + 179) // 180 if word_count else 0
    summary_bullets = _extract_summary_bullets(markdown, max_items=3)
    preview = _truncate(summary_bullets[0], 240) if summary_bullets else (_truncate(plain, 240) if plain else "")
    keywords = _extract_keywords(markdown or title or "", locale=locale, max_items=6)
    block_counts = _count_markdown_blocks(markdown)
    sentence_count = _count_sentences(markdown)
    citation_count = len(_extract_markdown_links(markdown))
    callout_count = _extract_callout_count(markdown)
    fact_like_count = _extract_numbered_fact_count(markdown)
    headings = [match.group(1).strip() for match in _MARKDOWN_HEADING_RE.finditer(markdown) if match.group(1).strip()]
    fact_cards = _extract_fact_cards(markdown, locale=locale, max_items=6)
    citation_cards = _extract_markdown_link_cards(markdown, max_items=6)
    quote_cards = _extract_quote_cards(markdown, locale=locale, max_items=4)
    computed_claim_bundle = claim_bundle if isinstance(claim_bundle, dict) else build_claim_bundle(
        markdown,
        evidence_context=source_bundle,
        locale=locale,
        max_items=4,
    )

    return {
        "kind": "section",
        "version": 3,
        "title": str(title or ""),
        "sectionIndex": int(section_index or 0),
        "status": str(status or "completed"),
        "preview": preview,
        "summaryBullets": summary_bullets,
        "keywords": keywords,
        "headings": headings[:6],
        "factCards": fact_cards,
        "citationCards": citation_cards,
        "quoteCards": quote_cards,
        "sourceBundle": copy.deepcopy(source_bundle) if isinstance(source_bundle, dict) else None,
        "claimBundle": copy.deepcopy(computed_claim_bundle),
        "claimCards": copy.deepcopy(computed_claim_bundle.get("claimCards") or []),
        "wordCount": int(word_count),
        "charCount": int(char_count),
        "headingCount": int(heading_count),
        "estimatedReadMinutes": int(estimated_read_minutes),
        "direction": _detect_text_direction(markdown or title or "", locale=locale),
        "generatedAt": generated_at or "",
        "hasContent": bool(markdown.strip()),
        "sentenceCount": int(sentence_count),
        "citationCount": int(citation_count),
        "calloutCount": int(callout_count),
        "factLikeCount": int(fact_like_count),
        **block_counts,
    }


def normalize_section_entry_for_ui(section_entry: Dict[str, Any], locale: str = "en") -> Dict[str, Any]:
    entry = copy.deepcopy(section_entry or {})
    title = str(entry.get("title") or "")
    content = str(entry.get("content") or "")
    section_index = int(entry.get("section_index") or entry.get("sectionIndex") or 0)
    status = str(entry.get("status") or ("completed" if content else "pending"))
    generated_at = entry.get("generated_at") or entry.get("generatedAt") or ""
    source_bundle = entry.get("source_bundle") if isinstance(entry.get("source_bundle"), dict) else None
    claim_bundle = entry.get("claim_bundle") if isinstance(entry.get("claim_bundle"), dict) else None
    entry["status"] = status
    generated_ui_payload = build_section_ui_payload(
        title=title,
        content=content,
        section_index=section_index,
        locale=locale,
        status=status,
        generated_at=str(generated_at or ""),
        source_bundle=source_bundle,
        claim_bundle=claim_bundle,
    )
    existing_ui_payload = entry.get("ui_payload") if isinstance(entry.get("ui_payload"), dict) else {}
    entry["ui_payload"] = {
        **generated_ui_payload,
        **existing_ui_payload,
    }
    if source_bundle:
        entry["source_bundle"] = copy.deepcopy(source_bundle)
        entry["ui_payload"]["sourceBundle"] = copy.deepcopy(source_bundle)
    if claim_bundle:
        entry["claim_bundle"] = copy.deepcopy(claim_bundle)
        entry["ui_payload"]["claimBundle"] = copy.deepcopy(claim_bundle)
        entry["ui_payload"]["claimCards"] = copy.deepcopy(claim_bundle.get("claimCards") or [])
    entry["has_content"] = bool(entry.get("has_content") or content.strip())
    return entry



def build_report_state_payload(
    report: Any,
    outline: Any,
    sections: List[Dict[str, Any]],
    progress: Optional[Dict[str, Any]] = None,
    locale: str = "en",
) -> Dict[str, Any]:
    normalized_sections = [normalize_section_entry_for_ui(section, locale=locale) for section in (sections or [])]
    completed_sections = [section for section in normalized_sections if section.get("status") == "completed"]
    current_section = next((section for section in normalized_sections if section.get("status") == "current"), None)

    outline_dict = outline.to_dict() if hasattr(outline, "to_dict") else (copy.deepcopy(outline) if isinstance(outline, dict) else None)
    report_dict = report.to_dict() if hasattr(report, "to_dict") else (copy.deepcopy(report) if isinstance(report, dict) else None)

    total_sections = len(normalized_sections) or len((outline_dict or {}).get("sections") or [])
    completed_count = len(completed_sections)
    pending_count = max(total_sections - completed_count - (1 if current_section else 0), 0)
    total_words = sum(int(((section.get("ui_payload") or {}).get("wordCount") or 0)) for section in normalized_sections)
    total_read_minutes = sum(int(((section.get("ui_payload") or {}).get("estimatedReadMinutes") or 0)) for section in normalized_sections)
    evidence_totals = {
        "toolCalls": 0,
        "facts": 0,
        "entities": 0,
        "relationships": 0,
        "interviews": 0,
        "questions": 0,
        "quotes": 0,
        "citations": 0,
        "finalAnswers": 0,
        "claims": 0,
        "claimsWithEvidence": 0,
        "evidenceItems": 0,
        "evidenceRefs": 0,
    }
    tools_used: List[str] = []
    seen_tools = set()
    seen_evidence_ids = set()
    seen_support_ref_ids = set()

    for section in normalized_sections:
        provenance = section.get("provenance") or {}
        evidence = provenance.get("evidence") or {}
        ui_payload = section.get("ui_payload") or {}
        claim_bundle = ui_payload.get("claimBundle") if isinstance(ui_payload.get("claimBundle"), dict) else {}
        source_bundle = ui_payload.get("sourceBundle") if isinstance(ui_payload.get("sourceBundle"), dict) else (section.get("source_bundle") if isinstance(section.get("source_bundle"), dict) else {})
        source_counts = source_bundle.get("counts") if isinstance(source_bundle.get("counts"), dict) else {}
        source_evidence_refs = _coerce_list(source_bundle.get("evidenceIndex"))
        if not source_evidence_refs:
            for fallback_type, cards in (
                ("fact", source_bundle.get("factCards")),
                ("citation", source_bundle.get("citationCards")),
                ("quote", source_bundle.get("quoteCards")),
                ("entity", source_bundle.get("entityCards")),
                ("relation", source_bundle.get("relationCards")),
                ("interview", source_bundle.get("interviewCards")),
                ("question", source_bundle.get("questionCards")),
            ):
                for card in _coerce_list(cards):
                    ref = _build_evidence_ref(card, fallback_type=fallback_type)
                    if ref:
                        source_evidence_refs.append(ref)
            source_evidence_refs = _dedupe_evidence_refs(source_evidence_refs)

        evidence_totals["toolCalls"] += int(provenance.get("toolCalls") or source_counts.get("toolResults") or 0)
        evidence_totals["facts"] += int(evidence.get("facts") or source_counts.get("facts") or 0)
        evidence_totals["entities"] += int(evidence.get("entities") or source_counts.get("entities") or 0)
        evidence_totals["relationships"] += int(evidence.get("relationships") or source_counts.get("relations") or 0)
        evidence_totals["interviews"] += int(evidence.get("interviews") or source_counts.get("interviews") or 0)
        evidence_totals["questions"] += int(evidence.get("questions") or source_counts.get("questions") or 0)
        evidence_totals["citations"] += int(evidence.get("citations") or source_counts.get("citations") or 0)
        evidence_totals["finalAnswers"] += int(provenance.get("finalAnswers") or 0)
        evidence_totals["quotes"] += int(provenance.get("quoteCount") or source_counts.get("quotes") or 0)
        evidence_totals["claims"] += int(claim_bundle.get("claimCount") or len(ui_payload.get("claimCards") or []) or 0)
        evidence_totals["claimsWithEvidence"] += int(claim_bundle.get("claimsWithEvidence") or 0)
        evidence_totals["evidenceItems"] += int(source_counts.get("evidenceItems") or len(source_evidence_refs) or 0)

        for ref in source_evidence_refs:
            evidence_id = str((ref or {}).get("evidenceId") or "").strip()
            if evidence_id:
                seen_evidence_ids.add(evidence_id)

        for claim_card in _coerce_list(ui_payload.get("claimCards")):
            for ref_id in _coerce_list((claim_card or {}).get("supportingRefIds")):
                value = str(ref_id or "").strip()
                if value:
                    seen_support_ref_ids.add(value)

        for tool_name in source_bundle.get("toolsUsed") or provenance.get("toolsUsed") or []:
            if tool_name and tool_name not in seen_tools:
                seen_tools.add(tool_name)
                tools_used.append(str(tool_name))

    evidence_totals["evidenceItems"] = max(int(evidence_totals["evidenceItems"]), len(seen_evidence_ids))
    evidence_totals["evidenceRefs"] = len(seen_support_ref_ids)

    latest_generated_at = _pick_latest_iso([((section.get("ui_payload") or {}).get("generatedAt") or section.get("generated_at")) for section in normalized_sections])
    completed_sorted = sorted(
        completed_sections,
        key=lambda item: (
            _parse_dt(((item.get("ui_payload") or {}).get("generatedAt") or item.get("generated_at"))) or datetime.min,
            int(item.get("section_index") or 0),
        ),
    )
    latest_completed = completed_sorted[-1] if completed_sorted else None

    progress_dict = copy.deepcopy(progress or {})
    status = (
        (report_dict or {}).get("status")
        or progress_dict.get("status")
        or ("completed" if total_sections and completed_count >= total_sections else "pending")
    )
    started_at = (report_dict or {}).get("created_at") or progress_dict.get("updated_at") or latest_generated_at
    updated_at = _pick_latest_iso([
        progress_dict.get("updated_at"),
        latest_generated_at,
        (report_dict or {}).get("completed_at"),
        (report_dict or {}).get("created_at"),
    ])
    direction = "rtl" if normalize_locale(locale) == "ar" or any(((section.get("ui_payload") or {}).get("direction") == "rtl") for section in normalized_sections) else "ltr"

    latest_completed_summary = None
    if latest_completed:
        latest_completed_summary = {
            "sectionIndex": int(latest_completed.get("section_index") or 0),
            "title": str(latest_completed.get("title") or ""),
            "generatedAt": str(((latest_completed.get("ui_payload") or {}).get("generatedAt") or latest_completed.get("generated_at") or "")),
            "preview": str(((latest_completed.get("ui_payload") or {}).get("preview") or "")),
        }

    total_claims = int(evidence_totals["claims"])
    supported_claim_rate = round((int(evidence_totals["claimsWithEvidence"]) / total_claims), 4) if total_claims else 0

    return {
        "report": report_dict,
        "outline": outline_dict,
        "sections": normalized_sections,
        "progress": progress_dict,
        "summary": {
            "status": str(status or "pending"),
            "isComplete": bool(str(status or "") == "completed"),
            "totalSections": int(total_sections),
            "completedSections": int(completed_count),
            "pendingSections": int(pending_count),
            "completionRate": round((completed_count / total_sections), 4) if total_sections else 0,
            "currentSectionIndex": int(current_section.get("section_index") or 0) if current_section else None,
            "currentSectionTitle": str((current_section or {}).get("title") or progress_dict.get("current_section") or ""),
            "completedTitles": [str(section.get("title") or "") for section in completed_sections if str(section.get("title") or "")],
            "totalWords": int(total_words),
            "estimatedReadMinutes": int(total_read_minutes),
            "latestGeneratedAt": latest_generated_at,
            "startedAt": started_at or "",
            "updatedAt": updated_at or "",
            "direction": direction,
            "latestCompletedSection": latest_completed_summary,
            "sectionsWithEvidence": int(sum(1 for section in normalized_sections if ((section.get("provenance") or {}).get("toolCalls") or ((section.get("source_bundle") or {}).get("counts") or {}).get("toolResults") or 0) > 0)),
            "sectionsWithClaims": int(sum(1 for section in normalized_sections if len(((section.get("ui_payload") or {}).get("claimCards") or [])) > 0)),
            "supportedClaimRate": supported_claim_rate,
            "evidenceTotals": evidence_totals,
            "toolsUsed": tools_used,
        },
    }


def normalize_log_entry_for_ui(log_entry: Dict[str, Any], locale: str = "en") -> Dict[str, Any]:
    entry = copy.deepcopy(log_entry)
    details = entry.get("details")
    if not isinstance(details, dict):
        return entry

    action = entry.get("action")
    if action == "tool_result":
        generated_ui_payload = normalize_tool_result_for_ui(
            details.get("tool_name", ""),
            details.get("result_structured") if details.get("result_structured") is not None else details.get("result"),
            locale=locale,
        )
        existing_ui_payload = details.get("ui_payload") if isinstance(details.get("ui_payload"), dict) else {}
        details["ui_payload"] = {
            **(generated_ui_payload or {}),
            **existing_ui_payload,
        } if generated_ui_payload or existing_ui_payload else None
    elif action == "llm_response":
        evidence_context = details.get("evidence_context") if isinstance(details.get("evidence_context"), dict) else None
        generated_ui_payload = build_llm_response_ui_payload(
            details.get("response", ""),
            locale=locale,
            has_final_answer=bool(details.get("has_final_answer")),
            evidence_context=evidence_context,
        )
        existing_ui_payload = details.get("ui_payload") if isinstance(details.get("ui_payload"), dict) else {}
        details["ui_payload"] = {
            **generated_ui_payload,
            **existing_ui_payload,
        }
    elif action in {"section_content", "section_complete"}:
        content = str(details.get("content") or "")
        if content:
            details["ui_payload"] = details.get("ui_payload") or {
                "kind": "section_content",
                "version": 1,
                "preview": _truncate(content, 240),
            }

    return entry
