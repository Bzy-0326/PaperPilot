import re

from app.services.llm import call_ollama_json


LIGHT_ANALYZER_SYSTEM = """
你是论文推荐产品中的中文分析助手。

请根据研究主题、论文标题、论文摘要和链接，输出适合产品展示的正式中文 JSON。
不要解释你的思考过程，不要输出 markdown，只返回 JSON。

输出结构：
{
  "one_sentence_summary": "string",
  "final_conclusion": "string",
  "recommendation": "read|skim|skip",
  "recommendation_zh": "推荐精读|建议速读|暂不推荐",
  "topic_fit": "high|medium|low",
  "topic_fit_zh": "高度相关|中度相关|相关性较弱",
  "novelty_level": "high|medium|low",
  "novelty_level_zh": "高创新|中等创新|创新性一般",
  "reproducibility_level": "high|medium|low",
  "reproducibility_level_zh": "较易复现|可复现性中等|复现门槛较高",
  "reproducibility_reason": "string",
  "study_goal": "string",
  "method_summary": "string",
  "content_summary": "string",
  "implementation_evidence": "string",
  "innovations": ["string"],
  "limitations": ["string"],
  "evidence_signals": ["string"],
  "tags": ["string"]
}

要求：
1. `one_sentence_summary` 用 1 句话概括论文最值得用户知道的核心结论。
2. `final_conclusion` 用 1 到 2 句话给出推荐判断，但要与 `one_sentence_summary` 保持一致，不要说相反的话。
3. `study_goal` 不是一句空泛判断，而是要写清：
   - 论文所处的问题背景
   - 当前方法存在哪些不足
   - 作者想解决什么问题
   - 为什么这个问题重要
   长度控制在 2 到 4 句。
4. `content_summary` 放在详情页摘要区域，应该比一句话总结更完整，写 2 到 4 句，包含：
   - 论文提出了什么
   - 主要做了哪些实验或验证
   - 最终得到什么结果或结论
5. `method_summary` 放在实验方法区域，写 2 到 4 句，重点说：
   - 方法框架
   - 核心模块或关键机制
   - 输入输出关系
   - 实验设计或验证方式
6. 所有字段都优先输出自然中文，不要大段保留英文原文；必要时可保留少量方法名或模型名。
7. 不要写“模型分析”“根据提示”“作为助手”“JSON”等元话语。
8. `implementation_evidence` 只写代码、附录、训练细节、数据集、实验设置、复现说明等证据。
9. `innovations` 和 `limitations` 各输出 2 到 4 条简洁中文。
10. `tags` 输出 3 到 6 个标签，优先是论文主题、方法关键词、任务关键词。
11. 如果摘要信息不充分，不要编造；但要尽量利用已有信息组织成完整中文表达。
"""


DEFAULT_ANALYSIS = {
    "one_sentence_summary": "",
    "final_conclusion": "",
    "recommendation": "skim",
    "recommendation_zh": "建议速读",
    "topic_fit": "medium",
    "topic_fit_zh": "中度相关",
    "novelty_level": "medium",
    "novelty_level_zh": "中等创新",
    "reproducibility_level": "medium",
    "reproducibility_level_zh": "可复现性中等",
    "reproducibility_reason": "",
    "study_goal": "",
    "method_summary": "",
    "content_summary": "",
    "implementation_evidence": "",
    "innovations": [],
    "limitations": [],
    "evidence_signals": [],
    "tags": [],
}

VALID_RECOMMENDATION = {"read", "skim", "skip"}
VALID_LEVEL = {"high", "medium", "low"}


def _normalize_tags(tags):
    if not isinstance(tags, list):
        return []

    cleaned = []
    seen = set()
    for tag in tags:
        if not isinstance(tag, str):
            continue
        text = tag.strip()
        if not text or text in seen:
            continue
        seen.add(text)
        cleaned.append(text)
    return cleaned[:6]


def _normalize_string_list(items, max_len=4):
    if not isinstance(items, list):
        return []

    cleaned = []
    seen = set()
    for item in items:
        if not isinstance(item, str):
            continue
        text = item.strip()
        if not text or text in seen:
            continue
        seen.add(text)
        cleaned.append(text)
    return cleaned[:max_len]


def _clean_text(text: str) -> str:
    value = str(text or "").strip()
    value = re.sub(r"\s+", " ", value)
    return value


def _looks_like_meta_text(text: str) -> bool:
    lowered = _clean_text(text).lower()
    bad_markers = [
        "ollama",
        "json",
        "system prompt",
        "根据提示",
        "模型分析",
        "轻分析",
        "推荐系统",
        "as an assistant",
    ]
    return any(marker in lowered for marker in bad_markers)


def _normalize_result(result: dict) -> dict:
    if not isinstance(result, dict):
        result = {}

    normalized = DEFAULT_ANALYSIS.copy()
    normalized.update(result)

    if normalized.get("recommendation") not in VALID_RECOMMENDATION:
        normalized["recommendation"] = DEFAULT_ANALYSIS["recommendation"]
        normalized["recommendation_zh"] = DEFAULT_ANALYSIS["recommendation_zh"]

    if normalized.get("topic_fit") not in VALID_LEVEL:
        normalized["topic_fit"] = DEFAULT_ANALYSIS["topic_fit"]
        normalized["topic_fit_zh"] = DEFAULT_ANALYSIS["topic_fit_zh"]

    if normalized.get("novelty_level") not in VALID_LEVEL:
        normalized["novelty_level"] = DEFAULT_ANALYSIS["novelty_level"]
        normalized["novelty_level_zh"] = DEFAULT_ANALYSIS["novelty_level_zh"]

    if normalized.get("reproducibility_level") not in VALID_LEVEL:
        normalized["reproducibility_level"] = DEFAULT_ANALYSIS["reproducibility_level"]
        normalized["reproducibility_level_zh"] = DEFAULT_ANALYSIS["reproducibility_level_zh"]

    for key in [
        "one_sentence_summary",
        "final_conclusion",
        "recommendation_zh",
        "topic_fit_zh",
        "novelty_level_zh",
        "reproducibility_level_zh",
        "reproducibility_reason",
        "study_goal",
        "method_summary",
        "content_summary",
        "implementation_evidence",
    ]:
        normalized[key] = _clean_text(normalized.get(key) or "")
        if _looks_like_meta_text(normalized[key]):
            normalized[key] = ""

    normalized["innovations"] = _normalize_string_list(normalized.get("innovations"), max_len=4)
    normalized["limitations"] = _normalize_string_list(normalized.get("limitations"), max_len=4)
    normalized["evidence_signals"] = _normalize_tags(normalized.get("evidence_signals"))
    normalized["tags"] = _normalize_tags(normalized.get("tags"))

    if normalized["topic_fit"] == "low":
        normalized["recommendation"] = "skip"
        normalized["recommendation_zh"] = "暂不推荐"

    if not normalized["final_conclusion"] and normalized["one_sentence_summary"]:
        normalized["final_conclusion"] = normalized["one_sentence_summary"]

    if not normalized["content_summary"] and normalized["one_sentence_summary"]:
        normalized["content_summary"] = normalized["one_sentence_summary"]

    return normalized


def _extract_candidate_tags(project_topic: str, title: str) -> list[str]:
    tags = []
    title_text = _clean_text(title)
    candidates = re.split(r"[:：,\-()（）/]", title_text)

    if project_topic.strip():
        tags.append(project_topic.strip())

    for part in candidates:
        text = part.strip()
        if len(text) < 2 or len(text) > 24:
            continue
        if text.lower() in {"a", "an", "the", "for", "with"}:
            continue
        tags.append(text)

    return _normalize_tags(tags)


def _build_fallback_analysis(project_topic: str, title: str, abstract_text: str) -> dict:
    summary = _clean_text(abstract_text)
    if len(summary) > 220:
        summary = summary[:217].rstrip() + "..."

    sentences = re.split(r"(?<=[。.!?])\s+", _clean_text(abstract_text))
    sentences = [s for s in sentences if s]

    study_goal = " ".join(sentences[:2])[:320] if sentences else ""
    content_summary = " ".join(sentences[:3])[:360] if sentences else summary
    method_summary = " ".join(sentences[1:3])[:320] if len(sentences) > 1 else ""

    fallback_summary = summary or "这篇论文与当前主题存在一定关联，建议先了解其研究目标、方法框架和实验结果。"

    return {
        "one_sentence_summary": fallback_summary,
        "final_conclusion": fallback_summary,
        "recommendation": "skim",
        "recommendation_zh": "建议速读",
        "topic_fit": "medium",
        "topic_fit_zh": "中度相关",
        "novelty_level": "medium",
        "novelty_level_zh": "中等创新",
        "reproducibility_level": "medium",
        "reproducibility_level_zh": "可复现性中等",
        "reproducibility_reason": "当前结果基于标题和摘要生成，建议继续结合原文、附录或代码链接确认复现条件。",
        "study_goal": study_goal,
        "method_summary": method_summary,
        "content_summary": content_summary,
        "implementation_evidence": "",
        "innovations": [],
        "limitations": [],
        "evidence_signals": ["已读取论文标题", "已读取论文摘要"],
        "tags": _extract_candidate_tags(project_topic, title),
    }


def run_light_analysis(
    project_topic: str,
    title: str,
    abstract_text: str,
    paper_url: str = "",
) -> dict:
    short_text = abstract_text[:5000] if abstract_text else ""
    user_prompt = f"""
研究主题：
{project_topic}

论文标题：
{title}

论文摘要：
{short_text}

论文链接：
{paper_url}
"""

    try:
        result = call_ollama_json(LIGHT_ANALYZER_SYSTEM, user_prompt)
    except Exception:
        result = _build_fallback_analysis(
            project_topic=project_topic,
            title=title,
            abstract_text=abstract_text,
        )

    return _normalize_result(result)
