def map_label_score(label: str) -> int:
    mapping = {
        "high": 85,
        "medium": 60,
        "low": 30,
        "yes": 85,
        "unclear": 50,
        "no": 20,
    }
    return mapping.get(label, 0)


def get_open_science_score(open_science: dict) -> int:
    code_score = map_label_score(open_science.get("code_available", "no"))
    data_score = map_label_score(open_science.get("data_available", "unclear"))
    weights_score = map_label_score(open_science.get("weights_available", "unclear"))

    return round((code_score * 0.5) + (data_score * 0.2) + (weights_score * 0.3))


def get_empirical_score(full_text: str) -> int:
    text = full_text.lower()

    score = 20

    if any(k in text for k in ["experiment", "results", "evaluation", "benchmark"]):
        score += 25
    if any(k in text for k in ["baseline", "compared with", "comparison"]):
        score += 20
    if "ablation" in text:
        score += 20
    if any(k in text for k in ["accuracy", "f1", "auc", "auroc", "rmse", "pearson"]):
        score += 15

    return min(score, 100)


def final_score(topic_score: int, novelty_score: int, open_score: int, empirical_score: int, profile: str) -> int:
    weights = {
        "innovation": (0.35, 0.35, 0.20, 0.10),
        "stability": (0.35, 0.20, 0.20, 0.25),
        "reproducibility": (0.30, 0.20, 0.35, 0.15),
    }

    w_topic, w_novelty, w_open, w_emp = weights.get(profile, weights["innovation"])

    score = (
        topic_score * w_topic +
        novelty_score * w_novelty +
        open_score * w_open +
        empirical_score * w_emp
    )
    return round(score)


def get_recommendation(topic_score: int, novelty_score: int, total_score: int) -> str:
    if topic_score < 40:
        return "skip"
    if total_score >= 75 and novelty_score >= 60:
        return "read"
    if total_score >= 50:
        return "skim"
    return "skip"


def get_recommendation_zh(recommendation: str) -> str:
    mapping = {
        "read": "推荐精读",
        "skim": "建议略读",
        "skip": "可跳过",
    }
    return mapping.get(recommendation, "建议略读")