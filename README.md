# 🌍 智能旅行规划助手

> 输入需求，一键生成专属行程 — 基于多 Agent 协作的智能旅行规划 H5 应用

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.x-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6.svg)](https://www.typescriptlang.org/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.x-06B6D4.svg)](https://tailwindcss.com/)
[![LangChain](https://img.shields.io/badge/LangChain-latest-1C3C3C.svg)](https://www.langchain.com/)

## ✨ 功能特性

- **智能行程规划** — 输入出发地、目的地、预算、出行方式、天数、偏好，AI 自动生成完整行程
- **四 Agent 协作** — 景点搜索、天气查询、酒店推荐、规划协调四个 Agent 分工协作
- **三档预算方案** — 经济/舒适/豪华三套方案自由切换，严格控制预算
- **每日路线地图** — 高德地图标注当天景点位置 + 游览路线连线
- **实时进度反馈** — SSE 流式推送每个 Agent 的工作状态
- **长截图导出** — 一键导出完整行程为 PNG 图片

## 🏗️ 系统架构

```
React H5 (前端)
    │  HTTP + SSE
FastAPI (后端)
    │  LangChain + LangGraph
Agent 层 (4个 Agent)
    │  MCP Protocol
高德地图 API (外部服务)
```

### 四层架构

| 层 | 技术栈 | 职责 |
|---|--------|------|
| 前端 | React 18 + Vite + TailwindCSS + TypeScript | 表单填写、SSE 进度监听、结果渲染、长截图导出 |
| 后端 | Python FastAPI + Pydantic | 请求校验、Agent 调度、SSE 推送、结果聚合 |
| Agent 层 | LangChain + LangGraph + MCP SDK | 景点搜索、天气查询、酒店推荐、行程规划 |
| 外部服务 | 高德地图 Web API + JS API 2.0 | POI 搜索、天气、路径规划、静态地图 |

### Agent 编排流程

```
用户请求
  ├── 并行执行 ──┬── 景点搜索 Agent → 高德 POI 2.0
  │              ├── 天气查询 Agent → 高德天气 API
  │              └── 酒店推荐 Agent → 高德周边搜索
  │
  └── 串行执行 ──── 规划协调 Agent → 生成三档方案
```

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- 高德地图 API Key（[申请地址](https://console.amap.com/dev/key/app)）
- LLM API Key（OpenAI 兼容接口）

### 后端启动

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入：
#   AMAP_API_KEY=你的高德Key
#   LLM_API_KEY=你的LLM Key
#   LLM_BASE_URL=https://api.openai.com/v1
#   LLM_MODEL=gpt-4o

# 启动服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 修改高德 JS API Key
# 编辑 index.html，将 YOUR_AMAP_KEY 替换为实际 Key
# 编辑 src/App.tsx，将 AMAP_KEY 替换为实际 Key

# 启动开发服务器
npm run dev
```

打开浏览器访问 http://localhost:3000

### 生产构建

```bash
# 前端构建
cd frontend && npm run build

# 后端部署（使用 gunicorn）
cd backend && gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

## 📡 API 接口

### POST /api/plan — 创建规划任务

```json
// Request
{
  "origin": "上海",
  "destination": "杭州",
  "budget": 3000,
  "intercity_mode": "high_speed_rail",
  "city_transit": "mixed",
  "days": 3,
  "preferences": ["nature", "history"],
  "start_date": "2026-06-20"
}

// Response
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2026-06-05T10:00:00Z"
}
```

### GET /api/plan/{task_id}/status — SSE 实时进度

```
event: agent_started
data: {"agent": "attractions"}

event: agent_completed
data: {"agent": "attractions", "found": 15}

event: task_done
data: {"status": "completed"}
```

### GET /api/plan/{task_id}/result — 获取规划结果

返回完整的三档（经济/舒适/豪华）行程方案，包含每日景点、酒店、餐饮、交通、天气和路线坐标。

## 📁 项目结构

```
smart-travel-planning/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI 应用入口
│   │   ├── config.py                  # 配置管理
│   │   ├── api/routes.py              # API 路由
│   │   ├── schemas/                   # Pydantic 数据模型
│   │   │   ├── request.py             # 请求模型
│   │   │   └── response.py            # 响应模型
│   │   ├── agents/                    # Agent 层
│   │   │   ├── attraction_agent.py    # 景点搜索 Agent
│   │   │   ├── weather_agent.py       # 天气查询 Agent
│   │   │   ├── hotel_agent.py         # 酒店推荐 Agent
│   │   │   ├── planner_agent.py       # 规划协调 Agent
│   │   │   └── orchestrator.py        # Agent 编排器
│   │   ├── mcp/                       # MCP 工具层
│   │   │   ├── tools.py               # MCP Tool 定义
│   │   │   └── amap_client.py         # 高德 API 客户端
│   │   ├── services/task_manager.py   # 任务状态 + SSE
│   │   └── utils/budget.py            # 预算分档计算
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx                    # 根组件
│   │   ├── components/
│   │   │   ├── Header.tsx             # 页面头部
│   │   │   ├── PlanForm.tsx           # 规划表单
│   │   │   ├── ProgressPanel.tsx      # Agent 进度面板
│   │   │   ├── ResultPanel.tsx        # 结果面板（三档Tab）
│   │   │   ├── DailyCard.tsx          # 每日行程卡片
│   │   │   ├── DailyMap.tsx           # 每日路线地图
│   │   │   ├── CostSummary.tsx        # 费用总览
│   │   │   └── ExportButton.tsx       # 长截图导出
│   │   ├── hooks/usePlan.ts           # 规划状态 Hook
│   │   ├── api/client.ts              # API 客户端
│   │   └── types/plan.ts              # TypeScript 类型
│   ├── index.html
│   └── package.json
│
└── docs/
    └── superpowers/
        ├── specs/...-design.md        # 系统设计文档
        └── plans/...-plan.md          # 实施计划
```

## 🔑 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `AMAP_API_KEY` | 高德地图 Web API Key | - |
| `LLM_API_KEY` | LLM API Key | - |
| `LLM_BASE_URL` | LLM API 地址 | `https://api.openai.com/v1` |
| `LLM_MODEL` | 模型名称 | `gpt-4o` |
| `HOST` | 服务监听地址 | `0.0.0.0` |
| `PORT` | 服务端口 | `8000` |

## 🛠️ 技术栈

**前端**
- React 18 + TypeScript
- Vite 5
- TailwindCSS 3
- 高德 Maps JS API 2.0
- html2canvas（长截图导出）

**后端**
- Python FastAPI
- LangChain + LangGraph
- MCP Python SDK
- Pydantic v2
- httpx（异步 HTTP）

**外部 API**
- 高德 POI 2.0（景点/酒店搜索）
- 高德天气 API
- 高德路径规划 API
- 高德静态图 API

## 📝 License

MIT

---

🤖 由 AI Agent 协作构建 · 数据来源高德地图 · 规划结果仅供参考
