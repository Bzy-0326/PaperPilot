"use client";

import { useEffect, useMemo, useState } from "react";

type RecommendationItem = {
  paper_id: number;
  title: string;
  paper_url?: string;
  pdf_url?: string;
  one_sentence_summary?: string;
  recommendation_zh?: string;
  score?: number;
  recommendation_score?: number;
  relative_rank?: number;
  priority_bucket?: "top_pick" | "strong_pick" | "watch_list";
  priority_label?: string;
  tags?: string[];
  topic_fit_zh?: string;
  novelty_level_zh?: string;
  reproducibility_level_zh?: string;
  evidence_signals?: string[];
};

type FollowUpBucket = "reading" | "reproduce" | "topic";

type FollowUpItem = {
  id?: number;
  paper_id: number;
  title: string;
  one_sentence_summary?: string;
  tags?: string[];
  topic?: string;
  added_at: string;
  updated_at?: string;
  bucket: FollowUpBucket;
};

type LLMProvider = "demo" | "ollama" | "deepseek" | "kimi" | "qwen" | "openai_compatible";

type LLMConfig = {
  provider: LLMProvider;
  model: string;
  base_url: string;
  api_key: string;
};

type LLMStatus = {
  provider?: string;
  model?: string;
};

type ModelPreset = {
  id: string;
  label: string;
  provider: LLMProvider;
  model: string;
  base_url: string;
};

type ResearchMode = "default" | "deep_read" | "reproduce" | "inspiration" | "related_work";

const STORAGE_KEY = "paper_reader_home_state_v8";
const MODEL_SETTINGS_KEY = "paper_reader_model_settings_v1";
const COMPARE_IDS_KEY = "paper_reader_compare_ids_v1";
const RESEARCH_MODE_KEY = "paper_reader_mode_v1";
const DEFAULT_LLM_CONFIG: LLMConfig = {
  provider: "demo",
  model: "paperpilot-demo",
  base_url: "demo://built-in",
  api_key: "",
};

const MODEL_PRESETS: ModelPreset[] = [
  { id: "paperpilot-demo", label: "PaperPilot Demo / no setup", provider: "demo", model: "paperpilot-demo", base_url: "demo://built-in" },
  { id: "ollama-qwen25-7b", label: "Ollama / qwen2.5:7b", provider: "ollama", model: "qwen2.5:7b", base_url: "http://localhost:11434" },
  { id: "ollama-qwen3-4b", label: "Ollama / qwen3:4b", provider: "ollama", model: "qwen3:4b", base_url: "http://localhost:11434" },
  { id: "deepseek-chat", label: "DeepSeek / deepseek-chat", provider: "deepseek", model: "deepseek-chat", base_url: "https://api.deepseek.com/v1" },
  { id: "kimi-8k", label: "Kimi / moonshot-v1-8k", provider: "kimi", model: "moonshot-v1-8k", base_url: "https://api.moonshot.cn/v1" },
  { id: "qwen-plus", label: "Qwen / qwen-plus", provider: "qwen", model: "qwen-plus", base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1" },
  { id: "custom-openai", label: "自定义 OpenAI 兼容接口", provider: "openai_compatible", model: "", base_url: "" },
];

const RESEARCH_MODES: Array<{ id: ResearchMode; label: string; description: string }> = [
  { id: "default", label: "综合推荐", description: "按整体阅读价值排序，适合先快速看今天最值得投入的论文。" },
  { id: "deep_read", label: "最值得精读", description: "优先突出更值得投入阅读时间、适合深挖方法与结论的论文。" },
  { id: "reproduce", label: "最适合复现", description: "优先突出复现路径更清晰、上手阻力更低的候选。" },
  { id: "inspiration", label: "最适合选题启发", description: "优先突出更有新意、适合拿来找方向和想法的论文。" },
  { id: "related_work", label: "最适合补相关工作", description: "优先突出与当前主题贴合度更高、适合快速补背景的论文。" },
];

const FOLLOW_UP_BUCKETS: Array<{ id: FollowUpBucket; label: string; description: string }> = [
  { id: "reading", label: "待读清单", description: "准备投入时间精读的论文。" },
  { id: "reproduce", label: "复现清单", description: "打算动手实现、验证和复现的论文。" },
  { id: "topic", label: "选题备选", description: "适合继续观察和沉淀成方向的论文。" },
];

const HOME_TEXT = {
  zh: {
    title: "每日论文推荐",
    subtitle: "输入你的研究主题，快速拿到更值得先看的论文结果。",
    toolbox: "研究工具箱",
    settings: "模型设置",
    currentMode: "当前模式",
    localMode: "本地 Ollama",
    onlineMode: "在线 API",
    model: "模型",
    defaultModel: "默认",
    dailyRecommend: "每日推荐",
    generating: "生成中...",
    summary: "一句话总结",
    viewDetail: "查看详情",
    addCompare: "加入对比",
    removeCompare: "移出对比",
    addFollowUp: "加入跟进",
    currentView: "当前浏览",
    waitingCompare: "已加入 {count} 篇待对比",
    emptyMiniHint: "可在研究工具箱里切换浏览目标、发起论文对照或管理跟进清单",
    modeLabel: "当前浏览",
    queueLabel: "对照队列",
    followUpTitle: "我的跟进",
    papersSaved: "篇论文已加入清单",
    browseGoal: "浏览目标",
    browseGoalHint: "换一个视角看同一批论文，排序会自动跟着切换。",
    compareTitle: "论文对照",
    compareHint: "已选择 {count} 篇论文，最多 3 篇。发起后会直接给出更适合优先精读、复现或补背景的候选建议。",
    startCompare: "开始对照",
    close: "关闭",
    modelPreset: "模型预设",
    provider: "模型来源",
    modelName: "模型名称",
    baseUrl: "服务地址",
    apiKey: "API Key",
    settingsHint: "先确定分析模型，保存后返回首页继续使用。系统会记住你最近一次的模型配置。",
    settingsTipLocal: "如果你用本地模型，请确认已经安装 Ollama，并拉取了对应模型。",
    settingsTipApi: "如果你用在线模型，推荐优先选择预设，减少模型名称、服务地址和 API Key 的填写错误。",
    reading: "待读清单",
    reproduce: "复现清单",
    topic: "选题备选",
    open: "打开",
    remove: "移除",
    noFollowUp: "还没有加入内容，可以在推荐卡片里点击“加入跟进”。",
    added: "已加入",
    add: "添加",
    recommendationScore: "推荐分",
    waitingSummary: "输入你的研究主题，开始生成今日推荐。",
    inputPlaceholder: "LLM / RAG / Multimodal / Reasoning",
    countPlaceholder: "未设置",
    joinSuccess: "已加入{label}。",
    removeSuccess: "已从{label}移除。",
    joinFailed: "加入跟进失败，请稍后重试。",
    removeFailed: "移除跟进失败，请稍后重试。",
    searchFailed: "推荐生成失败，请检查模型配置、API Key 或后端服务状态。",
    analyzing: "正在分析论文并生成每日推荐，请稍等...",
    needTopic: "请先输入研究主题。",
    needSettings: "请先完成模型配置。",
    needApiKey: "在线模型需要填写 API Key。",
    compareNeedTwo: "至少选择 2 篇论文后才能开始对照。",
    modelConfigRemember: "系统会记住你最近一次的模型配置。",
  },
  en: {
    title: "Daily Paper Picks",
    subtitle: "Enter your research topic to get a cleaner, ranked list of papers worth reading first.",
    toolbox: "Research Toolbox",
    settings: "Model Settings",
    currentMode: "Mode",
    localMode: "Local Ollama",
    onlineMode: "Online API",
    model: "Model",
    defaultModel: "Default",
    dailyRecommend: "Recommend",
    generating: "Generating...",
    summary: "Takeaway",
    viewDetail: "View Details",
    addCompare: "Add to Compare",
    removeCompare: "Remove from Compare",
    addFollowUp: "Save",
    currentView: "Current View",
    waitingCompare: "{count} paper(s) queued for comparison",
    emptyMiniHint: "Use the toolbox to switch reading goals, compare candidates, or manage follow-up lists.",
    modeLabel: "Current View",
    queueLabel: "Compare Queue",
    followUpTitle: "My Follow-Ups",
    papersSaved: "paper(s) saved",
    browseGoal: "Reading Goal",
    browseGoalHint: "Switch the perspective and the ranking will update automatically.",
    compareTitle: "Paper Comparison",
    compareHint: "{count} paper(s) selected, up to 3. Start comparison to see which one is better for deep reading, reproduction, or background reading.",
    startCompare: "Start Compare",
    close: "Close",
    modelPreset: "Preset",
    provider: "Provider",
    modelName: "Model Name",
    baseUrl: "Base URL",
    apiKey: "API Key",
    settingsHint: "Choose your analysis model first. The app will remember your latest configuration.",
    settingsTipLocal: "If you use a local model, make sure Ollama is installed and the model has been pulled.",
    settingsTipApi: "If you use an online model, presets are recommended to reduce mistakes in model name, base URL, and API key.",
    reading: "Reading List",
    reproduce: "Reproduction List",
    topic: "Topic Candidates",
    open: "Open",
    remove: "Remove",
    noFollowUp: "Nothing saved yet. Use “Save” on a recommendation card to add papers here.",
    added: "Added",
    add: "Add",
    recommendationScore: "Score",
    waitingSummary: "Enter your research topic to generate today's recommendations.",
    inputPlaceholder: "LLM / RAG / Multimodal / Reasoning",
    countPlaceholder: "Not set",
    joinSuccess: "Added to {label}.",
    removeSuccess: "Removed from {label}.",
    joinFailed: "Failed to save follow-up. Please try again.",
    removeFailed: "Failed to remove follow-up. Please try again.",
    searchFailed: "Failed to generate recommendations. Please check model settings, API key, or backend status.",
    analyzing: "Analyzing papers and generating daily recommendations...",
    needTopic: "Please enter a research topic first.",
    needSettings: "Please complete model settings first.",
    needApiKey: "An API key is required for online models.",
    compareNeedTwo: "Select at least 2 papers before starting comparison.",
    modelConfigRemember: "Your latest model configuration will be remembered.",
  },
} as const;

function getApiBaseUrl() {
  if (typeof window !== "undefined") {
    return `${window.location.protocol}//${window.location.hostname}:8000`;
  }
  return "http://127.0.0.1:8000";
}

function getPriorityLabel(rank: number, language: UILanguage) {
  if (language === "en") {
    if (rank === 1) return "Top Pick";
    if (rank <= 3) return "Read Soon";
    return "Worth Watching";
  }
  if (rank === 1) return "优先推荐";
  if (rank <= 3) return "建议速读";
  return "建议关注";
}

function getPriorityTone(bucket?: RecommendationItem["priority_bucket"], rank?: number) {
  if (bucket === "top_pick" || rank === 1) {
    return { badgeBg: "#fff7ed", badgeColor: "#9a3412", badgeBorder: "#fed7aa", cardBorder: "#111827", cardBg: "#fffdfa" };
  }
  if (bucket === "strong_pick" || (rank && rank <= 3)) {
    return { badgeBg: "#eff6ff", badgeColor: "#1d4ed8", badgeBorder: "#bfdbfe", cardBorder: "#dbeafe", cardBg: "#ffffff" };
  }
  return { badgeBg: "#f3f4f6", badgeColor: "#374151", badgeBorder: "#e5e7eb", cardBorder: "#e5e7eb", cardBg: "#ffffff" };
}

function translateAssessmentValue(value: string | undefined, language: UILanguage) {
  const text = String(value || "").trim();
  if (!text || language === "zh") return text;
  const pairs: Array<[string, string]> = [
    ["优先精读", "Read First"],
    ["推荐精读", "Recommended for Deep Read"],
    ["优先推荐", "Top Pick"],
    ["建议速读", "Read Soon"],
    ["建议关注", "Worth Watching"],
    ["高度相关", "Highly Relevant"],
    ["高相关", "Highly Relevant"],
    ["中度相关", "Moderately Relevant"],
    ["较高创新", "High Novelty"],
    ["高创新", "High Novelty"],
    ["中等创新", "Moderate Novelty"],
    ["较易复现", "Easy to Reproduce"],
    ["可复现性中等", "Moderate Reproducibility"],
    ["中等", "Moderate"],
    ["较难复现", "Hard to Reproduce"],
    ["暂无", "Unavailable"],
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

function modeHint(mode: ResearchMode, item: RecommendationItem, language: UILanguage) {
  if (mode === "deep_read") {
    return item.topic_fit_zh
      ? language === "zh"
        ? `精读价值：${item.topic_fit_zh}`
        : `Deep-read fit: ${translateAssessmentValue(item.topic_fit_zh, "en")}`
      : language === "zh"
        ? "精读价值较高，适合投入更多时间。"
        : "Worth deeper reading and more focused attention.";
  }
  if (mode === "reproduce") {
    return item.reproducibility_level_zh
      ? language === "zh"
        ? `复现判断：${item.reproducibility_level_zh}`
        : `Reproduction fit: ${translateAssessmentValue(item.reproducibility_level_zh, "en")}`
      : language === "zh"
        ? "复现信息仍可继续补充。"
        : "Reproduction evidence can still be improved.";
  }
  if (mode === "inspiration") {
    return item.novelty_level_zh
      ? language === "zh"
        ? `启发判断：${item.novelty_level_zh}`
        : `Inspiration signal: ${translateAssessmentValue(item.novelty_level_zh, "en")}`
      : language === "zh"
        ? "适合用来快速找方向。"
        : "Useful for quickly finding new directions.";
  }
  if (mode === "related_work") {
    return item.topic_fit_zh
      ? language === "zh"
        ? `相关工作价值：${item.topic_fit_zh}`
        : `Background value: ${translateAssessmentValue(item.topic_fit_zh, "en")}`
      : language === "zh"
        ? "适合拿来补当前主题的背景。"
        : "Useful for filling in the background around this topic.";
  }
  return item.one_sentence_summary || (language === "zh" ? "适合先快速浏览。" : "A good candidate for a quick first pass.");
}

function scoreByLevel(value?: string, highWords: string[] = ["高", "较易"]) {
  const text = value || "";
  if (highWords.some((word) => text.includes(word))) return 3;
  if (text.includes("中") || text.includes("一定")) return 2;
  if (text) return 1;
  return 0;
}

function scoreRecommendation(value?: string) {
  const text = value || "";
  if (text.includes("优先") || text.includes("推荐")) return 3;
  if (text.includes("速读") || text.includes("关注")) return 2;
  if (text) return 1;
  return 0;
}

function scoreEvidence(item: RecommendationItem) {
  return Array.isArray(item.evidence_signals) ? item.evidence_signals.length : 0;
}

function getSortScore(item: RecommendationItem, mode: ResearchMode, index: number) {
  const base = typeof item.recommendation_score === "number" ? item.recommendation_score : 90 - index * 3;
  const topicFit = scoreByLevel(item.topic_fit_zh, ["高"]);
  const novelty = scoreByLevel(item.novelty_level_zh, ["高"]);
  const reproducibility = scoreByLevel(item.reproducibility_level_zh, ["较易", "高"]);
  const recommendation = scoreRecommendation(item.recommendation_zh);
  const evidence = scoreEvidence(item);

  if (mode === "deep_read") return base + topicFit * 12 + recommendation * 10 + novelty * 4;
  if (mode === "reproduce") return base + reproducibility * 14 + evidence * 5 + topicFit * 6;
  if (mode === "inspiration") return base + novelty * 15 + recommendation * 7 + topicFit * 4;
  if (mode === "related_work") return base + topicFit * 15 + recommendation * 6 + reproducibility * 2;
  return base;
}

function formatBucketLabel(bucket: FollowUpBucket) {
  return FOLLOW_UP_BUCKETS.find((item) => item.id === bucket)?.label || "我的跟进";
}

function translateBucketLabel(bucket: FollowUpBucket, language: UILanguage) {
  if (language === "en") {
    if (bucket === "reading") return "Reading List";
    if (bucket === "reproduce") return "Reproduction List";
    return "Topic Candidates";
  }
  return formatBucketLabel(bucket);
}

function translateModeLabel(mode: ResearchMode, language: UILanguage) {
  if (language === "zh") {
    return RESEARCH_MODES.find((item) => item.id === mode)?.label || "综合推荐";
  }
  const labels: Record<ResearchMode, string> = {
    default: "Overall",
    deep_read: "Deep Read",
    reproduce: "Reproduce",
    inspiration: "Inspiration",
    related_work: "Related Work",
  };
  return labels[mode];
}

function translateModeDescription(mode: ResearchMode, language: UILanguage) {
  if (language === "zh") {
    return RESEARCH_MODES.find((item) => item.id === mode)?.description || "";
  }
  const descriptions: Record<ResearchMode, string> = {
    default: "Rank by overall reading value so you can quickly see today's strongest candidates.",
    deep_read: "Prioritize papers worth investing real reading time in.",
    reproduce: "Prioritize papers with clearer reproduction paths and lower implementation friction.",
    inspiration: "Prioritize papers that are more likely to spark ideas or new directions.",
    related_work: "Prioritize papers that help you fill in the background around your current topic.",
  };
  return descriptions[mode];
}

function translateProviderLabel(provider: LLMProvider, language: UILanguage) {
  if (language === "zh") {
    if (provider === "demo") return "内置 Demo";
    if (provider === "ollama") return "本地 Ollama";
    if (provider === "openai_compatible") return "OpenAI 兼容接口";
    return `${provider.charAt(0).toUpperCase()}${provider.slice(1)} API`;
  }
  if (provider === "demo") return "Built-in Demo";
  if (provider === "ollama") return "Local Ollama";
  if (provider === "openai_compatible") return "OpenAI-compatible API";
  if (provider === "deepseek") return "DeepSeek API";
  if (provider === "kimi") return "Kimi API";
  if (provider === "qwen") return "Qwen API";
  return provider;
}

export default function HomePage() {
  const [projectTopic, setProjectTopic] = useState("");
  const [limit, setLimit] = useState(5);
  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState<RecommendationItem[]>([]);
  const [message, setMessage] = useState("输入你的研究主题，开始生成今日推荐。");
  const [hasSearched, setHasSearched] = useState(false);
  const [hydrated, setHydrated] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showFeatureDrawer, setShowFeatureDrawer] = useState(false);
  const [llmConfig, setLlmConfig] = useState<LLMConfig>(DEFAULT_LLM_CONFIG);
  const [backendLLM, setBackendLLM] = useState<LLMStatus | null>(null);
  const [selectedPresetId, setSelectedPresetId] = useState("paperpilot-demo");
  const [selectedCompareIds, setSelectedCompareIds] = useState<number[]>([]);
  const [researchMode, setResearchMode] = useState<ResearchMode>("default");
  const [followUpItems, setFollowUpItems] = useState<FollowUpItem[]>([]);
  const [activeFollowUpMenuId, setActiveFollowUpMenuId] = useState<number | null>(null);
  const uiLanguage = "zh" as const;
  const text = HOME_TEXT.zh;
  useEffect(() => {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      if (raw) {
        const saved = JSON.parse(raw);
        setProjectTopic(saved.projectTopic || "");
        setLimit(saved.limit || 5);
        setItems(saved.items || []);
        setMessage(saved.message || "输入你的研究主题，开始生成今日推荐。");
        setHasSearched(Boolean(saved.hasSearched));
      }

      const rawCompareIds = sessionStorage.getItem(COMPARE_IDS_KEY);
      if (rawCompareIds) {
        const parsed = JSON.parse(rawCompareIds);
        if (Array.isArray(parsed)) setSelectedCompareIds(parsed.filter((value) => typeof value === "number").slice(0, 3));
      }

      const savedMode = sessionStorage.getItem(RESEARCH_MODE_KEY) as ResearchMode | null;
      if (savedMode && RESEARCH_MODES.some((mode) => mode.id === savedMode)) setResearchMode(savedMode);

      const rawModelSettings = localStorage.getItem(MODEL_SETTINGS_KEY);
      if (rawModelSettings) {
        const savedModelSettings = JSON.parse(rawModelSettings);
        const merged = { ...DEFAULT_LLM_CONFIG, ...(savedModelSettings || {}), api_key: "" };
        setLlmConfig(merged);
        const matchedPreset = MODEL_PRESETS.find((preset) => preset.provider === merged.provider && preset.model === merged.model && preset.base_url === merged.base_url);
        setSelectedPresetId(matchedPreset?.id || "custom-openai");
      }

    } catch (error) {
      console.error("读取首页状态失败", error);
    } finally {
      setHydrated(true);
    }
  }, []);

  useEffect(() => {
    fetch(`${getApiBaseUrl()}/llm/status`)
      .then((res) => res.json())
      .then((data) => setBackendLLM(data.llm || null))
      .catch((error) => console.error("读取模型状态失败", error));
  }, []);

  useEffect(() => {
    fetch(`${getApiBaseUrl()}/follow-ups`)
      .then((res) => res.json())
      .then((data) => setFollowUpItems(Array.isArray(data.items) ? data.items : []))
      .catch((error) => console.error("读取跟进清单失败", error));
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ projectTopic, limit, items, message, hasSearched }));
      sessionStorage.setItem(COMPARE_IDS_KEY, JSON.stringify(selectedCompareIds));
      sessionStorage.setItem(RESEARCH_MODE_KEY, researchMode);
      localStorage.setItem(MODEL_SETTINGS_KEY, JSON.stringify({ provider: llmConfig.provider, model: llmConfig.model, base_url: llmConfig.base_url }));
    } catch (error) {
      console.error("保存首页状态失败", error);
    }
  }, [projectTopic, limit, items, message, hasSearched, llmConfig, hydrated, selectedCompareIds, researchMode]);

  const llmPayload = useMemo(() => {
    const payload: Partial<LLMConfig> = { provider: llmConfig.provider, model: llmConfig.model.trim(), base_url: llmConfig.base_url.trim() };
    if (llmConfig.api_key.trim()) payload.api_key = llmConfig.api_key.trim();
    return payload;
  }, [llmConfig]);

  const displayedItems = useMemo(() => {
    return [...items].sort((a, b) => getSortScore(b, researchMode, b.relative_rank || 99) - getSortScore(a, researchMode, a.relative_rank || 99));
  }, [items, researchMode]);

  const activeMode = RESEARCH_MODES.find((mode) => mode.id === researchMode) || RESEARCH_MODES[0];

  const followUpGroups = useMemo(() => {
    return FOLLOW_UP_BUCKETS.map((bucket) => ({ ...bucket, items: followUpItems.filter((item) => item.bucket === bucket.id) }));
  }, [followUpItems]);

  const runDailyRecommendation = async () => {
    if (!projectTopic.trim()) return setMessage(text.needTopic);
    if (llmConfig.provider !== "demo" && (!llmConfig.model.trim() || !llmConfig.base_url.trim())) {
      setMessage(text.needSettings);
      return setShowSettings(true);
    }
    if (!["demo", "ollama"].includes(llmConfig.provider) && !llmConfig.api_key.trim()) {
      setMessage(text.needApiKey);
      return setShowSettings(true);
    }

    let timeoutId: number | undefined;
    try {
      setLoading(true);
      setHasSearched(true);
      setSelectedCompareIds([]);
      setMessage(text.analyzing);
      const controller = new AbortController();
      timeoutId = window.setTimeout(() => controller.abort(), 35000);

      const res = await fetch(`${getApiBaseUrl()}/papers/daily/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project_topic: projectTopic, limit, llm_config: llmPayload }),
        signal: controller.signal,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || data?.error_message || "推荐生成失败");
      setItems(data.items || []);
      setMessage(data.message || text.waitingSummary);
    } catch (error) {
      console.error(error);
      if (error instanceof DOMException && error.name === "AbortError") {
        setMessage("本次生成耗时过长，已停止等待。你可以稍后再试，或先检查模型与后端状态。");
      } else {
        setMessage(text.searchFailed);
      }
    } finally {
      if (timeoutId) window.clearTimeout(timeoutId);
      setLoading(false);
    }
  };

  const handleTopicKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key !== "Enter" || loading) return;
    event.preventDefault();
    void runDailyRecommendation();
  };

  const handleProviderChange = (provider: LLMProvider) => {
    const preset = MODEL_PRESETS.find((item) => item.provider === provider);
    if (preset) {
      setSelectedPresetId(preset.id);
      setLlmConfig((prev) => ({ ...prev, provider: preset.provider, model: preset.model, base_url: preset.base_url, api_key: ["demo", "ollama"].includes(provider) ? "" : prev.api_key }));
      return;
    }
    setSelectedPresetId("custom-openai");
    setLlmConfig((prev) => ({ ...prev, provider, model: "", base_url: "", api_key: ["demo", "ollama"].includes(provider) ? "" : prev.api_key }));
  };

  const handlePresetChange = (presetId: string) => {
    setSelectedPresetId(presetId);
    const preset = MODEL_PRESETS.find((item) => item.id === presetId);
    if (!preset) return;
    setLlmConfig((prev) => ({ ...prev, provider: preset.provider, model: preset.model, base_url: preset.base_url, api_key: ["demo", "ollama"].includes(preset.provider) ? "" : prev.api_key }));
  };

  const goToDetail = (item: RecommendationItem | FollowUpItem) => {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ projectTopic, limit, items, message, hasSearched }));
    } catch (error) {
      console.error("保存详情页回退数据失败", error);
    }
    window.location.href = `/paper/${item.paper_id}?topic=${encodeURIComponent(projectTopic || item.topic || "")}`;
  };

  const toggleCompareSelection = (paperId: number) => {
    setSelectedCompareIds((prev) => {
      if (prev.includes(paperId)) return prev.filter((id) => id !== paperId);
      if (prev.length >= 3) return [...prev.slice(1), paperId];
      return [...prev, paperId];
    });
  };

  const openComparePage = () => {
    if (selectedCompareIds.length < 2) return setMessage(text.compareNeedTwo);
    sessionStorage.setItem(COMPARE_IDS_KEY, JSON.stringify(selectedCompareIds));
    window.location.href = `/compare?topic=${encodeURIComponent(projectTopic)}&ids=${selectedCompareIds.join(",")}`;
  };

  const addToFollowUp = async (bucket: FollowUpBucket, item: RecommendationItem) => {
    try {
      const res = await fetch(`${getApiBaseUrl()}/follow-ups`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          paper_id: item.paper_id,
          bucket,
          topic: projectTopic,
          title: item.title,
          one_sentence_summary: item.one_sentence_summary,
          tags: item.tags || [],
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || "保存跟进失败");
      const saved = data.item as FollowUpItem;
      setFollowUpItems((prev) => {
        const withoutCurrent = prev.filter((entry) => !(entry.paper_id === saved.paper_id && entry.bucket === saved.bucket));
        return [saved, ...withoutCurrent];
      });
      setActiveFollowUpMenuId(null);
      setMessage(text.joinSuccess.replace("{label}", translateBucketLabel(bucket, uiLanguage)));
    } catch (error) {
      console.error(error);
      setMessage(text.joinFailed);
    }
  };

  const removeFromFollowUp = async (paperId: number, bucket: FollowUpBucket) => {
    try {
      const res = await fetch(`${getApiBaseUrl()}/follow-ups/${paperId}?bucket=${encodeURIComponent(bucket)}`, {
        method: "DELETE",
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || "移除跟进失败");
      setFollowUpItems((prev) => prev.filter((item) => !(item.paper_id === paperId && item.bucket === bucket)));
      setActiveFollowUpMenuId(null);
      setMessage(text.removeSuccess.replace("{label}", translateBucketLabel(bucket, uiLanguage)));
    } catch (error) {
      console.error(error);
      setMessage(text.removeFailed);
    }
  };

  const isInFollowUp = (paperId: number, bucket: FollowUpBucket) => {
    return followUpItems.some((item) => item.paper_id === paperId && item.bucket === bucket);
  };
  return (
    <>
      <main style={{ maxWidth: 1080, margin: "0 auto", padding: "32px 20px 48px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "flex-start", marginBottom: 20 }}>
          <div>
            <h1 style={{ fontSize: 32, fontWeight: 800, marginBottom: 12 }}>{text.title}</h1>
            <p style={{ color: "#4b5563", lineHeight: 1.8 }}>{text.subtitle}</p>
          </div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <button type="button" onClick={() => setShowFeatureDrawer(true)} style={toolboxButtonStyle}>{text.toolbox}</button>
            <button type="button" onClick={() => setShowSettings(true)} style={settingsButtonStyle}>{text.settings}</button>
          </div>
        </div>

        <div style={statusBarStyle}>
            <span>{text.currentMode}：{translateProviderLabel(llmConfig.provider, uiLanguage)}</span>
          <span>{text.model}：{llmConfig.model || text.countPlaceholder}</span>
          {backendLLM?.model && <span>{text.defaultModel}：{backendLLM.model}</span>}
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "minmax(0,1fr) 120px 160px", gap: 12, marginBottom: 16 }}>
          <input value={projectTopic} onChange={(e) => setProjectTopic(e.target.value)} onKeyDown={handleTopicKeyDown} placeholder={text.inputPlaceholder} style={inputStyle} />
          <input type="number" min={1} max={20} value={limit} onChange={(e) => setLimit(Number(e.target.value))} style={inputStyle} />
          <button type="button" onClick={runDailyRecommendation} disabled={loading} style={{ ...buttonStyle, background: loading ? "#9ca3af" : "#111827" }}>{loading ? text.generating : text.dailyRecommend}</button>
        </div>

        <div style={messageStyle(message)}>{message}</div>

        {hasSearched && items.length > 0 && (
          <div style={miniStateBarStyle}>
            <span>{text.currentView}：{translateModeLabel(activeMode.id, uiLanguage)}</span>
            <span>{selectedCompareIds.length > 0 ? text.waitingCompare.replace("{count}", String(selectedCompareIds.length)) : text.emptyMiniHint}</span>
          </div>
        )}

        {hasSearched && (
          <div style={{ display: "grid", gap: 18 }}>
            {displayedItems.map((item, index) => {
              const rank = index + 1;
              const priorityLabel = getPriorityLabel(rank, uiLanguage);
              const recommendationScore = typeof item.recommendation_score === "number" ? item.recommendation_score : typeof item.score === "number" ? Math.round(item.score * 20) : Math.max(72, 98 - index * 4);
              const tone = getPriorityTone(item.priority_bucket, rank);
              const selected = selectedCompareIds.includes(item.paper_id);
              const activeFollowUps = FOLLOW_UP_BUCKETS.filter((bucket) => isInFollowUp(item.paper_id, bucket.id));

              return (
                <article key={item.paper_id} style={{ border: `1px solid ${tone.cardBorder}`, borderRadius: 18, padding: 22, boxShadow: "0 4px 18px rgba(15, 23, 42, 0.05)", background: tone.cardBg }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "flex-start", marginBottom: 14 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                      <span style={topBadgeStyle}>TOP {rank}</span>
                      <span style={{ display: "inline-flex", alignItems: "center", gap: 6, padding: "6px 10px", borderRadius: 999, background: tone.badgeBg, color: tone.badgeColor, border: `1px solid ${tone.badgeBorder}`, fontSize: 13, fontWeight: 700 }}>{priorityLabel}</span>
                      {item.recommendation_zh && <span style={softBadgeStyle}>{translateAssessmentValue(item.recommendation_zh, uiLanguage)}</span>}
                      <span style={scoreStyle}>{text.recommendationScore} {recommendationScore}</span>
                    </div>
                    <label style={compareCheckStyle(selected)}>
                      <input type="checkbox" checked={selected} onChange={() => toggleCompareSelection(item.paper_id)} style={{ margin: 0 }} />
                      <span>{selected ? text.removeCompare : text.addCompare}</span>
                    </label>
                  </div>

                  <h2 style={{ fontSize: 24, fontWeight: 800, marginBottom: 12, color: "#111827", lineHeight: 1.4 }}>{item.title}</h2>
                  <p style={{ marginBottom: 10, color: "#1f2937", lineHeight: 1.85 }}><strong style={{ color: "#111827" }}>{text.summary}：</strong>{item.one_sentence_summary || (uiLanguage === "zh" ? "暂未生成一句话总结。" : "No takeaway available yet.")}</p>
                  <p style={{ marginBottom: 14, color: "#475569", lineHeight: 1.75, fontSize: 14, fontWeight: 500 }}>{modeHint(researchMode, item, uiLanguage)}</p>

                  {item.reproducibility_level_zh && (
                    <p style={{ marginBottom: 12, color: "#475569", lineHeight: 1.7, fontSize: 14 }}>
                      <strong style={{ color: "#111827" }}>{uiLanguage === "zh" ? "复现判断" : "Reproducibility"}：</strong>{" "}
                      {translateAssessmentValue(item.reproducibility_level_zh, uiLanguage)}
                    </p>
                  )}

                  {(item.tags || []).length > 0 && (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, margin: "14px 0 16px" }}>
                      {item.tags?.map((tag) => <span key={tag} style={tagStyle}>{translateTag(tag, uiLanguage)}</span>)}
                    </div>
                  )}

                  {activeFollowUps.length > 0 && (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 14 }}>
                      {activeFollowUps.map((bucket) => (
                        <button key={`${item.paper_id}-${bucket.id}`} type="button" onClick={() => void removeFromFollowUp(item.paper_id, bucket.id)} style={activeFollowUpChipStyle(bucket.id)}>
                          <span>{translateBucketLabel(bucket.id, uiLanguage)}</span>
                          <span style={{ fontWeight: 900 }}>×</span>
                        </button>
                      ))}
                    </div>
                  )}

                  <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center", position: "relative" }}>
                    <button type="button" onClick={() => goToDetail(item)} style={detailButtonStyle}>{text.viewDetail}</button>
                    <button type="button" onClick={() => toggleCompareSelection(item.paper_id)} style={secondaryActionStyle(selected)}>{selected ? text.removeCompare : text.addCompare}</button>
                    <div style={{ position: "relative" }}>
                      <button type="button" onClick={() => setActiveFollowUpMenuId((prev) => prev === item.paper_id ? null : item.paper_id)} style={followUpButtonStyle}>{text.addFollowUp}</button>
                      {activeFollowUpMenuId === item.paper_id && (
                        <div style={followUpMenuStyle}>
                          {FOLLOW_UP_BUCKETS.map((bucket) => {
                            const added = isInFollowUp(item.paper_id, bucket.id);
                            return (
                              <button key={bucket.id} type="button" onClick={() => void (added ? removeFromFollowUp(item.paper_id, bucket.id) : addToFollowUp(bucket.id, item))} style={followUpMenuItemStyle(added)}>
                                <span>{translateBucketLabel(bucket.id, uiLanguage)}</span>
                                <span style={{ color: added ? "#166534" : "#94a3b8", fontSize: 12 }}>{added ? text.remove : text.add}</span>
                              </button>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </main>

      {showSettings && (
        <div style={modalMaskStyle} onClick={() => setShowSettings(false)}>
          <div style={modalCardStyle} onClick={(event) => event.stopPropagation()}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", marginBottom: 14 }}>
              <div>
                <h2 style={{ fontSize: 22, fontWeight: 800, marginBottom: 6 }}>{text.settings}</h2>
                <p style={{ color: "#6b7280", lineHeight: 1.7 }}>{text.settingsHint}</p>
              </div>
              <button type="button" onClick={() => setShowSettings(false)} style={closeButtonStyle}>{text.close}</button>
            </div>

            <div style={modalHintStyle}>
              {llmConfig.provider === "demo"
                ? (uiLanguage === "zh"
                    ? "内置 Demo 模式不需要 API Key 或本地模型，适合第一次快速体验产品效果。"
                    : "Built-in demo mode needs no API key or local model. Use it for a quick first product preview.")
                : llmConfig.provider === "ollama"
                  ? text.settingsTipLocal
                  : text.settingsTipApi}
            </div>
            {llmConfig.provider === "demo" && (
              <div style={{ color: "#475569", fontSize: 13, lineHeight: 1.8, marginTop: 10, marginBottom: 4 }}>
                {uiLanguage === "zh"
                  ? "Demo 建议先搜 LLM、RAG、CoT、Reasoning 或 Multimodal。若要做更广的自定义主题搜索，请切换到自己的 API Key 或本地模型。"
                  : "For demo mode, start with LLM, RAG, CoT, Reasoning, or Multimodal. For broader custom topic search, switch to your own API key or a local model."}
              </div>
            )}

            <div style={configGridStyle}>
              <label style={fieldStyle}><span style={labelStyle}>{text.modelPreset}</span><select value={selectedPresetId} onChange={(e) => handlePresetChange(e.target.value)} style={inputStyle}>{MODEL_PRESETS.map((preset) => <option key={preset.id} value={preset.id}>{preset.label}</option>)}</select></label>
              <label style={fieldStyle}><span style={labelStyle}>{text.provider}</span><select value={llmConfig.provider} onChange={(e) => handleProviderChange(e.target.value as LLMProvider)} style={inputStyle}><option value="demo">{translateProviderLabel("demo", uiLanguage)}</option><option value="ollama">{translateProviderLabel("ollama", uiLanguage)}</option><option value="deepseek">{translateProviderLabel("deepseek", uiLanguage)}</option><option value="kimi">{translateProviderLabel("kimi", uiLanguage)}</option><option value="qwen">{translateProviderLabel("qwen", uiLanguage)}</option><option value="openai_compatible">{translateProviderLabel("openai_compatible", uiLanguage)}</option></select></label>
              <label style={fieldStyle}><span style={labelStyle}>{text.modelName}</span><input value={llmConfig.model} onChange={(e) => { setSelectedPresetId("custom-openai"); setLlmConfig((prev) => ({ ...prev, model: e.target.value })); }} placeholder="paperpilot-demo / qwen2.5:7b / deepseek-chat / qwen-plus" style={inputStyle} /></label>
              <label style={fieldStyle}><span style={labelStyle}>{text.baseUrl}</span><input value={llmConfig.base_url} onChange={(e) => { setSelectedPresetId("custom-openai"); setLlmConfig((prev) => ({ ...prev, base_url: e.target.value })); }} placeholder="demo://built-in / http://localhost:11434" style={inputStyle} /></label>
              <label style={fieldStyle}><span style={labelStyle}>{text.apiKey}</span><input type="password" value={llmConfig.api_key} onChange={(e) => setLlmConfig((prev) => ({ ...prev, api_key: e.target.value }))} placeholder={["demo", "ollama"].includes(llmConfig.provider) ? "No API key needed" : "Enter a valid API key"} style={inputStyle} /></label>
            </div>
          </div>
        </div>
      )}
      {showFeatureDrawer && (
        <div style={drawerMaskStyle} onClick={() => setShowFeatureDrawer(false)}>
          <aside style={drawerPanelStyle} onClick={(event) => event.stopPropagation()}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "flex-start", marginBottom: 6 }}>
              <div>
                <h2 style={{ fontSize: 28, fontWeight: 900, color: "#111827", margin: "0 0 8px" }}>{text.toolbox}</h2>
                <p style={{ color: "#64748b", lineHeight: 1.8, margin: 0 }}>{uiLanguage === "zh" ? "切换不同浏览目标，把候选放到一起对照，并持续整理自己的后续跟进清单。" : "Switch reading goals, compare candidates, and keep lightweight follow-up lists in one place."}</p>
              </div>
              <button type="button" onClick={() => setShowFeatureDrawer(false)} style={closeButtonStyle}>{text.close}</button>
            </div>

            <div style={drawerHeroStyle}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 800, color: "#0f766e", marginBottom: 6 }}>{text.modeLabel}</div>
                <div style={{ fontSize: 24, fontWeight: 900, color: "#0f172a", marginBottom: 8 }}>{translateModeLabel(activeMode.id, uiLanguage)}</div>
                <div style={{ color: "#334155", lineHeight: 1.8 }}>{translateModeDescription(activeMode.id, uiLanguage)}</div>
              </div>
              <div style={drawerHeroHintStyle}>
                <div style={{ fontSize: 13, color: "#475569", fontWeight: 700, marginBottom: 8 }}>{text.followUpTitle}</div>
                <div style={{ fontSize: 28, fontWeight: 900, color: "#111827" }}>{followUpItems.length}</div>
                <div style={{ fontSize: 13, color: "#64748b" }}>{text.papersSaved}</div>
              </div>
            </div>

            <div style={drawerContentGridStyle}>
              <div style={{ display: "grid", gap: 18 }}>
                <div style={drawerCardStyle}>
                  <div style={{ marginBottom: 14 }}>
                    <div style={{ fontWeight: 800, color: "#111827", marginBottom: 6, fontSize: 18 }}>{text.browseGoal}</div>
                    <div style={{ color: "#475569", fontSize: 14, lineHeight: 1.8 }}>{text.browseGoalHint}</div>
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
                    {RESEARCH_MODES.map((mode) => (
                      <button key={mode.id} type="button" onClick={() => setResearchMode(mode.id)} style={modeButtonStyle(researchMode === mode.id)}>{translateModeLabel(mode.id, uiLanguage)}</button>
                    ))}
                  </div>
                </div>

                <div style={drawerCompareCardStyle}>
                  <div>
                    <div style={{ fontWeight: 800, color: "#111827", marginBottom: 6, fontSize: 18 }}>{text.compareTitle}</div>
                    <div style={{ color: "#334155", fontSize: 14, lineHeight: 1.8 }}>{text.compareHint.replace("{count}", String(selectedCompareIds.length))}</div>
                  </div>
                  <button type="button" onClick={openComparePage} disabled={selectedCompareIds.length < 2} style={{ ...buttonStyle, padding: "12px 18px", background: selectedCompareIds.length >= 2 ? "#0f766e" : "#9ca3af", width: "fit-content" }}>{text.startCompare}</button>
                </div>
              </div>

              <div style={drawerCardStyle}>
                <div style={{ marginBottom: 14 }}>
                  <div style={{ fontWeight: 800, color: "#111827", marginBottom: 6, fontSize: 18 }}>{text.followUpTitle}</div>
                  <div style={{ color: "#475569", fontSize: 14, lineHeight: 1.8 }}>{uiLanguage === "zh" ? "把值得继续处理的论文留下来，后面可以直接回到详情页继续看。" : "Keep promising papers here so you can return to their detail pages later."}</div>
                </div>

                <div style={{ display: "grid", gap: 14 }}>
                  {followUpGroups.map((group) => (
                    <div key={group.id} style={followUpGroupStyle}>
                      <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center", marginBottom: 10 }}>
                        <div>
                          <div style={{ fontWeight: 800, color: "#111827" }}>{translateBucketLabel(group.id, uiLanguage)}</div>
                          <div style={{ fontSize: 13, color: "#64748b" }}>{uiLanguage === "zh" ? group.description : group.id === "reading" ? "Papers you plan to read carefully." : group.id === "reproduce" ? "Papers you may try to implement or verify." : "Papers worth keeping as topic candidates."}</div>
                        </div>
                        <span style={followUpCountStyle}>{group.items.length}</span>
                      </div>

                      {group.items.length > 0 ? (
                        <div style={{ display: "grid", gap: 10 }}>
                          {group.items.slice(0, 4).map((item) => (
                            <div key={`${group.id}-${item.paper_id}`} style={followUpRowStyle}>
                              <div style={{ minWidth: 0 }}>
                                <div style={{ fontSize: 14, fontWeight: 700, color: "#111827", lineHeight: 1.5 }}>{item.title}</div>
                                <div style={{ fontSize: 12, color: "#64748b", lineHeight: 1.7 }}>{item.one_sentence_summary || "已加入跟进清单。"}</div>
                              </div>
                              <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
                                <button type="button" onClick={() => goToDetail(item)} style={tinyButtonStyle}>{text.open}</button>
                                <button type="button" onClick={() => removeFromFollowUp(item.paper_id, item.bucket)} style={tinyGhostButtonStyle}>{text.remove}</button>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div style={{ fontSize: 13, color: "#94a3b8", lineHeight: 1.8 }}>{text.noFollowUp}</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </aside>
        </div>
      )}
    </>
  );
}

const inputStyle: React.CSSProperties = { padding: "12px 14px", border: "1px solid #d1d5db", borderRadius: 12, fontSize: 16, color: "#111827", background: "#fff" };
const buttonStyle: React.CSSProperties = { border: "none", borderRadius: 12, padding: "12px 16px", fontSize: 16, fontWeight: 700, cursor: "pointer", color: "#fff" };
const statusBarStyle: React.CSSProperties = { display: "flex", gap: 14, flexWrap: "wrap", marginBottom: 18, padding: "10px 12px", borderRadius: 12, background: "#f8fafc", border: "1px solid #e5e7eb", color: "#475569", fontSize: 13 };
const settingsButtonStyle: React.CSSProperties = { border: "1px solid #d1d5db", borderRadius: 12, padding: "10px 14px", background: "#fff", color: "#111827", fontSize: 14, fontWeight: 700, cursor: "pointer", whiteSpace: "nowrap" };
const toolboxButtonStyle: React.CSSProperties = { border: "1px solid #cbd5e1", borderRadius: 12, padding: "10px 14px", background: "#f8fafc", color: "#0f172a", fontSize: 14, fontWeight: 800, cursor: "pointer", whiteSpace: "nowrap" };
const topBadgeStyle: React.CSSProperties = { display: "inline-flex", alignItems: "center", justifyContent: "center", minWidth: 72, padding: "6px 12px", borderRadius: 999, background: "#111827", color: "#fff", fontSize: 13, fontWeight: 800 };
const softBadgeStyle: React.CSSProperties = { padding: "6px 10px", borderRadius: 999, background: "#f3f4f6", color: "#374151", fontSize: 13, fontWeight: 600 };
const scoreStyle: React.CSSProperties = { padding: "6px 10px", borderRadius: 999, background: "#ecfccb", color: "#365314", fontSize: 13, fontWeight: 800, border: "1px solid #bef264" };
const tagStyle: React.CSSProperties = { padding: "6px 10px", borderRadius: 999, background: "#eef2ff", color: "#3730a3", fontSize: 13 };
const detailButtonStyle: React.CSSProperties = { display: "inline-block", border: "1px solid #d1d5db", borderRadius: 12, padding: "9px 16px", background: "#fff", cursor: "pointer", fontSize: 14, fontWeight: 700, color: "#111827" };
const followUpButtonStyle: React.CSSProperties = { display: "inline-block", border: "1px solid #d1d5db", borderRadius: 12, padding: "9px 16px", background: "#f8fafc", cursor: "pointer", fontSize: 14, fontWeight: 700, color: "#111827" };
const miniStateBarStyle: React.CSSProperties = { display: "flex", gap: 14, flexWrap: "wrap", marginBottom: 18, padding: "12px 14px", borderRadius: 14, background: "#ffffff", border: "1px solid #e5e7eb", color: "#475569", fontSize: 14 };
const modalMaskStyle: React.CSSProperties = { position: "fixed", inset: 0, background: "rgba(15, 23, 42, 0.32)", display: "flex", alignItems: "center", justifyContent: "center", padding: 20, zIndex: 50 };
const modalCardStyle: React.CSSProperties = { width: "min(760px, 100%)", background: "#fff", borderRadius: 20, border: "1px solid #e5e7eb", padding: 22, boxShadow: "0 30px 80px rgba(15, 23, 42, 0.18)" };
const configGridStyle: React.CSSProperties = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 };
const fieldStyle: React.CSSProperties = { display: "grid", gap: 8 };
const labelStyle: React.CSSProperties = { fontSize: 13, fontWeight: 700, color: "#374151" };
const closeButtonStyle: React.CSSProperties = { border: "1px solid #e5e7eb", borderRadius: 10, padding: "8px 12px", background: "#fff", cursor: "pointer", fontWeight: 700 };
const modalHintStyle: React.CSSProperties = { padding: "12px 14px", borderRadius: 12, background: "#f8fafc", color: "#475569", lineHeight: 1.8, marginBottom: 14, border: "1px solid #e5e7eb" };
const drawerMaskStyle: React.CSSProperties = { position: "fixed", inset: 0, background: "rgba(15, 23, 42, 0.34)", display: "flex", alignItems: "center", justifyContent: "center", padding: 24, zIndex: 55 };
const drawerPanelStyle: React.CSSProperties = { width: "min(1120px, calc(100vw - 48px))", maxHeight: "84vh", background: "#ffffff", borderRadius: 28, padding: "28px", boxShadow: "0 28px 90px rgba(15, 23, 42, 0.22)", overflowY: "auto", display: "grid", gap: 20 };
const drawerHeroStyle: React.CSSProperties = { display: "grid", gridTemplateColumns: "minmax(0,1fr) 200px", gap: 18, padding: "20px 22px", borderRadius: 22, background: "linear-gradient(135deg, #f8fafc 0%, #ecfeff 100%)", border: "1px solid #dbeafe" };
const drawerHeroHintStyle: React.CSSProperties = { borderRadius: 18, background: "#ffffff", border: "1px solid #e5e7eb", padding: "16px 18px", display: "grid", alignContent: "start" };
const drawerContentGridStyle: React.CSSProperties = { display: "grid", gridTemplateColumns: "minmax(0,1fr) minmax(380px,0.95fr)", gap: 18 };
const drawerCardStyle: React.CSSProperties = { padding: "20px", borderRadius: 22, background: "#ffffff", border: "1px solid #e5e7eb", boxShadow: "0 4px 18px rgba(15, 23, 42, 0.04)" };
const drawerCompareCardStyle: React.CSSProperties = { display: "grid", gap: 16, padding: "20px", borderRadius: 22, background: "#f0fdf4", border: "1px solid #bbf7d0", alignContent: "space-between" };
const followUpGroupStyle: React.CSSProperties = { padding: "14px", borderRadius: 16, background: "#f8fafc", border: "1px solid #e5e7eb" };
const followUpCountStyle: React.CSSProperties = { display: "inline-flex", alignItems: "center", justifyContent: "center", minWidth: 28, height: 28, borderRadius: 999, background: "#e2e8f0", color: "#334155", fontSize: 12, fontWeight: 800 };
const followUpRowStyle: React.CSSProperties = { display: "flex", justifyContent: "space-between", gap: 12, alignItems: "flex-start", padding: "10px 12px", borderRadius: 14, background: "#ffffff", border: "1px solid #e2e8f0" };
const tinyButtonStyle: React.CSSProperties = { border: "1px solid #d1d5db", borderRadius: 10, padding: "7px 10px", background: "#fff", cursor: "pointer", fontSize: 12, fontWeight: 700, color: "#111827" };
const tinyGhostButtonStyle: React.CSSProperties = { border: "1px solid #e5e7eb", borderRadius: 10, padding: "7px 10px", background: "#f8fafc", cursor: "pointer", fontSize: 12, fontWeight: 700, color: "#475569" };
const followUpMenuStyle: React.CSSProperties = { position: "absolute", top: "calc(100% + 8px)", left: 0, width: 220, borderRadius: 16, background: "#fff", border: "1px solid #e5e7eb", boxShadow: "0 18px 40px rgba(15, 23, 42, 0.12)", padding: 8, display: "grid", gap: 6, zIndex: 20 };
function activeFollowUpChipStyle(bucket: FollowUpBucket): React.CSSProperties { const tone = bucket === "reading" ? { bg: "#eff6ff", color: "#1d4ed8", border: "#bfdbfe" } : bucket === "reproduce" ? { bg: "#ecfeff", color: "#155e75", border: "#a5f3fc" } : { bg: "#fef3c7", color: "#92400e", border: "#fcd34d" }; return { display: "inline-flex", alignItems: "center", gap: 8, padding: "7px 10px", borderRadius: 999, border: `1px solid ${tone.border}`, background: tone.bg, color: tone.color, cursor: "pointer", fontSize: 12, fontWeight: 800 }; }
function followUpMenuItemStyle(added: boolean): React.CSSProperties { const tone = added ? { bg: "#f0fdf4", color: "#166534", border: "#bbf7d0" } : { bg: "#ffffff", color: "#111827", border: "#e5e7eb" }; return { display: "flex", justifyContent: "space-between", gap: 10, alignItems: "center", width: "100%", border: `1px solid ${tone.border}`, borderRadius: 12, padding: "10px 12px", background: tone.bg, color: tone.color, cursor: "pointer", fontSize: 13, fontWeight: 700, textAlign: "left" as const }; }
function compareCheckStyle(selected: boolean): React.CSSProperties { return { display: "inline-flex", alignItems: "center", gap: 8, padding: "8px 10px", borderRadius: 12, background: selected ? "#ecfeff" : "#f8fafc", color: selected ? "#155e75" : "#475569", border: `1px solid ${selected ? "#a5f3fc" : "#e5e7eb"}`, fontSize: 13, fontWeight: 700, cursor: "pointer" }; }
function secondaryActionStyle(selected: boolean): React.CSSProperties { return { display: "inline-block", border: `1px solid ${selected ? "#a5f3fc" : "#d1d5db"}`, borderRadius: 12, padding: "9px 16px", background: selected ? "#ecfeff" : "#fff", cursor: "pointer", fontSize: 14, fontWeight: 700, color: selected ? "#155e75" : "#111827" }; }
function modeButtonStyle(active: boolean): React.CSSProperties { return { border: `1px solid ${active ? "#c7d2fe" : "#e5e7eb"}`, borderRadius: 999, padding: "10px 16px", background: active ? "#eef2ff" : "#fff", color: active ? "#3730a3" : "#374151", fontSize: 14, fontWeight: 700, cursor: "pointer" }; }
function messageStyle(message: string): React.CSSProperties { return { marginBottom: 20, padding: "12px 14px", borderRadius: 12, background: "#f5f5f5", color: "#333", fontWeight: message.includes("失败") ? 700 : 400 }; }
