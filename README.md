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
| 架构路径 | **路径 C · B3 真 Skill 化** —— 自写 5-Agent 主架构 + 真 Skill Loader（参考 Hermes / agentskills.io） |

详细产品文档见上一级目录 `产品文档.md`，技术架构决策见 `技术架构思考.md`。

---

## 架构概览：B3 真 Skill 化

每个 Agent 是一个**真正的 Skill**：自带 `SKILL.md`（元数据 + 文档）+ `agent.py`（实现）。
启动时 `skill_loader.py` 扫描 `core/agents/*/SKILL.md`，按 `order` 排序，校验 schema 链路，注入 orchestrator。

```
            ┌─────────────────────┐
            │   Web 前端           │
            └──────────┬──────────┘
                       │ HTTP
            ┌──────────▼──────────┐
            │   FastAPI 后端       │
            │   + 主编排器          │
            │   ← skill_loader     │ ← 扫描 core/agents/*/SKILL.md
            └──────────┬──────────┘
                       │
      ┌────────┬───────┼───────┬────────┐
      ▼        ▼       ▼       ▼        ▼
   [采集]   [风格分析] [提示词] [图片]   [文案]
   Skill1   Skill2    Skill3   Skill4   Skill5
   每个 Skill = SKILL.md + agent.py + (可选) references/
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
├── core/                              # 主架构
│   ├── schemas.py                     # 【接口契约】Pydantic 数据结构
│   ├── orchestrator.py                # 主编排器（5 Agent 状态机，过渡期硬编码）
│   ├── skill_loader.py                # 【待实现】Skill 动态加载器
│   └── agents/                        # 5 个 Skill
│       ├── collector/                 # Step 1 · 采集
│       │   ├── SKILL.md               # 元数据 + 文档
│       │   └── agent.py               # 实现（async def run）
│       ├── analyzer/                  # Step 2 · 风格分析（kafka 负责）
│       │   ├── SKILL.md               # ★ 详细版
│       │   └── agent.py
│       ├── prompter/                  # Step 3 · 提示词工程
│       ├── generator/                 # Step 4 · 图片生成
│       └── copywriter/                # Step 5 · 文案
├── tools/                             # 工具层
│   ├── cloudsway.py                   # Cloudsway 三件套
│   ├── llm.py                         # LLM 统一 client
│   └── image_gen.py                   # 文生图 API
├── server/main.py                     # FastAPI 后端
├── apps/web/                          # 前端（待选型）
├── tests/smoke_test.py                # 端到端 mock 冒烟测试
├── examples/                          # ★ Agent 对接 JSON 样例
│   ├── analyzer_input_sample.json     # collector → analyzer 契约
│   └── analyzer_output_sample.json    # analyzer → prompter 契约
├── docs/
│   └── SKILL_PROTOCOL.md              # Skill 协议（loader 实现者必读）
├── pyproject.toml / Makefile / .env.example
└── README.md
```

---

## 团队分工（已拍板）

| 角色 | 负责 Skill / 模块 | 关键交付 |
|------|------------------|---------|
| **kafka** | `core/agents/analyzer/` | 风格 DNA 提取（视觉 + 文案双通道） |
| **队友 X** | `core/skill_loader.py` + `core/orchestrator.py` 改造 + 其他 4 个 Skill 编排 | Skill Loader 实现 + 主链路串联 |
| **队友 Y** | `server/` + 部署 + `apps/web/` + Demo | 后端联调 + 前端 + 演示 |

> **关键约束**：
> - 每人只动自己目录里的文件
> - 改 `core/schemas.py` 必须群内通知
> - 改 SKILL.md 的 frontmatter 必须群内通知（影响 loader）

---

## kafka 负责的 Skill：analyzer（风格分析）

- **目录**：`core/agents/analyzer/`
- **SKILL.md**：`core/agents/analyzer/SKILL.md` —— 完整契约 + 实现思路 + Prompt 草稿
- **输入样例**：`examples/analyzer_input_sample.json`（拷给上游 collector 队友看）
- **输出样例**：`examples/analyzer_output_sample.json`（拷给下游 prompter 队友看）

---

## 5 条防集成铁律

1. **接口契约先行** —— `core/schemas.py` 是【唯一】真理源。改 schema 必须先群里说
2. **统一骨架** —— 本仓库就是这个骨架。所有人 clone 后只往里填，不重起结构
3. **Mock 优先** —— 每个 Agent 都先返回 mock，保证主流程能跑通
4. **每 2 小时强制集成** —— 整点 `git pull --rebase` + 跑 `make smoke`
5. **共享开发环境** —— 奇绩服务器 / Docker / Codespaces 三选一

---

## 快速开始

```bash
# 1. 克隆
git clone git@github.com:blockafka/interior-design-agent.git
cd interior-design-agent

# 2. 安装依赖
make install

# 3. 配置环境变量
cp .env.example .env  # 编辑填入 API keys

# 4. 跑通端到端 Mock（验证骨架完整）
make smoke

# 5. 启动后端开发服务器
make dev  # 访问 http://localhost:8000/docs
```

---

## Git 工作流

```bash
git pull --rebase origin main
# ... 改你负责目录里的文件 ...
git add <你负责的文件>
git commit -m "feat(analyzer): <做了什么>"
git push origin main
```

**Commit 前缀**：`feat:` 新功能 · `fix:` 修 bug · `refactor:` 重构 · `docs:` 文档

---

## 关键文档

| 文档 | 用途 |
|------|------|
| `core/schemas.py` | 所有数据契约的唯一真理源 |
| `core/agents/*/SKILL.md` | 每个 Skill 的元数据 + 实现指令 |
| `docs/SKILL_PROTOCOL.md` | Skill Loader 实现者必读 |
| `examples/*.json` | Agent 对接 JSON 样例 |

---

## 待拍板决策（见 `产品文档.md` 附录 C）

- [ ] 文生图技术栈：奇绩本地 / 云端 API / 微软 credits
- [ ] LLM 选型：Claude / GPT / Doubao
- [ ] 前端框架：Next.js / Streamlit / Gradio

---

*版本：v0.1.0（B3 Skill 化骨架）· 创建于 2026/06/27*
