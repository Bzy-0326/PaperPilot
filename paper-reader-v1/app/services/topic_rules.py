import re
from functools import lru_cache
from typing import Dict, List, Tuple, Set

from app.services.topic_expander import expand_topic_with_llm


TOPIC_ALIAS_MAP: Dict[str, List[str]] = {
    "llm": [
        "llm",
        "llms",
        "large language model",
        "large language models",
        "大语言模型",
        "语言大模型",
        "语言模型",
    ],
    "multimodal": [
        "multimodal",
        "multi modal",
        "multi-modal",
        "多模态",
        "vision language",
        "vision-language",
        "vision language model",
        "vision-language model",
        "vlm",
        "vlms",
    ],
    "rag": [
        "rag",
        "retrieval augmented generation",
        "retrieval-augmented generation",
        "检索增强生成",
        "检索增强",
    ],
    "protein": [
        "protein",
        "proteins",
        "蛋白质",
        "蛋白",
        "protein design",
        "protein engineering",
        "protein folding",
    ],
    "antibody": [
        "antibody",
        "antibodies",
        "抗体",
        "antibody design",
        "nanobody",
        "nanobodies",
    ],
}


TOPIC_EXPANSION_MAP: Dict[str, List[str]] = {
    "llm": [
        "instruction tuning",
        "supervised fine-tuning",
        "sft",
        "rlhf",
        "alignment",
        "pretraining",
        "post-training",
        "in-context learning",
        "prompting",
        "reasoning",
        "tool use",
        "quantization",
        "transformer",
    ],
    "multimodal": [
        "image-text",
        "cross-modal",
        "visual grounding",
        "vision encoder",
        "image understanding",
        "vision-language pretraining",
    ],
    "rag": [
        "retrieval",
        "retriever",
        "vector search",
        "embedding search",
        "knowledge base",
        "document retrieval",
        "indexing",
        "reranker",
        "hybrid search",
        "query rewriting",
    ],
    "protein": [
        "enzyme",
        "structure prediction",
        "peptide",
        "amino acid",
        "protein sequence",
        "protein structure",
        "binder design",
    ],
    "antibody": [
        "antigen",
        "affinity",
        "epitope",
        "binder",
        "cdr",
        "therapeutic antibody",
    ],
}


TOPIC_NEGATIVE_HINTS: Dict[str, List[str]] = {
    "rag": [
        "water quality",
        "water-quality",
        "environmental monitoring",
        "hydrology",
        "geology",
        "soil",
        "forest inventory",
        "crop yield",
        "medical image reconstruction",
        "tomographic reconstruction",
        "remote sensing reconstruction",
    ]
}


GENERIC_WEAK_TERMS = {
    "prediction",
    "predictions",
    "analysis",
    "analytics",
    "model",
    "models",
    "method",
    "methods",
    "approach",
    "approaches",
    "framework",
    "frameworks",
    "system",
    "systems",
    "task",
    "tasks",
    "understanding",
    "intelligence",
    "forecast",
    "forecasts",
}


def _normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.strip().lower()
    text = text.replace("（", "(").replace("）", ")")
    text = text.replace("：", ":").replace("，", ",")
    text = text.replace("_", " ").replace("-", " ")
    text = re.sub(r"\s+", " ", text)
    return text


def _phrase_variants(term: str) -> Set[str]:
    term = _normalize_text(term)
    if not term:
        return set()

    variants = {term}
    variants.add(term.replace("-", " "))
    variants.add(term.replace(" ", "-"))

    words = term.split()
    if len(words) > 1:
        variants.add("".join(words))

    if len(term) > 3 and not term.endswith("s"):
        variants.add(f"{term}s")

    return {v for v in variants if v}


def _find_predefined_canonical_topic(normalized_topic: str) -> str:
    if not normalized_topic:
        return ""

    for canonical_topic, aliases in TOPIC_ALIAS_MAP.items():
        alias_pool = set()
        for alias in aliases:
            alias_pool.update(_phrase_variants(alias))
        if normalized_topic in alias_pool:
            return canonical_topic

    return ""


@lru_cache(maxsize=256)
def _get_dynamic_topic_bundle(topic: str) -> Dict[str, List[str] | str]:
    normalized = _normalize_text(topic)

    if not normalized:
        return {
            "canonical_topic": "",
            "aliases": [],
            "expansions": [],
        }

    result = expand_topic_with_llm(normalized)

    canonical_topic = _normalize_text(str(result.get("canonical_topic", "")))
    aliases = result.get("aliases", [])
    expansions = result.get("expansions", [])

    if not isinstance(aliases, list):
        aliases = []
    if not isinstance(expansions, list):
        expansions = []

    clean_aliases = []
    seen_aliases = set()
    for item in aliases:
        text = _normalize_text(str(item))
        if not text or text in seen_aliases:
            continue
        seen_aliases.add(text)
        clean_aliases.append(text)

    clean_expansions = []
    seen_expansions = set()
    for item in expansions:
        text = _normalize_text(str(item))
        if not text or text in seen_expansions:
            continue
        seen_expansions.add(text)
        clean_expansions.append(text)

    if not canonical_topic:
        canonical_topic = normalized

    return {
        "canonical_topic": canonical_topic,
        "aliases": clean_aliases,
        "expansions": clean_expansions,
    }


def normalize_topic_label(topic: str) -> str:
    normalized = _normalize_text(topic)

    if not normalized:
        return ""

    predefined = _find_predefined_canonical_topic(normalized)
    if predefined:
        return predefined

    dynamic_result = _get_dynamic_topic_bundle(normalized)
    canonical_topic = _normalize_text(str(dynamic_result.get("canonical_topic", "")))

    if canonical_topic:
        return canonical_topic

    return normalized


def get_topic_aliases(topic: str) -> List[str]:
    canonical_topic = normalize_topic_label(topic)
    result: Set[str] = set()

    if canonical_topic in TOPIC_ALIAS_MAP:
        for alias in TOPIC_ALIAS_MAP[canonical_topic]:
            result.update(_phrase_variants(alias))
        result.add(canonical_topic)
        return sorted(result, key=len, reverse=True)

    dynamic_result = _get_dynamic_topic_bundle(topic)

    for alias in dynamic_result.get("aliases", []):
        result.update(_phrase_variants(alias))

    result.add(canonical_topic)

    if not result:
        result.update(_phrase_variants(topic))

    return sorted(result, key=len, reverse=True)


def get_topic_keywords(topic: str) -> List[str]:
    canonical_topic = normalize_topic_label(topic)
    result: Set[str] = set()

    result.update(get_topic_aliases(topic))

    if canonical_topic in TOPIC_EXPANSION_MAP:
        for item in TOPIC_EXPANSION_MAP[canonical_topic]:
            result.update(_phrase_variants(item))

    if canonical_topic not in TOPIC_ALIAS_MAP:
        dynamic_result = _get_dynamic_topic_bundle(topic)
        for item in dynamic_result.get("expansions", []):
            result.update(_phrase_variants(item))

    return sorted(result, key=len, reverse=True)


def _contains_term(text: str, term: str) -> bool:
    if not text or not term:
        return False

    text = f" {text} "
    term = term.strip()

    if not term:
        return False

    if re.search(r"[\u4e00-\u9fff]", term):
        return term in text

    escaped = re.escape(term)
    pattern = rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"
    return re.search(pattern, text) is not None


def _collect_matches(text: str, terms: List[str]) -> List[str]:
    matches = []
    seen = set()

    for term in terms:
        if term in seen:
            continue
        if _contains_term(text, term):
            seen.add(term)
            matches.append(term)

    return matches


def _extract_query_tokens(topic: str) -> List[str]:
    normalized = _normalize_text(topic)
    if not normalized:
        return []

    parts = re.split(r"\s+", normalized)
    stopwords = {
        "the", "a", "an", "of", "for", "to", "and", "in", "on", "with",
        "model", "models", "system", "systems", "based"
    }

    tokens = []
    for part in parts:
        if len(part) <= 2:
            continue
        if part in stopwords:
            continue
        tokens.append(part)

    return tokens


def _is_generic_weak_term(term: str) -> bool:
    normalized = _normalize_text(term)
    return normalized in GENERIC_WEAK_TERMS


def _split_unknown_topic_terms(topic: str) -> Tuple[List[str], List[str], List[str]]:
    """
    返回：
    - strong_aliases: 原词和强别名
    - support_terms: 较强扩展，可辅助
    - weak_terms: 泛词，只能弱参考
    """
    aliases = get_topic_aliases(topic)
    keywords = get_topic_keywords(topic)

    strong_aliases = []
    support_terms = []
    weak_terms = []

    alias_set = set(aliases)

    for term in aliases:
        if _is_generic_weak_term(term):
            weak_terms.append(term)
        else:
            strong_aliases.append(term)

    for term in keywords:
        if term in alias_set:
            continue
        if _is_generic_weak_term(term):
            weak_terms.append(term)
        else:
            support_terms.append(term)

    # 去重并保序
    def dedupe_keep_order(items: List[str]) -> List[str]:
        result = []
        seen = set()
        for item in items:
            if item in seen:
                continue
            seen.add(item)
            result.append(item)
        return result

    return (
        dedupe_keep_order(strong_aliases),
        dedupe_keep_order(support_terms),
        dedupe_keep_order(weak_terms),
    )


def is_topic_candidate(project_topic: str, title: str, abstract_text: str) -> Tuple[bool, List[str]]:
    canonical_topic = normalize_topic_label(project_topic)
    normalized_title = _normalize_text(title)
    normalized_abstract = _normalize_text(abstract_text)
    full_text = f"{normalized_title} {normalized_abstract}".strip()

    aliases = get_topic_aliases(project_topic)
    keywords = get_topic_keywords(project_topic)
    expansion_terms = [k for k in keywords if k not in aliases]

    alias_matches = _collect_matches(full_text, aliases)
    expansion_matches = _collect_matches(full_text, expansion_terms)

    negative_hints = TOPIC_NEGATIVE_HINTS.get(canonical_topic, [])
    negative_matches = _collect_matches(full_text, negative_hints)

    if canonical_topic == "rag":
        if negative_matches and len(alias_matches) == 0:
            return False, []

        strong_aliases = {
            "rag",
            "检索增强生成",
            "检索增强",
            "retrieval augmented generation",
            "retrieval-augmented generation",
        }

        if any(m in strong_aliases for m in alias_matches):
            return True, sorted(set(alias_matches + expansion_matches))

        retrieval_like = {
            "retrieval",
            "retriever",
            "document retrieval",
            "knowledge base",
            "vector search",
            "embedding search",
        }

        hit_retrieval_like = any(m in retrieval_like for m in alias_matches + expansion_matches)
        distinct_hits = len(set(alias_matches + expansion_matches))

        if hit_retrieval_like and distinct_hits >= 2 and not negative_matches:
            return True, sorted(set(alias_matches + expansion_matches))

        return False, []

    if canonical_topic == "multimodal":
        strong_hit = any(
            m in {
                "multimodal",
                "多模态",
                "vision language",
                "vision-language",
                "vision language model",
                "vision-language model",
                "vlm",
                "vlms",
            }
            for m in alias_matches
        )
        if strong_hit:
            return True, sorted(set(alias_matches + expansion_matches))

        combo_a = any(_contains_term(full_text, x) for x in ["image", "visual", "vision", "图像"])
        combo_b = any(_contains_term(full_text, x) for x in ["text", "language", "文本", "语言"])
        if combo_a and combo_b:
            return True, sorted(set(alias_matches + expansion_matches + ["image", "text"]))

        return False, []

    if canonical_topic == "llm":
        if len(alias_matches) >= 1:
            return True, sorted(set(alias_matches + expansion_matches))
        if len(set(expansion_matches)) >= 2:
            return True, sorted(set(alias_matches + expansion_matches))
        return False, []

    if canonical_topic in TOPIC_ALIAS_MAP:
        if len(alias_matches) >= 1:
            return True, sorted(set(alias_matches + expansion_matches))

        if len(set(expansion_matches)) >= 2:
            return True, sorted(set(alias_matches + expansion_matches))

        return False, []

    # 未知主题：收紧，不再宽放
    strong_aliases, support_terms, weak_terms = _split_unknown_topic_terms(project_topic)

    strong_alias_matches = _collect_matches(full_text, strong_aliases)
    support_matches = _collect_matches(full_text, support_terms)
    weak_matches = _collect_matches(full_text, weak_terms)

    query_tokens = _extract_query_tokens(project_topic)
    token_hits = [token for token in query_tokens if _contains_term(full_text, token)]

    # 1) 原词 / 强别名命中优先
    if len(strong_alias_matches) >= 1:
        return True, sorted(set(strong_alias_matches + support_matches))

    # 2) 标题里命中两个 query token，且有一个 support term，才放行
    title_token_hits = [token for token in query_tokens if _contains_term(normalized_title, token)]
    if len(set(title_token_hits)) >= 2 and len(support_matches) >= 1:
        return True, sorted(set(title_token_hits + support_matches))

    # 3) support term 至少 2 个才放行
    if len(set(support_matches)) >= 2:
        return True, sorted(set(support_matches + token_hits))

    # 4) 弱词绝不能单独放行
    if len(weak_matches) >= 1 and len(strong_alias_matches) == 0 and len(support_matches) == 0:
        return False, []

    return False, []


def passes_post_llm_topic_check(
    project_topic: str,
    title: str,
    abstract_text: str,
    analysis: dict,
) -> bool:
    canonical_topic = normalize_topic_label(project_topic)
    normalized_title = _normalize_text(title)
    normalized_abstract = _normalize_text(abstract_text)

    one_sentence_summary = _normalize_text(analysis.get("one_sentence_summary", ""))
    final_conclusion = _normalize_text(analysis.get("final_conclusion", ""))
    recommendation = _normalize_text(analysis.get("recommendation", ""))
    topic_fit = _normalize_text(analysis.get("topic_fit", ""))

    tags = analysis.get("tags", [])
    if not isinstance(tags, list):
        tags = []
    normalized_tags = " ".join(_normalize_text(str(tag)) for tag in tags)

    full_text = " ".join(
        part for part in [
            normalized_title,
            normalized_abstract,
            one_sentence_summary,
            final_conclusion,
            normalized_tags,
        ]
        if part
    )

    aliases = get_topic_aliases(project_topic)
    keywords = get_topic_keywords(project_topic)

    alias_matches = _collect_matches(full_text, aliases)
    keyword_matches = _collect_matches(full_text, keywords)

    if topic_fit == "low":
        return False

    if recommendation == "skip":
        return False

    if canonical_topic == "rag":
        negative_hints = TOPIC_NEGATIVE_HINTS.get("rag", [])
        negative_matches = _collect_matches(full_text, negative_hints)

        strong_aliases = {
            "rag",
            "检索增强生成",
            "检索增强",
            "retrieval augmented generation",
            "retrieval-augmented generation",
        }

        if any(m in strong_aliases for m in alias_matches):
            return True

        if negative_matches:
            return False

        if len(set(keyword_matches)) >= 2 and topic_fit in {"medium", "high"}:
            return True

        return False

    if canonical_topic == "multimodal":
        if len(alias_matches) >= 1:
            return True

        combo_a = any(_contains_term(full_text, x) for x in ["image", "visual", "vision", "图像"])
        combo_b = any(_contains_term(full_text, x) for x in ["text", "language", "文本", "语言"])
        if combo_a and combo_b and topic_fit in {"medium", "high"}:
            return True

        return False

    if canonical_topic == "llm":
        if len(alias_matches) >= 1:
            return True
        if len(set(keyword_matches)) >= 2 and topic_fit in {"medium", "high"}:
            return True
        return False

    if canonical_topic in TOPIC_ALIAS_MAP:
        if len(alias_matches) >= 1:
            return True

        if len(set(keyword_matches)) >= 2 and topic_fit in {"medium", "high"}:
            return True

        return False

    # 未知主题：后置检查同样收紧
    strong_aliases, support_terms, weak_terms = _split_unknown_topic_terms(project_topic)

    strong_alias_matches = _collect_matches(full_text, strong_aliases)
    support_matches = _collect_matches(full_text, support_terms)
    weak_matches = _collect_matches(full_text, weak_terms)

    query_tokens = _extract_query_tokens(project_topic)
    token_hits = [token for token in query_tokens if _contains_term(full_text, token)]

    if len(strong_alias_matches) >= 1:
        return True

    if topic_fit in {"medium", "high"} and len(set(support_matches)) >= 2:
        return True

    if topic_fit == "high" and len(set(token_hits)) >= 2 and len(set(support_matches)) >= 1:
        return True

    if len(weak_matches) >= 1 and len(strong_alias_matches) == 0 and len(support_matches) == 0:
        return False

    return False