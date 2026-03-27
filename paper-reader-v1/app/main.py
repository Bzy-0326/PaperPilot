import json
from pathlib import Path
import shutil
import traceback
from typing import Any, Optional

import requests
from fastapi import Body, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.db import SessionLocal, engine
from app.models import Base, FollowUpItem, Paper
from app.services.analyzer import run_full_analysis
from app.services.file_naming import (
    build_reader_download_pdf_name,
    build_standard_pdf_name,
)
from app.services.hf_papers_fetcher import fetch_hf_daily_papers
from app.services.light_analyzer import run_light_analysis
from app.services.llm_client import get_effective_llm_info, temporary_llm_config
from app.services.paper_repository import (
    delete_light_analyses_by_topic,
    get_fresh_cached_recommendations,
    get_recommendation_comparison,
    get_papers_by_ids,
    get_recent_papers,
    get_recommendation_detail,
    list_papers,
    list_recommendations,
    save_light_analysis,
    save_papers,
)
from app.services.pdf_parser import parse_pdf_basic
from app.services.topic_expander import expand_topic_with_llm
from app.services.topic_rules import (
    get_topic_aliases,
    get_topic_keywords,
    is_topic_candidate,
    normalize_topic_label,
    passes_post_llm_topic_check,
)


app = FastAPI(title="Paper Reader V1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
DOWNLOAD_DIR = UPLOAD_DIR / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)


class LLMConfigPayload(BaseModel):
    provider: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None


class DailyRunRequest(BaseModel):
    project_topic: str = Field(default="llm")
    limit: int = Field(default=5, ge=1, le=20)
    llm_config: Optional[LLMConfigPayload] = None


class AnalyzeLightRequest(BaseModel):
    project_topic: str = Field(default="llm")
    limit: int = Field(default=10, ge=1, le=50)
    paper_ids: list[int] = Field(default_factory=list)
    llm_config: Optional[LLMConfigPayload] = None


class CompareRequest(BaseModel):
    project_topic: str = Field(default="llm")
    paper_ids: list[int] = Field(default_factory=list, min_length=2, max_length=3)


class FollowUpPayload(BaseModel):
    paper_id: int
    bucket: str = Field(min_length=1, max_length=20)
    topic: Optional[str] = None
    title: str = Field(min_length=1)
    one_sentence_summary: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


def _normalize_llm_payload(llm_config: Optional[LLMConfigPayload]) -> Optional[dict[str, Any]]:
    if not llm_config:
        return None

    payload = llm_config.model_dump(exclude_none=True)
    return payload or None


def _run_daily_pipeline(
    project_topic: str,
    limit: int,
    llm_config: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    normalized_topic = normalize_topic_label(project_topic)
    cached_items = get_fresh_cached_recommendations(
        project_topic=normalized_topic,
        limit=limit,
        max_age_hours=12,
    )

    if cached_items:
        return {
            "message": "已基于近期结果生成每日推荐。",
            "project_topic": normalized_topic,
            "fetched_count": 0,
            "checked_count": 0,
            "returned_count": len(cached_items),
            "items": cached_items,
            "cache_hit": True,
            "llm": get_effective_llm_info(llm_config),
        }

    papers = fetch_hf_daily_papers()
    save_papers(papers)
    delete_light_analyses_by_topic(normalized_topic)

    candidate_rows = get_recent_papers(50)
    checked_count = 0
    returned_count = 0

    with temporary_llm_config(llm_config):
        for row in candidate_rows:
            if returned_count >= limit:
                break

            title = row.title or ""
            abstract_text = row.abstract or ""

            is_candidate, _matched_keywords = is_topic_candidate(
                project_topic=normalized_topic,
                title=title,
                abstract_text=abstract_text,
            )
            if not is_candidate:
                continue

            checked_count += 1

            analysis = run_light_analysis(
                project_topic=normalized_topic,
                title=title,
                abstract_text=abstract_text,
                paper_url=row.paper_url or "",
            )

            if not passes_post_llm_topic_check(
                project_topic=normalized_topic,
                title=title,
                abstract_text=abstract_text,
                analysis=analysis,
            ):
                continue

            save_light_analysis(row.id, normalized_topic, analysis)
            returned_count += 1

    items = list_recommendations(project_topic=normalized_topic, limit=limit)

    if len(items) == 0:
        message = f"今天没有找到与主题“{normalized_topic}”匹配的推荐论文。"
    elif len(items) < limit:
        message = f"今天只找到 {len(items)} 篇与主题“{normalized_topic}”相关的推荐论文。"
    else:
        message = "已生成今日推荐。"

    return {
        "message": message,
        "project_topic": normalized_topic,
        "fetched_count": len(papers),
        "checked_count": checked_count,
        "returned_count": len(items),
        "items": items,
        "cache_hit": False,
        "llm": get_effective_llm_info(llm_config),
    }


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Paper Reader V1 running",
        "features": [
            "upload_pdf_analysis",
            "hf_daily_fetch",
            "light_recommendations",
            "daily_run",
            "recommendation_detail",
            "llm_status",
        ],
    }


@app.get("/llm/status")
def get_llm_status():
    return {
        "llm": get_effective_llm_info(),
        "note": "Supports local Ollama and user-provided OpenAI-compatible providers.",
    }


@app.get("/papers/daily/fetch")
def fetch_daily_papers_api():
    papers = fetch_hf_daily_papers()
    save_papers(papers)
    return {
        "message": "已抓取并保存 Hugging Face Daily 论文。",
        "count": len(papers),
        "papers": papers[:10],
    }


@app.get("/papers")
def get_papers(limit: int = 30):
    return {"items": list_papers(limit)}


@app.post("/papers/analyze_light")
def analyze_light_papers(data: AnalyzeLightRequest = Body(...)):
    project_topic = normalize_topic_label(data.project_topic)
    llm_config = _normalize_llm_payload(data.llm_config)

    if data.paper_ids:
        rows = get_papers_by_ids(data.paper_ids)
    else:
        rows = get_recent_papers(data.limit)

    results = []
    with temporary_llm_config(llm_config):
        for row in rows:
            analysis = run_light_analysis(
                project_topic=project_topic,
                title=row.title,
                abstract_text=row.abstract or "",
                paper_url=row.paper_url or "",
            )
            save_light_analysis(row.id, project_topic, analysis)
            results.append(
                {
                    "paper_id": row.id,
                    "title": row.title,
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
                    "tags": analysis.get("tags", []),
                }
            )

    return {
        "message": "轻分析完成。",
        "project_topic": project_topic,
        "count": len(results),
        "items": results,
        "llm": get_effective_llm_info(llm_config),
    }


@app.get("/papers/recommendations")
def get_recommendations(project_topic: str, limit: int = 20):
    normalized_topic = normalize_topic_label(project_topic)
    return {
        "project_topic": normalized_topic,
        "items": list_recommendations(project_topic=normalized_topic, limit=limit),
    }


@app.get("/papers/recommendation/{paper_id}")
def get_recommendation_detail_api(paper_id: int, project_topic: str):
    normalized_topic = normalize_topic_label(project_topic)
    item = get_recommendation_detail(paper_id=paper_id, project_topic=normalized_topic)
    if not item:
        raise HTTPException(status_code=404, detail="Recommendation detail not found")
    return item


@app.post("/papers/compare")
def compare_recommendations(data: CompareRequest = Body(...)):
    normalized_topic = normalize_topic_label(data.project_topic)
    items = get_recommendation_comparison(
        paper_ids=data.paper_ids,
        project_topic=normalized_topic,
    )
    return {
        "project_topic": normalized_topic,
        "count": len(items),
        "items": items,
    }


@app.get("/follow-ups")
def get_follow_ups():
    db = SessionLocal()
    try:
        rows = (
            db.query(FollowUpItem)
            .order_by(FollowUpItem.updated_at.desc(), FollowUpItem.id.desc())
            .all()
        )
        items = []
        for row in rows:
            items.append(
                {
                    "id": row.id,
                    "paper_id": row.paper_id,
                    "bucket": row.bucket,
                    "topic": row.topic,
                    "title": row.title,
                    "one_sentence_summary": row.one_sentence_summary,
                    "tags": json.loads(row.tags_json) if row.tags_json else [],
                    "added_at": row.created_at.isoformat() if row.created_at else None,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                }
            )
        return {"items": items, "count": len(items)}
    finally:
        db.close()


@app.post("/follow-ups")
def save_follow_up(data: FollowUpPayload = Body(...)):
    db = SessionLocal()
    try:
        bucket = data.bucket.strip()
        if bucket not in {"reading", "reproduce", "topic"}:
            raise HTTPException(status_code=400, detail="Invalid follow-up bucket")

        row = (
            db.query(FollowUpItem)
            .filter(
                FollowUpItem.paper_id == data.paper_id,
                FollowUpItem.bucket == bucket,
            )
            .first()
        )

        payload = {
            "topic": (data.topic or "").strip() or None,
            "title": data.title.strip(),
            "one_sentence_summary": (data.one_sentence_summary or "").strip() or None,
            "tags_json": json.dumps(data.tags or [], ensure_ascii=False),
        }

        if row:
            for key, value in payload.items():
                setattr(row, key, value)
        else:
            row = FollowUpItem(
                paper_id=data.paper_id,
                bucket=bucket,
                **payload,
            )
            db.add(row)

        db.commit()
        db.refresh(row)
        return {
            "message": "Follow-up saved",
            "item": {
                "id": row.id,
                "paper_id": row.paper_id,
                "bucket": row.bucket,
                "topic": row.topic,
                "title": row.title,
                "one_sentence_summary": row.one_sentence_summary,
                "tags": json.loads(row.tags_json) if row.tags_json else [],
                "added_at": row.created_at.isoformat() if row.created_at else None,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            },
        }
    finally:
        db.close()


@app.delete("/follow-ups/{paper_id}")
def delete_follow_up(paper_id: int, bucket: str):
    db = SessionLocal()
    try:
        row = (
            db.query(FollowUpItem)
            .filter(
                FollowUpItem.paper_id == paper_id,
                FollowUpItem.bucket == bucket,
            )
            .first()
        )
        if not row:
            raise HTTPException(status_code=404, detail="Follow-up item not found")

        db.delete(row)
        db.commit()
        return {"message": "Follow-up removed", "paper_id": paper_id, "bucket": bucket}
    finally:
        db.close()


@app.get("/papers/{paper_id}/download_pdf")
def download_paper_pdf(paper_id: int):
    db = SessionLocal()
    try:
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
    finally:
        db.close()

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    if not paper.pdf_url:
        raise HTTPException(status_code=404, detail="PDF link not found")

    try:
        response = requests.get(
            paper.pdf_url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=60,
        )
        response.raise_for_status()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to download PDF: {exc}") from exc

    download_name = build_reader_download_pdf_name(
        source_date=paper.source_date,
        title=paper.title,
        original_name=paper.pdf_url,
    )
    file_path = DOWNLOAD_DIR / download_name
    file_path.write_bytes(response.content)

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=download_name,
    )


@app.get("/debug/topic_expand")
def debug_topic_expand(project_topic: str):
    expanded = expand_topic_with_llm(project_topic)
    return {
        "input_topic": project_topic,
        "normalized_topic": normalize_topic_label(project_topic),
        "expanded": expanded,
        "rule_aliases": get_topic_aliases(project_topic),
        "rule_keywords": get_topic_keywords(project_topic),
        "llm": get_effective_llm_info(),
    }


@app.get("/papers/daily/run")
def run_daily_pipeline_get(project_topic: str = "llm", limit: int = 5):
    return _run_daily_pipeline(project_topic=project_topic, limit=limit)


@app.post("/papers/daily/run")
def run_daily_pipeline_post(data: DailyRunRequest = Body(...)):
    llm_config = _normalize_llm_payload(data.llm_config)
    return _run_daily_pipeline(
        project_topic=data.project_topic,
        limit=data.limit,
        llm_config=llm_config,
    )


@app.post("/analyze_pdf")
async def analyze_pdf(
    project_topic: str = Form(...),
    read_goal: str = Form("快速判断这篇论文是否值得继续精读"),
    score_profile: str = Form("innovation"),
    file: UploadFile = File(...),
):
    try:
        temp_path = UPLOAD_DIR / file.filename
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        parsed = parse_pdf_basic(str(temp_path))

        standard_name = build_standard_pdf_name(
            full_text=parsed["full_text"],
            original_name=file.filename,
        )

        final_path = UPLOAD_DIR / standard_name
        if temp_path != final_path:
            if final_path.exists():
                final_path.unlink()
            temp_path.rename(final_path)

        parsed = parse_pdf_basic(str(final_path))

        result = run_full_analysis(
            project_topic=project_topic,
            read_goal=read_goal,
            score_profile=score_profile,
            full_text=parsed["full_text"],
            links=parsed["links"],
        )

        return {
            "final_conclusion": result.get("final_conclusion"),
            "recommendation": result.get("decision", {}).get("recommendation_zh"),
            "file_summary": {
                "original_name": file.filename,
                "saved_name": final_path.name,
            },
            "detail": {
                "analysis": result.get("analysis"),
                "open_science": result.get("open_science"),
                "repo_summary": result.get("repo_summary"),
                "topic_fit": result.get("topic_fit"),
                "scores": result.get("scores"),
                "decision": result.get("decision"),
                "file_info": {
                    "file_name": final_path.name,
                    "saved_to": str(final_path),
                    "project_topic": project_topic,
                    "read_goal": read_goal,
                    "score_profile": score_profile,
                },
                "pdf_info": {
                    "page_count": parsed["page_count"],
                    "text_preview": parsed["full_text"][:1000],
                    "link_count": len(parsed["links"]),
                    "links": parsed["links"][:20],
                },
            },
        }
    except Exception as exc:
        return {
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "traceback": traceback.format_exc(),
        }
