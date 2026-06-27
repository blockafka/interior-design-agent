# Analyzer Agent 开发计划

> Step 2 · 风格分析 Agent 的真实实现计划（`core/agents/analyzer/`）
>
> 负责：kafka · 状态：开发中 · 创建：2026-06-27
>
> 本文档是 `core/agents/analyzer/SKILL.md` 契约的**实施细节版**。SKILL.md 是"对外契约"（给 loader / 评委 / 队友看），本文档是"开发笔记"（只给 kafka 自己看）。

---

## 0. 已敲定的技术决策（kafka 拍板）

1. **LLM**：`doubao-seed-2-0-pro-260215`（多模态，视觉 + 文案都用它）
2. **API**：`https://api.openai-next.com/v1/chat/completions`（OpenAI 兼容协议）
3. **API key**：直接用 kafka 给的，放 `.env`（不进 git）
4. **LLM client**：统一抽到 `tools/llm.py`，全队共用

---

## 1. 目标 & 边界

**做什么**：把 `core/agents/analyzer/agent.py` 从 mock 改成**真实多模态 LLM 调用**。输入仍是 mock 的 `CollectedContent`（来自 `examples/analyzer_input_sample.json`），输出真实 `StyleDNA`。

**不做什么**：
- 上下游 Agent（collector / prompter / generator / copywriter）保持 mock
- skill_loader、前后端联调
- 性能优化（重试 1 次后失败就兜底，不做指数退避）

---

## 2. 输入输出契约（参考但不重写）

| 项 | 文件 |
|---|------|
| 输入 schema | `core/schemas.py::CollectedContent`（含 N 篇 `CollectedPost`） |
| 输出 schema | `core/schemas.py::StyleDNA`（含 `visual` / `copy` 两个 dict） |
| 输入样例 | `examples/analyzer_input_sample.json` |
| 输出样例 | `examples/analyzer_output_sample.json` |

**关键字段名（容易写错）**：
- `CollectedPost.body` ← 是 `body`，不是 `content`
- `CollectedPost.metadata` ← dict，里面装 `likes` / `comments` / `collects` / `publish_time`

**开发期 vs 生产期的图片来源（重要）**：

- **生产期**（collector 真实接入后）：`CollectedPost.image_urls` 是公网可访问的 http URL（小红书 CDN 或自建图床），analyzer 直接把 URL 传给 vision LLM
- **开发期**（当前）：collector 还在 mock，**测试时用本仓库外的 `material/` 目录的本地图**（绝对路径 `/Users/kafka/Desktop/files/bussiness_test/Hackathon/Beyond Prompt: Agents in Action/material`），目录下含 4 个风格子目录（新中式 / 日式原木 / 极简自然风 / 法式中古风），每个 3 张图。**毛坯房目录不属于 analyzer 输入**（那是给下游 generator 用的户型空白图）
- **怎么注入**：不修改 `examples/analyzer_input_sample.json` 本身，而是在 `test_analyzer_live.py` 里把本地图转 base64 data URI 后**覆盖** `image_urls` 字段（每次测一个风格）
- **代码侧透明**：`tools/llm.py::chat_with_images` 同时支持 http URL 和 `data:image/...;base64,...`（OpenAI vision API 规范），所以 analyzer 业务逻辑**完全不区分两者**。集成期切换到真实 URL 零修改

---

## 3. 风格分析核心逻辑 [★ 本文档主体]

### 3.1 总体编排（`agent.py` 主入口）

```python
async def run(content: CollectedContent) -> StyleDNA:
    # 步骤 1: 样本筛选（按互动量降序，取 Top 5）
    samples = _select_top_posts(content.posts, k=5)

    # 步骤 2: 视觉 + 文案并行分析（asyncio.gather）
    visual, copy_dna = await asyncio.gather(
        _analyze_visual(samples),
        _analyze_copy(samples),
    )

    # 步骤 3: 组装 StyleDNA
    return StyleDNA(
        target_account_id=content.target_account_id,
        visual=visual,
        copy=copy_dna,
        sample_post_ids=[p.post_id for p in samples],
    )
```

**为什么 Top 5？** 控制 token + 让爆款决定风格（粉丝喜欢的就是风格）。

**为什么并行？** 两个 LLM 调用互不依赖，asyncio.gather 等于免费提速一倍。

---

### 3.2 样本筛选逻辑

```python
def _select_top_posts(posts: list[CollectedPost], k: int = 5) -> list[CollectedPost]:
    """按互动量降序，取前 K 篇。
    互动量 = likes + collects * 2（收藏比点赞含金量高）
    无 metadata 的笔记排到末尾。
    """
    def score(p: CollectedPost) -> int:
        m = p.metadata or {}
        return m.get("likes", 0) + m.get("collects", 0) * 2

    return sorted(posts, key=score, reverse=True)[:k]
```

---

### 3.3 视觉通道（`_analyze_visual`）

**输入处理**：
1. 从 Top 5 posts 收集所有 `image_urls`，去重
2. 限制总图片数 ≤ 8（防 token 爆炸）
3. 拼成 OpenAI 多模态 `messages` 格式

**LLM 调用形态**（OpenAI 兼容 vision API）：

```python
messages = [
    {"role": "system", "content": VISUAL_SYSTEM_PROMPT},
    {"role": "user", "content": [
        {"type": "text", "text": VISUAL_USER_PROMPT},
        {"type": "image_url", "image_url": {"url": "https://..."}},
        {"type": "image_url", "image_url": {"url": "https://..."}},
        # ... 最多 8 张
    ]},
]
```

#### Visual Prompt 草稿

**System Prompt**：
```
你是专业的室内设计风格分析师。你的任务是从一组小红书家装笔记的图片中，提取该账号的统一视觉风格 DNA。

【输出要求】
- 只输出一个 JSON 对象
- 不要任何 markdown 代码块包裹（不要 ```json ）
- 不要任何解释性文字、不要前后缀
- 所有字段都必须填写，不能省略
```

**User Prompt（文字部分）**：
```
请观察以下图片，总结该账号的视觉风格 DNA。严格按此 JSON schema 输出：

{
  "color_palette": ["颜色 1", "颜色 2", "颜色 3"],
  "material": ["材质 1", "材质 2", "材质 3"],
  "composition": "一句话描述构图特点",
  "lighting": "一句话描述光线风格"
}

【字段说明】
- color_palette: 3-5 个主色（中文颜色名如"奶油白"，或 HEX 如"#F5E6D3"，可混用）
- material: 3-5 个常见材质（如"实木"、"亚麻"、"陶瓷"、"藤编"）
- composition: 一句话（如"对称构图为主，远近景结合，多用 45° 视角"）
- lighting: 一句话（如"自然光为主，下午斜光，无主灯设计"）

【参考输出示例】
{
  "color_palette": ["奶油白", "原木色", "雾霾蓝"],
  "material": ["实木", "亚麻", "藤编"],
  "composition": "对称构图为主，多用 45° 视角",
  "lighting": "自然光为主，下午斜光，无主灯"
}

现在请分析以下图片：
```

#### JSON 解析 + 校验

```python
def _parse_visual_json(text: str) -> dict:
    """LLM 输出 → 视觉 dict。做 4 件事：
    1. 剥掉可能的 ```json ... ``` 包裹
    2. JSON 解析
    3. 必填字段校验
    4. 类型校验
    """
    cleaned = _strip_markdown_fence(text)
    data = json.loads(cleaned)

    required = {
        "color_palette": list,
        "material": list,
        "composition": str,
        "lighting": str,
    }
    for key, typ in required.items():
        if key not in data:
            raise ValueError(f"visual: 缺少字段 {key}")
        if not isinstance(data[key], typ):
            raise ValueError(f"visual: {key} 类型应为 {typ.__name__}")

    return data
```

#### 视觉通道兜底链（3 级）

```
[1st 调用] → 解析成功？ → 返回
                 ↓ 失败
[2nd 调用，附带错误反馈] → 解析成功？ → 返回
                 ↓ 失败
[3rd: 用 MOCK_VISUAL 兜底]  ← 主链路永不挂
```

#### 开发期 fixture 注入（文案 + 图片**配对**切换）

**核心原则**：测试期**文案和图片必须风格一致**——否则 analyzer 拿到打架的输入（文案讲奶油风、图却是日式原木），输出会撕裂、`visual` 和 `copy` 描述不是同一个东西，且 LLM 行为不可预测，调试时分不清是 prompt 差还是输入打架。

**实现方式**：**不**从 `examples/analyzer_input_sample.json` 加载（那是奶油风文案，跟 material 4 个风格都不匹配，仅作为对外 schema 契约样例保留）。改为在 `tests/test_analyzer_live.py` 里维护 `STYLE_FIXTURES`，4 个风格各一套**配对**的文案 + 图：

```python
STYLE_FIXTURES = {
    "新中式":      {"target_account_id": "...", "posts": [<3 篇匹配 material/新中式/ 的笔记>]},
    "日式原木":    {"target_account_id": "...", "posts": [<3 篇匹配 material/日式原木/ 的笔记>]},
    "极简自然风":  {"target_account_id": "...", "posts": [<3 篇匹配 material/极简自然风/ 的笔记>]},
    "法式中古风":  {"target_account_id": "...", "posts": [<3 篇匹配 material/法式中古风/ 的笔记>]},
}
```

**配对规则**：fixture 里的 title / body 中提到的色彩 / 材质 / 氛围词，要和对应 `material/<style>/` 图里能看到的视觉元素**一致**。例如 `日式原木` fixture 里的文案应该提"橡木"、"白蜡木"、"亚麻"、"漫射光"、"绿植"，跟 `material/日式原木/` 的图能对得上。

**helper 函数**（放在 `tests/test_analyzer_live.py` 里，**不进 analyzer 业务代码**）：

```python
import base64
from pathlib import Path

MATERIAL_DIR = Path(
    "/Users/kafka/Desktop/files/bussiness_test/Hackathon/Beyond Prompt: Agents in Action/material"
)

def _local_image_to_data_uri(path: Path) -> str:
    suffix = path.suffix.lower()
    mime = "image/png" if suffix == ".png" else "image/jpeg"
    b64 = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime};base64,{b64}"

def _build_mock_image_urls(style: str) -> list[str]:
    """从 material/<style>/ 加载图，转 base64 data URI。
    style 取值：新中式 / 日式原木 / 极简自然风 / 法式中古风
    """
    style_dir = MATERIAL_DIR / style
    return [
        _local_image_to_data_uri(p)
        for p in sorted(style_dir.iterdir())
        if p.suffix.lower() in (".jpg", ".jpeg", ".png")
    ]
```

**注入方式**：见 §9 完整测试入口代码——从 `STYLE_FIXTURES[TEST_STYLE]` 构造 `CollectedContent`，同时调 `_build_mock_image_urls(TEST_STYLE)` 拿图，把图按顺序分到 3 个 post 上（每 post 1 张）。

**关键约束**：`STYLE_FIXTURES` + helper **只在 `tests/test_analyzer_live.py` 里**，不进 `agent.py`。analyzer 业务代码看到的永远是 `list[str]` image_urls（不管 str 是 http URL 还是 data URI），保持单一职责，**生产期 collector 切回真实 URL 时 analyzer 零修改**。

---

### 3.4 文案通道（`_analyze_copy`）

**输入处理**：
1. 把 Top 5 posts 的 `title` + `body` 拼成单一文本块
2. 每篇 `body` 截断到 500 字（防 token 爆炸）
3. 用 `---` 分隔每篇

```python
def _pack_text(posts: list[CollectedPost]) -> str:
    chunks = []
    for i, p in enumerate(posts, 1):
        body = (p.body or "")[:500]
        chunks.append(f"【笔记 {i}】\n标题：{p.title}\n正文：{body}")
    return "\n\n---\n\n".join(chunks)
```

**LLM 调用形态**（纯文本）：

```python
messages = [
    {"role": "system", "content": COPY_SYSTEM_PROMPT},
    {"role": "user", "content": COPY_USER_PROMPT_TEMPLATE.format(text=packed_text)},
]
```

#### Copy Prompt 草稿

**System Prompt**：
```
你是专业的小红书内容风格分析师。你的任务是从一组家装笔记的标题和正文中，提取该账号的统一文案风格 DNA。

【输出要求】
- 只输出一个 JSON 对象
- 不要任何 markdown 代码块包裹
- 不要任何解释性文字
- 所有字段都必须填写
```

**User Prompt（template）**：
```
请观察以下笔记的文案，总结该账号的文案风格 DNA。严格按此 JSON schema 输出：

{
  "voice": "一句话描述整体语气",
  "keywords": ["关键词 1", "关键词 2", ...],
  "sentence_pattern": "一句话描述句式特点",
  "hashtag_pattern": ["#hashtag 1", "#hashtag 2", ...]
}

【字段说明】
- voice: 一句话（如"治愈系第一人称温暖叙事，强调氛围感"）
- keywords: 5-10 个高频核心词（去掉无意义的助词、连接词）
- sentence_pattern: 一句话（如"短句为主，多用感叹号，emoji 适度点缀"）
- hashtag_pattern: 5-8 个该账号惯用 hashtag（从正文显式提取，或基于内容主题合理推断）

【参考输出示例】
{
  "voice": "治愈系第一人称温暖叙事",
  "keywords": ["奶油风", "无主灯", "原木", "藤编", "氛围感", "治愈"],
  "sentence_pattern": "短句为主，多用感叹号，emoji 适度点缀",
  "hashtag_pattern": ["#家装日记", "#奶油风", "#治愈系家居"]
}

【输入笔记】
{text}
```

#### JSON 解析 + 校验

与 3.3 结构相同，必填字段改为：

```python
required = {
    "voice": str,
    "keywords": list,
    "sentence_pattern": str,
    "hashtag_pattern": list,
}
```

#### 兜底链

同 3.3（重试 1 次 → 失败用 `MOCK_COPY` 兜底）。

---

## 4. tools/llm.py 设计

**唯一职责**：把 OpenAI 兼容 chat completion 封装成最简单的 async 函数。所有 Agent 通过它调 LLM。

```python
"""统一 LLM 调用层（OpenAI 兼容协议）"""

import os
import httpx

_DEFAULT_BASE_URL = "https://api.openai-next.com/v1"
_DEFAULT_MODEL = "doubao-seed-2-0-pro-260215"


async def chat(
    *,
    system: str | None = None,
    user: str,
    model: str = _DEFAULT_MODEL,
    temperature: float = 0.7,
    timeout: float = 30.0,
) -> str:
    """纯文本对话，返回 LLM 的文本回复。"""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user})
    return await _call(messages, model, temperature, timeout)


async def chat_with_images(
    *,
    system: str | None = None,
    user_text: str,
    image_urls: list[str],
    model: str = _DEFAULT_MODEL,
    temperature: float = 0.7,
    timeout: float = 60.0,
) -> str:
    """多模态对话，user 同时包含文字和图片。"""
    user_content = [{"type": "text", "text": user_text}]
    for url in image_urls:
        user_content.append({"type": "image_url", "image_url": {"url": url}})
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user_content})
    return await _call(messages, model, temperature, timeout)


async def _call(messages, model, temperature, timeout) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY 未设置，请检查 .env")
    base_url = os.getenv("OPENAI_BASE_URL", _DEFAULT_BASE_URL)

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"model": model, "messages": messages, "temperature": temperature},
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
```

---

## 5. 错误处理矩阵

| 错误源 | 处置 |
|---|---|
| `.env` 没有 `OPENAI_API_KEY` | `tools/llm.py` 启动期直接 raise（让人立刻发现） |
| HTTP 4xx/5xx | httpx 抛 → analyzer 捕获 → 重试 1 次 → 仍失败用 mock 兜底 |
| LLM 输出带 ```` ```json ```` 包裹 | 解析前 strip 代码块 |
| LLM 输出 JSON 格式错 | 重试 1 次（把错误信息回传 LLM）→ 失败 mock 兜底 |
| LLM 输出 JSON 但字段缺失 | 同上 |
| 图片 URL 无法访问 | LLM 会拒绝或乱猜 → 校验失败走兜底；**根本解法见 §8** |
| 整个调用超时（30s 文本 / 60s 多模态） | 走兜底 |

**统一重试形态**：

```python
async def _call_with_retry(call_fn, parse_fn, mock_fallback):
    """call_fn(error_hint=None) → 文本；parse_fn(文本) → dict；失败回 mock。"""
    try:
        return parse_fn(await call_fn())
    except (json.JSONDecodeError, ValueError) as e:
        try:
            return parse_fn(await call_fn(error_hint=str(e)))
        except Exception:
            return mock_fallback
    except Exception:
        return mock_fallback
```

---

## 6. 代码组织（新增 / 修改文件清单）

```
core/agents/analyzer/
├── SKILL.md              # 已有，不动
├── agent.py              # ★ 重写：run + _analyze_visual + _analyze_copy + _select_top_posts
├── _prompts.py           # ★ 新增：VISUAL/COPY 的 SYSTEM + USER prompt
├── _mocks.py             # ★ 新增：MOCK_VISUAL / MOCK_COPY 兜底数据
└── __init__.py           # 已有

tools/
└── llm.py                # ★ 新增（见 §4）

tests/
└── test_analyzer_live.py # ★ 新增：吃真 LLM 跑一次

.env                      # 本地，不进 git
.env.example              # 更新，加 OPENAI_API_KEY=sk-xxx 占位
```

---

## 7. 开发顺序（checklist）

**阶段 1 · 基础设施（15 分钟）**
- [ ] 1.1 建 `.env`，写入 `OPENAI_API_KEY` 和 `OPENAI_BASE_URL`
- [ ] 1.2 更新 `.env.example`（不含真 key）
- [ ] 1.3 装 `httpx`（如已装跳过）
- [ ] 1.4 写 `tools/llm.py`
- [ ] 1.5 5 行小脚本调 `chat()` 跑通 "Hello"

**阶段 2 · 文案通道（25 分钟）**
- [ ] 2.1 写 `_prompts.py` 的 COPY 部分
- [ ] 2.2 写 `_mocks.py`
- [ ] 2.3 写 `_analyze_copy()` + JSON 解析 + 兜底
- [ ] 2.4 写 `_select_top_posts()`
- [ ] 2.5 写 `run()` 主入口（视觉先用 mock）
- [ ] 2.6 跑 `test_analyzer_live.py` 看 copy 输出

**阶段 3 · 视觉通道（25 分钟）**
- [ ] 3.1 写 `_prompts.py` 的 VISUAL 部分
- [ ] 3.2 写 `_analyze_visual()` + JSON 解析 + 兜底
- [ ] 3.3 在 `test_analyzer_live.py` 里加 `_local_image_to_data_uri` + `_build_mock_image_urls` helper，扫描 `material/<style>/` 注入到 mock 数据
- [ ] 3.4 跑 `test_analyzer_live.py` 看完整 StyleDNA（先用 `日式原木`，再切其他 3 个风格交叉验证）

**阶段 4 · 联调（10 分钟）**
- [ ] 4.1 跑 `make smoke` 看下游能否消费
- [ ] 4.2 commit + push

**总预算：75 分钟内出 v1**

---

## 8. 已知风险 & 兜底

| 风险 | 概率 | 影响 | 处置 |
|---|---|---|---|
| 测试期 mock 数据里的 xhscdn URL 不可访问 | **已解决** | - | 测试期用 `material/` 本地图转 base64 data URI 注入（见 §3.3 末小节） |
| LLM 输出 JSON 不严格 | 中 | Pydantic 校验炸 | 解析层 strip + 重试 + mock 兜底 |
| doubao API 限流 / 抖动 | 中 | 偶发 5xx | 30s 超时 + 兜底 |
| 单张图过大导致 token 爆 / 超时 | 中 | 调用失败 | `material/` 里最大约 1.5MB，应能通过；不通过的话考虑预压缩 |
| pydantic UserWarning（`copy` shadowing `BaseModel`） | 低 | 仅警告不报错 | 本次不处理，hackathon 后清理 |

### 测试数据策略（已定）

- **测试期**：`tests/test_analyzer_live.py` 里维护 `STYLE_FIXTURES`（4 个风格各 3 篇配对文案）+ 调 helper 从 `material/<style>/` 加载图转 base64 data URI。**文案和图片同风格、同切换**，保证 analyzer 拿到的是一致输入
- **生产期**：collector 真实运行后，`CollectedContent.posts` 已带 http URL 图 + 真实笔记文案，analyzer 透传给 vision/text LLM，**业务代码无需任何修改**
- **代码侧透明**：`tools/llm.py::chat_with_images` 的 `image_url.url` 字段同时接受 http URL 和 `data:image/...;base64,...`，对 LLM 来说两者等价
- **`examples/analyzer_input_sample.json` 角色**：仅作为给上下游队友看 schema 结构的"对外契约样例"（保留奶油风文案不影响），**测试代码不再加载它**

**测试风格清单**（可逐个跑验证 analyzer 对不同风格的辨识能力）：

| 风格 | 目录 | 文件 |
|------|------|------|
| 新中式 | `material/新中式/` | 1.PNG / 2.PNG / 3.PNG |
| 日式原木 | `material/日式原木/` | 1.jpeg / 2.jpeg / 3.jpeg |
| 极简自然风 | `material/极简自然风/` | 1.png / 2.png / 3.png |
| 法式中古风 | `material/法式中古风/` | 1.png / 2.png / 3.png |

> `material/毛坯房/` 是给下游 generator/prompter 的"户型空白图"，**不是 analyzer 的输入**，跳过。

---

## 9. 测试入口

```python
# tests/test_analyzer_live.py
"""真实跑 analyzer（吃真 LLM），打印 StyleDNA。
开发期数据：本地维护的 STYLE_FIXTURES（文案）+ material/<style>/ 本地图（视觉），
两者风格严格配对，保证 analyzer 拿到的输入不打架。
"""
import asyncio
import base64
from datetime import datetime
from pathlib import Path

from core.agents.analyzer.agent import run
from core.schemas import CollectedContent, CollectedPost


MATERIAL_DIR = Path(
    "/Users/kafka/Desktop/files/bussiness_test/Hackathon/Beyond Prompt: Agents in Action/material"
)
TEST_STYLE = "日式原木"  # 可切换：新中式 / 极简自然风 / 法式中古风


# ============================================================
# 4 套配对 fixture
# 文案中描述的色彩 / 材质 / 氛围词与 material/<style>/ 图片视觉一致
# ============================================================
STYLE_FIXTURES = {
    "新中式": {
        "target_account_id": "xhs_dongfangyun",
        "posts": [
            {
                "post_id": "xhs_001_zhongshi",
                "title": "100㎡新中式，黑胡桃 + 月白绒布把家做成了茶室",
                "body": "终于装完啦！新中式最难的就是分寸感，多一分老气、少一分单薄。我家选了黑胡桃木做主调，月白色绒布沙发压住调子，黄铜把手做点缀。客厅墙面留白只挂了一幅水墨，地面铺哑光大理石。最爱玄关那盏铜灯，傍晚开起来整个家都暖了。新中式不是堆元素，是留白的艺术。",
                "metadata": {"likes": 9821, "comments": 312, "collects": 4502, "publish_time": "2026-04-12"},
            },
            {
                "post_id": "xhs_002_zhongshi",
                "title": "茶室角一平米，把日子过出诗意",
                "body": "家里硬挤出来的茶室角，黑胡桃矮几 + 月白蒲团 + 一盏铜壶。墙上挂水墨小品，旁边搁支白瓷瓶。每天泡杯茶坐这里读半小时书，整个人都松了。新中式真的是中国人骨子里的审美，不需要懂多少，喜欢就够了。",
                "metadata": {"likes": 6234, "comments": 198, "collects": 3210, "publish_time": "2026-05-03"},
            },
            {
                "post_id": "xhs_003_zhongshi",
                "title": "玄关黄铜把手细节，新中式的灵魂在五金件",
                "body": "全屋装修最值的就是把柜门把手全换成黄铜。一开始觉得只是细节，住进来发现真不一样——每次开柜门都有点小仪式感。新中式的灵魂从来不在大件家具，而在五金、灯具、画轴这些不起眼的地方。",
                "metadata": {"likes": 5872, "comments": 145, "collects": 2891, "publish_time": "2026-05-28"},
            },
        ],
    },
    "日式原木": {
        "target_account_id": "xhs_yuanmuwu",
        "posts": [
            {
                "post_id": "xhs_001_riyuan",
                "title": "85㎡日式原木风，全屋都是治愈感",
                "body": "日式原木风装下来真的太爱了。全屋大量原木：橡木餐桌、白蜡木衣柜、藤编置物架。墙面统一刷白，地板浅色橡木复合地板。窗帘亚麻材质，下午阳光透过来是漫射的柔和感。家里几乎没有装饰画，但每个角落都摆了绿植——龟背竹、琴叶榕、玉露。极简但不冷，住进来每天心情都好。",
                "metadata": {"likes": 8765, "comments": 234, "collects": 4123, "publish_time": "2026-04-20"},
            },
            {
                "post_id": "xhs_002_riyuan",
                "title": "客厅藤编 + 漫射光，下班回来瘫一晚",
                "body": "客厅最爱的两样：藤编沙发椅 + 一盏纸灯。纸灯的漫射光特别治愈，亮但不刺眼。沙发椅藤编面坐久不闷，软垫是亚麻面料。日式风的精髓就是材质——原木、藤、亚麻、纸，全是温润的天然材质，呆久了真的会有种被治愈的感觉。无印良品风没有错。",
                "metadata": {"likes": 6543, "comments": 167, "collects": 3287, "publish_time": "2026-05-10"},
            },
            {
                "post_id": "xhs_003_riyuan",
                "title": "卧室白蜡木衣柜定制完，温柔感拉满",
                "body": "纠结很久最后选了白蜡木做衣柜，价格比板材贵一倍但真的值。木纹清晰、颜色温润，跟整屋原木调完全融为一体。柜门是无把手设计，干净利落。床头摆一盏小台灯，亚麻床品，墙上贴一幅暖色挂画。日式不是性冷淡，是温暖的克制。",
                "metadata": {"likes": 5421, "comments": 132, "collects": 2654, "publish_time": "2026-05-25"},
            },
        ],
    },
    "极简自然风": {
        "target_account_id": "xhs_qingjianjia",
        "posts": [
            {
                "post_id": "xhs_001_jijian",
                "title": "极简控的全屋自然色系，每天都像在度假",
                "body": "极简自然风，不堆砌不复杂。墙面雾灰白乳胶漆，地板灰咖色微水泥。家具走 less is more 路线：一张大沙发、一张长餐桌、一盏垂吊灯。色彩控制在米白、灰、卡其、燕麦色 4 个色域里。最重要的是大量留白，让空间自己呼吸。住进来才明白，少即是多不是口号，是生活方式。",
                "metadata": {"likes": 11234, "comments": 421, "collects": 5872, "publish_time": "2026-04-05"},
            },
            {
                "post_id": "xhs_002_jijian",
                "title": "雾灰白墙 + 微水泥地，高级感从基础开始",
                "body": "整屋只用两种基础色：墙面雾灰白、地面微水泥灰咖。看似单调，住进来才知道是高级感的基础。没有花花绿绿的硬装、没有复杂线条、没有过度装饰。家具家电的色彩都自动收敛进这个体系。极简风的难点不在加什么，而在敢减什么。",
                "metadata": {"likes": 7892, "comments": 256, "collects": 3654, "publish_time": "2026-05-08"},
            },
            {
                "post_id": "xhs_003_jijian",
                "title": "高级灰客厅，留白才是真奢华",
                "body": "客厅整体高级灰调，沙发燕麦色，地毯卡其色。墙上没有挂画，留了大面积空白。茶几上只放一本书 + 一支花瓶。极简从来不是空，是精挑细选每一件物品。每个出现在视野里的东西都必须有理由。住进来三个月，反而越来越不想买东西了。",
                "metadata": {"likes": 6321, "comments": 187, "collects": 3012, "publish_time": "2026-06-01"},
            },
        ],
    },
    "法式中古风": {
        "target_account_id": "xhs_zhongguyou",
        "posts": [
            {
                "post_id": "xhs_001_fashi",
                "title": "复古法式中古风改造完工！每个角落都像油画",
                "body": "法式中古风真的让家有了灵魂。墙面用脏粉色 + 法式护墙板线条，地板做人字拼鱼骨地板，颜色偏暗的橡木。家具全部是中古单品：复古天鹅绒沙发、雕花木桌、铜质烛台。配上几幅油画和老式挂钟。每个细节都在讲故事，氛围感无敌。法式中古最迷人的就是时间的痕迹，新东西做不出来。",
                "metadata": {"likes": 14523, "comments": 587, "collects": 7234, "publish_time": "2026-03-28"},
            },
            {
                "post_id": "xhs_002_fashi",
                "title": "人字拼鱼骨地板 + 脏粉色墙，复古感的关键",
                "body": "整屋装修最贵也最值的就是人字拼地板。深色橡木做人字拼，配脏粉色护墙板，复古感瞬间到位。法式中古不是法式简约，要的就是这种带年代感的色调和工艺。再加一盏老式黄铜吊灯，氛围感拉满。新房做出旧时光的感觉，这就是法式中古的魅力。",
                "metadata": {"likes": 9876, "comments": 342, "collects": 4587, "publish_time": "2026-04-25"},
            },
            {
                "post_id": "xhs_003_fashi",
                "title": "复古天鹅绒沙发 + 铜烛台，氛围感全靠它们",
                "body": "客厅 C 位是一张墨绿色天鹅绒沙发，配一对铜质烛台 + 大理石茶几。墙上挂几幅小油画，旁边搁一台老式留声机（装饰用）。最近又淘了一对中古黄铜壁灯，晚上点起来整个客厅都柔了。法式中古就是不断淘宝、不断完善，享受这个过程。",
                "metadata": {"likes": 8234, "comments": 271, "collects": 3987, "publish_time": "2026-05-20"},
            },
        ],
    },
}


# ============================================================
# helper: 本地图 → base64 data URI
# ============================================================
def _local_image_to_data_uri(path: Path) -> str:
    suffix = path.suffix.lower()
    mime = "image/png" if suffix == ".png" else "image/jpeg"
    b64 = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime};base64,{b64}"


def _build_mock_image_urls(style: str) -> list[str]:
    style_dir = MATERIAL_DIR / style
    return [
        _local_image_to_data_uri(p)
        for p in sorted(style_dir.iterdir())
        if p.suffix.lower() in (".jpg", ".jpeg", ".png")
    ]


# ============================================================
# 主入口：从 STYLE_FIXTURES + material/ 构造 CollectedContent
# ============================================================
async def main():
    fixture = STYLE_FIXTURES[TEST_STYLE]
    mock_urls = _build_mock_image_urls(TEST_STYLE)

    content = CollectedContent(
        target_account_id=fixture["target_account_id"],
        collected_at=datetime.now(),
        posts=[
            CollectedPost(
                post_id=p["post_id"],
                title=p["title"],
                body=p["body"],
                metadata=p["metadata"],
                image_urls=[mock_urls[i]] if i < len(mock_urls) else [],
            )
            for i, p in enumerate(fixture["posts"])
        ],
    )

    style = await run(content)
    print(f"=== 测试风格：{TEST_STYLE} ===")
    print(style.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
```

跑：`python -m tests.test_analyzer_live`

**预期**：StyleDNA 的 `visual.color_palette` / `material` / `composition` / `lighting` 应该和 `copy.voice` / `keywords` / `hashtag_pattern` **在同一个风格上自洽**（视觉说黑胡桃 + 月白 + 留白，文案说新中式 + 茶室 + 黄铜五金）。如果切换 4 个风格跑下来都能产出风格一致的 StyleDNA，说明视觉 + 文案双通道都正常，且**两通道不打架**。

> 如果发现某次跑出来 `visual` 描述新中式但 `copy` 描述日式，说明输入 fixture 配错了（图和文案不是一套风格），不是 analyzer 的问题——回去检查 STYLE_FIXTURES。

---

## 10. 为什么这么设计（一句话理由）

- **样本筛选按互动量降序** —— 粉丝喜欢的笔记定义风格，不是随便挑
- **视觉 + 文案双通道并行** —— 错误隔离 + Prompt 各管一摊 + 时间不浪费
- **3 级兜底** —— 主链路永不挂（hackathon demo 关键）
- **抽到 tools/llm.py** —— prompter / copywriter 后面要用，今天就铺好
- **Prompt 里贴完整 JSON 示例** —— 比单纯描述字段稳得多，业内成熟做法
