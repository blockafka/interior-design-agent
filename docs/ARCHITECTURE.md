# AI 家居定制设计 Agent — 系统架构

> 全场景自动获客运营内容系统。三层架构：**hermes**（编排调度后台）+ **claude**（AI 模型调度与技能核心）+ **web**（用户交互界面）。

## 一、三层架构

```
┌──────────────────────────────────────────────────────────────┐
│  web 层 —— 用户交互界面                                          │
│  interior-content-skill/web  (React + Vite)                    │
│  选对标账号 + 填户型需求 → SSE 实时进度 → 看效果图/文案           │
└───────────────┬──────────────────────────────────────────────┘
                │  HTTP / SSE  (/api/accounts, /api/generate)
┌───────────────▼──────────────────────────────────────────────┐
│  claude 层 —— AI 模型调度与技能核心                              │
│  interior-content-skill/server (FastAPI/SSE)                   │
│  interior-content-skill/core   (orchestrator + 4 Agent)        │
│    analyzer → prompter → generator → copywriter                │
│  skills/xhs-content-collector  (采集技能：浏览器自动化)          │
└───────────────┬───────────────────────────┬──────────────────┘
                │ 读共享样本目录             │ 调度执行
┌───────────────▼─────────────┐  ┌──────────▼──────────────────┐
│  data/xhs_collected/        │  │  hermes 层 —— 编排调度后台    │
│  采集器产物 = Agent 样本源   │◄─┤  hermes/engine.py            │
│  <博主>/<日期_标题>/...      │  │  读 schedule→注入secret→执行 │
└─────────────────────────────┘  └─────────────────────────────┘
```

### 层职责
| 层 | 目录 | 职责 |
|---|---|---|
| **hermes** | `hermes/` | 读 `schedules/*.json`，按 cron / 手动触发采集任务，注入 secrets，落 run summary |
| **claude** | `interior-content-skill/core`、`server`、`skills/` | 4 个 Agent 串联出图出文；采集 skill 抓素材；FastAPI 暴露 API |
| **web** | `interior-content-skill/web` | React 表单 + Pipeline 可视化 + 结果展示 |

## 二、端到端数据流

1. **采集**：`hermes/engine.py run xhs-designers-daily` → 调用 `skills/xhs-content-collector` 抓小红书图文 → 写入 `data/xhs_collected/<博主>/<日期_标题>/{metadata.json, body.txt, image_urls.txt, images/}`。
2. **直连**：`server` 通过环境变量 `COLLECT_ROOT` 指向 `data/xhs_collected`，`GET /api/accounts` 即列出采集到的真实账号。
3. **生成**：web 选账号 + 填户型 → `POST /api/generate`(SSE) → `collect_loader` 读样本 → `analyzer`(风格) → `prompter`(提示词) → `generator`(3 张效果图) → `copywriter`(小红书文案)。
4. **展示**：SSE 实时推送每步进度与中间结果，web 渲染效果图 + 可复制成稿。

## 三、运行手册

### 0. 安装依赖（首次）
```bash
python -m pip install -r requirements.txt
python -m playwright install chromium          # 采集才需要
cd interior-content-skill/web && npm install
```

### 1. 配置环境
编辑 `interior-content-skill/.env`：
```
OPENAI_API_KEY=<你的key>
OPENAI_BASE_URL=https://api.openai-next.com/v1
IMAGE_GEN_MODEL=gemini-3.1-flash-image-preview
COLLECT_ROOT=../data/xhs_collected        # 指向采集器产物（共享目录直连）
```

### 2. 采集素材（可选；已附带 25 账号样本可跳过）
```bash
# 先人工扫码保存登录态（凭据，不入库）
python skills/xhs-content-collector/scripts/xhs_login_auto.py data/xhs/auth/storage_state.json

# 经 hermes 调度采集
export XHS_STORAGE_STATE_PATH=data/xhs/auth/storage_state.json
python hermes/engine.py run xhs-designers-daily         # 立即跑一次
python hermes/engine.py run xhs-designers-daily --dry-run  # 只看命令不执行
python hermes/engine.py list                            # 列出 schedule
python hermes/engine.py daemon                          # 常驻按 cron 调度
# 运行回执：hermes/runs/<run_id>.json（含退出码、产物计数；不含凭据内容）
```

### 3. 启动后端 + 前端
```bash
# 后端 :8000
cd interior-content-skill
python -m uvicorn server.main:app --port 8000

# 前端 :5173（路径含中文/冒号时用本地 vite 而非 npm run dev）
cd interior-content-skill/web
./node_modules/.bin/vite
```
浏览器打开 http://localhost:5173 → 选账号 → 填户型 → 生成。

## 四、集成改动点（本次）

| 动作 | 文件 | 说明 |
|---|---|---|
| 迁入 | `skills/xhs-content-collector/**` | 采集器主力脚本 + references + 辅助脚本 |
| 迁入 | `hermes/schedules`、`hermes/tasks`、`config` | 调度与任务定义 |
| 新建 | `hermes/engine.py` | 轻量真引擎（list / run / daemon，cron 自实现） |
| 改 | `server/main.py` | `COLLECT_SAMPLE_DIR` 改读 `COLLECT_ROOT` env；`liked_count` 兼容 `like_count` |
| 改 | `core/collect_loader.py` | `likes` 字段兼容采集器 `like_count` |
| 新建 | `requirements.txt`、`.env` | 统一依赖与配置 |

**复用未改**：4 个 Agent、orchestrator、SSE server 主体、React web、采集器脚本本体。

## 五、安全红线

- `storage_state.json` 视同登录凭据：不入 git、不进日志、不进 prompt、不打包。hermes 引擎只传**路径**，绝不读取/打印其内容；run summary 仅记录 secret 键名是否就绪。
- 不采集账密/验证码/原始 cookie；遇 `login_required`/`captcha_required` 立即停止并请求人工刷新登录态。
- 采集频率保守（采集器内置随机延时 + 定期休息）。

## 六、后续路线图

- **中期**：`server` 增 `/api/collect` 让 web 一键触发 hermes 采集；Agent 把点赞/收藏/评论纳入风格权重；登录态失效自动告警。
- **远期**：多平台采集适配层、采集→生成→发布全自动闭环、SaaS 多租户。
