"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";

type HomeItem = {
  paper_id: number;
  title?: string;
  paper_url?: string;
  pdf_url?: string;
  source_date?: string;
  one_sentence_summary?: string;
  final_conclusion?: string;
  recommendation_zh?: string;
  topic_fit_zh?: string;
  novelty_level_zh?: string;
  reproducibility_level_zh?: string;
  reproducibility_reason?: string;
  tags?: string[];
  score?: number;
  github_url?: string;
  dataset_links?: string[];
};

type DetailItem = {
  paper_id: number;
  title?: string;
  paper_url?: string;
  pdf_url?: string;
  source_date?: string;
  one_sentence_summary?: string;
  final_conclusion?: string;
  recommendation_zh?: string;
  topic_fit_zh?: string;
  novelty_level_zh?: string;
  reproducibility_level_zh?: string;
  reproducibility_reason?: string;
  study_goal?: string;
  method_summary?: string;
  content_summary?: string;
  implementation_evidence?: string;
  innovations?: string[];
  limitations?: string[];
  evidence_signals?: string[];
  tags?: string[];
  github_url?: string;
  dataset_links?: string[];
  appendix_evidence?: string;
  appendix_signals?: string[];
  score?: number;
};
const STORAGE_KEY = "paper_reader_home_state_v4";

const DETAIL_TEXT = {
  zh: {
    back: "返回首页",
    loading: "正在加载详情...",
    empty: "当前没有可展示的论文详情。",
    titleFallback: "论文详情",
    date: "日期",
    recommendation: "推荐性",
    novelty: "创新性",
    reproducibility: "可复现性",
    needMore: "待补充",
    reproducibilityCard: "可复现性",
    codeCard: "开源代码",
    dataCard: "数据与资源",
    materialsCard: "实现材料",
    recommendationConclusion: "推荐结论",
    background: "研究背景与目标",
    summary: "内容摘要",
    method: "实验方法",
    innovation: "创新点",
    limitation: "局限性总结",
    evidence: "复现证据信号",
    resources: "复现资源",
    github: "GitHub",
    dataset: "数据集来源",
    pdf: "PDF",
    downloadPdf: "下载 PDF（自动命名）",
    viewPaper: "查看原文（前往原始论文链接）",
  },
  en: {
    back: "Back Home",
    loading: "Loading details...",
    empty: "No paper details available.",
    titleFallback: "Paper Details",
    date: "Date",
    recommendation: "Recommendation",
    novelty: "Novelty",
    reproducibility: "Reproducibility",
    needMore: "Pending",
    reproducibilityCard: "Reproducibility",
    codeCard: "Open-source Code",
    dataCard: "Data & Resources",
    materialsCard: "Implementation Evidence",
    recommendationConclusion: "Recommendation",
    background: "Background and Goal",
    summary: "Summary",
    method: "Method",
    innovation: "Innovations",
    limitation: "Limitations",
    evidence: "Reproduction Signals",
    resources: "Resources",
    github: "GitHub",
    dataset: "Dataset Links",
    pdf: "PDF",
    downloadPdf: "Download PDF (Renamed)",
    viewPaper: "Open Original Paper",
  },
} as const;

function getApiBaseUrl() {
  if (typeof window !== "undefined") {
    return `${window.location.protocol}//${window.location.hostname}:8000`;
  }
  return "http://127.0.0.1:8000";
}

function safeList(value?: string[] | null) {
  return Array.isArray(value) ? value.filter(Boolean) : [];
}

function cleanText(value?: string | null) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function translateAssessmentValue(value: string | undefined, language: UILanguage) {
  const text = String(value || "").trim();
  if (!text || language === "zh") return text;
  const pairs: Array<[string, string]> = [
    ["推荐精读", "Recommended for Deep Read"],
    ["优先精读", "Read First"],
    ["优先推荐", "Top Pick"],
    ["建议速读", "Read Soon"],
    ["建议关注", "Worth Watching"],
    ["高度相关", "Highly Relevant"],
    ["高相关", "Highly Relevant"],
    ["中度相关", "Moderately Relevant"],
    ["高创新", "High Novelty"],
    ["较高创新", "High Novelty"],
    ["中等创新", "Moderate Novelty"],
    ["较易复现", "Easy to Reproduce"],
    ["可复现性中等", "Moderate Reproducibility"],
    ["较难复现", "Hard to Reproduce"],
    ["较完整", "Relatively Complete"],
    ["偏少", "Limited"],
    ["暂无", "Unavailable"],
    ["待补充", "Pending"],
  ];
  let translated = text;
  for (const [zh, en] of pairs) {
    translated = translated.replaceAll(zh, en);
  }
  return translated;
}

function translateTag(tag: string, language: UILanguage) {
  if (language === "zh") return tag;
  const mapping: Record<string, string> = {
    "行为克隆": "Behavior Cloning",
    "动作量化": "Action Quantization",
    "样本复杂度": "Sample Complexity",
    "连续控制": "Continuous Control",
    "理论分析": "Theory Analysis",
    "模型增强": "Model Enhancement",
    "金融LLM": "Finance LLM",
    "金融 LLM": "Finance LLM",
    "工具调用": "Tool Use",
    "基准测试": "Benchmarking",
    "大型语言模型": "Large Language Models",
    "金融模型上下文协议": "Financial MCP",
    "评估指标": "Evaluation Metrics",
    "音频-视觉导航": "Audio-Visual Navigation",
    "连续环境": "Continuous Environments",
    "智能体导航": "Agent Navigation",
    "多模态": "Multimodal",
    "目标推理": "Goal Reasoning",
    "推理": "Reasoning",
    "复现": "Reproduction",
    "选题": "Topic Ideas",
  };
  return mapping[tag] || tag;
}


function isRealGithubUrl(url?: string | null) {
  if (!url) return false;
  try {
    const parsed = new URL(url);
    return (
      (parsed.hostname === "github.com" || parsed.hostname === "www.github.com") &&
      parsed.pathname.split("/").filter(Boolean).length >= 2
    );
  } catch {
    return false;
  }
}

function normalizeEvidenceSignals(signals: string[], language: UILanguage) {
  const mapping: { keyword: string; label: string }[] = [
    { keyword: "github", label: language === "zh" ? "提供 GitHub 线索" : "GitHub evidence" },
    { keyword: "code", label: language === "zh" ? "提到代码或仓库" : "Code or repository mentioned" },
    { keyword: "repository", label: language === "zh" ? "提到代码仓库" : "Repository mentioned" },
    { keyword: "dataset", label: language === "zh" ? "提到数据集" : "Dataset mentioned" },
    { keyword: "data", label: language === "zh" ? "说明数据来源" : "Data source described" },
    { keyword: "appendix", label: language === "zh" ? "附录提供额外说明" : "Appendix evidence available" },
    { keyword: "supplementary", label: language === "zh" ? "补充材料可用" : "Supplementary material available" },
    { keyword: "implementation", label: language === "zh" ? "说明实现细节" : "Implementation details mentioned" },
    { keyword: "training", label: language === "zh" ? "说明训练细节" : "Training details mentioned" },
    { keyword: "hyperparameter", label: language === "zh" ? "给出超参数信息" : "Hyperparameters reported" },
    { keyword: "benchmark", label: language === "zh" ? "包含公开评测结果" : "Benchmark results included" },
    { keyword: "reproduce", label: language === "zh" ? "提到复现相关说明" : "Reproduction notes mentioned" },
  ];

  const normalized = new Set<string>();
  for (const raw of signals) {
    const text = raw.toLowerCase();
    let matched = false;
    for (const item of mapping) {
      if (text.includes(item.keyword)) {
        normalized.add(item.label);
        matched = true;
      }
    }
    if (!matched && raw.trim()) {
      normalized.add(raw.trim());
    }
  }
  return Array.from(normalized);
}

function getReproLevelStyle(level?: string) {
  const text = level || "待补充";
  if (text.includes("较易") || text.toLowerCase().includes("easy")) {
    return { bg: "#dcfce7", color: "#166534", border: "#bbf7d0" };
  }
  if (text.includes("中等") || text.toLowerCase().includes("moderate")) {
    return { bg: "#fef3c7", color: "#92400e", border: "#fde68a" };
  }
  if (text.includes("较高") || text.toLowerCase().includes("hard")) {
    return { bg: "#fee2e2", color: "#991b1b", border: "#fecaca" };
  }
  return { bg: "#f3f4f6", color: "#374151", border: "#e5e7eb" };
}

function formatAvailability(value: boolean, language: UILanguage) {
  return value ? (language === "zh" ? "有" : "Available") : language === "zh" ? "暂无" : "Unavailable";
}

function InfoBadge({ label, value, language }: { label: string; value?: string | number | null; language: UILanguage }) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        padding: "7px 12px",
        borderRadius: 999,
        background: "#f3f4f6",
        color: "#374151",
        fontSize: 12,
        fontWeight: 600,
      }}
    >
      <span style={{ color: "#6b7280" }}>{label}:</span>
      <span>{String(value || (language === "zh" ? "待补充" : "Pending"))}</span>
    </span>
  );
}

function SoftTag({ text, tone = "default" }: { text: string; tone?: "default" | "evidence" | "topic" }) {
  const styles =
    tone === "evidence"
      ? { bg: "#ecfeff", color: "#155e75" }
      : tone === "topic"
        ? { bg: "#eef2ff", color: "#3730a3" }
        : { bg: "#f3f4f6", color: "#4b5563" };

  return (
    <span
      style={{
        display: "inline-block",
        padding: "6px 10px",
        borderRadius: 999,
        background: styles.bg,
        color: styles.color,
        fontSize: 12,
        lineHeight: 1.2,
      }}
    >
      {text}
    </span>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section style={{ marginBottom: 28 }}>
      <h2
        style={{
          fontSize: 22,
          fontWeight: 800,
          color: "#111827",
          margin: "0 0 14px",
          letterSpacing: "-0.02em",
        }}
      >
        {title}
      </h2>
      {children}
    </section>
  );
}

function TextCard({ children, subtle = false }: { children: React.ReactNode; subtle?: boolean }) {
  return (
    <div
      style={{
        border: "1px solid #e5e7eb",
        borderRadius: 14,
        background: subtle ? "#fafafa" : "#ffffff",
        padding: 18,
        color: "#374151",
        lineHeight: 1.9,
        fontSize: 14,
      }}
    >
      {children}
    </div>
  );
}

function NumberPoint({ index, text }: { index: number; text: string }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "flex-start",
        gap: 12,
        border: "1px solid #e5e7eb",
        borderRadius: 12,
        padding: "12px 14px",
        background: "#fafafa",
        marginBottom: 10,
      }}
    >
      <div
        style={{
          width: 24,
          height: 24,
          borderRadius: 999,
          background: "#0f172a",
          color: "#fff",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 12,
          fontWeight: 700,
          flexShrink: 0,
          marginTop: 1,
        }}
      >
        {index}
      </div>
      <div style={{ color: "#374151", lineHeight: 1.8, fontSize: 14 }}>{text}</div>
    </div>
  );
}

function QuickStatCard({ title, value, helper }: { title: string; value: string; helper: string }) {
  return (
    <div
      style={{
        border: "1px solid #e5e7eb",
        borderRadius: 16,
        padding: 16,
        background: "#fff",
        minHeight: 118,
        boxShadow: "0 1px 2px rgba(15, 23, 42, 0.03)",
      }}
    >
      <div style={{ fontSize: 13, color: "#6b7280", marginBottom: 10, fontWeight: 600 }}>{title}</div>
      <div
        style={{
          fontSize: 22,
          fontWeight: 800,
          color: "#111827",
          marginBottom: 8,
          letterSpacing: "-0.02em",
        }}
      >
        {value}
      </div>
      <div style={{ fontSize: 13, color: "#4b5563", lineHeight: 1.7 }}>{helper}</div>
    </div>
  );
}

export default function PaperDetailPage() {
  const params = useParams();
  const searchParams = useSearchParams();

  const paperId = Number(params.paperId as string);
  const topic = searchParams.get("topic") || "";

  const [loading, setLoading] = useState(true);
  const [detail, setDetail] = useState<DetailItem | null>(null);
  const [fallbackItem, setFallbackItem] = useState<HomeItem | null>(null);
  const [error, setError] = useState("");
  const uiLanguage = "zh" as const;
  const text = DETAIL_TEXT.zh;

  useEffect(() => {
  }, []);

  useEffect(() => {
    let matched: HomeItem | null = null;

    try {
      const localRaw = localStorage.getItem(`paper_detail_fallback_${paperId}`);
      if (localRaw) {
        const parsed = JSON.parse(localRaw) as HomeItem;
        if (parsed && Number(parsed.paper_id) === paperId) {
          matched = parsed;
        }
      }

      if (!matched) {
        const sessionRaw = sessionStorage.getItem(STORAGE_KEY);
        if (sessionRaw) {
          const saved = JSON.parse(sessionRaw);
          const items = (saved.items || []) as HomeItem[];
          const found = items.find((x) => Number(x.paper_id) === paperId);
          if (found) matched = found;
        }
      }

      if (matched) {
        setFallbackItem(matched);
      }
    } catch (e) {
      console.error("读取详情页 fallback 失败", e);
    }
  }, [paperId]);

  useEffect(() => {
    const run = async () => {
      try {
        setLoading(true);
        setError("");

        const url = `${getApiBaseUrl()}/papers/recommendation/${paperId}?project_topic=${encodeURIComponent(topic)}`;
        const res = await fetch(url);
        const data = await res.json();

        if (!res.ok) {
          throw new Error(data?.detail || "详情加载失败");
        }

        setDetail(data);
      } catch (err: unknown) {
        console.error(err);
        setError("详情接口暂未返回完整结果，当前页面优先展示首页已有信息。");
      } finally {
        setLoading(false);
      }
    };

    if (paperId) void run();
  }, [paperId, topic]);

  const item = useMemo<DetailItem | null>(() => {
    if (detail) return detail;
    if (fallbackItem) return { ...fallbackItem } as DetailItem;
    return null;
  }, [detail, fallbackItem]);

  const innovations = safeList(item?.innovations).map(cleanText).filter(Boolean);
  const limitations = safeList(item?.limitations).map(cleanText).filter(Boolean);
  const tags = safeList(item?.tags).map(cleanText).filter(Boolean);
  const datasetLinks = safeList(item?.dataset_links);
  const reproducibilitySignals = normalizeEvidenceSignals(
    Array.from(new Set([...safeList(item?.evidence_signals), ...safeList(item?.appendix_signals)])),
    uiLanguage,
  );

  const oneSentenceSummary = cleanText(item?.one_sentence_summary);
  const studyGoal = cleanText(item?.study_goal);
  const contentSummary = cleanText(item?.content_summary) || oneSentenceSummary;
  const methodSummary = cleanText(item?.method_summary);
  const implementationEvidence = cleanText(item?.implementation_evidence);

  const paperLink = item?.paper_url || item?.pdf_url || "";
  const reproStyle = getReproLevelStyle(item?.reproducibility_level_zh);
  const realGithubUrl = isRealGithubUrl(item?.github_url) ? item?.github_url || "" : "";

  const hasGithub = !!realGithubUrl;
  const hasDataset = datasetLinks.length > 0;
  const hasImplementation = !!implementationEvidence;
  const hasAppendix = !!cleanText(item?.appendix_evidence);
  const pdfDownloadUrl = item?.pdf_url ? `${getApiBaseUrl()}/papers/${paperId}/download_pdf` : "";

  const expandedStudyGoal = [studyGoal, cleanText(item?.reproducibility_reason)]
    .filter(Boolean)
    .join(" ");

  const expandedMethodSummary = [methodSummary, implementationEvidence, cleanText(item?.appendix_evidence)]
    .filter(Boolean)
    .join(" ");

  const displayedOneSentenceSummary = oneSentenceSummary;
  const displayedStudyGoal = expandedStudyGoal;
  const displayedContentSummary = contentSummary;
  const displayedMethodSummary = expandedMethodSummary;
  const displayedImplementationEvidence = implementationEvidence;
  const displayedInnovations = innovations;
  const displayedLimitations = limitations;

  return (
    <main
      style={{
        maxWidth: 980,
        margin: "0 auto",
        padding: "24px 16px 56px",
        background: "#f8fafc",
        minHeight: "100vh",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, marginBottom: 14 }}>
        <button
          type="button"
          onClick={() => {
            window.location.href = "/";
          }}
          style={{
            border: "none",
            background: "transparent",
            color: "#4f46e5",
            cursor: "pointer",
            padding: 0,
            fontSize: 14,
            fontWeight: 600,
          }}
        >
          {text.back}
        </button>
      </div>

      {loading && !item && <div style={{ color: "#6b7280", fontSize: 14 }}>{text.loading}</div>}
      {!loading && !item && <div style={{ color: "#b91c1c", fontSize: 14 }}>{text.empty}</div>}

      {item && (
        <div
          style={{
            border: "1px solid #e5e7eb",
            borderRadius: 22,
            background: "#ffffff",
            padding: 22,
            boxShadow: "0 8px 30px rgba(15, 23, 42, 0.06)",
          }}
        >
          <section style={{ marginBottom: 26 }}>
            <h1
              style={{
                fontSize: 34,
                lineHeight: 1.25,
                fontWeight: 900,
                margin: "0 0 16px",
                color: "#111827",
                letterSpacing: "-0.03em",
              }}
            >
              {item.title || text.titleFallback}
            </h1>

            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 12 }}>
              <InfoBadge label={text.date} value={item.source_date || text.needMore} language={uiLanguage} />
              <InfoBadge label={text.recommendation} value={translateAssessmentValue(item.recommendation_zh, uiLanguage) || text.needMore} language={uiLanguage} />
              <InfoBadge label={text.novelty} value={translateAssessmentValue(item.novelty_level_zh, uiLanguage) || text.needMore} language={uiLanguage} />
              <span
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 6,
                  padding: "7px 12px",
                  borderRadius: 999,
                  background: reproStyle.bg,
                  color: reproStyle.color,
                  border: `1px solid ${reproStyle.border}`,
                  fontSize: 12,
                  fontWeight: 700,
                }}
              >
                {text.reproducibility}: {translateAssessmentValue(item.reproducibility_level_zh, uiLanguage) || text.needMore}
              </span>
            </div>

            {tags.length > 0 && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {tags.map((tag) => (
                  <SoftTag key={tag} text={translateTag(tag, uiLanguage)} tone="topic" />
                ))}
              </div>
            )}
          </section>

          <section style={{ marginBottom: 24 }}>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))",
                gap: 14,
              }}
            >
              <QuickStatCard
                title={text.reproducibilityCard}
                value={translateAssessmentValue(item.reproducibility_level_zh, uiLanguage) || text.needMore}
                helper={cleanText(item?.reproducibility_reason) || (uiLanguage === "zh" ? "当前还缺少更明确的复现结论。" : "There is still limited evidence for a stronger reproduction conclusion.")}
              />
              <QuickStatCard
                title={text.codeCard}
                value={formatAvailability(hasGithub, uiLanguage)}
                helper={hasGithub ? (uiLanguage === "zh" ? "已检索到真实 GitHub 仓库，可继续核查实现细节。" : "A real GitHub repository was found, so implementation details can be checked further.") : (uiLanguage === "zh" ? "当前未检索到可信 GitHub 仓库。" : "No reliable GitHub repository was found yet.")}
              />
              <QuickStatCard
                title={text.dataCard}
                value={formatAvailability(hasDataset, uiLanguage)}
                helper={hasDataset ? (uiLanguage === "zh" ? "已检索到可访问的数据集或资源链接。" : "Accessible dataset or resource links were found.") : (uiLanguage === "zh" ? "暂未找到明确的数据集或资源链接。" : "No clear dataset or resource links were found yet.")}
              />
              <QuickStatCard
                title={text.materialsCard}
                value={uiLanguage === "zh" ? (hasImplementation || hasAppendix ? "较完整" : "偏少") : (hasImplementation || hasAppendix ? "Relatively Complete" : "Limited")}
                helper={
                  hasImplementation || hasAppendix
                    ? (uiLanguage === "zh" ? "检测到实现说明、附录或训练细节，复现判断会更稳。" : "Implementation notes, appendix evidence, or training details were found, making the reproduction judgment more reliable.")
                    : (uiLanguage === "zh" ? "当前实现材料偏少，复现判断需要进一步查看原文。" : "Implementation evidence is still limited, so the original paper is worth checking directly.")
                }
              />
            </div>
          </section>

          {displayedOneSentenceSummary && (
            <Section title={text.recommendationConclusion}>
              <TextCard subtle>{displayedOneSentenceSummary}</TextCard>
            </Section>
          )}

          {displayedStudyGoal && (
            <Section title={text.background}>
              <TextCard subtle>{displayedStudyGoal}</TextCard>
            </Section>
          )}

          {displayedContentSummary && (
            <Section title={text.summary}>
              <TextCard subtle>{displayedContentSummary}</TextCard>
            </Section>
          )}

          {displayedMethodSummary && (
            <Section title={text.method}>
              <TextCard subtle>{displayedMethodSummary}</TextCard>
            </Section>
          )}

          {displayedInnovations.length > 0 && (
            <Section title={text.innovation}>
              <div>
                {displayedInnovations.map((point, index) => (
                  <NumberPoint key={`${point}-${index}`} index={index + 1} text={point} />
                ))}
              </div>
            </Section>
          )}

          {displayedLimitations.length > 0 && (
            <Section title={text.limitation}>
              <div>
                {displayedLimitations.map((point, index) => (
                  <NumberPoint key={`${point}-${index}`} index={index + 1} text={point} />
                ))}
              </div>
            </Section>
          )}

          {(reproducibilitySignals.length > 0 || displayedImplementationEvidence) && (
            <Section title={text.evidence}>
              <TextCard subtle>
                {displayedImplementationEvidence && (
                  <div style={{ color: "#4b5563", fontSize: 14, lineHeight: 1.8, marginBottom: reproducibilitySignals.length > 0 ? 12 : 0 }}>
                    {displayedImplementationEvidence}
                  </div>
                )}
                {reproducibilitySignals.length > 0 && (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                    {reproducibilitySignals.map((signal) => (
                      <SoftTag key={signal} text={signal} tone="evidence" />
                    ))}
                  </div>
                )}
              </TextCard>
            </Section>
          )}

          <Section title={text.resources}>
            <TextCard subtle>
              <div style={{ marginBottom: 18 }}>
                <div style={{ fontSize: 16, fontWeight: 800, marginBottom: 6, color: "#111827" }}>{text.github}</div>
                <div style={{ color: "#374151", lineHeight: 1.8, fontSize: 14 }}>
                  {realGithubUrl ? (
                    <a href={realGithubUrl} target="_blank" rel="noreferrer">
                      {realGithubUrl}
                    </a>
                  ) : (
                    (uiLanguage === "zh" ? "暂无" : "Unavailable")
                  )}
                </div>
              </div>

              <div style={{ marginBottom: 18 }}>
                <div style={{ fontSize: 16, fontWeight: 800, marginBottom: 6, color: "#111827" }}>{text.dataset}</div>
                <div style={{ color: "#374151", lineHeight: 1.8, fontSize: 14 }}>
                  {datasetLinks.length > 0 ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                      {datasetLinks.map((link, index) => (
                        <a key={`${link}-${index}`} href={link} target="_blank" rel="noreferrer">
                          {link}
                        </a>
                      ))}
                    </div>
                  ) : (
                    (uiLanguage === "zh" ? "原文或站点暂未引出更明确的数据集来源链接。" : "The paper or landing page does not provide a clearer dataset source link yet.")
                  )}
                </div>
              </div>

              <div>
                <div style={{ fontSize: 16, fontWeight: 800, marginBottom: 6, color: "#111827" }}>{text.pdf}</div>
                <div style={{ color: "#374151", lineHeight: 1.8, fontSize: 14 }}>
                  {item.pdf_url ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                      <a href={item.pdf_url} target="_blank" rel="noreferrer">
                        {item.pdf_url}
                      </a>
                      <a
                        href={pdfDownloadUrl}
                        style={{
                          display: "inline-flex",
                          width: "fit-content",
                          alignItems: "center",
                          justifyContent: "center",
                          padding: "8px 12px",
                          borderRadius: 10,
                          background: "#eff6ff",
                          color: "#1d4ed8",
                          textDecoration: "none",
                          fontWeight: 700,
                        }}
                      >
                        {text.downloadPdf}
                      </a>
                    </div>
                  ) : paperLink ? (
                    <a href={paperLink} target="_blank" rel="noreferrer">
                      {paperLink}
                    </a>
                  ) : (
                    (uiLanguage === "zh" ? "暂无" : "Unavailable")
                  )}
                </div>
              </div>
            </TextCard>
          </Section>

          {error && (
            <div
              style={{
                marginTop: 8,
                marginBottom: 20,
                color: "#92400e",
                background: "#fffbeb",
                border: "1px solid #fde68a",
                borderRadius: 12,
                padding: 12,
                fontSize: 13,
                lineHeight: 1.8,
              }}
            >
              {error}
            </div>
          )}

          <a
            href={paperLink || "#"}
            target="_blank"
            rel="noreferrer"
            style={{
              display: "block",
              width: "100%",
              textAlign: "center",
              padding: "15px 16px",
              borderRadius: 14,
              background: paperLink ? "#0f172a" : "#9ca3af",
              color: "#fff",
              textDecoration: "none",
              fontWeight: 800,
              fontSize: 15,
              letterSpacing: "0.01em",
              pointerEvents: paperLink ? "auto" : "none",
              boxShadow: paperLink ? "0 8px 20px rgba(15, 23, 42, 0.18)" : "none",
            }}
          >
            {text.viewPaper}
          </a>
        </div>
      )}
    </main>
  );
}
