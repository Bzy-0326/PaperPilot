from app.services.llm import call_ollama_json
from app.services.github_repo_agent import GitHubRepoAgent
from app.utils.scoring import (
    map_label_score,
    get_open_science_score,
    get_empirical_score,
    final_score,
    get_recommendation,
    get_recommendation_zh,
)


def novelty_level_to_zh(level: str) -> str:
    mapping = {
        "high": "高创新",
        "medium": "中等创新",
        "low": "创新有限",
    }
    return mapping.get(level, "创新有限")


def topic_fit_to_zh(level: str) -> str:
    mapping = {
        "high": "高度相关",
        "medium": "部分相关",
        "low": "相关性较低",
    }
    return mapping.get(level, "相关性较低")


def innovation_type_to_zh(label: str) -> str:
    mapping = {
        "architecture": "架构创新",
        "objective_or_training": "训练目标创新",
        "data_or_benchmark": "数据或基准创新",
        "inference_or_decoding": "推理流程创新",
        "engineering_integration": "工程整合创新",
        "little_to_no_method_novelty": "方法创新有限",
    }
    return mapping.get(label, "方法创新有限")


def build_open_science_summary(open_science: dict) -> str:
    code_available = open_science.get("code_available", "unclear")
    data_available = open_science.get("data_available", "unclear")
    weights_available = open_science.get("weights_available", "unclear")
    code_links = open_science.get("code_links", [])
    weights_links = open_science.get("weights_links", [])

    if code_available == "yes" and weights_available == "yes":
        return "已检测到代码仓库和模型权重页面，复现参考价值较高。"
    if code_available == "yes" and weights_available in ["unclear", "no"]:
        return "已检测到代码仓库，具备一定复现参考价值，但模型权重公开情况不完全明确。"
    if code_available == "yes":
        return "已检测到代码仓库，具备一定复现参考价值。"
    if code_available != "yes" and weights_available == "yes":
        return "已检测到模型权重页面，但未发现明确代码仓库，复现支持有限。"
    if data_available == "yes":
        return "检测到数据公开信息，但代码和权重信息有限。"
    if code_links or weights_links:
        return "检测到部分开源链接，但开源范围仍需人工确认。"
    return "未检测到明确的代码、数据或模型权重公开信息，复现支持有限。"


SUMMARIZER_SYSTEM = """
你是 SummarizerAgent。
你必须只输出一个合法 JSON 对象。
不要输出解释，不要输出 markdown，不要输出代码块，不要输出注释。
所有 JSON 的值内容必须使用简体中文。

输出字段必须严格为：
{
  "one_sentence_summary": "string",
  "study_goal": "string",
  "core_method": "string"
}
"""

NOVELTY_SYSTEM = """
你是 NoveltyAgent。
你必须只输出一个合法 JSON 对象。
不要输出解释，不要输出 markdown，不要输出代码块，不要输出注释。
所有 JSON 的值内容必须使用简体中文。

输出字段必须严格为：
{
  "novelty_level": "high|medium|low",
  "innovation_type": "architecture|objective_or_training|data_or_benchmark|inference_or_decoding|engineering_integration|little_to_no_method_novelty",
  "architecture_used": ["string"],
  "relative_novelty_summary": "string"
}

规则：
1. novelty_level:
   - high: 明显提出新架构或关键新机制
   - medium: 在已有架构上有较明显改造
   - low: 主要沿用现有架构或方法创新有限
2. innovation_type:
   - architecture: 主要新意在架构或关键模块
   - objective_or_training: 主要新意在训练目标、损失、训练策略
   - data_or_benchmark: 主要新意在数据集、基准或评测设置
   - inference_or_decoding: 主要新意在推理、采样、解码流程
   - engineering_integration: 主要是已有方法组合、适配、整合
   - little_to_no_method_novelty: 方法创新有限
3. architecture_used 尽量提取论文用到的主要架构、基础框架或模型族
4. relative_novelty_summary 要回答“相对已有路线，这篇论文的新意主要落在哪里”
5. 不要编造没有在文本中出现的信息
"""

OPEN_SCIENCE_SYSTEM = """
你是 OpenScienceAgent。
你必须只输出一个合法 JSON 对象。
不要输出解释，不要输出 markdown，不要输出代码块，不要输出注释。
所有 JSON 的值内容必须使用简体中文。

输出字段必须严格为：
{
  "code_available": "yes|no|unclear",
  "code_links": ["string"],
  "data_available": "yes|no|unclear",
  "data_links": ["string"],
  "weights_available": "yes|no|unclear",
  "weights_links": ["string"]
}

规则：
1. 如果发现 github.com、gitlab.com，优先判断 code_available 为 yes
2. 如果发现 huggingface.co，优先判断 weights_available 为 yes 或 unclear
3. 如果没有明确证据，不要瞎猜，输出 unclear
4. 不要编造不存在的链接
"""

TOPIC_SYSTEM = """
你是 TopicFitAgent。
你必须只输出一个合法 JSON 对象。
不要输出解释，不要输出 markdown，不要输出代码块，不要输出注释。
所有 JSON 的值内容必须使用简体中文。

输出字段必须严格为：
{
  "topic_fit": "high|medium|low",
  "reason": "string"
}
"""

DECISION_SYSTEM = """
你是 DecisionAgent。
你必须只输出一个合法 JSON 对象。
不要输出解释，不要输出 markdown，不要输出代码块，不要输出注释。
所有 JSON 的值内容必须使用简体中文。

输出字段必须严格为：
{
  "pros": ["string"],
  "cons": ["string"]
}
"""

CONCLUSION_SYSTEM = """
你是 ConclusionAgent。
你必须只输出一个合法 JSON 对象。
不要输出解释，不要输出 markdown，不要输出代码块，不要输出注释。
所有 JSON 的值内容必须使用简体中文。

输出字段必须严格为：
{
  "final_conclusion": "string"
}

要求：
1. 必须直接给出明确态度
2. 开头必须使用“推荐精读：”“建议略读：”或“可跳过：”
3. 要综合主题相关性、创新性和开源复现价值
4. 语气像科研助理，不要空话
5. 尽量一句话说清楚
"""


def run_summarizer_agent(project_topic: str, read_goal: str, full_text: str) -> dict:
    short_text = full_text[:12000]
    user_prompt = f"""
项目主题: {project_topic}
阅读目标: {read_goal}

论文文本:
{short_text}
"""
    return call_ollama_json(SUMMARIZER_SYSTEM, user_prompt)


def run_novelty_agent(project_topic: str, read_goal: str, full_text: str) -> dict:
    short_text = full_text[:12000]
    user_prompt = f"""
项目主题: {project_topic}
阅读目标: {read_goal}

论文文本:
{short_text}
"""
    result = call_ollama_json(NOVELTY_SYSTEM, user_prompt)
    result["novelty_level_zh"] = novelty_level_to_zh(result.get("novelty_level", "low"))
    result["innovation_type_zh"] = innovation_type_to_zh(
        result.get("innovation_type", "little_to_no_method_novelty")
    )
    return result


def run_open_science_agent(full_text: str, links: list) -> dict:
    short_text = full_text[:8000]
    link_lines = "\n".join([x["url"] for x in links[:30] if isinstance(x, dict) and "url" in x])

    user_prompt = f"""
论文文本:
{short_text}

提取到的链接:
{link_lines}
"""
    result = call_ollama_json(OPEN_SCIENCE_SYSTEM, user_prompt)
    result["open_science_summary"] = build_open_science_summary(result)
    return result


def run_topic_fit_agent(project_topic: str, full_text: str) -> dict:
    short_text = full_text[:8000]
    user_prompt = f"""
当前主题: {project_topic}

论文文本:
{short_text}
"""
    result = call_ollama_json(TOPIC_SYSTEM, user_prompt)
    result["topic_fit_zh"] = topic_fit_to_zh(result.get("topic_fit", "low"))
    return result


def run_decision_agent(
    score_profile: str,
    total_score: int,
    recommendation: str,
    summary_result: dict,
    novelty_result: dict,
    open_science_result: dict,
    topic_fit_result: dict,
    repo_summary_result: dict
) -> dict:
    user_prompt = f"""
评分模板: {score_profile}
总分: {total_score}
推荐结果: {recommendation}

论文总结:
{summary_result}

创新性分析:
{novelty_result}

开源分析:
{open_science_result}

仓库复现分析:
{repo_summary_result}

主题相关性:
{topic_fit_result}
"""
    return call_ollama_json(DECISION_SYSTEM, user_prompt)


def run_conclusion_agent(
    recommendation_zh: str,
    summary_result: dict,
    novelty_result: dict,
    open_science_result: dict,
    topic_fit_result: dict,
    repo_summary_result: dict
) -> dict:
    user_prompt = f"""
推荐结论: {recommendation_zh}

论文总结:
{summary_result}

创新性分析:
{novelty_result}

开源分析:
{open_science_result}

仓库复现分析:
{repo_summary_result}

主题相关性:
{topic_fit_result}
"""
    return call_ollama_json(CONCLUSION_SYSTEM, user_prompt)


def extract_github_url(open_science_result: dict, links: list) -> str:
    code_links = open_science_result.get("code_links", []) if isinstance(open_science_result, dict) else []

    for link in code_links:
        if isinstance(link, str) and "github.com" in link:
            return link

    for item in links:
        if isinstance(item, dict):
            url = item.get("url", "")
            if "github.com" in url:
                return url
        elif isinstance(item, str) and "github.com" in item:
            return item

    return ""


def run_full_analysis(
    project_topic: str,
    read_goal: str,
    score_profile: str,
    full_text: str,
    links: list
) -> dict:
    github_repo_agent = GitHubRepoAgent()

    summary_result = run_summarizer_agent(project_topic, read_goal, full_text)
    novelty_result = run_novelty_agent(project_topic, read_goal, full_text)
    open_science_result = run_open_science_agent(full_text, links)
    topic_fit_result = run_topic_fit_agent(project_topic, full_text)

    github_url = extract_github_url(open_science_result, links)
    repo_summary_result = github_repo_agent.analyze(github_url)

    topic_score = map_label_score(topic_fit_result.get("topic_fit", "low"))
    novelty_score = map_label_score(novelty_result.get("novelty_level", "low"))
    open_score = get_open_science_score(open_science_result)
    empirical_score = get_empirical_score(full_text)

    total_score = final_score(
        topic_score,
        novelty_score,
        open_score,
        empirical_score,
        score_profile
    )

    recommendation = get_recommendation(topic_score, novelty_score, total_score)
    recommendation_zh = get_recommendation_zh(recommendation)

    decision_extra = run_decision_agent(
        score_profile=score_profile,
        total_score=total_score,
        recommendation=recommendation,
        summary_result=summary_result,
        novelty_result=novelty_result,
        open_science_result=open_science_result,
        topic_fit_result=topic_fit_result,
        repo_summary_result=repo_summary_result
    )

    conclusion_result = run_conclusion_agent(
        recommendation_zh=recommendation_zh,
        summary_result=summary_result,
        novelty_result=novelty_result,
        open_science_result=open_science_result,
        topic_fit_result=topic_fit_result,
        repo_summary_result=repo_summary_result
    )

    return {
        "final_conclusion": conclusion_result.get(
            "final_conclusion",
            f"{recommendation_zh}：这篇论文已完成自动分析，请结合创新性与开源情况判断是否进一步阅读。"
        ),
        "analysis": {
            **summary_result,
            "novelty_level": novelty_result.get("novelty_level"),
            "novelty_level_zh": novelty_result.get("novelty_level_zh"),
            "innovation_type": novelty_result.get("innovation_type"),
            "innovation_type_zh": novelty_result.get("innovation_type_zh"),
            "architecture_used": novelty_result.get("architecture_used", []),
            "relative_novelty_summary": novelty_result.get("relative_novelty_summary", ""),
        },
        "open_science": open_science_result,
        "repo_summary": repo_summary_result,
        "topic_fit": topic_fit_result,
        "scores": {
            "profile": score_profile,
            "topic_score": topic_score,
            "novelty_score": novelty_score,
            "open_science_score": open_score,
            "empirical_score": empirical_score,
            "readworthiness_score": total_score
        },
        "decision": {
            "recommendation": recommendation,
            "recommendation_zh": recommendation_zh,
            "readworthiness_score": total_score,
            "profile": score_profile,
            "pros": decision_extra.get("pros", []),
            "cons": decision_extra.get("cons", [])
        }
    }