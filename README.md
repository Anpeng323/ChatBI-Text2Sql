# ChatBI-Text2Sql

> 把自然语言问题转化为 SQL、查询数据库、自动可视化并给出分析结论的对话式 BI 平台。

ChatBI-Text2Sql 是一个通用 **Text-to-SQL** 数据分析助手：用户输入「按省份统计订单数量」这类中文问题，后端经 MiniMax 大模型做 NL2SQL、执行只读 SQL 校验后查询 MySQL，再返回一个流式回答（含生成的 SQL、原始数据、ECharts 图表、Markdown 分析结论与可点选的追问）。数据库层已抽象为统一适配器，表结构由系统自动从 `information_schema` 探测注入，天然适配任意表结构。

## ✨ 核心特性

- **通用 Schema 自动探测**：读取 `information_schema` 生成表 / 字段 / 类型 / 注释，动态注入提示词，无需手写表结构。
- **NL2SQL 准确性增强**：
  - 只读 SQL 校验（仅允许 `SELECT`、单语句、强制 `LIMIT`、超时限制、禁止访问 `information_schema` / `mysql` 等系统库）。
  - 执行失败自动修正一次；空结果如实说明，**绝不编造数字**。
  - 每次对话最多调用一次查询工具，拿到结果后由无工具模型产出最终分析，避免模型空转递归。
- **真实流式对话**：基于 SSE 的多轮会话，按事件流逐块渲染（`thinking → sql → data → answer → chart → suggestions → done`），会话间历史隔离。
- **交互式可视化**：后端生成 ECharts `option` JSON，前端渲染（tooltip / 放大 / 导出）。
- **Markdown 富文本回答**：分析结论以标题 / 加粗 / 列表 / 表格等 Markdown 格式呈现。
- **追问引导 + 历史会话**：每轮生成可点选追问，侧栏管理多会话。

## 🧱 技术架构

| 层 | 技术栈 |
|----|--------|
| 大模型 | MiniMax（OpenAI 兼容接口，通过 `langchain-openai` 调用） |
| 后端 | FastAPI + LangGraph（ReAct Agent）+ SSE 流式 |
| 数据库 | MySQL 8.0（适配器可扩展） |
| 前端 | React 18 + TypeScript + Vite + Tailwind CSS + ECharts + Zustand |

## 📁 目录结构

```
ChatBI-Text2Sql/
├── backend/                FastAPI 后端
│   ├── app/
│   │   ├── api/           路由（chat / sessions / schema / export）
│   │   ├── core/          配置、提示词、SQL 安全校验
│   │   ├── db/            MySQL 适配器（统一接口）
│   │   ├── llm/           MiniMax 客户端 + LangGraph 编排
│   │   ├── tools/         exc_sql 执行工具
│   │   └── services/      对话编排服务
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/               React + Vite + Tailwind 前端
├── run_dev.sh             本地一键启动（后端 + 前端）
└── .gitignore
```

## 🚀 快速开始

### 1. 准备后端密钥

```bash
cd backend
cp .env.example .env
# 编辑 .env，填入 MINIMAX_API_KEY 与 DB_URL
```

> ⚠️ `backend/.env` 含密钥，**已被 .gitignore 忽略，请勿提交。**

### 2. 一键启动（推荐，本地开发）

```bash
bash run_dev.sh
```

- 后端：http://127.0.0.1:8000 （API 文档 `/docs`）
- 前端：http://127.0.0.1:5173 （Vite 已代理 `/api` → 8000）

### 3. 仅启动后端

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 4. 仅启动前端（需后端已在运行）

```bash
cd frontend
npm install
npm run dev
```

### 5. 生产构建前端 + 后端托管

```bash
cd frontend && npm run build      # 产物输出到 frontend/dist
cd ../backend && uvicorn app.main:app --port 8000
# 后端会自动挂载 frontend/dist，直接访问 http://127.0.0.1:8000
```

### 6. Docker

```bash
docker build -t chatbi-text2sql -f backend/Dockerfile .
docker run -p 8000:8000 --env-file backend/.env chatbi-text2sql
```

## 🔌 主要 API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat` | SSE 流式问答（body：`session_id`, `message`, `stream`） |
| GET  | `/api/schema` | 自动探测的表结构 |
| GET/POST/DELETE | `/api/sessions` | 会话列表 / 新建 / 删除 |
| GET  | `/api/export/csv` | 导出某次查询结果为 CSV |

### SSE 事件流

`POST /api/chat` 以 `text/event-stream` 返回，事件 `type` 依次为：

```
thinking      # 模型思考/规划
sql           # 生成的 SQL
data          # 查询返回的原始数据（表格）
answer        # 分析结论（Markdown，增量 delta 流式）
chart         # ECharts option
suggestions   # 可点选追问
done          # 结束
error         # 出错（如有）
```

## ⚙️ 配置项（环境变量）

在 `backend/.env` 中设置（参考 `backend/.env.example`）：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `MINIMAX_API_KEY` | MiniMax 模型 Key（必填） | 空 |
| `MINIMAX_MODEL` | 模型名 | `MiniMax-Text-01` |
| `MINIMAX_BASE_URL` | 兼容接口地址 | `https://api.minimax.chat/v1` |
| `LLM_TEMPERATURE` | 采样温度 | `0.0` |
| `LLM_MAX_TOKENS` | 最大生成 token | `2048` |
| `LLM_TIMEOUT` | 超时（秒） | `60` |
| `LLM_MAX_RETRIES` | 重试次数 | `3` |
| `DB_URL` | SQLAlchemy MySQL 连接串 | 见 `.env.example` |
| `DB_MAX_EXECUTION_TIME_MS` | 查询最大执行时间（防慢查询） | `15000` |
| `MAX_RESULT_ROWS` | 图表/预览截断行数 | `200` |
| `EXPORT_MAX_ROWS` | 导出全量上限 | `50000` |
| `RETRY_ON_SQL_ERROR` | SQL 失败自动修正一次 | `true` |
| `DEFAULT_CHART_LIMIT` | 图表采样行数 | `30` |
| `APP_HOST` / `APP_PORT` | 服务监听地址 | `127.0.0.1` / `8000` |
| `CORS_ALLOW_ORIGINS` | 跨域允许源（逗号分隔） | `*` |

## 🔒 安全说明

- `exc_sql` 执行前经 `core/security.SQLValidator` 校验：仅允许 `SELECT`、单语句、强制 `LIMIT`、禁止访问系统库；连接层附加 `MAX_EXECUTION_TIME` 防慢查询。
- `backend/.env` 含密钥，已被 `.gitignore` 忽略，**切勿提交**。
- 当前为演示 / 内部工具形态；生产部署请补充鉴权、速率限制与审计，并将 `CORS_ALLOW_ORIGINS` 收紧为具体前端域名。

## 🗺️ 路线图

- 多数据源适配器（PostgreSQL / ClickHouse 等）
- 允许用户纠错 / 标注「正确 SQL」以微调提示词
- 复杂多表 JOIN 与指标口径管理

## 📄 License

本项目仅供学习与研究使用。
