# 🌍 智能旅行规划助手 — 对话版

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.x-61DAFB.svg)](https://react.dev/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.x-1C3C3C.svg)](https://www.langchain.com/langgraph)

> 基于 AI 对话的智能旅行规划器 — 像跟旅行规划师聊天一样，边聊边规划、随时调整行程

## ✨ 核心特性

- **💬 对话式交互** — 豆包/DeepSeek 风格的移动端对话界面，像聊天一样规划旅行
- **🧠 多 Agent 协作** — LangGraph StateGraph 编排：意图识别 → 需求提取 → 工具调用 → 行程生成
- **📊 实时执行日志** — 每个工具调用/节点执行通过 SSE 实时推送，前端可展开查看
- **🔄 动态调整** — "第二天换成西湖" — 增量重规划，只改受影响的天数
- **💰 三档方案** — 经济/舒适/豪华，按预算灵活选择
- **🗺️ 高德地图集成** — 景点搜索、天气查询、酒店推荐、路线规划全覆盖

## 🏗️ 系统架构

```
用户 ←→ 前端 (React H5)
         │ POST + SSE
         ▼
     FastAPI → SSE Bridge → LangGraph StateGraph
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
   intent_router      extract_requirements    answer_question
         │                    │                    │
         └────────┬───────────┘                    │
                  ▼                                │
           gather_data                             │
          (并行调用高德工具)                          │
                  │                                │
                  ▼                                │
           generate_plan                           │
          (三档并行 LLM 生成)                        │
                  │                                │
                  ▼                                │
           present_plan ─────────── replan ────────┘
                                  (增量调整)
```

### SSE 事件流

| 事件 | 触发时机 | 前端作用 |
|------|----------|----------|
| `chat_token` | LLM 输出每个 token | 流式渲染文字 |
| `node_enter` / `node_exit` | LangGraph 节点开始/结束 | 显示节点状态 |
| `tool_call` / `tool_result` | 工具调用开始/返回 | ToolCallCard 状态更新 |
| `chat_message_done` | 消息生成完毕 | 关闭流式态 |
| `plan_generated` | 行程生成完成 | 展示 PlanCard |

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- 高德地图 API Key（Web服务 + Web端JS API）
- LLM API Key（OpenAI 兼容接口，支持 DeepSeek 等）

### 后端

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入高德 Key 和 LLM Key
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

打开 http://localhost:3000/travel

## 📡 API 接口

### 对话接口（新）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat` | 创建新对话，返回 `thread_id` |
| POST | `/api/chat/{thread_id}` | 发送消息，返回 SSE 事件流 |
| GET | `/api/chat/{thread_id}/history` | 获取对话历史 |
| GET | `/api/chat/{thread_id}/plan` | 获取当前行程计划 |
| POST | `/api/chat/{thread_id}/reset` | 重置对话 |

### 传统接口（保留兼容）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/plan` | 创建规划任务 |
| GET | `/api/plan/{task_id}/status` | SSE 进度推送 |
| GET | `/api/plan/{task_id}/result` | 获取规划结果 |

## 📁 项目结构

```
backend/
├── app/
│   ├── main.py                    # FastAPI 入口
│   ├── config.py                  # 配置管理
│   ├── api/
│   │   ├── routes.py              # 旧 REST 端点（保留兼容）
│   │   └── chat_routes.py         # 新对话 API
│   ├── graph/                     # LangGraph 核心
│   │   ├── state.py               # GraphState 定义
│   │   ├── builder.py             # StateGraph 构建
│   │   ├── router.py              # 条件路由
│   │   ├── tools.py               # 高德工具注册
│   │   ├── checkpointer.py        # 记忆持久化
│   │   ├── nodes/                 # 图节点
│   │   │   ├── intent_router.py   # 意图分类
│   │   │   ├── greeting.py        # 问候
│   │   │   ├── extract_requirements.py  # 需求提取
│   │   │   ├── gather_data.py     # 数据采集
│   │   │   ├── generate_plan.py   # 行程生成
│   │   │   ├── present_plan.py    # 结果展示
│   │   │   ├── answer_question.py # 问答
│   │   │   └── replan.py          # 增量重规划
│   │   └── prompts/               # 提示词模板
│   ├── llm/factory.py             # LLM 统一工厂
│   ├── mcp/                       # 高德 MCP 工具层
│   ├── schemas/                   # Pydantic 模型
│   ├── services/
│   │   ├── task_manager.py        # SSE 任务管理
│   │   └── sse_bridge.py          # LangGraph → SSE 桥接
│   └── utils/budget.py            # 预算计算
└── requirements.txt

frontend/
├── src/
│   ├── App.tsx                    # 路由（含 /chat/*）
│   ├── pages/
│   │   ├── HomePage.tsx           # 首页（对话入口 + 传统表单）
│   │   ├── ChatPage.tsx           # 对话主页面
│   │   └── PlanningPage.tsx       # 旧规划页（保留）
│   ├── components/chat/           # 对话 UI 组件
│   │   ├── ChatHeader.tsx         # 顶部栏
│   │   ├── ChatInput.tsx          # 输入框
│   │   ├── MessageList.tsx        # 消息列表
│   │   ├── MessageBubble.tsx      # 消息气泡（含 react-markdown）
│   │   ├── ToolCallCard.tsx       # 工具调用卡片
│   │   ├── PlanCard.tsx           # 行程卡片
│   │   ├── WelcomeSuggestions.tsx # 快捷提示
│   │   └── TypingIndicator.tsx    # 输入指示器
│   ├── hooks/useChat.ts           # 对话 hook（SSE + 流式）
│   └── types/chat.ts              # 对话类型定义
└── package.json
```

## 🔑 环境变量

### 后端

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `AMAP_API_KEY` | 高德 Web服务 Key | - |
| `LLM_API_KEY` | LLM API Key | - |
| `LLM_BASE_URL` | LLM API 地址 | `https://api.openai.com/v1` |
| `LLM_MODEL` | 模型名称 | `gpt-4o` |
| `LLM_MEMORY_DB` | 对话记忆数据库路径 | `travel_plans.db` |

### 前端

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `VITE_AMAP_KEY` | 高德 Web端(JS API) Key | - |

## 🛠️ 技术栈

**前端**: React 18 + Vite + TypeScript + TailwindCSS + react-markdown
**后端**: Python FastAPI + LangChain + LangGraph + httpx
**外部**: 高德地图 Web API (POI/天气/路径规划)
**记忆**: MemorySaver（开发）→ SqliteSaver（生产）

## 📝 License

MIT
