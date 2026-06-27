# interior-design-agent

> **AI 家装设计 Agent · Beyond Prompt: Agents in Action 黑客松 · 北京站**
>
> 输入对标账号 + 客户户型需求，生成一套可发布、可成交的小红书图文营销素材。

---

## 项目定位

这是一个面向家装 / 家居定制公司的 **AI 内容获客 Agent**。

它不是单纯的效果图工具，也不是泛泛的小红书文案生成器。核心闭环是：

1. 读取对标账号的历史图文内容。
2. 提取该账号的视觉风格和文案风格，形成 `StyleDNA`。
3. 根据客户户型 / 需求生成设计效果图 prompt。
4. 调图片生成模型产出设计效果图。
5. 用对标账号的语气包装这套效果图，生成可发布的小红书营销文案。

最终目标：帮助家装公司把“设计能力”快速转成“获客内容”。

---

## 当前状态

截至 2026-06-27，主链路已经接通 **非 collector 路径**：

```text
本地采集文件夹
  → Analyzer Agent
  → Prompter Agent
  → Generator Agent
  → Copywriter Agent
  → FinalPost
```

已完成：

- Step 2 `analyzer`：真实多模态 LLM 分析，输出 `StyleDNA`。
- Step 3 `prompter`：根据 `StyleDNA + UserRequest` 生成图片 prompt。
- Step 4 `generator`：支持真实图片生成配置，当前使用 `openai_image` provider。
- Step 5 `copywriter`：真实多模态 LLM 文案生成，读取生成效果图并产出小红书营销内容。
- Collector 旁路：采集 Agent 未接入时，可用 `data/collect/<账号>` 文件夹模拟 collector 最终输出。

暂未完成：

- Step 1 `collector` 真实采集 Agent。
- `skill_loader.py` 动态加载替换硬编码 orchestrator。
- 前端 / 公网部署。

---

## Agent 数据流

```text
UserRequest
  ↓
CollectedContent
  ↓ analyzer
StyleDNA
  ↓ prompter
ImagePromptBundle
  ↓ generator
GeneratedImages
  ↓ copywriter
CopyContent
  ↓ orchestrator
FinalPost
```

所有数据结构定义在 `core/schemas.py`，这是唯一数据契约源。

---

## 目录结构

```text
interior-design-agent/
├── core/
│   ├── schemas.py                    # Pydantic 数据契约
│   ├── orchestrator.py               # 5 Agent 主编排器；当前支持 collect_dir 旁路
│   ├── collect_loader.py             # 本地 collector 输出文件夹 → CollectedContent
│   └── agents/
│       ├── collector/                # Step 1 · 采集；当前未真实接入
│       ├── analyzer/                 # Step 2 · 风格分析
│       ├── prompter/                 # Step 3 · 提示词工程
│       ├── generator/                # Step 4 · 图片生成
│       └── copywriter/               # Step 5 · 小红书营销文案
├── tools/
│   ├── llm.py                        # OpenAI-compatible LLM / vision client
│   └── image_gen.py                  # 图片生成 provider 封装
├── data/
│   └── collect/厚来设计/             # collector 输出示例，可用于非采集链路联调
├── tests/
│   ├── smoke_from_collect.py         # 主编排器非 collector 链路冒烟测试
│   ├── test_pipeline_from_collect.py # 分步骤查看各 Agent 输出
│   ├── test_analyzer_live.py         # analyzer 真实 LLM 测试
│   └── test_copywriter_live.py       # copywriter 真实 LLM 测试
├── docs/
│   ├── SKILL_PROTOCOL.md
│   ├── analyzer_dev_plan.md
│   └── copywriter_dev_plan.md
└── pyproject.toml
```

---

## 环境配置

复制并填写环境变量：

```bash
cp .env.example .env
```

关键配置：

```env
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://api.openai-next.com/v1

IMAGE_GEN_PROVIDER=openai_image
IMAGE_GEN_MODEL=gemini-3.1-flash-image-preview
```

说明：

- `OPENAI_API_KEY` 用于 LLM 和图片生成的 OpenAI-compatible 接口。
- `.env` 已被 `.gitignore` 忽略，不要提交。
- `data/generated/` 是运行时生成图片目录，也不要提交。

---

## 安装依赖

```bash
python -m pip install -e '.[dev]'
```

运行时依赖里包含：

- `openai>=1.0`
- `httpx[socks]>=0.27`
- `Pillow>=10.0`

`httpx[socks]` 是为了兼容本地 SOCKS 代理环境；`Pillow` 用于本地图片压缩和 data URI 生成。

---

## 如何测试

### 1. 跑非 collector 主链路

```bash
python -m tests.smoke_from_collect
```

这个命令会读取：

```text
data/collect/厚来设计
```

然后跳过真实 collector，直接跑：

```text
collect_loader → analyzer → prompter → generator → copywriter
```

输出会包含：

- request id
- target account
- 最终标题
- hashtags
- 生成图片路径
- generated_at

### 2. 查看每一步 Agent 输出

```bash
python -m tests.test_pipeline_from_collect
```

用于调试每个 Agent 的中间结果：

- `CollectedContent`
- `StyleDNA`
- `ImagePromptBundle`
- `GeneratedImages`
- `CopyContent`

### 3. 单测 analyzer

```bash
python -m tests.test_analyzer_live
```

可通过环境变量切换测试风格：

```bash
TEST_STYLE=新中式 python -m tests.test_analyzer_live
TEST_STYLE=日式原木 python -m tests.test_analyzer_live
TEST_STYLE=极简自然风 python -m tests.test_analyzer_live
TEST_STYLE=法式中古风 python -m tests.test_analyzer_live
```

### 4. 单测 copywriter

```bash
python -m tests.test_copywriter_live
```

同样支持 `TEST_STYLE` 切换。

---

## Collector 输出格式

真实 collector 还没接入时，本项目用本地文件夹模拟 collector 最终输出。示例目录：

```text
data/collect/厚来设计/
└── <单篇笔记>/
    ├── metadata.json
    ├── body.txt
    ├── full_text_snapshot.txt
    ├── image_urls.txt
    ├── images/
    │   ├── 01.webp
    │   └── ...
    └── 采集状态.txt
```

`core/collect_loader.py` 会把这个目录转成 `CollectedContent`，并把本地图片压缩成 base64 data URI，方便 analyzer 的多模态模型直接读取。

---

## 图片生成

当前配置：

```env
IMAGE_GEN_PROVIDER=openai_image
IMAGE_GEN_MODEL=gemini-3.1-flash-image-preview
```

生成结果会写入：

```text
data/generated/<uuid>.png
```

对外返回路径为：

```text
/static/generated/<uuid>.png
```

copywriter 会把 `/static/generated/...` 转成本地图片 data URI 再喂给多模态 LLM，确保文案真正看得到生成效果图。

---

## Skill 协议

每个 Agent 保持一致的 Skill 目录格式：

```text
core/agents/<name>/
├── SKILL.md
├── agent.py
└── __init__.py
```

`SKILL.md` 负责对外说明输入、输出、工具依赖和状态；`agent.py` 暴露固定入口：

```python
async def run(...):
    ...
```

完整协议见 `docs/SKILL_PROTOCOL.md`。

---

## Git 与数据约束

- `.env` 不提交。
- `data/generated/` 不提交。
- 大体量运行时产物不提交。
- `data/collect/厚来设计` 是当前非 collector 联调用的示例采集数据，可以保留在仓库中。

---

## 当前推荐 Demo 命令

```bash
python -m tests.smoke_from_collect
```

这是目前最接近完整产品闭环的命令：跳过尚未接入的 collector，跑通后面 4 个 Agent，并输出最终小红书图文结果。
