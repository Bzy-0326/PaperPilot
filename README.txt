# Paper Reader 本地开发与协作说明

这是一个前后端分离的本地开发版项目。

## 项目结构

- `paper-reader-ui`：前端（Next.js）
- `paper-reader-v1`：后端（FastAPI / Python）

---

## 当前已验证环境

### 前端环境
- Node.js：`v24.14.0`
- npm：`11.9.0`

### 后端环境
- Python：`3.11`

> 注意：
> 后端建议固定使用 Python 3.11。
> Python 3.13 可能会在安装 `tokenizers` 等依赖时失败。

---

## 一、给新电脑使用前要安装的东西

### 1. 安装 Node.js
安装与你当前一致的版本，或尽量接近：

- Node.js `v24.14.0`

安装完成后，在终端执行：

```bash
node -v
npm -v