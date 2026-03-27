# 论文推荐系统项目完整交接总结（可直接用于新聊天续接）

## 1. 项目目标与当前阶段定位

本项目当前已经明确的目标是：

- 做一个**可体验的论文推荐产品原型（MVP / v0.1）**
- 用户输入主题后，系统能够：
  1. 抓取当天论文
  2. 做主题理解与扩展
  3. 进行候选筛选
  4. 做轻分析
  5. 返回推荐卡片
- 先解决**输入主题与输出论文必须对上**的问题
- 在主题匹配稳定后，再继续做：
  - 产品体验补齐
  - 其他用户本地可运行 / 可部署
  - 扩展到 arXiv 等数据源
  - RAG + 标签树系统
  - 反馈系统与个性化能力

当前已经达成的核心共识是：

> 现阶段先不追求“推荐多聪明”，先保证“输入主题和输出论文必须对上”，并在此基础上形成一个别人可体验、可运行的大体版本。

---

## 2. 产品主线与后续总路线（当前最新共识）

当前项目的总路线已经明确，应按下面顺序推进：

### 第一阶段：收一个可体验版本（v0.1）
目标：先让用户能用、能体验、能反馈。

包含：
- 单主题输入
- 每日论文推荐
- 主题归一化 + 动态扩展 + 候选过滤 + 轻分析
- 推荐卡片展示
- 空结果 / 少结果提示
- 别人在自己电脑上能运行

### 第二阶段：让其他用户也能用
目标：不再只是在开发者自己电脑上可用。

包含：
- `.env.example`
- `requirements.txt`
- 启动说明
- README
- 前后端启动命令与运行步骤
- 后端地址 / 模型地址 / 数据库路径可配置
- 为后续局域网 / 服务器部署做准备

### 第三阶段：扩展数据源
目标：不再只依赖 Hugging Face daily。

优先级：
1. arXiv
2. Papers with Code
3. OpenReview / 会议信源
4. GitHub / repo signal

### 第四阶段：架构升级
目标：从当前规则 + LLM 工作流升级为更强系统。

包含：
- RAG 系统
- 标签树 / 主题层次体系
- 多源融合召回
- 更强排序与解释性
- 用户反馈与偏好

---

## 3. 当前已经打通的主链路

后端已经从“抓取论文列表”进展到“能输出推荐结果”，前端也已从 Swagger/手动请求进展到最小可用产品页面。

### 已打通接口与能力

#### 1）抓取与入库
- `GET /papers/daily/fetch`
- 可从 Hugging Face Daily Papers 抓取论文
- 可写入 SQLite

#### 2）论文列表
- `GET /papers`
- 可返回数据库中的论文列表

#### 3）轻分析
- `POST /papers/analyze_light`
- 可对论文执行轻分析
- 可把轻分析结果写入 `paper_analyses`

#### 4）推荐列表
- `GET /papers/recommendations`
- 可返回推荐结果列表
- 返回内容包含：
  - 标题
  - 一句话总结
  - 推荐语
  - recommendation / recommendation_zh
  - topic_fit / topic_fit_zh
  - novelty_level / novelty_level_zh
  - reproducibility_level / reproducibility_level_zh
  - tags
  - score

#### 5）一键产品接口
- `GET /papers/daily/run?project_topic=xxx&limit=5`
- 当前产品主入口
- 能自动完成：
  1. 抓取
  2. 入库
  3. 主题过滤
  4. 轻分析
  5. 返回推荐结果

#### 6）调试接口
- `GET /debug/topic_expand?project_topic=xxx`
- 用于调试主题扩展链路
- 可查看：
  - `input_topic`
  - `normalized_topic`
  - `expanded.canonical_topic`
  - `expanded.aliases`
  - `expanded.expansions`
  - `rule_aliases`
  - `rule_keywords`

---

## 4. 前端当前状态

前端已具备最小可用产品页面。

### 已完成能力
- 页面地址：`http://localhost:3000/`
- 输入框允许用户输入主题
- 数量输入框可控制返回篇数
- “每日推荐”按钮可触发推荐流程
- 能展示推荐卡，包括：
  - 标题
  - 一句话总结
  - 推荐语
  - 标签
  - 评分
  - 论文链接

### 已修复问题

#### 1）页面自动请求问题
之前一打开页面就自动执行推荐流程，导致：
- 不点按钮也会转圈
- 后端重复分析
- 体验混乱

已确认：
- 页面加载时不自动请求
- 只有用户点击按钮才执行

#### 2）消息提示方向
当前已经明确：
- 若无结果，应显示“今日无与主题 xxx 严格匹配的论文”
- 若结果不足，应显示“今日仅找到 N 篇与主题 xxx 严格匹配的论文”
- 不能统一只显示“每日推荐流程执行完成”

---

## 5. 数据库与后端结构问题（已识别）

### 已遇到过的问题
- 旧 SQLite 表结构未更新
- 新增字段（如 `score`）后旧表不兼容
- 导致推荐查询报错或结果异常

### 已确认处理方式
- 开发阶段允许删除旧数据库重建
- 当前数据库文件为：
  - `paper_reader.db`

---

## 6. 当前最大问题与本轮核心解决方向

本轮对话中已经明确，当前最大问题不是前端，也不只是模型能力，而是：

> **输入主题与输出论文匹配不稳定，且未知主题的泛化能力不足。**

### 历史问题表现
- 同一批论文在不同主题下反复出现
- `rag` / `RAG` 会混入环境、水质、重建类论文
- `protein` / `antibody` 可能返回明显无关内容
- `rag` 和 `RAG` 大小写行为不一致
- 无结果时提示不明确

### 新阶段扩展后出现的问题
在加入“未知主题动态扩展”后，还观察到：
- `document intelligence` 一开始只能靠原词兜底，扩展几乎为空
- `time series forecasting` 一开始也只能靠原词，或扩展过宽导致召回不准
- 3B 模型对未知主题扩展能力偏弱，需要程序兜底

---

## 7. 已达成的最重要技术共识

### 共识 1：不能一味依赖更强大模型硬修正
用户初心是：
- 尽量走小模型路线
- 降低成本
- 降低使用门槛
- 提高普及性

所以不能一开始就完全依赖强商用模型暴力修正结果。

### 共识 2：程序要先帮助模型，而不是让模型自由判断
正式路线已经统一为：

> **程序先严格筛，再让小模型做精筛和解释。**

### 共识 3：当前先不深挖高级功能，先收 MVP
暂缓：
- 个性化推荐
- 复杂重排
- 反馈闭环
- PostgreSQL
- 豆包 API 等外部复杂接入
- 过早做部署扩展

### 共识 4：当前系统是 “agentic workflow”，不是完整 agent
当前系统已具备：
- 多步骤处理
- 工具调用
- 中间决策
- 模型输出结构化约束
- 失败重试与 fallback

但还不算完整 agent，因为还没有：
- 自动多轮规划
- 自动对比方案
- 自动反思与再搜索

所以当前更准确定位是：

> **一个带 LLM 的多阶段工作流系统 / agentic workflow**

---

## 8. 推荐流程的正式版本（当前已统一）

### 第一层：主题标准化
先把用户输入归一化，避免：
- `rag`
- `RAG`
- ` Rag `
被当成不同主题

### 第二层：主题别名与扩展词生成
分成两类：

#### A. 强别名 / 原词 / canonical alias
用于主题本体匹配，例如：
- `llm`
- `large language model`
- `大语言模型`

#### B. 扩展词 / support terms
用于辅助召回，例如：
- `ocr`
- `layout analysis`
- `temporal modeling`
- `long horizon forecasting`

### 第三层：程序硬过滤
对标题和摘要：
- 如果完全不命中强别名 / 有效扩展
- 直接排除
- 根本不送入 LLM

### 第四层：小模型轻分析
只对通过候选过滤的论文做轻分析：
- 一句话总结
- 推荐语
- topic_fit
- recommendation
- tags

### 第五层：程序二次兜底
即使已经通过轻分析，也再复核：
- `topic_fit == low` 排除
- `recommendation == skip` 排除
- 若 summary / tags / 标题摘要整体仍不体现主题，也排除

### 第六层：严格返回
- 不够就少返回
- 绝不为了凑数补无关论文

---

## 9. 当前关键模块与职责

### 后端关键文件
- `app/models.py`
- `app/services/light_analyzer.py`
- `app/services/paper_repository.py`
- `app/services/topic_rules.py`
- `app/services/topic_expander.py`
- `app/services/llm_client.py`
- `app/main.py`

### 前端关键文件
- `app/page.tsx`

### 各文件职责

#### `app/models.py`
负责数据库模型：
- `Paper`
- `PaperAnalysis`

#### `app/services/light_analyzer.py`
负责轻分析：
- 调用模型
- 规范输出
- 输出 recommendation / topic_fit / tags 等字段

#### `app/services/paper_repository.py`
负责：
- 入库
- 查询
- 保存 light analysis
- 按 topic 获取 recommendations
- 删除某主题下的旧 analysis

#### `app/services/topic_rules.py`
负责：
- 主题标准化
- alias / keywords 获取
- 候选论文硬过滤
- 后置二次兜底
- 规则收紧（原词强匹配优先、泛词不单独放行）

#### `app/services/topic_expander.py`
负责：
- 对非手写主题做动态扩展
- 输出：
  - `canonical_topic`
  - `aliases`
  - `expansions`
- 扩展为空时二次重试
- 仍不够时走程序 fallback 扩展

#### `app/services/llm_client.py`
负责：
- 调用 Ollama / OpenAI 兼容接口
- 向 topic_expander 等模块提供 `chat_json(...)`

#### `app/main.py`
负责 FastAPI 路由整合：
- daily fetch
- analyze_light
- recommendations
- daily run
- pdf 深分析
- topic_expand 调试接口

#### `app/page.tsx`
负责前端页面：
- 输入主题
- 点击“每日推荐”
- 请求 `/papers/daily/run`
- 展示推荐卡和提示信息

---

## 10. 主题规则与动态扩展的演进过程

### 最初阶段
- 只靠少量人工手写关键词
- 只能覆盖少数预设主题：
  - `rag`
  - `protein`
  - `antibody`
  - `multimodal`
  - `llm`

### 第二阶段
- 引入 `normalize_topic_label(...)`
- 支持大小写 / 中英别名统一
- 例如：
  - `大语言模型` -> `llm`
  - `LLM` -> `llm`

### 第三阶段
- 引入 `topic_expander.py`
- 对未知主题调用模型，生成：
  - 英文别名
  - 中文别名
  - 上下位相关表达
  - 论文常见写法

### 第四阶段
- 观察到 3B 模型对未知主题扩展偏弱
- 加入：
  - 二次重试
  - fallback 扩展
  - 轻量启发式扩展（如 document intelligence / time series forecasting）

### 第五阶段
- 进入“只收紧规则，不再扩宽”阶段
- 对未知主题做三层分级：
  - 强别名（strong aliases）
  - 辅助扩展（support terms）
  - 泛弱词（weak terms）
- 目标：
  - 原词强匹配优先
  - 扩展词弱匹配辅助
  - 泛词不能单独放行

---

## 11. `document intelligence` 与 `time series forecasting` 的实际测试结论

### `document intelligence`
调试接口结果已经明显改善，当前扩展中包含：
- `document understanding`
- `document ai`
- `idp`
- `ocr`
- `layout analysis`
- `table extraction`
- `information extraction`
- `key information extraction`

这说明：
- 已经不只是靠原词匹配
- 已具备较好的未知主题扩展能力
- 这一主题已经接近可体验状态

### `time series forecasting`
调试接口结果明显比之前强，扩展中包含：
- `temporal modeling`
- `sequence modeling`
- `trend prediction`
- `time series analysis`
- `univariate forecasting`
- `multivariate forecasting`
- `long horizon forecasting`

这说明：
- 主题扩展链路已经打通
- 但这类主题更容易扩得过宽
- 因此更需要规则收紧来控制泛召回

### 总结判断
当前可以下这个结论：

> **`qwen2.5:3b + 程序 fallback` 已经能满足“日常扩展能力第一版需求”，但未知主题仍需要规则分层控制。**

---

## 12. 7B 模型切换的共识与现状

### 已达成共识
值得尝试把扩展模块从 `qwen2.5:3b` 升到 `qwen2.5:7b`，因为：
- 7B 通常比 3B 更稳
- 对 JSON 输出、别名补全、未知主题扩展更友好
- 本地 Ollama 不按 token 收费，主要是机器资源成本

### 当前已做动作
- 已执行：
  - `ollama pull qwen2.5:7b`

### 重要说明
只执行 `ollama pull qwen2.5:7b` **不等于已经切换到 7B**。
真正切换要满足：
1. `.env` 中设置：
   - `OLLAMA_MODEL=qwen2.5:7b`
2. 重启后端
3. 通过调试接口或日志确认 `llm_client.py` 确实使用 7B

### 当前建议
- 先确认 7B 能正常调用
- 再继续用“规则收紧版” `topic_rules.py` 测试结果
- 当前方向是：

> **更稳一点的扩展模型 + 更收一点的匹配规则**

---

## 13. 当前规则收紧的正式方向（已达成一致）

当前 `topic_rules.py` 的优化方向，不再是继续扩宽，而是：

### 原词 / 强别名优先
例如：
- `document intelligence`
- `document understanding`
- `time series forecasting`

### 高相关扩展辅助
例如：
- `ocr`
- `layout analysis`
- `table extraction`
- `temporal modeling`
- `multivariate forecasting`

### 泛词不能单独放行
例如：
- `analysis`
- `prediction`
- `understanding`
- `model`
- `intelligence`
- `forecast`

### 未知主题收紧原则
- 强别名命中优先放行
- 标题中 query token 命中至少两个且有 support term 才考虑放行
- support term 至少命中两个才放行
- 弱词不能单独放行

---

## 14. 关于“是不是 agent”的共识总结

### 当前判断
现在这套不是单纯“写提示词”，而是：

- 提示词工程
- 工作流编排
- 规则控制
- 中间决策
- 模型输出结构化
- fallback 和重试

### 最准确定位
当前不是完整 agent，而是：

> **LLM 增强的多阶段工作流 / agentic workflow / 轻量论文推荐 agent 雏形**

### 为什么不算完整 agent
还缺：
- 自动规划多条路线
- 自动比较不同策略
- 自动反思为何结果差
- 自动多轮再搜索 / 再检索
- 长期记忆与偏好闭环

但当前这不是后续第一优先级。

---

## 15. 当前暂不做的内容（重要约束）

为了防止发散，已经明确：

### 暂不优先做
- 豆包 API 接入
- 复杂个性化推荐
- 高级重排体系
- PostgreSQL 迁移
- 过早做复杂部署
- 多源融合排序
- 完整反馈闭环

### 原因
因为当前仍处于：

> **先收一个可体验版本，让用户能开始体验，再细致优化。**

---

## 16. 未来确定要做、但按阶段后置的能力

### 1）RAG + 标签树系统
用户明确希望后续一定做，不是被忘了，而是被放在第二代架构升级阶段。

#### 标签树负责
- 主题体系化
- 上下位主题映射
- 用户输入标准化
- 减少完全依赖自由词匹配

#### RAG 负责
- 构建论文 / repo / task / method 知识库
- 做语义召回
- 支持更复杂的检索表达
- 提升解释性和组合筛选能力

#### 放置阶段
- 不应抢在 MVP 前面做
- 应放在：
  - 当前可体验版本跑通之后
  - arXiv 扩源之后
  - 作为 v0.3 / v0.4 的架构升级项

### 2）让其他用户也能使用（本地部署 / 可运行）
用户明确希望尽快看到，不应遗漏。

#### 第一层
先做到“别人拿到代码能在自己电脑上跑”：
- README
- `.env.example`
- `requirements.txt`
- 前后端启动命令
- 环境说明

#### 第二层
再做“局域网 / 服务器部署”：
- API 地址可配置
- 模型地址可配置
- 数据库路径可配置
- `0.0.0.0` 运行
- 前端环境变量配置

### 3）扩展到 arXiv 及更多数据源
用户明确希望后续不止爬取 Hugging Face daily。

#### 当前优先级
- 优先扩到 arXiv
- 再考虑 Papers with Code / OpenReview / GitHub signals

#### 原因
- Hugging Face daily 覆盖太窄
- 真实使用后会很快遇到覆盖不足问题
- arXiv 是最自然、最必要的下一扩展点

---

## 17. 当前正式版本规划（最新统一版本）

### v0.1：可体验版
目标：用户开始体验。

包含：
- 当前主题推荐链路跑稳
- 单主题输入
- Hugging Face daily
- 动态扩展 + 规则过滤 + 轻分析
- 推荐列表展示
- 前端基础体验
- 别人在自己电脑上能跑

### v0.2：可部署试用版
目标：不只开发者自己能用。

包含：
- README / `.env.example`
- 环境整理
- 本地部署说明
- 局域网 / 服务器准备
- 收藏 / 历史 / 基础反馈能力（可选）

### v0.3：扩源版
目标：不止依赖 Hugging Face daily。

包含：
- 接 arXiv
- 多源合并
- 去重
- 更稳定排序

### v0.4：架构升级版
目标：进入第二代系统。

包含：
- 标签树
- RAG 知识库
- 更强主题体系与语义召回
- 多源融合解释性推荐

---

## 18. 当前最应该继续做的事（新聊天接续主线）

如果开启新聊天，最应该无缝继续的主线不是继续发散加功能，而是：

### 立即主线
1. 确认 7B 是否真正切换成功
2. 用“规则收紧版 `topic_rules.py`”测试：
   - `llm`
   - `大语言模型`
   - `document intelligence`
   - `time series forecasting`
3. 判断：
   - 主题扩展是否更稳
   - 规则收紧后是否更准
4. 若稳定，则开始收 v0.1 体验版

### v0.1 收口阶段应做
1. 当前推荐链路跑稳
2. 补前端体验：
   - 空结果提示
   - 少量结果提示
   - loading / error 状态
   - 主题示例
3. 整理项目运行方式：
   - README
   - `.env.example`
   - requirements
   - 启动说明
4. 让别人本地能跑

### v0.1 完成后下一步
5. 接 arXiv
6. 再规划 RAG + 标签树系统

---

## 19. 新聊天可直接复制的接续提示

下面这段可以直接复制到新聊天里，保证流程不断：

> 当前项目是一个论文推荐系统，后端 FastAPI、前端 Next.js 已打通，当前已形成产品主入口 `/papers/daily/run?project_topic=xxx&limit=5`。已完成 Hugging Face daily 抓取、轻分析、推荐展示、主题归一化、动态主题扩展、调试接口 `/debug/topic_expand`。现阶段不再发散加功能，优先确认 `qwen2.5:7b` 是否真正切换成功，并基于“规则收紧版” `topic_rules.py` 继续测试 `llm / 大语言模型 / document intelligence / time series forecasting`。当前正式路线是：先收一个可体验版 v0.1（让用户开始体验、让别人本地能跑），再尽快接 arXiv，后续再做 RAG + 标签树系统、扩展部署与多源融合。后续所有升级路线不要遗漏：v0.1 可体验版 → v0.2 可部署试用版 → v0.3 arXiv 扩源版 → v0.4 RAG + 标签树架构升级版。

---

## 20. 本文件用途说明

本文件用于：
- 新聊天无缝续接
- 防止技术路线遗漏
- 防止后续优化方向跑偏
- 作为当前阶段完整阶段总结与交接说明

