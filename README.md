# interior-design-agent

> **AI 家装设计 Agent · Beyond Prompt: Agents in Action 黑客松 · 北京站**
>
> 输入对标账号 + 客户户型 → 30 秒生成可发布、可成交的小红书图文营销素材。

---

## 项目信息

| 项 | 内容 |
|----|------|
| 赛道 | Track C · ToB 场景 AI Agent（自定义企业痛点） |
| 团队 | 3 人 |
| 开发周期 | 2026/06/27 11:00 – 06/28 14:30 |
| 架构路径 | **路径 C** —— 自写 5-Agent 主架构 + 借鉴 Hermes / agentskills.io 工程思路 |

详细产品文档见上一级目录 `产品文档.md`，技术架构决策见 `技术架构思考.md`。

---

## 架构概览

```
            ┌─────────────────────┐
            │   Web 前端           │
            └──────────┬──────────┘
                       │ HTTP
            ┌──────────▼──────────┐
            │   FastAPI 后端       │
            │   + 主 Agent 编排器  │
            └──────────┬──────────┘
                       │
      ┌────────┬───────┼───────┬────────┐
      ▼        ▼       ▼       ▼        ▼
   [采集]   [风格分析] [提示词] [图片]   [文案]
   Agent1   Agent2    Agent3   Agent4   Agent5
      │        │       │       │        │
      ▼        ▼       ▼       ▼        ▼
   ┌─────────────────────────────────────┐
   │  工具层（Cloudsway / LLM / 文生图）  │
   └─────────────────────────────────────┘
```

**数据流**：`UserRequest → CollectedContent → StyleDNA → ImagePromptBundle → GeneratedImages → CopyContent → FinalPost`

所有数据结构定义在 `core/schemas.py`，**唯一真理源**。

---

## 目录结构

```
interior-design-agent/
├── core/                    # 主架构（编排 + Agent）
│   ├── schemas.py           # 【接口契约】Pydantic 数据结构
│   ├── orchestrator.py      # 主编排器（5 Agent 状态机）
│   └── agents/              # 5 个 Agent
│       ├── collector.py     # Agent 1：内容采集
│       ├── analyzer.py      # Agent 2：风格 DNA 提取
│       ├── prompter.py      # Agent 3：反向提示词工程
│       ├── generator.py     # Agent 4：图片生成
│       └── copywriter.py    # Agent 5：文案生成
├── tools/                   # 工具层（封装外部 API）
│   ├── cloudsway.py         # Cloudsway 三件套
│   ├── llm.py               # LLM 统一 client
│   └── image_gen.py         # 文生图 API
├── server/                  # FastAPI 后端
│   └── main.py              # API 入口
├── apps/web/                # 前端（待选型：Next.js / Streamlit / Gradio）
├── tests/
│   └── smoke_test.py        # 端到端 mock 冒烟测试
├── data/
│   ├── style_dna/           # 风格 DNA 库（Markdown 格式）
│   └── samples/             # 样本数据 / Demo 兜底素材
├── scripts/                 # 辅助脚本
├── pyproject.toml           # Python 依赖管理
├── Makefile                 # 一键命令
├── .env.example             # 环境变量模板
└── README.md                # 本文档
```

---

## 团队分工建议（3 人需开会拍板）

| 角色 | 主目录 | 关键交付 |
|------|--------|---------|
| **A · Agent 工程师** | `core/` + `tools/` | 5 Agent 真实实现 + 主编排器 + 工具封装 |
| **B · 后端 + 部署** | `server/` + 部署脚本 | FastAPI + 公网部署 + 联调 |
| **C · 前端 + Demo** | `apps/web/` + PPT 素材 | UI + 演示流程 + Demo 素材 / 兜底物料 |

> **关键约束**：每个人只能改自己目录里的文件。改 `core/schemas.py` 必须群内同步。

---

## 5 条防集成铁律（避免上次返工）

1. **接口契约先行** —— `core/schemas.py` 是【唯一】真理源。改 schema 必须先在群里说一声。
2. **统一骨架** —— 本仓库就是这个骨架。所有人 clone 后只往里填，不重起结构。
3. **Mock 优先** —— 在依赖未就绪前，每个 Agent 都先返回 mock 数据，保证主流程能跑通。
4. **每 2 小时强制集成** —— 整点 `git pull --rebase` + 跑 `make smoke`，发现问题立即解决。
5. **共享开发环境** —— 奇绩服务器 / Docker / Codespaces 三选一，杜绝"我本地能跑"。

---

## 快速开始

```bash
# 1. 克隆
git clone https://github.com/blockafka/interior-design-agent.git
cd interior-design-agent

# 2. 安装依赖
make install

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 CLOUDSWAY_API_KEY 等

# 4. 跑通端到端 Mock（验证骨架完整）
make smoke

# 5. 启动后端开发服务器
make dev
# 访问 http://localhost:8000/docs 查看接口

# 6. 前端开发（待选型确认后启动）
cd apps/web
```

---

## Git 工作流

```bash
# 每次开工前
git pull --rebase origin main

# 完成单个 Agent / 模块后
git add <你负责的文件>
git commit -m "feat(<模块>): <做了什么>"
git push origin main

# 严禁
# - 直接覆盖别人的文件
# - 改 schemas.py 不通知
# - push 之前不跑 make smoke
```

**Commit 前缀约定**：
- `feat:` 新功能 · `fix:` 修 bug · `refactor:` 重构 · `docs:` 文档 · `chore:` 杂项

---

## 待拍板决策（见 `产品文档.md` 附录 C）

- [ ] 文生图技术栈：奇绩本地 / 云端 API / 微软 credits
- [ ] LLM 选型：Claude / GPT / Doubao
- [ ] 前端框架：Next.js / Streamlit / Gradio
- [ ] 三人分工正式确认

---

*版本：v0.0.1（项目骨架）· 创建于 2026/06/27*
