import re
from typing import Dict, List

from app.services.llm_client import chat_json


SYSTEM_PROMPT = """
你是一个论文主题检索扩展助手。

任务：
把用户输入的研究主题，扩展为适合论文标题和摘要匹配的主题词集合。

要求：
1. 只输出 JSON
2. 不要解释
3. canonical_topic 尽量是简洁英文标签
4. aliases 必须包含：
   - 用户原始主题
   - 常见英文等价表达
   - 常见中文表达（如果有）
   - 缩写（如果常见）
5. expansions 必须包含：
   - 论文标题/摘要中常见相关术语
   - 上下位相关表达
   - 常见任务名、对象名、方法名
6. 不要发散到明显无关领域
7. aliases 尽量 4 到 8 个
8. expansions 尽量 6 到 15 个
9. 返回格式固定：

{
  "canonical_topic": "...",
  "aliases": ["..."],
  "expansions": ["..."]
}
"""


def expand_topic_with_llm(project_topic: str) -> Dict:
    topic = project_topic.strip().lower()

    if not topic:
        return {
            "canonical_topic": "",
            "aliases": [],
            "expansions": [],
        }

    result = _run_llm_expand(topic)

    if _is_result_good_enough(result, topic):
        return result

    retry_result = _run_llm_expand_with_stronger_prompt(topic)

    if _is_result_good_enough(retry_result, topic):
        return retry_result

    return _fallback_expand(topic)


def _run_llm_expand(topic: str) -> Dict:
    user_prompt = f"""
用户输入主题：{topic}

请输出适合论文标题和摘要检索的主题扩展结果。

要求：
- canonical_topic：尽量标准、简洁的英文主题标签
- aliases：主题本身的中英文别名、缩写、等价表达
- expansions：论文里常见相关术语，但不要发散太远
- aliases 至少给 4 个（如果确实存在）
- expansions 至少给 6 个（如果确实存在）
- 只输出 JSON
"""

    try:
        result = chat_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.2,
        )
        return _normalize_result(result, topic)
    except Exception:
        return _fallback_min_result(topic)


def _run_llm_expand_with_stronger_prompt(topic: str) -> Dict:
    user_prompt = f"""
用户输入主题：{topic}

你上一次输出太保守了。
这次请更积极地给出检索扩展词。

强要求：
1. aliases 不要只返回原词
2. expansions 不要为空
3. expansions 里优先给论文标题和摘要中常出现的术语
4. 不要泛化到明显无关领域
5. 只输出 JSON

输出示例：
{{
  "canonical_topic": "example topic",
  "aliases": ["example topic", "example-topic", "中文表达", "常见缩写"],
  "expansions": ["related task", "common method", "common benchmark", "related concept"]
}}
"""

    try:
        result = chat_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.3,
        )
        return _normalize_result(result, topic)
    except Exception:
        return _fallback_min_result(topic)


def _normalize_result(result: Dict, topic: str) -> Dict:
    if not isinstance(result, dict):
        return _fallback_min_result(topic)

    canonical_topic = str(result.get("canonical_topic", "")).strip().lower()
    aliases = result.get("aliases", [])
    expansions = result.get("expansions", [])

    if not isinstance(aliases, list):
        aliases = []
    if not isinstance(expansions, list):
        expansions = []

    aliases = _clean_list(aliases)
    expansions = _clean_list(expansions)

    if not canonical_topic:
        canonical_topic = topic

    if topic not in aliases:
        aliases.insert(0, topic)

    return {
        "canonical_topic": canonical_topic,
        "aliases": aliases,
        "expansions": expansions,
    }


def _clean_list(items: List) -> List[str]:
    result = []
    seen = set()

    for item in items:
        text = str(item).strip().lower()
        text = re.sub(r"\s+", " ", text)

        if not text:
            continue
        if text in seen:
            continue

        seen.add(text)
        result.append(text)

    return result


def _is_result_good_enough(result: Dict, topic: str) -> bool:
    aliases = result.get("aliases", [])
    expansions = result.get("expansions", [])

    if not isinstance(aliases, list):
        aliases = []
    if not isinstance(expansions, list):
        expansions = []

    useful_aliases = [x for x in aliases if x.strip().lower() != topic]
    useful_expansions = [x for x in expansions if x.strip()]

    if len(useful_aliases) >= 2 and len(useful_expansions) >= 4:
        return True

    return False


def _fallback_min_result(topic: str) -> Dict:
    return {
        "canonical_topic": topic,
        "aliases": [topic],
        "expansions": [],
    }


def _fallback_expand(topic: str) -> Dict:
    aliases = set()
    expansions = set()

    aliases.add(topic)
    aliases.update(_basic_phrase_variants(topic))

    tokens = _split_topic_tokens(topic)

    # 通用兜底：原词拆分和简单变体
    if len(tokens) >= 2:
        expansions.add(" ".join(tokens))
        expansions.add("-".join(tokens))
        expansions.add("".join(tokens))

    # 轻量启发式：只补常见业务方向，不走特别偏僻长尾
    topic_text = f" {topic} "

    if "document" in topic_text and "intelligence" in topic_text:
        aliases.update([
            "document understanding",
            "intelligent document processing",
            "idp",
            "document ai",
        ])
        expansions.update([
            "document analysis",
            "document parsing",
            "document understanding",
            "ocr",
            "layout analysis",
            "document layout understanding",
            "information extraction",
            "form understanding",
            "table extraction",
            "key information extraction",
        ])

    if "time" in topic_text and "series" in topic_text and "forecast" in topic_text:
        aliases.update([
            "time series prediction",
            "forecasting for time series",
            "temporal forecasting",
        ])
        expansions.update([
            "temporal modeling",
            "sequence modeling",
            "long horizon forecasting",
            "multivariate forecasting",
            "univariate forecasting",
            "time series analysis",
            "temporal prediction",
            "trend prediction",
            "sequence prediction",
            "forecast model",
        ])

    if "reasoning" in topic_text:
        aliases.update([
            "reasoning model",
            "logical reasoning",
        ])
        expansions.update([
            "chain of thought",
            "step-by-step reasoning",
            "mathematical reasoning",
            "logical reasoning",
            "deliberation",
            "test-time scaling",
        ])

    if "agent" in topic_text:
        aliases.update([
            "ai agent",
            "autonomous agent",
            "llm agent",
        ])
        expansions.update([
            "tool use",
            "planning",
            "multi-agent",
            "workflow automation",
            "task planning",
            "web agent",
        ])

    if "vision" in topic_text and "language" in topic_text:
        aliases.update([
            "vision-language",
            "vision language model",
            "vlm",
        ])
        expansions.update([
            "image-text",
            "visual grounding",
            "multimodal understanding",
            "vision encoder",
            "cross-modal learning",
        ])

    aliases = _clean_list(list(aliases))
    expansions = _clean_list(list(expansions))

    return {
        "canonical_topic": topic,
        "aliases": aliases,
        "expansions": expansions,
    }


def _basic_phrase_variants(text: str) -> List[str]:
    text = text.strip().lower()
    if not text:
        return []

    variants = {text}
    variants.add(text.replace("-", " "))
    variants.add(text.replace(" ", "-"))

    words = text.split()
    if len(words) > 1:
        variants.add("".join(words))

    if len(text) > 3 and not text.endswith("s"):
        variants.add(f"{text}s")

    return list(variants)


def _split_topic_tokens(text: str) -> List[str]:
    text = text.strip().lower()
    text = text.replace("-", " ")
    text = re.sub(r"\s+", " ", text)
    parts = text.split()

    stopwords = {
        "the", "a", "an", "of", "for", "to", "and", "in", "on", "with"
    }

    return [p for p in parts if p and p not in stopwords]