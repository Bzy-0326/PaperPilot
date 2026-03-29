from __future__ import annotations

from typing import Any

from app.db import SessionLocal
from app.models import Paper
from app.services.paper_repository import list_recommendations, save_light_analysis, save_papers


DEMO_PAPERS: list[dict[str, Any]] = [
    {
        "source": "paperpilot_demo",
        "source_paper_id": "demo-hidden-states",
        "title": "Nudging Hidden States: Training-Free Model Steering for Chain-of-Thought Reasoning in Large Audio-Language Models",
        "abstract": "A demo paper about improving chain-of-thought reasoning for audio-language models without additional training.",
        "authors": ["PaperPilot Demo"],
        "paper_url": "https://arxiv.org/abs/2503.00001",
        "pdf_url": "https://arxiv.org/pdf/2503.00001",
        "source_date": "2026-03-29",
    },
    {
        "source": "paperpilot_demo",
        "source_paper_id": "demo-vfig",
        "title": "VFIG: Vectorizing Complex Figures in SVG with Vision-Language Models",
        "abstract": "A demo paper about turning complex figures into SVG using vision-language models.",
        "authors": ["PaperPilot Demo"],
        "paper_url": "https://arxiv.org/abs/2503.00002",
        "pdf_url": "https://arxiv.org/pdf/2503.00002",
        "source_date": "2026-03-29",
    },
    {
        "source": "paperpilot_demo",
        "source_paper_id": "demo-avo",
        "title": "AVO: Agentic Variation Operators for Autonomous Evolutionary Search",
        "abstract": "A demo paper about agentic variation operators that improve autonomous search performance.",
        "authors": ["PaperPilot Demo"],
        "paper_url": "https://arxiv.org/abs/2503.00003",
        "pdf_url": "https://arxiv.org/pdf/2503.00003",
        "source_date": "2026-03-29",
    },
    {
        "source": "paperpilot_demo",
        "source_paper_id": "demo-rag",
        "title": "Retrieval Layer Planning for Long-Context RAG Systems",
        "abstract": "A demo paper about improving retrieval planning and context packing for RAG systems.",
        "authors": ["PaperPilot Demo"],
        "paper_url": "https://arxiv.org/abs/2503.00004",
        "pdf_url": "https://arxiv.org/pdf/2503.00004",
        "source_date": "2026-03-29",
    },
    {
        "source": "paperpilot_demo",
        "source_paper_id": "demo-multimodal",
        "title": "Multimodal Alignment Signals for Efficient Reasoning Agents",
        "abstract": "A demo paper about multimodal alignment signals for efficient reasoning agents.",
        "authors": ["PaperPilot Demo"],
        "paper_url": "https://arxiv.org/abs/2503.00005",
        "pdf_url": "https://arxiv.org/pdf/2503.00005",
        "source_date": "2026-03-29",
    },
]


DEMO_ANALYSES: dict[str, dict[str, Any]] = {
    "demo-hidden-states": {
        "one_sentence_summary": "该研究通过训练外的隐藏状态引导，让大型音频语言模型在链式推理上更稳、更容易先读出价值。",
        "final_conclusion": "如果你想先看一篇能快速理解产品价值和方法思路的论文，这篇最适合作为 Demo 首页的首推候选。",
        "recommendation": "read",
        "recommendation_zh": "推荐精读",
        "topic_fit": "high",
        "topic_fit_zh": "高度相关",
        "novelty_level": "high",
        "novelty_level_zh": "高创新",
        "reproducibility_level": "medium",
        "reproducibility_level_zh": "可复现性中等",
        "reproducibility_reason": "方法思路清晰，但需要进一步公开训练或评测细节才能稳定复现。",
        "study_goal": "论文关注如何在不重新训练模型的情况下提高链式推理表现，目标是用更轻量的方式提升大型音频语言模型的复杂推理能力。",
        "method_summary": "作者引入训练外的隐藏状态引导策略，在推理时通过中间表示约束模型生成过程，并减少纯提示工程的不稳定性。",
        "content_summary": "文章强调了训练外方法在链式推理中的实用价值，既保留了较强的解释性，也更适合做快速产品体验展示。",
        "implementation_evidence": "文中描述了核心推理流程、实验场景和结果对比，但完整训练配置与可运行实现仍需要更多公开材料。",
        "innovations": [
            "提出训练外的隐藏状态引导策略，用更轻量的方式提升推理表现。",
            "把音频语言模型的链式推理改进问题转化为更易控制的中间表示优化问题。",
            "兼顾方法可解释性与产品展示价值，适合做推荐与对比场景中的首屏候选。 ",
        ],
        "limitations": [
            "公开实现和更完整的超参数说明仍不足。",
            "目前的结果更像方法验证，距离完整复现还有一定门槛。",
        ],
        "evidence_signals": ["appendix details", "benchmark results"],
        "tags": ["大型语言模型", "链式推理", "模型引导", "音频语言模型", "训练外方法"],
    },
    "demo-vfig": {
        "one_sentence_summary": "VFIG 用视觉-语言模型把复杂图形转换为 SVG，更适合关注多模态表示与工程落地的用户先读。",
        "final_conclusion": "如果你想看更容易转成产品截图和对比展示的候选，这篇在可视化表达和内容完整度上更有优势。",
        "recommendation": "read",
        "recommendation_zh": "推荐精读",
        "topic_fit": "high",
        "topic_fit_zh": "高度相关",
        "novelty_level": "high",
        "novelty_level_zh": "高创新",
        "reproducibility_level": "medium",
        "reproducibility_level_zh": "可复现性中等",
        "reproducibility_reason": "任务定义清楚，数据与评测路径明确，但模型细节和资源开销仍需要额外说明。",
        "study_goal": "论文目标是把复杂科研图形自动转换为更高质量的 SVG 表达，降低图像在学术演示和后续编辑中的使用成本。",
        "method_summary": "作者把视觉理解与矢量化生成结合起来，利用视觉-语言模型理解复杂图形结构，再完成 SVG 层级化表达。",
        "content_summary": "这篇论文兼具多模态、工程化和展示友好度，非常适合作为首页推荐、详情分析和论文对比里的高价值样本。",
        "implementation_evidence": "文中描述了数据构建、评测集与系统流程，也提供了比较清晰的实验目标和指标，但开源材料仍不算完整。",
        "innovations": [
            "把复杂科研图形矢量化问题与视觉-语言模型结合，扩展了多模态模型的应用边界。",
            "把结果直接落到 SVG 这种更适合二次编辑和产品展示的格式上。",
            "相比纯识别任务，更强调图形结构理解与输出质量。 ",
        ],
        "limitations": [
            "依赖较大的视觉-语言模型与特定训练资源。",
            "复杂图形场景下的稳定性还需要更多公开案例验证。",
        ],
        "evidence_signals": ["dataset available", "benchmark results", "evaluation protocol"],
        "tags": ["矢量化", "SVG", "视觉-语言模型", "复杂图形", "多模态"],
    },
    "demo-avo": {
        "one_sentence_summary": "AVO 把自主编码代理引入进化搜索流程，适合关注智能体和自动优化方向的用户快速扫读。",
        "final_conclusion": "如果你想找更偏探索性和方向启发的候选，这篇适合作为选题或灵感类推荐。",
        "recommendation": "skim",
        "recommendation_zh": "建议速读",
        "topic_fit": "medium",
        "topic_fit_zh": "中度相关",
        "novelty_level": "high",
        "novelty_level_zh": "高创新",
        "reproducibility_level": "medium",
        "reproducibility_level_zh": "可复现性中等",
        "reproducibility_reason": "整体路线明确，但搜索过程和环境设定会影响最终复现难度。",
        "study_goal": "论文想解决自主搜索中变异操作过于固定的问题，让代理能够更灵活地产生新的搜索候选。",
        "method_summary": "作者把智能体引入进化搜索流程，使其能够根据当前状态动态选择或生成变异操作，提高搜索质量。",
        "content_summary": "这篇更偏方法灵感和方向启发，适合在候选集中做补充阅读，而不是最先投入精读时间。",
        "implementation_evidence": "实验结论完整，但若要做真正复现，还需要更细的搜索配置和环境构建说明。",
        "innovations": [
            "用代理驱动变异操作，替代传统进化搜索里固定的变异模板。",
            "把搜索过程做成更可适应的决策过程，增加方法灵活性。",
        ],
        "limitations": [
            "对实验环境和搜索预算较敏感。",
            "如果缺少更细节的设置，复现路径会有波动。",
        ],
        "evidence_signals": ["benchmark results"],
        "tags": ["自主编码代理", "变异操作", "多头注意力机制", "GPU优化", "进化搜索", "LLM"],
    },
    "demo-rag": {
        "one_sentence_summary": "这篇 Demo 论文聚焦长上下文 RAG 的检索规划，更适合作为实际应用型主题的快速体验样本。",
        "final_conclusion": "如果你更关心 RAG 这类热门主题，Demo 模式也能先给出像样的候选体验，不会因为没 Key 就卡住。",
        "recommendation": "read",
        "recommendation_zh": "推荐精读",
        "topic_fit": "high",
        "topic_fit_zh": "高度相关",
        "novelty_level": "medium",
        "novelty_level_zh": "中等创新",
        "reproducibility_level": "high",
        "reproducibility_level_zh": "较易复现",
        "reproducibility_reason": "检索规划、上下文打包和评测目标都较为明确，更适合做应用向复现。",
        "study_goal": "文章希望改善长上下文 RAG 系统中检索层规划不稳定的问题，让系统在不同知识任务下都能更稳定地找到有用证据。",
        "method_summary": "作者提出分层检索规划与上下文打包策略，优先保证证据召回质量，再优化上下文压缩与最终回答稳定性。",
        "content_summary": "相比更偏方法探索的论文，这篇更适合展示产品里“复现优先”或“实用优先”的排序逻辑。",
        "implementation_evidence": "任务定义清晰、工程目标明确，也更容易被一般开发者理解和尝试。",
        "innovations": [
            "把长上下文 RAG 的性能问题拆分成检索规划与上下文打包两个更可控的阶段。",
            "更强调应用落地与稳定性，而不仅仅是单点指标提升。",
        ],
        "limitations": [
            "创新性不如更偏方法探索的论文强。",
            "如果没有公开完整实验脚本，工程复现仍需自行补齐部分细节。",
        ],
        "evidence_signals": ["code available", "evaluation protocol", "dataset available"],
        "tags": ["RAG", "检索规划", "长上下文", "工程落地", "知识增强"],
    },
    "demo-multimodal": {
        "one_sentence_summary": "这篇 Demo 样本强调多模态对齐与推理效率，适合补足热门主题下的多样性展示。",
        "final_conclusion": "如果你想让第一次体验里能看到更多主题维度，这篇适合作为多模态方向的补充样本。",
        "recommendation": "skim",
        "recommendation_zh": "建议关注",
        "topic_fit": "medium",
        "topic_fit_zh": "中度相关",
        "novelty_level": "medium",
        "novelty_level_zh": "中等创新",
        "reproducibility_level": "medium",
        "reproducibility_level_zh": "可复现性中等",
        "reproducibility_reason": "方向清楚，但实现细节与推理效率优化通常需要更多工程经验。",
        "study_goal": "论文尝试在多模态推理代理中引入更轻量的对齐信号，让模型在保持能力的同时降低推理成本。",
        "method_summary": "通过更紧凑的对齐信号设计，减少多模态代理在推理过程中对冗余特征的依赖，提升效率与稳定性。",
        "content_summary": "它更适合出现在推荐列表的中后段，用来向用户说明产品不仅会给一个方向的论文，还会给多维度候选。",
        "implementation_evidence": "公开材料有限，但论文结构完整，适合作为演示环境中的辅助样本。",
        "innovations": [
            "从多模态对齐信号角度优化推理效率，而不是只堆更大的模型。",
            "强调推理成本与效果的平衡，适合产品场景中的价值表达。",
        ],
        "limitations": [
            "开源实现与完整复现实验材料有限。",
            "多模态场景依赖的基础设施较重。",
        ],
        "evidence_signals": ["appendix details"],
        "tags": ["多模态", "对齐信号", "推理效率", "智能体", "轻量优化"],
    },
}


def ensure_demo_recommendations(project_topic: str, limit: int = 5) -> list[dict[str, Any]]:
    save_papers(DEMO_PAPERS)

    db = SessionLocal()
    try:
        rows = (
            db.query(Paper)
            .filter(Paper.source == "paperpilot_demo")
            .all()
        )
        paper_id_by_source = {row.source_paper_id: row.id for row in rows}
    finally:
        db.close()

    for paper in DEMO_PAPERS:
        source_paper_id = paper["source_paper_id"]
        paper_id = paper_id_by_source.get(source_paper_id)
        if not paper_id:
            continue
        save_light_analysis(
            paper_id=paper_id,
            project_topic=project_topic,
            analysis=DEMO_ANALYSES[source_paper_id],
        )

    return list_recommendations(project_topic=project_topic, limit=limit)
