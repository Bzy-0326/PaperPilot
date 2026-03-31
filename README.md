# PaperPilot

[![Next.js](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Python-009688)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Deploy-Docker-blue)](https://www.docker.com/)
[![Bring Your Own API](https://img.shields.io/badge/LLM-BYO%20API-111827)](#快速开始)

> 别再只是囤论文了，先决定下一篇该读什么。

PaperPilot 是一个面向研究者的 AI 论文推荐与决策助手。

它不是再给你一长串原始论文列表，而是帮你：

- 在同一主题下对论文进行排序
- 并排比较几篇候选论文
- 判断哪篇更值得优先投入时间
- 把有价值的论文纳入后续跟进清单

它还会把下载下来的 PDF 自动整理成更易读的文件名，带上标题和日期，后面搜索、保存、归档都会轻松很多。

> 当前默认是 **Demo 模式**，不需要 API Key，也不需要本地模型。建议先搜索 `LLM`、`RAG`、`CoT`、`Reasoning`、`Multimodal`。如果你想做更广的真实主题搜索和实时分析，再切换到你自己的 API Key 或本地 Ollama 模型。

## PaperPilot 想解决什么问题？

大多数论文工具擅长“帮你找到论文”，但真正让人头疼的是找到以后：

- 我到底应该先读哪篇？
- 哪篇更值得精读？
- 哪篇更适合复现？
- 哪些论文值得继续跟进，而不是看完就忘？

PaperPilot 想做的，不是让你收藏更多论文，而是帮你把“发现论文”变成“做阅读决策”。

## 核心能力

- **同主题排序推荐**：不是原始列表，而是更适合阅读决策的排序结果
- **候选论文对比**：把 2 到 3 篇论文放在一起，快速判断先投入哪篇
- **面向决策的详情页**：不只给摘要，还会给推荐结论、背景、方法、创新点和局限性
- **跟进清单**：可以把论文加入待读、复现、选题备选，后续继续处理

## 为什么更贴近真实研究工作流？

- PDF 下载后会自动规范文件名，包含论文标题和日期
- 下载后的论文更容易在本地搜索、整理和归档
- 从“看到论文”到“继续跟进”，整个流程不会在一次浏览后断掉

## Demo 演示

先看这段演示 GIF，可以快速理解产品怎么工作：

![Demo](./docs/assets/demo.gif)

## 产品速览

### 1. 每日推荐

首页会把一个研究主题整理成排序后的推荐结果，展示推荐分、一句话总结和紧凑的操作入口。

![Homepage](./docs/assets/homepage.jpg)

### 2. 论文对比

它不是简单把两篇论文并排摆出来，而是帮助你判断：在当前主题下，哪篇更值得先投入时间。

![Compare View](./docs/assets/compare-page.jpg)

### 3. 详情分析

每篇论文都有更适合做决策的详情页，包含推荐结论、研究背景、摘要、方法、创新点、局限性和复现信息。

![Detail Page](./docs/assets/detail-page.jpg)

### 4. 跟进工作流

你可以把论文加入待读、复现、选题备选，而不是看完一次就丢掉。

<p align="center">
  <img src="./docs/assets/follow-up-reading.png" alt="待读清单" width="32%" />
  <img src="./docs/assets/follow-up-reproduce.png" alt="复现清单" width="32%" />
  <img src="./docs/assets/follow-up-topic.png" alt="选题备选" width="32%" />
</p>

## 为什么不是普通论文搜索工具？

很多工具帮你“搜论文”。
PaperPilot 更关注“接下来该怎么读”。

它不只是列论文，而是帮助你：

- 在同一主题下排序候选论文
- 在深入阅读前先比较多个候选
- 把有价值的论文留在跟进流程里
- 用更易读的文件名保存 PDF，方便后续查找和管理

## 适合谁？

如果你经常会遇到下面这些问题，PaperPilot 会比较适合你：

- 我找到 20 篇论文了，但不知道先读哪 3 篇
- 这几篇看起来都差不多，哪篇对我的项目更有用？
- 哪篇更值得复现？
- 哪些论文应该留下来持续跟进？

## 快速开始

这个仓库优先为“最低上手门槛”设计。

### 你真正需要什么？

“把应用跑起来”和“让推荐分析功能真正工作”是两件事：

- `Docker` 负责把前后端服务跑起来
- `模型能力` 负责完成推荐、分析、对比和跟进推理

所以现在有三条路径：

- `Docker + 内置 Demo`：应用能直接启动，并立刻展示完整产品预览
- `Docker + 你自己的 API Key`：推荐的大多数用户路径，上手最轻
- `Docker + 本地 Ollama 模型`：也能用，但部署更重

### 最轻体验：Docker + 内置 Demo

如果你只是想先看看产品长什么样、流程顺不顺，这是最容易的路径。

你需要：

- Docker Desktop

你不需要：

- API Key
- Ollama
- 本地模型
- Node.js
- Python

运行：

```bash
docker compose up --build
```

然后打开网页，保持默认的 `PaperPilot Demo / no setup`。

为了最清楚地体验产品效果，建议先搜索这些 Demo 主题：

- `LLM`
- `RAG`
- `CoT`
- `Reasoning`
- `Multimodal`

这个模式适合：

- 第一次尝试
- 看截图和 GIF
- GitHub 路人先快速体验产品逻辑

它的限制也要讲清楚：

- 返回的是内置样例推荐，不是实时大模型分析
- 更适合看产品流程，不适合评估真实推荐质量
- 对 `LLM`、`RAG`、`CoT`、`Reasoning`、`Multimodal` 这类预览主题效果最好
- 如果你想做更广的主题搜索、实时推荐生成和真实分析结果，还是需要自己的 API Key 或本地 Ollama 模型

### 推荐路径：Docker + 你自己的 API Key

这是最适合大多数用户的正式使用方式。

你不需要：

- Ollama
- 本地 7B 模型下载
- Node.js
- Python

你需要：

- Docker Desktop
- 你自己的 API Key，例如 `DeepSeek`、`Kimi`、`Qwen` 或其他 OpenAI-compatible 服务

运行：

```bash
docker compose up --build
```

然后打开：

- 前端：[http://localhost:3000](http://localhost:3000)
- 后端文档：[http://localhost:8000/docs](http://localhost:8000/docs)

进入应用后：

1. 打开 `模型设置`
2. 选择 `DeepSeek`、`Kimi`、`Qwen` 或其他 OpenAI-compatible API
3. 填入自己的 API Key
4. 输入一个主题，例如 `CoT`、`LLM`、`RAG`、`Reasoning`、`Multimodal`
5. 开始使用

为什么推荐这条路：

- 部署门槛最低
- 不需要下载本地模型
- 跨平台体验更好
- 更适合 GitHub 用户

缺点：

- 需要自己的 API Key
- 依赖外部模型服务可用性
- 模型调用成本取决于 provider

通常来说，在 Top 3 / Top 5 这种轻量日常推荐场景里，API 消耗不会特别高。具体成本还是取决于 provider、模型和你的使用频率。

### 如果你没有自己的 API Key

你仍然可以先用内置 Demo 模式体验完整产品流程。

如果你不想用 API Key，但又想要真实推荐和分析结果，那么替代方案就是：

- 安装 `Ollama`
- 下载一个本地模型
- 使用本地推理路径运行产品

只是这条路的门槛会明显高于默认的公开使用方式。

## 部署模式

### 1. Demo / 预览模式

适合：

- 第一次访问的用户
- 快速看产品效果
- 截图、GIF、演示
- 还没准备模型能力，但想先体验界面的人

需要：

- Docker

优点：

- 不用配模型
- 不用 API Key
- 体验完整 UI 和工作流最快

缺点：

- 返回的是内置样例推荐
- 不适合评估真实推荐质量

推荐：

- 作为 GitHub 路人的第一体验路径

### 2. 公开 / 轻量模式

适合：

- 第一次正式使用的用户
- GitHub 访客
- 演示和跨平台体验

需要：

- Docker
- 你自己的 API Key

优点：

- 上手最轻
- 不用下载本地模型
- Windows / macOS 体验都更好

缺点：

- 需要 API Key
- 依赖第三方模型服务

推荐：

- 这是大多数用户在体验完 Demo 后最应该切换到的正式路径

### 3. 进阶本地模式

适合那些明确想做本地推理、而且不想依赖外部 API 的用户。

需要：

- Docker
- Ollama
- 一个本地模型，比如 `qwen2.5:7b`

示例：

```bash
ollama pull qwen2.5:7b
```

然后在应用里使用：

- provider: `ollama`
- model: `qwen2.5:7b`
- base URL: `http://localhost:11434`

优点：

- 不需要外部 API Key
- 更适合本地私有化使用

缺点：

- 部署更重
- 本地模型体积较大
- 对第一次使用者不够友好

推荐：

- 只有当你明确要本地推理时再选这条路

### 4. 开发模式

只有当你想修改代码时再用这条路。

这不是默认的公开上手路径。

#### Windows

前端：

```bash
cd paper-reader-ui
start_frontend.bat
```

后端：

```bash
cd paper-reader-v1
start_backend.bat
```

#### macOS / Linux

前端：

```bash
cd paper-reader-ui
./start_frontend.sh
```

后端：

```bash
cd paper-reader-v1
./start_backend.sh
```

说明：

- `.bat` 是 Windows 便捷脚本
- `.sh` 是 macOS / Linux 脚本
- 如果你只是想用产品，优先走 Docker，而不是本地开发环境

## 技术栈

### 前端

- Next.js
- TypeScript

### 后端

- FastAPI
- SQLite

### 模型层

- OpenAI-compatible API providers
- 可选 Ollama 本地推理

## 为什么先用 SQLite

这个项目故意保持轻量，方便：

- 演示
- GitHub 分享
- 本地产品展示
- 快速第一次部署

如果后续有更大的持久化需求，高级用户可以自行切换到外部数据库。

参考：

- [`paper-reader-v1/.env.example.txt`](./paper-reader-v1/.env.example.txt)

## 仓库结构

```text
paper-project/
|- README.md
|- LICENSE
|- .gitignore
|- docker-compose.yml
|- docs/
|- paper-reader-ui/
|- paper-reader-v1/
`- paper-reader skill/
```

## 这个开源项目想表达什么

它不只是代码堆在一起，而是想展示一种产品思考：

- 不是原始列表，而是排序
- 不是只有发现，而是决策支持
- 不是一次性浏览，而是跟进工作流
- 不是环境很重的原型，而是可以部署的产品
- 不是混乱下载，而是更适合保存的 PDF 文件管理

## 开源协议

MIT
