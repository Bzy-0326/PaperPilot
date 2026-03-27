"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

type CompareItem = {
  paper_id: number;
  title?: string;
  one_sentence_summary?: string;
  recommendation_zh?: string;
  topic_fit_zh?: string;
  novelty_level_zh?: string;
  reproducibility_level_zh?: string;
  onboarding_difficulty?: string;
  compare_reason?: string;
  best_for?: string[];
  tags?: string[];
  study_goal?: string;
  content_summary?: string;
  method_summary?: string;
  innovations?: string[];
  limitations?: string[];
};
const COMPARE_IDS_KEY = "paper_reader_compare_ids_v1";

const TEXT = {
  zh: {
    back: "返回首页",
    badge: "论文对照",
    title: "同主题论文决策对比",
    subtitle: "围绕当前主题，从阅读价值、复现可行性、创新性和适用场景，快速判断哪篇论文更值得你优先投入。",
    loading: "正在加载对照结果...",
    error: "论文对照加载失败，请稍后重试。",
    needSelect: "请先从首页选择至少 2 篇论文再进入对照页。",
    suggestion: "建议结论",
    candidates: "候选结论",
    contentDiff: "内容差异",
    insightDiff: "创新点与注意点",
    noResult: "暂无结果",
    currentFirst: "当前优先",
    candidate: "候选",
    takeaway: "一句话判断",
    bestFor: "更适合做什么",
    studyGoal: "研究目标",
    summary: "内容摘要",
    method: "方法路径",
    innovation: "核心创新点",
    limitation: "局限与注意点",
    noInfo: "暂无足够信息。",
    deepRead: "优先精读",
    reproduce: "优先复现",
    inspiration: "优先找灵感",
    relatedWork: "优先补相关工作",
  },
  en: {
    back: "Back Home",
    badge: "Compare",
    title: "Same-Topic Paper Comparison",
    subtitle: "Compare papers under the same topic and quickly decide which one deserves your time first.",
    loading: "Loading comparison results...",
    error: "Failed to load comparison results. Please try again later.",
    needSelect: "Please select at least 2 papers on the homepage before opening comparison.",
    suggestion: "Decision Summary",
    candidates: "Candidate Summary",
    contentDiff: "Content Differences",
    insightDiff: "Innovation and Trade-offs",
    noResult: "No result yet.",
    currentFirst: "Top Priority",
    candidate: "Candidate",
    takeaway: "Takeaway",
    bestFor: "Best Use",
    studyGoal: "Research Goal",
    summary: "Summary",
    method: "Method",
    innovation: "Key Innovations",
    limitation: "Limitations",
    noInfo: "Not enough information yet.",
    deepRead: "Read First",
    reproduce: "Reproduce First",
    inspiration: "Inspiration First",
    relatedWork: "Background First",
  },
} as const;

function getApiBaseUrl() {
  if (typeof window !== "undefined") {
    return `${window.location.protocol}//${window.location.hostname}:8000`;
  }
  return "http://127.0.0.1:8000";
}

function normalizeList(value?: string[]) {
  return Array.isArray(value) ? value.filter(Boolean) : [];
}

function cleanText(value?: string) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function pickTopPoints(list?: string[], limit = 3) {
  return normalizeList(list).slice(0, limit);
}

function levelScore(text?: string) {
  const value = text || "";
  if (value.includes("高") || value.includes("较易")) return 3;
  if (value.includes("中") || value.includes("一定")) return 2;
  if (value) return 1;
  return 0;
}

function recommendationScore(text?: string) {
  const value = text || "";
  if (value.includes("优先") || value.includes("推荐")) return 3;
  if (value.includes("速读") || value.includes("关注")) return 2;
  if (value) return 1;
  return 0;
}

function bestForScore(item: CompareItem, keyword: string) {
  return normalizeList(item.best_for).some((entry) => entry.includes(keyword)) ? 2 : 0;
}

function innovationCount(item: CompareItem) {
  return normalizeList(item.innovations).length;
}

function limitationCount(item: CompareItem) {
  return normalizeList(item.limitations).length;
}

function getDecisionScores(item: CompareItem) {
  const topic = levelScore(item.topic_fit_zh);
  const novelty = levelScore(item.novelty_level_zh);
  const reproduce = levelScore(item.reproducibility_level_zh);
  const recommend = recommendationScore(item.recommendation_zh);
  const innovation = innovationCount(item);
  const limitation = limitationCount(item);

  return {
    deepRead: topic * 4 + recommend * 3 + novelty * 2 + innovation,
    reproduce: reproduce * 5 + bestForScore(item, "复现") * 3 + topic * 2 - limitation,
    inspiration: novelty * 5 + bestForScore(item, "选题") * 3 + recommend * 2 + innovation,
    relatedWork: topic * 5 + bestForScore(item, "相关工作") * 3 + recommend * 2,
    overall: topic * 4 + recommend * 4 + novelty * 3 + reproduce * 3 + innovation - limitation,
  };
}

function pickWinnerIndex(items: CompareItem[], key: keyof ReturnType<typeof getDecisionScores>) {
  if (items.length === 0) return -1;
  const compared = items.map((item, index) => {
    const scores = getDecisionScores(item);
    return {
      index,
      primary: scores[key],
      tieBreakers: [
        scores.overall,
        scores.deepRead,
        scores.reproduce,
        scores.inspiration,
        scores.relatedWork,
        recommendationScore(item.recommendation_zh),
        levelScore(item.topic_fit_zh),
        levelScore(item.novelty_level_zh),
        levelScore(item.reproducibility_level_zh),
        innovationCount(item),
        -limitationCount(item),
        -index,
      ],
    };
  });

  compared.sort((a, b) => {
    if (b.primary !== a.primary) return b.primary - a.primary;
    for (let i = 0; i < a.tieBreakers.length; i += 1) {
      if (b.tieBreakers[i] !== a.tieBreakers[i]) return b.tieBreakers[i] - a.tieBreakers[i];
    }
    return 0;
  });

  return compared[0]?.index ?? -1;
}

function buildOutcomeReason(item: CompareItem, key: "deepRead" | "reproduce" | "inspiration" | "relatedWork") {
  if (key === "deepRead") {
    return item.topic_fit_zh || item.recommendation_zh || "阅读价值更突出";
  }
  if (key === "reproduce") {
    return item.reproducibility_level_zh || item.onboarding_difficulty || "复现路径更清晰";
  }
  if (key === "inspiration") {
    return item.novelty_level_zh || "创新点更适合提供启发";
  }
  return item.topic_fit_zh || "更适合补当前主题背景";
}

function decisionLabel(key: "deepRead" | "reproduce" | "inspiration" | "relatedWork") {
  if (key === "deepRead") return "优先精读";
  if (key === "reproduce") return "优先复现";
  if (key === "inspiration") return "优先找灵感";
  return "优先补相关工作";
}

function decisionLabelByLanguage(key: "deepRead" | "reproduce" | "inspiration" | "relatedWork", language: UILanguage) {
  if (language === "zh") return decisionLabel(key);
  if (key === "deepRead") return "Read First";
  if (key === "reproduce") return "Reproduce First";
  if (key === "inspiration") return "Inspiration First";
  return "Background First";
}

function Badge({ text, tone = "default" }: { text: string; tone?: "default" | "win" | "soft" }) {
  const palette = tone === "win"
    ? { bg: "#dcfce7", color: "#166534", border: "#86efac" }
    : tone === "soft"
      ? { bg: "#eff6ff", color: "#1d4ed8", border: "#bfdbfe" }
      : { bg: "#f8fafc", color: "#334155", border: "#e2e8f0" };

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: "6px 10px",
        borderRadius: 999,
        background: palette.bg,
        color: palette.color,
        border: `1px solid ${palette.border}`,
        fontSize: 12,
        fontWeight: 700,
      }}
    >
      {text}
    </span>
  );
}

function Surface({ children, highlighted = false }: { children: React.ReactNode; highlighted?: boolean }) {
  return (
    <div
      style={{
        border: `1px solid ${highlighted ? "#86efac" : "#e5e7eb"}`,
        borderRadius: 20,
        padding: 18,
        background: highlighted ? "#f0fdf4" : "#ffffff",
        boxShadow: highlighted ? "0 10px 26px rgba(22, 101, 52, 0.08)" : "0 6px 18px rgba(15, 23, 42, 0.04)",
      }}
    >
      {children}
    </div>
  );
}

function TextBlock({ title, text }: { title: string; text: string }) {
  return (
    <div style={{ display: "grid", gap: 8 }}>
      <div style={{ fontSize: 13, color: "#64748b", fontWeight: 800 }}>{title}</div>
      <div style={{ fontSize: 15, color: "#111827", lineHeight: 1.85 }}>{text || "暂无足够信息。"}</div>
    </div>
  );
}

function ListBlock({ title, items }: { title: string; items: string[] }) {
  return (
    <div style={{ display: "grid", gap: 10 }}>
      <div style={{ fontSize: 13, color: "#64748b", fontWeight: 800 }}>{title}</div>
      {items.length > 0 ? (
        <div style={{ display: "grid", gap: 8 }}>
          {items.map((item, index) => (
            <div key={`${title}-${index}-${item}`} style={{ fontSize: 15, color: "#111827", lineHeight: 1.8, padding: "10px 12px", borderRadius: 12, background: "#f8fafc", border: "1px solid #e5e7eb" }}>
              {item}
            </div>
          ))}
        </div>
      ) : (
        <div style={{ fontSize: 15, color: "#64748b", lineHeight: 1.8 }}>暂无足够信息。</div>
      )}
    </div>
  );
}

export default function ComparePage() {
  const uiLanguage = "zh" as const;
  const searchParams = useSearchParams();
  const topic = searchParams.get("topic") || "";
  const idsParam = searchParams.get("ids") || "";

  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState<CompareItem[]>([]);
  const [error, setError] = useState("");
  const text = TEXT.zh;

  const selectedIds = useMemo(() => {
    const parsed = idsParam.split(",").map((value) => Number(value.trim())).filter((value) => Number.isFinite(value));
    return parsed.slice(0, 3);
  }, [idsParam]);

  useEffect(() => {
    const cachedIdsRaw = sessionStorage.getItem(COMPARE_IDS_KEY);
    const cachedIds = cachedIdsRaw ? JSON.parse(cachedIdsRaw) : [];
    const paperIds = selectedIds.length >= 2 ? selectedIds : cachedIds;

    const run = async () => {
      if (!paperIds || paperIds.length < 2) {
        setLoading(false);
        setError(text.needSelect);
        return;
      }

      try {
        setLoading(true);
        setError("");
        const res = await fetch(`${getApiBaseUrl()}/papers/compare`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ project_topic: topic, paper_ids: paperIds }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data?.detail || text.error);
        setItems(data.items || []);
      } catch (err) {
        console.error(err);
        setError(text.error);
      } finally {
        setLoading(false);
      }
    };

    void run();
  }, [selectedIds, topic, text.error, text.needSelect]);

  const winners = useMemo(() => {
    if (items.length < 2) return null;
    return {
      overall: pickWinnerIndex(items, "overall"),
      deepRead: pickWinnerIndex(items, "deepRead"),
      reproduce: pickWinnerIndex(items, "reproduce"),
      inspiration: pickWinnerIndex(items, "inspiration"),
      relatedWork: pickWinnerIndex(items, "relatedWork"),
    };
  }, [items]);

  const winnerBadges = useMemo(() => {
    if (!winners) return [] as string[][];
    return items.map((_, index) => {
      const labels = [];
      if (winners.overall === index) labels.push("当前优先");
      if (winners.deepRead === index) labels.push("适合精读");
      if (winners.reproduce === index) labels.push("适合复现");
      if (winners.inspiration === index) labels.push("适合找灵感");
      if (winners.relatedWork === index) labels.push("适合补背景");
      return labels;
    });
  }, [items, winners]);

  return (
    <main style={{ maxWidth: 1340, margin: "0 auto", padding: "28px 20px 56px", minHeight: "100vh", background: "#f8fafc" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, marginBottom: 14 }}>
        <button type="button" onClick={() => { window.location.href = "/"; }} style={{ border: "none", background: "transparent", color: "#4f46e5", cursor: "pointer", padding: 0, fontSize: 14, fontWeight: 700 }}>
          {text.back}
        </button>
      </div>

      <div style={{ border: "1px solid #e5e7eb", borderRadius: 24, padding: 24, background: "#ffffff", boxShadow: "0 16px 40px rgba(15, 23, 42, 0.06)" }}>
        <div style={{ marginBottom: 28 }}>
          <div style={{ display: "inline-flex", padding: "8px 12px", borderRadius: 999, background: "#ecfeff", color: "#155e75", fontSize: 12, fontWeight: 800 }}>{text.badge}</div>
          <h1 style={{ fontSize: 34, lineHeight: 1.15, margin: "14px 0 10px", color: "#111827", fontWeight: 900 }}>{text.title}</h1>
          <p style={{ margin: 0, color: "#475569", lineHeight: 1.8, maxWidth: 920, fontSize: 15 }}>{text.subtitle}</p>
        </div>

        {loading && <div style={{ color: "#475569" }}>{text.loading}</div>}
        {!loading && error && <div style={{ color: "#b91c1c" }}>{error}</div>}

        {!loading && !error && items.length >= 2 && winners && (
          <div style={{ display: "grid", gap: 26 }}>
            <section style={{ display: "grid", gap: 14 }}>
              <div style={{ fontSize: 20, fontWeight: 900, color: "#111827" }}>{text.suggestion}</div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 14 }}>
                {(["deepRead", "reproduce", "inspiration", "relatedWork"] as const).map((key) => {
                  const winnerIndex = winners[key];
                  const winner = items[winnerIndex];
                  return (
                    <Surface key={key} highlighted>
                      <div style={{ display: "grid", gap: 10 }}>
                        <div style={{ fontSize: 14, fontWeight: 800, color: "#111827" }}>{decisionLabelByLanguage(key, uiLanguage)}</div>
                        <div style={{ color: "#0f172a", fontSize: 16, lineHeight: 1.6, fontWeight: 800 }}>
                          {winner?.title || text.noResult}
                        </div>
                        <div style={{ color: "#475569", fontSize: 14, lineHeight: 1.75 }}>
                          {buildOutcomeReason(winner, key)}
                        </div>
                      </div>
                    </Surface>
                  );
                })}
              </div>
            </section>

            <section style={{ display: "grid", gap: 14 }}>
              <div style={{ fontSize: 20, fontWeight: 900, color: "#111827" }}>{text.candidates}</div>
              <div style={{ display: "grid", gridTemplateColumns: `repeat(${items.length}, minmax(0, 1fr))`, gap: 16 }}>
                {items.map((item, index) => {
                  const badges = winnerBadges[index];
                  return (
                    <Surface key={item.paper_id} highlighted={winners.overall === index}>
                      <div style={{ display: "grid", gap: 14 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "flex-start" }}>
                          <div>
                            <div style={{ fontSize: 12, fontWeight: 800, color: "#2563eb", marginBottom: 8 }}>{text.candidate} {index + 1}</div>
                            <div style={{ fontSize: 24, fontWeight: 900, lineHeight: 1.32, color: "#111827" }}>{item.title || text.noResult}</div>
                          </div>
                          {winners.overall === index && <Badge text={text.currentFirst} tone="win" />}
                        </div>

                        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                          {badges.map((label) => <Badge key={label} text={label} tone="win" />)}
                          <Badge text={item.recommendation_zh || "推荐性待补充"} />
                          <Badge text={item.topic_fit_zh || "主题贴合待补充"} />
                          <Badge text={item.novelty_level_zh || "创新性待补充"} />
                          <Badge text={item.onboarding_difficulty || item.reproducibility_level_zh || "上手难度待补充"} />
                        </div>

                        <TextBlock title={text.takeaway} text={cleanText(item.one_sentence_summary) || text.noResult} />
                        <TextBlock title={text.bestFor} text={normalizeList(item.best_for).join(" / ") || (uiLanguage === "zh" ? "快速浏览" : "Quick scan")} />
                      </div>
                    </Surface>
                  );
                })}
              </div>
            </section>

            <section style={{ display: "grid", gap: 14 }}>
              <div style={{ fontSize: 20, fontWeight: 900, color: "#111827" }}>{text.contentDiff}</div>
              <div style={{ display: "grid", gridTemplateColumns: `repeat(${items.length}, minmax(0, 1fr))`, gap: 16 }}>
                {items.map((item) => (
                  <Surface key={`content-${item.paper_id}`}>
                    <div style={{ display: "grid", gap: 18 }}>
                      <TextBlock title={text.studyGoal} text={cleanText(item.study_goal) || cleanText(item.compare_reason) || text.noInfo} />
                      <TextBlock title={text.summary} text={cleanText(item.content_summary) || cleanText(item.one_sentence_summary) || text.noInfo} />
                      <TextBlock title={text.method} text={cleanText(item.method_summary) || text.noInfo} />
                    </div>
                  </Surface>
                ))}
              </div>
            </section>

            <section style={{ display: "grid", gap: 14 }}>
              <div style={{ fontSize: 20, fontWeight: 900, color: "#111827" }}>{text.insightDiff}</div>
              <div style={{ display: "grid", gridTemplateColumns: `repeat(${items.length}, minmax(0, 1fr))`, gap: 16 }}>
                {items.map((item) => (
                  <Surface key={`insight-${item.paper_id}`}>
                    <div style={{ display: "grid", gap: 16 }}>
                      <ListBlock title={text.innovation} items={pickTopPoints(item.innovations, 3)} />
                      <ListBlock title={text.limitation} items={pickTopPoints(item.limitations, 3)} />
                    </div>
                  </Surface>
                ))}
              </div>
            </section>
          </div>
        )}
      </div>
    </main>
  );
}
