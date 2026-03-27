import json
import os
import re
import tempfile
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from app.db import SessionLocal
from app.models import Paper, PaperAnalysis


def save_papers(papers: list[dict]):
    db = SessionLocal()
    try:
        for p in papers:
            source = p.get("source", "huggingface_papers")
            source_paper_id = p.get("source_paper_id")
            title = p.get("title", "").strip()

            exists = None
            if source and source_paper_id:
                exists = (
                    db.query(Paper)
                    .filter(
                        Paper.source == source,
                        Paper.source_paper_id == source_paper_id,
                    )
                    .first()
                )

            if exists:
                exists.title = title
                exists.abstract = p.get("abstract", "")
                exists.authors_json = json.dumps(p.get("authors", []), ensure_ascii=False)
                exists.paper_url = p.get("paper_url", "")
                exists.pdf_url = p.get("pdf_url", "")
                exists.source_date = p.get("source_date", "")
            else:
                db.add(
                    Paper(
                        source=source,
                        source_paper_id=source_paper_id,
                        title=title,
                        abstract=p.get("abstract", ""),
                        authors_json=json.dumps(p.get("authors", []), ensure_ascii=False),
                        paper_url=p.get("paper_url", ""),
                        pdf_url=p.get("pdf_url", ""),
                        source_date=p.get("source_date", ""),
                    )
                )

        db.commit()
    finally:
        db.close()


def list_papers(limit: int = 30):
    db = SessionLocal()
    try:
        rows = db.query(Paper).order_by(Paper.id.desc()).limit(limit).all()
        result = []
        for row in rows:
            result.append(
                {
                    "id": row.id,
                    "source": row.source,
                    "source_paper_id": row.source_paper_id,
                    "title": row.title,
                    "abstract": row.abstract,
                    "authors": json.loads(row.authors_json) if row.authors_json else [],
                    "paper_url": row.paper_url,
                    "pdf_url": row.pdf_url,
                    "source_date": row.source_date,
                }
            )
        return result
    finally:
        db.close()


def get_recent_papers(limit: int = 20):
    db = SessionLocal()
    try:
        return db.query(Paper).order_by(Paper.id.desc()).limit(limit).all()
    finally:
        db.close()


def get_recent_unanalyzed_papers_by_topic(project_topic: str, limit: int = 20):
    db = SessionLocal()
    try:
        analyzed_paper_ids = (
            db.query(PaperAnalysis.paper_id)
            .filter(
                PaperAnalysis.analysis_type == "light",
                PaperAnalysis.project_topic == project_topic,
            )
            .all()
        )
        analyzed_ids = [row[0] for row in analyzed_paper_ids]

        query = db.query(Paper).order_by(Paper.id.desc())
        if analyzed_ids:
            query = query.filter(~Paper.id.in_(analyzed_ids))

        return query.limit(limit).all()
    finally:
        db.close()


def get_papers_by_ids(paper_ids: list[int]):
    db = SessionLocal()
    try:
        if not paper_ids:
            return []
        return db.query(Paper).filter(Paper.id.in_(paper_ids)).all()
    finally:
        db.close()


def calc_light_score(analysis: dict) -> float:
    topic_fit = analysis.get("topic_fit", "low")
    novelty_level = analysis.get("novelty_level", "medium")
    reproducibility_level = analysis.get("reproducibility_level", "medium")
    recommendation = analysis.get("recommendation", "skip")

    topic_score_map = {"high": 5.0, "medium": 3.3, "low": 1.0}
    novelty_score_map = {"high": 4.8, "medium": 3.2, "low": 2.0}
    reproducibility_score_map = {"high": 4.4, "medium": 3.0, "low": 1.6}
    recommendation_bonus_map = {"read": 0.5, "skim": 0.1, "skip": -1.0}

    topic_score = topic_score_map.get(topic_fit, 1.0)
    novelty_score = novelty_score_map.get(novelty_level, 3.2)
    reproducibility_score = reproducibility_score_map.get(reproducibility_level, 3.0)
    recommendation_bonus = recommendation_bonus_map.get(recommendation, -1.0)

    final_score = (
        topic_score * 0.55
        + novelty_score * 0.30
        + reproducibility_score * 0.15
        + recommendation_bonus
    )

    reproducibility_reason = str(analysis.get("reproducibility_reason") or "").strip()
    implementation_evidence = str(analysis.get("implementation_evidence") or "").strip()
    evidence_signals = analysis.get("evidence_signals") or []

    strong_repro_evidence_count = 0
    if reproducibility_reason:
        strong_repro_evidence_count += 1
    if implementation_evidence:
        strong_repro_evidence_count += 1
    if evidence_signals:
        strong_repro_evidence_count += 1

    if reproducibility_level == "high" and strong_repro_evidence_count < 2:
        final_score -= 1.0
    if topic_fit == "medium":
        final_score = min(final_score, 4.2)
    if topic_fit == "low":
        final_score = min(final_score, 2.0)
    if final_score > 4.8:
        final_score = 4.8

    return round(max(1.0, final_score), 2)


def _build_relative_priority(rank: int) -> tuple[str, str, str]:
    if rank == 1:
        return ("top_pick", "优先推荐", "当前主题下最值得先看的论文。")
    if rank <= 3:
        return ("strong_pick", "重点推荐", "推荐度靠前，适合作为本轮优先阅读对象。")
    return ("watch_list", "建议关注", "可作为补充阅读，帮助完善主题视角。")


def _build_ranking_reasons(item: dict) -> list[str]:
    reasons: list[str] = []

    if item.get("topic_fit") == "high":
        reasons.append("与当前主题高度相关")
    elif item.get("topic_fit") == "medium":
        reasons.append("与当前主题有明确关联")

    if item.get("recommendation") == "read":
        reasons.append("更适合作为优先精读对象")
    elif item.get("recommendation") == "skim":
        reasons.append("建议先快速浏览核心方法与结果")

    if item.get("novelty_level") == "high":
        reasons.append("创新性表现较强")

    if item.get("reproducibility_level") == "high":
        reasons.append("复现条件相对更充分")
    elif item.get("reproducibility_level") == "medium":
        reasons.append("具备一定复现线索")

    evidence_signals = item.get("evidence_signals") or []
    if evidence_signals:
        reasons.append("存在实现或实验相关证据")

    reproducibility_reason = str(item.get("reproducibility_reason") or "").strip()
    if reproducibility_reason and len(reasons) < 4:
        reasons.append(reproducibility_reason[:32] + ("..." if len(reproducibility_reason) > 32 else ""))

    if not reasons:
        reasons.append("综合相关性、创新性与复现线索后进入本轮推荐")

    return reasons[:3]


def _attach_relative_ranking(items: list[dict]) -> list[dict]:
    ranked_items = []
    score_by_rank = {1: 98, 2: 95, 3: 92, 4: 88, 5: 84}

    for index, item in enumerate(items, start=1):
        priority_bucket, priority_label, priority_summary = _build_relative_priority(index)
        ranking_reasons = _build_ranking_reasons(item)
        recommendation_score = score_by_rank.get(index, max(76, 84 - (index - 5) * 3))

        ranked_items.append(
            {
                **item,
                "relative_rank": index,
                "recommendation_score": recommendation_score,
                "priority_bucket": priority_bucket,
                "priority_label": priority_label,
                "priority_summary": priority_summary,
                "ranking_reasons": ranking_reasons,
                "ranking_reason": "；".join(ranking_reasons[:2]),
            }
        )

    return ranked_items


def save_light_analysis(paper_id: int, project_topic: str, analysis: dict):
    from app.services.topic_rules import normalize_topic_label

    db = SessionLocal()
    try:
        score = calc_light_score(analysis)
        normalized_topic = normalize_topic_label(project_topic)

        exists = (
            db.query(PaperAnalysis)
            .filter(
                PaperAnalysis.paper_id == paper_id,
                PaperAnalysis.analysis_type == "light",
                PaperAnalysis.project_topic == normalized_topic,
            )
            .first()
        )

        payload = {
            "project_topic": normalized_topic,
            "one_sentence_summary": analysis.get("one_sentence_summary"),
            "final_conclusion": analysis.get("final_conclusion"),
            "recommendation": analysis.get("recommendation"),
            "recommendation_zh": analysis.get("recommendation_zh"),
            "topic_fit": analysis.get("topic_fit"),
            "topic_fit_zh": analysis.get("topic_fit_zh"),
            "novelty_level": analysis.get("novelty_level"),
            "novelty_level_zh": analysis.get("novelty_level_zh"),
            "reproducibility_level": analysis.get("reproducibility_level"),
            "reproducibility_level_zh": analysis.get("reproducibility_level_zh"),
            "tags_json": json.dumps(analysis.get("tags", []), ensure_ascii=False),
            "raw_json": json.dumps(analysis, ensure_ascii=False),
            "score": score,
        }

        if exists:
            for key, value in payload.items():
                setattr(exists, key, value)
        else:
            db.add(PaperAnalysis(paper_id=paper_id, analysis_type="light", **payload))

        db.commit()
    finally:
        db.close()


def delete_light_analyses_by_topic(project_topic: str):
    from app.services.topic_rules import normalize_topic_label

    db = SessionLocal()
    try:
        normalized_topic = normalize_topic_label(project_topic)
        (
            db.query(PaperAnalysis)
            .filter(
                PaperAnalysis.analysis_type == "light",
                PaperAnalysis.project_topic == normalized_topic,
            )
            .delete(synchronize_session=False)
        )
        db.commit()
    finally:
        db.close()


def list_recommendations(project_topic: str, limit: int = 10):
    from app.services.topic_rules import normalize_topic_label

    db = SessionLocal()
    try:
        normalized_topic = normalize_topic_label(project_topic)
        rows = (
            db.query(Paper, PaperAnalysis)
            .join(PaperAnalysis, Paper.id == PaperAnalysis.paper_id)
            .filter(PaperAnalysis.analysis_type == "light")
            .filter(PaperAnalysis.project_topic == normalized_topic)
            .order_by(PaperAnalysis.score.desc(), PaperAnalysis.id.desc())
            .limit(limit)
            .all()
        )

        result = []
        for paper, analysis in rows:
            extra = {}
            if analysis.raw_json:
                try:
                    extra = json.loads(analysis.raw_json)
                except Exception:
                    extra = {}

            result.append(
                {
                    "paper_id": paper.id,
                    "title": paper.title,
                    "paper_url": paper.paper_url,
                    "pdf_url": paper.pdf_url,
                    "source_date": paper.source_date,
                    "one_sentence_summary": analysis.one_sentence_summary,
                    "final_conclusion": analysis.final_conclusion,
                    "recommendation": analysis.recommendation,
                    "recommendation_zh": analysis.recommendation_zh,
                    "topic_fit": analysis.topic_fit,
                    "topic_fit_zh": analysis.topic_fit_zh,
                    "novelty_level": analysis.novelty_level,
                    "novelty_level_zh": analysis.novelty_level_zh,
                    "reproducibility_level": analysis.reproducibility_level,
                    "reproducibility_level_zh": analysis.reproducibility_level_zh,
                    "score": analysis.score,
                    "tags": json.loads(analysis.tags_json) if analysis.tags_json else [],
                    "reproducibility_reason": extra.get("reproducibility_reason", ""),
                    "evidence_signals": extra.get("evidence_signals", []),
                }
            )
        return _attach_relative_ranking(result)
    finally:
        db.close()


def get_fresh_cached_recommendations(project_topic: str, limit: int = 5, max_age_hours: int = 12):
    from app.services.topic_rules import normalize_topic_label

    db = SessionLocal()
    try:
        normalized_topic = normalize_topic_label(project_topic)
        rows = (
            db.query(PaperAnalysis)
            .filter(PaperAnalysis.analysis_type == "light")
            .filter(PaperAnalysis.project_topic == normalized_topic)
            .order_by(PaperAnalysis.updated_at.desc(), PaperAnalysis.id.desc())
            .limit(limit)
            .all()
        )

        if len(rows) < limit:
            return []

        newest_time = rows[0].updated_at
        if newest_time is None:
            return []

        if newest_time.tzinfo is None:
            newest_time = newest_time.replace(tzinfo=timezone.utc)

        if newest_time < datetime.now(timezone.utc) - timedelta(hours=max_age_hours):
            return []

        return list_recommendations(project_topic=normalized_topic, limit=limit)
    finally:
        db.close()


def _normalize_absolute_url(base_url: str, href: str) -> str:
    if not href:
        return ""
    href = href.strip()
    if not href or href.startswith("javascript:") or href.startswith("#"):
        return ""
    return urljoin(base_url, href)


def _is_http_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False


def _looks_like_dataset_url(url: str) -> bool:
    if not url:
        return False

    lowered = url.lower()
    parsed = urlparse(lowered)
    host = parsed.netloc
    path = parsed.path or ""

    generic_paths = {"/dataset", "/datasets", "/data", "/download", "/downloads"}
    if path in generic_paths:
        return False

    trusted_hosts = [
        "huggingface.co",
        "kaggle.com",
        "zenodo.org",
        "figshare.com",
        "archive.ics.uci.edu",
        "openml.org",
        "github.com",
        "drive.google.com",
        "dropbox.com",
        "paperswithcode.com",
    ]

    host_hit = any(h in host for h in trusted_hosts)
    path_hit = (
        "/datasets/" in path
        or "/dataset/" in path
        or "dataset" in path
        or "data" in path
        or "benchmark" in path
    )

    return host_hit and path_hit


def _is_reachable_url(url: str) -> bool:
    if not _is_http_url(url):
        return False

    try:
        resp = requests.head(
            url,
            allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        if resp.status_code < 400:
            return True
    except Exception:
        pass

    try:
        resp = requests.get(
            url,
            allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
            stream=True,
        )
        return resp.status_code < 400
    except Exception:
        return False


def _extract_real_resource_links_from_paper_page(paper_url: str) -> dict:
    if not paper_url:
        return {"github_url": "", "dataset_links": []}

    try:
        resp = requests.get(
            paper_url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=20,
        )
        resp.raise_for_status()
        html = resp.text
        soup = BeautifulSoup(html, "html.parser")

        github_url = ""
        dataset_links = []
        seen = set()

        for a in soup.find_all("a", href=True):
            raw_href = a["href"].strip()
            href = _normalize_absolute_url(paper_url, raw_href)
            if not href or href in seen:
                continue
            seen.add(href)

            href_lower = href.lower()
            if not github_url and "github.com" in href_lower and _is_reachable_url(href):
                github_url = href
            if _looks_like_dataset_url(href) and _is_reachable_url(href):
                dataset_links.append(href)

        if not github_url:
            match = re.search(r"https?://github\.com/[A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+", html)
            if match:
                candidate = match.group(0)
                if _is_reachable_url(candidate):
                    github_url = candidate

        deduped_dataset_links = []
        seen_dataset = set()
        for link in dataset_links:
            if link not in seen_dataset:
                seen_dataset.add(link)
                deduped_dataset_links.append(link)

        return {"github_url": github_url, "dataset_links": deduped_dataset_links[:6]}
    except Exception:
        return {"github_url": "", "dataset_links": []}


def _download_pdf_to_temp(pdf_url: str) -> str:
    if not pdf_url or not _is_http_url(pdf_url):
        return ""

    try:
        resp = requests.get(
            pdf_url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=30,
        )
        resp.raise_for_status()

        fd, path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        with open(path, "wb") as f:
            f.write(resp.content)
        return path
    except Exception:
        return ""


def _extract_pdf_text(pdf_path: str) -> str:
    if not pdf_path:
        return ""

    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(pdf_path)
        texts = []
        for page in reader.pages[:40]:
            try:
                texts.append(page.extract_text() or "")
            except Exception:
                continue
        return "\n".join(texts)
    except Exception:
        return ""


def _extract_appendix_evidence_from_pdf(pdf_url: str) -> dict:
    pdf_path = _download_pdf_to_temp(pdf_url)
    if not pdf_path:
        return {"appendix_evidence": "", "appendix_signals": []}

    try:
        full_text = _extract_pdf_text(pdf_path)
    finally:
        try:
            os.remove(pdf_path)
        except Exception:
            pass

    if not full_text:
        return {"appendix_evidence": "", "appendix_signals": []}

    lower_text = full_text.lower()
    appendix_keywords = [
        "appendix",
        "supplementary",
        "implementation details",
        "training details",
        "hyperparameter",
        "hyperparameters",
        "optimizer",
        "learning rate",
        "batch size",
        "dataset",
        "benchmark",
        "evaluation protocol",
        "ablation",
        "reproduc",
        "code will be released",
        "code is available",
        "publicly available",
    ]

    hits = [kw for kw in appendix_keywords if kw in lower_text]
    appendix_start = -1
    for marker in ["appendix", "supplementary", "implementation details"]:
        appendix_start = lower_text.find(marker)
        if appendix_start != -1:
            break

    excerpt = full_text[appendix_start:appendix_start + 2200] if appendix_start != -1 else full_text[:2200]

    signal_map = {
        "appendix": "附录提供额外说明",
        "supplementary": "补充材料可用",
        "implementation details": "实现细节较完整",
        "training details": "训练细节较完整",
        "hyperparameter": "给出超参数信息",
        "hyperparameters": "给出超参数信息",
        "optimizer": "给出优化器设置",
        "learning rate": "给出学习率设置",
        "batch size": "给出 batch size",
        "dataset": "说明了数据集信息",
        "benchmark": "包含公开评测结果",
        "evaluation protocol": "说明了评测协议",
        "ablation": "提供消融实验",
        "reproduc": "提到复现相关说明",
        "code will be released": "提到代码发布计划",
        "code is available": "提到代码可用",
        "publicly available": "提到公开可用资源",
    }

    appendix_signals = []
    seen = set()
    for kw in hits:
        label = signal_map.get(kw)
        if label and label not in seen:
            seen.add(label)
            appendix_signals.append(label)

    appendix_evidence = excerpt.strip()
    if len(appendix_evidence) > 900:
        appendix_evidence = appendix_evidence[:900] + "..."

    return {"appendix_evidence": appendix_evidence, "appendix_signals": appendix_signals[:8]}


def get_recommendation_detail(paper_id: int, project_topic: str):
    from app.services.topic_rules import normalize_topic_label

    db = SessionLocal()
    try:
        normalized_topic = normalize_topic_label(project_topic)
        row = (
            db.query(Paper, PaperAnalysis)
            .join(PaperAnalysis, Paper.id == PaperAnalysis.paper_id)
            .filter(Paper.id == paper_id)
            .filter(PaperAnalysis.analysis_type == "light")
            .filter(PaperAnalysis.project_topic == normalized_topic)
            .order_by(PaperAnalysis.id.desc())
            .first()
        )

        if not row:
            return None

        paper, analysis = row
        extra = {}
        if analysis.raw_json:
            try:
                extra = json.loads(analysis.raw_json)
            except Exception:
                extra = {}

        resource_links = _extract_real_resource_links_from_paper_page(paper.paper_url or "")
        appendix_info = _extract_appendix_evidence_from_pdf(paper.pdf_url or "")

        return {
            "paper_id": paper.id,
            "title": paper.title,
            "paper_url": paper.paper_url,
            "pdf_url": paper.pdf_url,
            "source_date": paper.source_date,
            "one_sentence_summary": analysis.one_sentence_summary,
            "final_conclusion": analysis.final_conclusion,
            "recommendation_zh": analysis.recommendation_zh,
            "topic_fit_zh": analysis.topic_fit_zh,
            "novelty_level_zh": analysis.novelty_level_zh,
            "reproducibility_level_zh": analysis.reproducibility_level_zh,
            "reproducibility_reason": extra.get("reproducibility_reason", ""),
            "study_goal": extra.get("study_goal", ""),
            "method_summary": extra.get("method_summary", ""),
            "content_summary": extra.get("content_summary", ""),
            "implementation_evidence": extra.get("implementation_evidence", ""),
            "innovations": extra.get("innovations", []),
            "limitations": extra.get("limitations", []),
            "evidence_signals": extra.get("evidence_signals", []),
            "tags": json.loads(analysis.tags_json) if analysis.tags_json else [],
            "github_url": resource_links.get("github_url", ""),
            "dataset_links": resource_links.get("dataset_links", []),
            "appendix_evidence": appendix_info.get("appendix_evidence", ""),
            "appendix_signals": appendix_info.get("appendix_signals", []),
        }
    finally:
        db.close()


def _build_best_for(detail: dict) -> list[str]:
    best_for: list[str] = []

    recommendation = str(detail.get("recommendation_zh") or "")
    reproducibility = str(detail.get("reproducibility_level_zh") or "")
    topic_fit = str(detail.get("topic_fit_zh") or "")
    novelty = str(detail.get("novelty_level_zh") or "")

    has_github = bool(detail.get("github_url"))
    has_dataset = bool(detail.get("dataset_links"))
    has_appendix = bool(detail.get("appendix_evidence"))

    if "推荐" in recommendation or "优先" in recommendation:
        best_for.append("精读")
    if "较易" in reproducibility or "中等" in reproducibility or has_github or has_dataset:
        best_for.append("复现")
    if "高度" in topic_fit:
        best_for.append("相关工作")
    if "高" in novelty:
        best_for.append("选题灵感")
    if has_appendix and "复现" not in best_for:
        best_for.append("复现")

    if not best_for:
        best_for.append("快速浏览")

    return best_for[:3]


def _build_onboarding_difficulty(detail: dict) -> str:
    reproducibility = str(detail.get("reproducibility_level_zh") or "")
    has_github = bool(detail.get("github_url"))
    has_dataset = bool(detail.get("dataset_links"))
    has_appendix = bool(detail.get("appendix_evidence"))

    evidence_count = sum([has_github, has_dataset, has_appendix])

    if "较易" in reproducibility and evidence_count >= 2:
        return "较易上手"
    if "中等" in reproducibility or evidence_count >= 1:
        return "需要一定准备"
    return "上手门槛偏高"


def _build_compare_reason(detail: dict) -> str:
    reasons: list[str] = []

    recommendation = str(detail.get("recommendation_zh") or "")
    topic_fit = str(detail.get("topic_fit_zh") or "")
    novelty = str(detail.get("novelty_level_zh") or "")
    reproducibility = str(detail.get("reproducibility_level_zh") or "")

    if recommendation:
        reasons.append(f"推荐性{recommendation}")
    if topic_fit:
        reasons.append(f"主题匹配{topic_fit}")
    if novelty:
        reasons.append(f"创新性{novelty}")
    if reproducibility:
        reasons.append(f"上手难度参考为{reproducibility}")

    if detail.get("github_url"):
        reasons.append("带 GitHub 线索")
    elif detail.get("dataset_links"):
        reasons.append("有数据资源线索")

    return "，".join(reasons[:3]) if reasons else "适合放到同主题候选里对比取舍。"


def get_recommendation_comparison(paper_ids: list[int], project_topic: str):
    normalized_topic = project_topic
    items: list[dict] = []

    for paper_id in paper_ids:
        detail = get_recommendation_detail(paper_id=paper_id, project_topic=normalized_topic)
        if not detail:
            continue

        items.append(
            {
                **detail,
                "best_for": _build_best_for(detail),
                "onboarding_difficulty": _build_onboarding_difficulty(detail),
                "has_github": bool(detail.get("github_url")),
                "has_dataset": bool(detail.get("dataset_links")),
                "has_pdf": bool(detail.get("pdf_url")),
                "compare_reason": _build_compare_reason(detail),
            }
        )

    return items
