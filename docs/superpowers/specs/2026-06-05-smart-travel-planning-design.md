# 智能旅行规划助手 — 系统设计文档

**日期**: 2026-06-05  
**状态**: 已确认  
**技术栈**: React + FastAPI + LangChain/LangGraph + MCP + 高德地图 API

---

## 1. 项目概述

智能旅行规划助手是一个移动端 H5 页面，用户输入出发地、目的地、预算、出行方式、出行天数、旅行偏好等参数后，系统调用多个 AI Agent 并行查询景点、天气、酒店信息，最后由规划协调 Agent 整合生成包含经济/舒适/豪华三档方案的完整行程。

## 2. 核心决策

| 维度 | 决策 |
|------|------|
| 酒店数据 | 高德周边搜索 POI 为主 + 预留 OTA 数据接口 |
| 预算控制 | 经济/舒适/豪华 三档方案，用户自由切换对比 |
| 出行方式 | 城市间交通(飞机/高铁/自驾/大巴) + 目的地内交通(公交/地铁/打车/租车/步行) |
| 用户系统 | 无需登录，纯工具型 |
| 导出功能 | html2canvas 完整长截图导出（含每日路线地图） |
| 每日地图 | 高德 JS API 在 Day Card 中嵌入迷你地图，标注景点位置+连线 |
| 页面结构 | 单页滚动式（表单 → 加载动画 → 结果展示） |
| 视觉风格 | 清新旅行风，蓝绿自然色调，圆角卡片 |
| 技术栈 | 全 Python 后端（FastAPI），放弃 Node.js |

## 3. 系统架构

### 3.1 四层架构总览

```
┌──────────────────────────────────────────────────────────┐
│                    Frontend (React H5)                     │
│  表单填写 → SSE进度监听 → 三档方案切换 → 长截图导出        │
└──────────────────────┬───────────────────────────────────┘
                       │ HTTP + SSE
┌──────────────────────▼───────────────────────────────────┐
│                Backend (Python FastAPI)                    │
│  请求校验 → Agent调度 → SSE进度推送 → 结果聚合              │
└──────────────────────┬───────────────────────────────────┘
                       │ LangChain + LangGraph
┌──────────────────────▼───────────────────────────────────┐
│                    Agent Layer                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┐ │
│  │ 景点搜索  │ │ 天气查询  │ │ 酒店推荐  │ │  规划协调    │ │
│  │  Agent   │ │  Agent   │ │  Agent   │ │   Agent     │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬──────┘ │
│       └─────────────┴────────────┴──────────────┘         │
│              并行执行（前三个），串行等待（协调）            │
└──────────────────────┬───────────────────────────────────┘
                       │ MCP Protocol (Python SDK)
┌──────────────────────▼───────────────────────────────────┐
│               External Services                            │
│  高德POI搜索 │ 高德天气 │ 高德路径规划 │ OTA酒店数据(预留)  │
└──────────────────────────────────────────────────────────┘
```

### 3.2 技术栈明细

| 层 | 技术 | 版本建议 | 说明 |
|---|------|---------|------|
| 前端框架 | React | 18.x | 函数组件 + Hooks |
| 构建工具 | Vite | 5.x | 快速 HMR |
| CSS | TailwindCSS | 3.x | 移动端响应式 |
| HTTP 客户端 | axios | 1.x | 请求 + SSE 流 |
| 长截图 | html2canvas | 1.x | 前端截图导出 |
| 地图 | 高德 Maps JS API | 2.0 | 每日迷你路线图 |
| 后端框架 | FastAPI | 0.115+ | 异步原生支持 SSE |
| 异步任务 | asyncio + BackgroundTasks | — | Python 标准库 |
| Agent 框架 | LangChain + LangGraph | 最新稳定版 | Agent 编排 + 工具调用 |
| MCP | mcp (Python SDK) | 最新版 | 标准化 Tool 协议 |
| HTTP 客户端 | httpx | 0.27+ | 异步请求高德 API |
| 数据校验 | Pydantic | 2.x | FastAPI 原生集成 |
| 外部 API | 高德地图 Web API | — | POI、天气、路径规划 |

## 4. Agent 设计

### 4.1 景点搜索 Agent

- **职责**: 根据目的地、出行天数、旅行偏好，搜索并推荐景点
- **MCP Tool 封装**: 
  - `search_attractions(keyword, city, radius)` → 调用高德 POI 2.0 周边搜索
  - `get_attraction_detail(poi_id)` → 调用高德 POI 详情查询
- **输入**: 目的地城市、坐标范围、偏好标签（自然风光/历史文化/美食购物/亲子休闲）
- **输出**: 景点列表（名称、坐标、评分、门票价格、建议游玩时长、分类标签）

### 4.2 天气查询 Agent

- **职责**: 查询出行期间的天气情况，给出出行建议
- **MCP Tool 封装**:
  - `get_weather_forecast(city, start_date, end_date)` → 调用高德天气 API
- **输入**: 目的地城市、出行日期范围
- **输出**: 每日天气（日期、温度高低、天气状况、降雨概率、风力、穿衣建议）

### 4.3 酒店推荐 Agent

- **职责**: 根据目的地、预算档位、景点分布推荐住宿
- **MCP Tool 封装**:
  - `search_hotels(city, location, radius, price_range)` → 高德周边搜索 + 酒店 POI 数据
  - `get_hotel_detail(hotel_id)` → 酒店详细信息
- **输入**: 目的地、景点坐标列表、预算档位(经济/舒适/豪华)
- **输出**: 酒店候选（名称、位置坐标、价格区间、评分、距主要景点距离、推荐入住天数）

### 4.4 规划协调 Agent

- **职责**: 整合前三个 Agent 的结果，结合出发地和出行方式，生成完整行程
- **MCP Tool 封装**:
  - `plan_route(origin, destination, waypoints, travel_mode)` → 高德路径规划 API
  - `calculate_transit(origin, dest, city)` → 城市间 + 市内交通计算
- **输入**: 前三个 Agent 的全部输出 + 出发地 + 出行方式 + 总预算
- **输出**: 
  - 按天划分的详细行程（景点顺序、交通方式、入住酒店、餐饮建议）
  - 经济/舒适/豪华三档方案
  - 每日花费明细 + 总花费概算
  - 预算使用率(%)

### 4.5 Agent 编排流程（LangGraph）

```
用户请求 → start
              │
              ├── 并行执行 ──┐
              │  景点搜索Agent │
              │  天气查询Agent │
              │  酒店推荐Agent │
              │              ┘
              │  等待全部完成
              │              │
              └── 规划协调Agent
                              │
                              └── 生成三档方案 → 返回结果
```

前三个 Agent 无依赖关系，并行执行。规划协调 Agent 等待前三个完成后串行执行。

## 5. 数据流

### 5.1 请求流程

```
1. 用户填表 → POST /api/plan
   Body: {
     origin: "上海",
     destination: "杭州",
     budget: 3000,
     travel_mode: "高铁+打车",
     days: 3,
     preferences: ["自然风光", "历史文化"],
     start_date: "2026-06-20"
   }

2. FastAPI 校验参数 → 生成 task_id → 返回 { task_id: "uuid" }

3. 后台异步执行 Agent 编排，每个 Agent 完成/失败时更新进度状态

4. 前端 GET /api/plan/{task_id}/status (SSE)
   实时接收进度事件：
   - agent_started: { agent: "attractions" }
   - agent_progress: { agent: "attractions", message: "搜索到15个景点" }
   - agent_completed: { agent: "attractions", result_preview: {...} }
   - agent_failed: { agent: "weather", error: "API超时" }
   - planning_started: {}
   - planning_completed: {}
   - task_done: { result_id: "..." }

5. 前端收到 task_done → GET /api/plan/{task_id}/result
   返回完整三档方案 JSON

6. 前端渲染结果 → 用户切换档位 → 导出长截图
```

### 5.2 状态管理（后端）

```python
# 任务状态机
TaskStatus = {
    "pending": "等待开始",
    "running": "Agent执行中",
    "attractions_done": "景点搜索完成",
    "weather_done": "天气查询完成",
    "hotels_done": "酒店推荐完成",
    "planning": "行程规划中",
    "completed": "已完成",
    "failed": "失败"
}
```

## 6. API 设计

### 6.1 POST /api/plan

创建规划任务。

**Request:**
```json
{
  "origin": "上海",
  "destination": "杭州",
  "budget": 3000,
  "travel_mode": "high_speed_rail+taxi",
  "days": 3,
  "preferences": ["nature", "history"],
  "start_date": "2026-06-20"
}
```

**Response:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2026-06-05T10:00:00Z"
}
```

### 6.2 GET /api/plan/{task_id}/status

SSE 端点，实时推送任务进度。

**Event types:**
```
event: agent_started
data: {"agent": "attractions", "timestamp": "..."}

event: agent_completed
data: {"agent": "attractions", "found": 15, "timestamp": "..."}

event: task_done
data: {"status": "completed", "result_id": "..."}

event: task_failed
data: {"status": "failed", "error": "Agent execution failed", "timestamp": "..."}
```

### 6.3 GET /api/plan/{task_id}/result

获取完整规划结果（三档方案）。

**Response:**
```json
{
  "task_id": "...",
  "input": { /* 用户输入参数 */ },
  "weather": { /* 每日天气数据 */ },
  "plans": {
    "economy": {
      "daily_plans": [
        {
          "day": 1,
          "date": "2026-06-20",
          "attractions": [
            {"name": "西湖", "duration": "3h", "ticket": 0, "time_slot": "09:00-12:00"}
          ],
          "hotel": {"name": "如家快捷", "price": 180, "location": "..."},
          "meals": [{"type": "lunch", "suggestion": "楼外楼", "estimated_cost": 60}],
          "transport": [{"from": "上海", "to": "杭州", "mode": "高铁", "cost": 73}],
          "daily_cost": 358
        }
      ],
      "total_cost": 2380,
      "budget_usage": 79.3
    },
    "comfort": { /* 同上结构 */ },
    "luxury": { /* 同上结构 */ }
  }
}
```

## 7. 预算三档方案设计

| 维度 | 经济档 | 舒适档 | 豪华档 |
|------|--------|--------|--------|
| 酒店/晚 | ≤200 元 | 200-500 元 | 500+ 元 |
| 餐饮/天 | 50-80 元 | 100-200 元 | 200-400 元 |
| 市内交通 | 公交/地铁为主 | 打车+地铁混合 | 专车/租车 |
| 景点选择 | 免费景点优先 | 性价比景点 | 全部包含 |
| 城市间交通 | 火车硬座/二等座 | 高铁二等座 | 高铁一等座/飞机 |

## 8. 前端设计

### 8.1 页面结构（单页滚动）

```
┌─────────────────────────────┐
│     🌍 智能旅行规划          │  ← Header
│     一键生成专属行程         │
├─────────────────────────────┤
│  表单卡片                    │
│  📍 出发地        [____]    │
│  🎯 目的地        [____]    │
│  💰 总预算        [____]    │
│  🚗 出行方式      [选择]    │
│  📅 出行日期      [日期]    │
│  📆 出行天数      [选择]    │
│  🏷️ 旅行偏好      [多选标签] │
│         [🚀 开始规划]        │
├─────────────────────────────┤
│  加载/进度区 (条件渲染)       │
│  ● 景点搜索 Agent 工作中...  │
│  ✅ 景点搜索完成 (15个景点)   │
│  ✅ 天气查询完成              │
│  🔄 酒店推荐中...            │
│  ⏳ 等待规划协调...           │
├─────────────────────────────┤
│  结果区 (条件渲染)            │
│  ┌─ Tab 切换 ─────────────┐ │
│  │ [经济 ¥2,380] [舒适] [豪华] │ │
│  └────────────────────────┘ │
│                              │
│  ┌─ Day 1 ─────────────────┐│
│  │ 📅 6月20日 杭州           ││
│  │ 🌤 晴 22°C~30°C          ││
│  │ 🚄 上海→杭州 高铁 73元    ││
│  │                          ││
│  │ ┌── 路线地图 ──────────┐ ││
│  │ │  🗺 高德迷你地图     │ ││
│  │ │  ①─→②─→③─→④       │ ││
│  │ │  景点标记+连线      │ ││
│  │ └────────────────────┘ ││
│  │                          ││
│  │ 🏛 ① 09:00 西湖 (免费·3h)││
│  │ 🍜    12:00 楼外楼 (~60)  ││
│  │ 🏯 ② 14:00 灵隐寺 (45·2h)││
│  │ 🏨 ③ 17:00 如家快捷(180)  ││
│  │ 💰 今日: ¥358             ││
│  └──────────────────────────┘│
│  ┌─ Day 2 ... ─────────────┐│
│  ┌─ Day 3 ... ─────────────┐│
│                              │
│  ┌─ 费用总览 ──────────────┐│
│  │ 交通: ¥580  住宿: ¥540  ││
│  │ 门票: ¥210  餐饮: ¥350  ││
│  │ 总计: ¥1,680/预算¥3,000 ││
│  │ ████████░░░░  56%       ││
│  └──────────────────────────┘│
│         [📥 导出长截图]       │
└─────────────────────────────┘
```

### 8.2 视觉风格

- **主色调**: 蓝绿渐变 (#3B82F6 → #10B981)，呼应旅行自然感
- **背景**: 浅灰绿 (#F0FDF4) + 白色卡片
- **卡片**: 圆角 16px，轻微阴影，毛玻璃效果
- **字体**: 系统默认中文字体栈，标题加粗
- **图标**: emoji + SVG 图标混用
- **动画**: 进度条脉冲动画、卡片滑入、档位切换淡入淡出

### 8.3 组件树

```
App
├── Header (logo + 标题)
├── PlanForm (表单卡片)
│   ├── CityInput (出发地/目的地，支持城市搜索)
│   ├── BudgetInput (预算滑块/输入)
│   ├── TravelModeSelect (出行方式多选)
│   ├── DatePicker (出行日期选择)
│   ├── DaysSelect (天数选择 1-15)
│   ├── PreferenceTags (偏好标签多选: 自然风光/历史文化/美食购物/亲子休闲)
│   └── SubmitButton (开始规划，loading态)
├── ProgressPanel (Agent进度，条件渲染)
│   └── AgentProgressItem × 4 (每个Agent的状态行)
├── ResultPanel (结果区，条件渲染)
│   ├── PlanTabs (经济/舒适/豪华 三档切换)
│   ├── DailyCard × N (每日行程卡片)
│   │   ├── WeatherBadge (天气标识)
│   │   ├── DailyMap (高德迷你地图，标注景点+连线)
│   │   ├── TransportItem (交通项)
│   │   ├── AttractionItem × N (景点项，带编号)
│   │   ├── MealItem × N (餐饮项)
│   │   ├── HotelItem (酒店项)
│   │   └── DayCostSummary (当日花费)
│   ├── CostSummary (费用总览 + 进度条)
│   └── ExportButton (导出长截图)
└── Footer (版权 + 数据来源标注)
```

### 8.4 每日路线地图

每个 Day Card 内嵌入一张迷你路线地图，使用高德 Maps JS API 2.0 渲染。

**实现方式:**
- 每个 DailyCard 挂载时，用当天的景点坐标列表初始化一个高德 Map 实例
- 地图尺寸固定为卡片全宽 × 180px，禁用缩放/拖拽（静态快照模式）
- 按游览顺序在景点位置添加带编号的 Marker（① ② ③ ...）
- 用 Polyline 按顺序连线，箭头方向表示游览路线
- 酒店位置用特殊图标标注（🏨）

**导出处理:**
- html2canvas 无法直接截取 WebGL/Canvas 渲染的地图瓦片
- 解决方案：导出时调用高德静态图 API 替换动态地图
  - `GET https://restapi.amap.com/v3/staticmap?markers=...&path=...&key=...`
  - 生成静态图片替代 canvas 地图，确保长截图中地图完整可见
- 导出流程：点击导出 → 所有 DailyMap 切换为静态图模式 → html2canvas 截图 → 恢复动态地图

**API 响应补充（每个 Day Plan 增加坐标点序列）:**
```json
{
  "day": 1,
  "route_coordinates": [
    {"lng": 120.14, "lat": 30.24, "name": "西湖", "type": "attraction", "order": 1},
    {"lng": 120.12, "lat": 30.23, "name": "灵隐寺", "type": "attraction", "order": 2},
    {"lng": 120.16, "lat": 30.25, "name": "如家快捷", "type": "hotel", "order": 3}
  ]
}
```

### 8.5 导出长截图流程

```
用户点击导出
  → 所有 DailyMap 切换为高德静态图 <img> (瞬时)
  → 等待所有图片加载完成
  → html2canvas 渲染整个 ResultPanel
  → 生成 PNG 下载
  → 恢复动态地图
```

## 9. 项目目录结构

```
smart-travel-planning/
├── frontend/                     # React H5 前端
│   ├── src/
│   │   ├── components/           # UI 组件
│   │   │   ├── Header.tsx
│   │   │   ├── PlanForm.tsx
│   │   │   ├── ProgressPanel.tsx
│   │   │   ├── ResultPanel.tsx
│   │   │   ├── DailyCard.tsx
│   │   │   ├── DailyMap.tsx
│   │   │   ├── CostSummary.tsx
│   │   │   └── ExportButton.tsx
│   │   ├── hooks/                # 自定义 Hooks
│   │   │   ├── useSSE.ts         # SSE 进度监听
│   │   │   └── usePlan.ts        # 规划请求管理
│   │   ├── api/                  # API 调用层
│   │   │   └── client.ts
│   │   ├── types/                # TypeScript 类型
│   │   │   └── plan.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── package.json
│
├── backend/                      # Python FastAPI 后端
│   ├── app/
│   │   ├── main.py               # FastAPI 应用入口
│   │   ├── config.py             # 配置管理（API Key 等）
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py         # API 路由定义
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── request.py        # 请求 Pydantic 模型
│   │   │   └── response.py       # 响应 Pydantic 模型
│   │   ├── agents/               # Agent 层
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py   # LangGraph Agent 编排
│   │   │   ├── attraction_agent.py
│   │   │   ├── weather_agent.py
│   │   │   ├── hotel_agent.py
│   │   │   └── planner_agent.py  # 规划协调 Agent
│   │   ├── mcp/                  # MCP Tool 层
│   │   │   ├── __init__.py
│   │   │   ├── tools.py          # MCP Server + Tool 注册
│   │   │   └── amap_client.py    # 高德地图 API 封装
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── task_manager.py   # 任务状态管理
│   │   └── utils/
│   │       └── budget.py         # 预算分档计算
│   ├── requirements.txt
│   └── .env.example
│
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-06-05-smart-travel-planning-design.md
```

## 10. 错误处理策略

| 场景 | 处理方式 |
|------|---------|
| 高德 API 超时/限流 | 重试 3 次（指数退避），仍失败则降级标记该 Agent 结果不完整 |
| 单个 Agent 失败 | 不阻塞其他 Agent，规划协调时标记缺失数据，部分能力降级 |
| 全部 Agent 失败 | 返回错误状态给前端，提示用户稍后重试 |
| 用户输入校验失败 | 前端即时校验 + 后端 Pydantic 二次校验，返回明确字段错误 |
| 预算无法满足 | 规划协调 Agent 给出最接近预算的方案 + 超出提示 |
| SSE 连接断开 | 前端自动重连，使用 lastEventId |
| 目的地无搜索结果 | 扩大搜索半径、放宽过滤条件、提示用户调整参数 |

## 11. 后续扩展（不在当前 MVP 范围）

- OTA 真实酒店价格 + 预订链接
- 用户系统 + 历史行程保存
- 行程分享卡片（带社交预览图）
- AI 对话式调整行程（"帮我把第二天换成更轻松的行程"）
- 多人出行预算分摊
- 实时交通/天气告警推送
