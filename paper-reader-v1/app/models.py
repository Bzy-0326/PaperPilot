from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from app.db import Base


class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False)
    source_paper_id = Column(String(255), nullable=True, index=True)
    title = Column(Text, nullable=False)
    abstract = Column(Text, nullable=True)
    authors_json = Column(Text, nullable=True)
    paper_url = Column(Text, nullable=True)
    pdf_url = Column(Text, nullable=True)
    arxiv_url = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=True)
    hf_score = Column(Float, nullable=True)
    source_date = Column(String(20), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PaperAnalysis(Base):
    __tablename__ = "paper_analyses"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False, index=True)

    analysis_type = Column(String(20), nullable=False)   # light / deep
    project_topic = Column(String(255), nullable=True, index=True)

    one_sentence_summary = Column(Text, nullable=True)
    final_conclusion = Column(Text, nullable=True)

    recommendation = Column(String(20), nullable=True)       # read / skim / skip
    recommendation_zh = Column(String(20), nullable=True)

    topic_fit = Column(String(20), nullable=True)            # high / medium / low
    topic_fit_zh = Column(String(20), nullable=True)

    novelty_level = Column(String(20), nullable=True)
    novelty_level_zh = Column(String(20), nullable=True)

    reproducibility_level = Column(String(20), nullable=True)
    reproducibility_level_zh = Column(String(40), nullable=True)

    tags_json = Column(Text, nullable=True)
    raw_json = Column(Text, nullable=True)

    score = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class FollowUpItem(Base):
    __tablename__ = "follow_up_items"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False, index=True)
    bucket = Column(String(20), nullable=False, index=True)
    topic = Column(String(255), nullable=True, index=True)
    title = Column(Text, nullable=False)
    one_sentence_summary = Column(Text, nullable=True)
    tags_json = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
