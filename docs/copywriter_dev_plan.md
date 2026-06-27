# Copywriter Agent 开发计划

> Step 5 · 文案 Agent 的真实实现计划（`core/agents/copywriter/`）
>
> 负责：kafka · 状态：**已实现 / 已联调进非 collector 主链路** · 创建：2026-06-27
>
> 本文档是 `core/agents/copywriter/SKILL.md` 契约的**实施细节版**。SKILL.md 是"对外契约"（给 loader / 评委 / 队友看），本文档是"开发笔记"（只给 kafka 自己看）。
>
> 结构与 `docs/analyzer_dev_plan.md` 严格对齐，便于对照。

---

## ★ 产品定位 · 文案的核心目的（2026-06-27 kafka 澄清，统领全文）

> **一句话**：copywriter 产出的不是"自嗨的文艺种草文案"，而是**帮家装公司营销获客的内容**——核心是展示「我们针对客户的 query 生成的效果图」有多好。

### 三要素

| 维度 | 内容 |
|------|------|
| **主体** | 我们针对客户的户型/需求（query）**量身定制生成**的设计效果图 |
| **目的** | 展示这套设计方案有多好，让读到的人想"我也要找他们设计" → **帮家装公司获客** |
| **手段** | 用「对标账号的爆款文案语气」（风格 DNA）来包装营销卖点——语气是外衣，营销是内核 |

### 视角融合（关键，别写拧了）

小红书家装获客内容的成熟套路 = **用博主的口吻讲"这个设计方案多绝"，暗藏"找同款设计师"的转化钩子**。所以：
- **形式**：对标账号的第一人称种草语气（治愈系 / 雅致 / 极简 / 浪漫，由 `StyleDNA.copy` 决定）
- **实质**：展示**我们生成的**效果图的营销卖点（材质巧 / 收纳足 / 氛围好 / 解决了这个户型的痛点）
- **不是**：单纯模仿博主写一篇跟"我们的效果图"无关的装修日记

### 这个定位对设计的 4 条约束

1. **户型 query 是叙事主线**（不是背景板）：文案要让读者感到"这是为**我这个户型/需求**定制的完美方案"。`UserRequest.user_notes`（户型信息）从"背景"升级为"营销切入点"
2. **D1 看图更必须了**：核心就是"展示效果图多好"，不看图怎么描述它的好？看图 = 让效果图自己"说话"
3. **Prompt 必须营销导向**（见 §4.4）：System Prompt 明确"你是家装公司内容营销写手，目的是展示这套效果图帮公司获客"，而非泛泛"写一篇种草笔记"
4. **少样本示例要体现 query 驱动**：示例 body 应展示"为某户型需求做的方案亮点 + 转化钩子"，而非泛泛装修心得

### ToB 价值闭环（路演讲这条）

```
企业用户（家装公司）输入客户 query（户型 / 需求）
    → 我们生成针对性效果图（generator）
    → copywriter 用爆款账号语气，包装成"展示这套设计多好"的营销图文
    → 家装公司直接发小红书获客
```

→ copywriter 的 ToB 价值 = **把"设计能力"自动转化为"获客内容"**，这是产品差异化的核心卖点之一。

---

## 0. 已拍板决策（5 个决策，按推荐方案实现）

> 这些是写代码前必须定的设计岔路。每个都给了推荐 + 理由，你勾"采纳推荐"或改即可。**未拍板前不动手实现。**

| # | 决策点 | 选项 | **推荐** | 理由 |
|---|--------|------|---------|------|
| **D1** | copywriter 要不要**看图**（多模态）？ | A. 多模态看图 / B. 纯文本只吃 StyleDNA+户型 | **A 看图** | 评委/企业客户看的就是"文案配不配图"。不看图 LLM 会瞎编图里没有的家具，扣完成度分。doubao 多模态 analyzer 已验证可用，零新增成本 |
| **D2** | 户型信息怎么给？ | A. 编一段文字塞 `user_notes` / B. 看 `floorplan_image_url` 户型图 | **A 编文字** | 你已说"编一段话就行"。户型图（毛坯房）对文案生成帮助有限，文字描述（面积/房型/居住人/痛点）信息密度更高且不占 vision token |
| **D3** | LLM 输出用什么格式？ | A. JSON（title/body/hashtags）/ B. 纯文本按标记切分 | **A JSON** | 跟 analyzer 一致、解析可靠、可校验字段。body 里的 emoji/换行 JSON 字符串能正常转义，不影响文案自然度 |
| **D4** | 测试默认风格？ | 4 选 1 | **日式原木** | 跟 analyzer 默认 `TEST_STYLE` 一致，端到端（analyzer→copywriter）衔接最顺；其余 3 个风格做交叉验证 |
| **D5** | 设计图 mock 用哪个目录？ | material/ 的 4 个风格目录 | **和 TEST_STYLE 联动** | 复用 analyzer 的 4 风格交叉验证套路，验证"不同风格 → 文案风格不同 + 都描述了图里真实元素" |

> 本文后续章节（Prompt / 测试代码 / 兜底）**全部按推荐方案（A/A/A/日式原木/联动）写**。若你改某项，相应章节跟着调。

---

## 1. 已敲定的技术决策（**全部复用 analyzer，本次零新增基础设施**）

| 项 | 值 | 来源 |
|---|---|---|
| LLM | `doubao-seed-2-0-pro-260215`（多模态） | analyzer 已选定 |
| API | `https://api.openai-next.com/v1/chat/completions`（OpenAI 兼容） | analyzer 已选定 |
| API key | 已在 `.env`（gitignored） | analyzer 已建 |
| LLM client | `tools/llm.py`（`chat` + `chat_with_images`） | analyzer 已写好，**copywriter 直接 import** |

**analyzer 踩过的 3 个坑，copywriter 直接受益（无需再踩）**：
1. **SOCKS 代理** → `llm.py` 已加 `trust_env=False` ✅
2. **大 payload**（material PNG ~1.5MB，base64 后 ~3MB，doubao 网关拒收）→ 测试 helper 用 Pillow 预压缩（长边 1024 + JPEG 75）✅
3. **429 限流** → 兜底链加 HTTP backoff ✅

> 结论：copywriter 这次**不需要碰 `tools/llm.py`、不需要碰 `.env`、不需要新装包**。只写 `copywriter/` 目录内的 4 个文件 + 1 个测试文件。

---

## 2. 目标 & 边界

**做什么**：把 `core/agents/copywriter/agent.py` 从硬编码 mock 改成**真实多模态 LLM 调用**——吃 `StyleDNA`（账号文案风格）+ `GeneratedImages`（设计图）+ `UserRequest`（户型），吐出符合该账号语气、且描述了图里真实元素的小红书图文。

**不做什么**：
- 上下游 Agent（collector / analyzer / prompter / generator）保持现状
- skill_loader、前后端联调
- 性能优化（重试 1 次后失败就兜底，不做指数退避）

---

## 3. 输入输出契约

| 项 | 文件 / 类型 |
|---|------|
| 输入 1 | `core/schemas.py::StyleDNA`（主要用 `copy` 字段） |
| 输入 2 | `core/schemas.py::GeneratedImages`（用 `image_urls`） |
| 输入 3 | `core/schemas.py::UserRequest`（用 `user_notes` 编的户型 + `floorplan_meta`） |
| 输出 | `core/schemas.py::CopyContent`（`title` / `body` / `hashtags`） |

**关键字段（容易写错）**：
- `StyleDNA.copy` 是 `dict`，键：`voice` / `keywords` / `sentence_pattern` / `hashtag_pattern`（**注意是 `hashtag_pattern` 不是 `hashtags`**）
- `StyleDNA.visual` 也是 `dict`，键：`color_palette` / `material` / `composition` / `lighting`（copywriter 参考，确保文案材质词和图一致）
- `GeneratedImages.image_urls` 是 `list[str]`（http URL 或 data URI 均可，见下）
- `UserRequest.user_notes` 是 `Optional[str]` ← 户型文字塞这里
- `UserRequest.floorplan_image_url` 必填但 copywriter **不用它**（D2 决定看文字不看户型图）→ 测试时给占位值
- `CopyContent.hashtags` ← 注意是 `hashtags`（输出），和输入的 `hashtag_pattern`（输入）名字不同

**开发期 vs 生产期的图片来源（复用 analyzer 结论）**：

- **生产期 / 当前联调期**：generator 已接入真实图片生成时，`GeneratedImages.image_urls` 返回 `/static/generated/<file>.png`；copywriter 会自动读取本地 `data/generated/<file>.png`，压缩并转成 data URI 给多模态 LLM。若未来 generator 返回公网 http URL，也可直接透传
- **单元测试期**：仍可用 `material/<style>/` 的**设计风格图**当"生成的设计图"mock——这些图本身就是设计效果图，语义对得上
- **代码侧透明**：`tools/llm.py::chat_with_images` 同时支持 http URL 和 `data:image/...;base64,...`，copywriter 业务主逻辑不关心图片来自真实生成、公网 URL 还是本地测试 fixture

---

## 4. 文案生成核心逻辑 [★ 本文档主体]

### 4.1 总体编排（`agent.py` 主入口）

**关键设计**：copywriter 是**单次多模态调用**（不像 analyzer 的双通道并行）。一次把"风格指令 + 户型 + 图"全喂进去，让 LLM 在一个上下文里产出图文自洽的文案。

> ⚠️ 文案的**核心目的不是写文艺种草，而是营销**：展示「我们针对客户 query 生成的效果图」多好，帮家装公司获客（见开头★产品定位）。这一条直接决定 §4.4 的 Prompt 写法——风格 DNA 只是"语气外衣"，营销才是"内核"。

```python
async def run(style: StyleDNA, images: GeneratedImages, request: UserRequest) -> CopyContent:
    # 步骤 1: 组装风格指令（从 StyleDNA.copy 提取）
    style_brief = _build_style_brief(style)        # voice / keywords / 句式 / hashtag

    # 步骤 2: 取户型文字（编的，或生产期真实 user_notes）
    floorplan_text = _extract_floorplan_text(request)

    # 步骤 3: 取设计图（≤ 4 张，防 token 爆）
    image_urls = images.image_urls[:4]

    # 步骤 4: 多模态调用（含 3 级兜底）
    raw = await _call_with_retry(
        call_fn=lambda error_hint=None: chat_with_images(
            system=COPYWRITER_SYSTEM_PROMPT,
            user_text=COPYWRITER_USER_PROMPT_TEMPLATE.format(
                style_brief=style_brief,
                floorplan=floorplan_text,
                error_hint=error_hint,
            ),
            image_urls=image_urls,
            temperature=0.8,   # 文案略高温度，更有"人味"
        ),
        parse_fn=_parse_copy_json,
        mock_fallback=MOCK_COPY,
    )

    # 步骤 5: 组装 CopyContent
    return CopyContent(
        title=raw["title"],
        body=raw["body"],
        hashtags=raw["hashtags"],
    )
```

**为什么单次调用（不拆 title/body 分两次）？** 文案的标题、正文、话题是一个整体，分开调容易风格撕裂（标题治愈系、正文突然硬广）。一个上下文一次产出，自洽性最好。

**为什么 `temperature=0.8`？** 文案需要创造力（比 analyzer 分析的 0.7 略高），但不能太高（>1.0 会胡言乱语、丢 hashtag）。

---

### 4.2 风格指令组装（`_build_style_brief`）

把 `StyleDNA.copy` 这个 dict 拼成 LLM 能读懂的"人话风格简报"：

```python
def _build_style_brief(style: StyleDNA) -> str:
    copy = style.copy or {}
    voice = copy.get("voice", "治愈系温暖叙事")
    keywords = copy.get("keywords", [])
    sentence = copy.get("sentence_pattern", "短句为主，适度 emoji")
    hashtags = copy.get("hashtag_pattern", [])

    kw = "、".join(keywords[:8]) if keywords else "（无）"
    ht = " ".join(hashtags[:6]) if hashtags else "（无）"

    return (
        f"【该账号文案风格 DNA —— 必须严格复刻】\n"
        f"- 整体语气：{voice}\n"
        f"- 高频关键词：{kw}\n"
        f"- 句式特点：{sentence}\n"
        f"- 惯用话题：{ht}\n"
    )
```

**为什么这么拼？** LLM 对"结构化人话"比"原始 JSON"理解更准。直接把 dict 丢进去它也行，但拼成简报后风格复刻度明显更高（业内 prompt 工程经验）。

---

### 4.3 LLM 调用形态（多模态）

```python
messages = [
    {"role": "system", "content": COPYWRITER_SYSTEM_PROMPT},
    {"role": "user", "content": [
        {"type": "text", "text": COPYWRITER_USER_PROMPT_TEMPLATE.format(...)},
        {"type": "image_url", "image_url": {"url": "<设计图1>"}},
        {"type": "image_url", "image_url": {"url": "<设计图2>"}},
        # ... ≤ 4 张
    ]},
]
```

走 `tools/llm.py::chat_with_images`，零自己造轮子。

---

### 4.4 Prompt 草稿

> Prompt 是落地"★ 产品定位"的核心载体——营销目的 + query 驱动 + 看图描述，三层都要写进 Prompt。

#### System Prompt

```
你是顶级家装公司的内容营销写手。你的任务：用「对标账号的爆款文案风格」包装一套「我们针对客户需求（query）量身生成的设计效果图」，写出一篇展示这套设计有多好的小红书图文，目的是吸引潜在业主、帮公司获客。

【核心目的（最重要）】
- 这套效果图是我们针对客户的具体户型/需求定制的——文案要让读者感到"这正是解决我家问题的方案"
- 突出效果图里的真实设计亮点（材质 / 色彩 / 布局 / 收纳 / 氛围），让效果图自己"说话"
- 终极目标：读到的人想"我也要找他们设计" → 帮家装公司获客

【硬性要求】
1. 标题 ≤ 20 字，钩子来自"户型痛点 + 这套设计的解决方案"（悬念 / 数字 / 反差），可含 1-2 个 emoji
2. 正文 150-300 字：
   - 围绕客户的户型 query 展开（这是为这个需求定制的方案）
   - 必须描述图片里能真实看到的设计元素（材质 / 色彩 / 家具 / 布局 / 收纳），不许凭空编造图里没有的东西
   - 用对标账号的语气写（风格 DNA），但服务于"展示这套设计多好"
3. 严格复刻风格 DNA 的语气 / 句式 / 高频词
4. hashtag 5-8 个，复刻该账号惯用话题，可加 1-2 个户型/需求相关话题
5. 只输出一个 JSON 对象，不要任何 markdown 代码块包裹，不要任何解释性文字
```

#### User Prompt（template）

```
{style_brief}

【客户的需求 / Query —— 我们就是针对这个生成的设计方案】
{floorplan}

【你的任务】
请观察下方「我们针对上述需求生成的设计效果图」，用上面的风格 DNA 语气，写一篇展示这套设计有多好的小红书营销图文。严格按此 JSON schema 输出：

{{
  "title": "标题（≤20字）",
  "body": "正文（150-300字，小红书风格，含 emoji 和换行）",
  "hashtags": ["#话题1", "#话题2", "#话题3", "#话题4", "#话题5"]
}}

【参考输出示例 —— 注意：围绕"85㎡ 日式需求"展开，突出设计亮点 + 转化钩子】
{{
  "title": "85㎡塞下原木+猫爬架？这套日式方案太绝了🌿",
  "body": "业主需求很明确：85㎡两室一厅，一对夫妻一只猫，要治愈、要收纳、还要给猫留地儿✨\\n\\n看这套方案：橡木餐桌配白蜡木通顶柜，收纳直接拉满还不显挤；客厅一面墙做了藤编猫爬架，猫的活动空间和原木风完美融为一体🌱；亚麻窗帘 + 无主灯漫射光，下午整个家都是温柔的柔光感。\\n\\n最难的是把'治愈'和'实用'同时塞进 85㎡——这套方案做到了。想要同款的可以留言～",
  "hashtags": ["#日式原木", "#85平装修", "#小户型收纳", "#治愈系家居", "#宠物友好家装"]
}}

{error_hint}

现在请观察以下设计图并输出：
```

> `{error_hint}` 在第一次调用时为空字符串；重试时填入上次解析失败的错误信息（如"上次 body 字段缺失，请补全"），让 LLM 自我纠正——和 analyzer 的兜底链一致。

**Prompt 设计要点（落地★产品定位）**：
- **营销目的写进 System** —— 明确"展示我们效果图多好、帮家装公司获客"，而非泛泛种草
- **query 驱动叙事** —— 户型需求是叙事主线，示例 body 开头即"业主需求很明确"
- **必须描述图里真实元素，不许凭空编造** —— D1 看图的核心收益，逼 LLM 言之有物（让效果图说话）
- **少样本示例带转化钩子** —— 结尾"想要同款的可以留言"暗藏获客转化
- **风格 DNA 放最前** —— LLM 对开头信息权重最高（语气是外衣，营销是内核）

---

### 4.5 JSON 解析 + 校验

```python
def _parse_copy_json(text: str) -> dict:
    """LLM 输出 → 文案 dict。做 4 件事：
    1. 剥掉可能的 ```json ... ``` 包裹
    2. JSON 解析
    3. 必填字段校验（title / body / hashtags）
    4. 类型 + 基础长度校验
    """
    cleaned = _strip_markdown_fence(text)
    data = json.loads(cleaned)

    # 必填字段
    if "title" not in data:
        raise ValueError("copy: 缺少字段 title")
    if "body" not in data:
        raise ValueError("copy: 缺少字段 body")
    if "hashtags" not in data:
        raise ValueError("copy: 缺少字段 hashtags")

    # 类型校验
    if not isinstance(data["title"], str) or not data["title"].strip():
        raise ValueError("copy: title 必须是非空字符串")
    if not isinstance(data["body"], str) or len(data["body"]) < 20:
        raise ValueError("copy: body 必须是 ≥20 字的字符串")
    if not isinstance(data["hashtags"], list) or len(data["hashtags"]) == 0:
        raise ValueError("copy: hashtags 必须是非空列表")

    return data
```

> 长度校验**宽松**（body ≥20 字即可，不卡 150-300 硬区间）——避免 LLM 偶尔输出 140 字就兜底，hackathon 优先"出稿"。

`_strip_markdown_fence` 直接复用 analyzer 的实现（见 §6 文件清单，从 `core/agents/analyzer/agent.py` 抄或抽公共——**推荐抽公共**，见 §11）。

---

### 4.6 兜底链（3 级，与 analyzer 一致）

```
[1st 调用] → 解析成功？ → 返回
                 ↓ 失败
[2nd 调用，附带 error_hint] → 解析成功？ → 返回
                 ↓ 失败
[3rd: 用 MOCK_COPY 兜底]  ← 主链路永不挂
```

```python
async def _call_with_retry(call_fn, parse_fn, mock_fallback):
    """call_fn(error_hint=None) → 文本；parse_fn(文本) → dict；失败回 mock。
    与 analyzer 的 _call_with_retry 同构。"""
    try:
        return parse_fn(await call_fn())
    except (json.JSONDecodeError, ValueError) as e:
        try:
            return parse_fn(await call_fn(error_hint=f"上次输出有误：{e}，请修正后重新输出完整 JSON。"))
        except Exception:
            return mock_fallback
    except Exception:
        return mock_fallback
```

---

### 4.7 开发期 fixture（4 风格 StyleDNA mock + 设计图 + 编的户型）

**核心原则**（复用 analyzer）：测试期 **StyleDNA 风格、设计图、文案预期** 三者必须同一风格，否则分不清是 prompt 差还是输入打架。

#### 4.7.1 4 套 StyleDNA mock（手写，对应 analyzer 4 风格交叉验证结果）

> 为什么手写而不调 analyzer 拿真实输出？copywriter 单元测试要**快、独立、可复现**。analyzer 已验证过，copywriter 不该耦合它（耦合了测试就慢 + 耗 token + 失败难定位）。手写 mock 还能精确控制输入测不同 voice 的响应。

```python
STYLE_DNA_MOCKS = {
    "日式原木": StyleDNA(
        target_account_id="xhs_yuanmuwu",
        visual={
            "color_palette": ["原木棕", "米白", "浅灰"],
            "material": ["橡木", "白蜡木", "亚麻", "藤编"],
            "composition": "大面积留白，绿植点缀，对称弱",
            "lighting": "漫射柔光为主，无主灯",
        },
        copy={
            "voice": "治愈系第一人称温暖叙事，强调被治愈的日常感",
            "keywords": ["原木", "藤编", "亚麻", "治愈", "漫射光", "绿植", "温润"],
            "sentence_pattern": "短句为主，感叹号适度，emoji 点缀（🌿✨）",
            "hashtag_pattern": ["#日式原木", "#家装日记", "#治愈系家居", "#原木风装修", "#无印良品风"],
        },
        sample_post_ids=["xhs_001_riyuan", "xhs_002_riyuan", "xhs_003_riyuan"],
    ),
    "新中式": StyleDNA(
        target_account_id="xhs_dongfangyun",
        visual={
            "color_palette": ["深胡桃棕", "月白", "黄铜金"],
            "material": ["黑胡桃木", "绒布", "黄铜", "岩板"],
            "composition": "留白为主，对称构图，水墨点缀",
            "lighting": "暖光为主，铜灯营造仪式感",
        },
        copy={
            "voice": "雅致内敛，讲分寸感与留白的艺术",
            "keywords": ["黑胡桃", "月白", "黄铜", "茶室", "留白", "分寸感", "新中式"],
            "sentence_pattern": "长短句结合，文气偏重，少 emoji",
            "hashtag_pattern": ["#新中式", "#茶室", "#黑胡桃", "#中式美学", "#家装日记"],
        },
        sample_post_ids=["xhs_001_zhongshi", "xhs_002_zhongshi", "xhs_003_zhongshi"],
    ),
    "极简自然风": StyleDNA(
        target_account_id="xhs_qingjianjia",
        visual={
            "color_palette": ["雾灰白", "燕麦", "卡其", "冷灰"],
            "material": ["微水泥", "原木", "棉麻"],
            "composition": "极致留白，少即是多，单点聚焦",
            "lighting": "无主灯，线性光",
        },
        copy={
            "voice": "克制理性，讲少即是多的生活方式",
            "keywords": ["极简", "雾灰白", "微水泥", "留白", "少即是多", "高级灰"],
            "sentence_pattern": "短句果断，少感叹号，几乎无 emoji",
            "hashtag_pattern": ["#极简风", "#微水泥", "#少即是多", "#极简主义", "#家装日记"],
        },
        sample_post_ids=["xhs_001_jijian", "xhs_002_jijian", "xhs_003_jijian"],
    ),
    "法式中古风": StyleDNA(
        target_account_id="xhs_zhongguyou",
        visual={
            "color_palette": ["奶油白", "脏粉", "胡桃棕", "湖蓝"],
            "material": ["天鹅绒", "橡木人字拼", "黄铜", "石膏线条"],
            "composition": "氛围感构图，复古单品为 C 位",
            "lighting": "暖黄光，铜烛台/壁灯营造氛围",
        },
        copy={
            "voice": "浪漫叙事，讲氛围感与时间痕迹的故事",
            "keywords": ["法式中古", "人字拼", "脏粉", "天鹅绒", "氛围感", "复古"],
            "sentence_pattern": "长句铺陈，感叹号多，emoji 偏浪漫（🤎🕯️）",
            "hashtag_pattern": ["#法式中古", "#复古风", "#人字拼", "#氛围感", "#家装日记"],
        },
        sample_post_ids=["xhs_001_fashi", "xhs_002_fashi", "xhs_003_fashi"],
    ),
}
```

#### 4.7.2 编的户型（UserRequest）

```python
MOCK_USER_REQUEST = UserRequest(
    target_account_id="xhs_yuanmuwu",   # 跟 TEST_STYLE 联动（测试里动态改）
    floorplan_image_url="",              # 占位 —— copywriter 不看户型图（D2）
    floorplan_meta={
        "area_sqm": 89,
        "layout": "两室一厅",
        "orientation": "南向",
    },
    user_notes=(
        "89㎡ 两室一厅，南北通透，南向主卧。"
        "常住一对年轻夫妻 + 一只猫，近一两年准备要小孩。"
        "希望整体温馨治愈、收纳充足、给猫留活动空间，预算 12-15 万。"
    ),
)
```

> 这就是你要我"编的一段话"——户型面积/房型/朝向/居住人/痛点/预算都齐了。你可以直接改这段文字调户型。

#### 4.7.3 设计图 mock（复用 material/ + 预压缩）

```python
MATERIAL_DIR = Path(
    "/Users/kafka/Desktop/files/bussiness_test/Hackathon/Beyond Prompt: Agents in Action/material"
)

def _local_image_to_data_uri(path: Path) -> str:
    """本地图 → base64 data URI（含 Pillow 预压缩，复用 analyzer 踩坑修复）。
    不压缩 doubao 网关会拒收 ~3MB payload。"""
    img = Image.open(path).convert("RGB")
    img.thumbnail((1024, 1024))        # 长边 1024
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=75)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/jpeg;base64,{b64}"

def _build_mock_design_images(style: str) -> GeneratedImages:
    """从 material/<style>/ 加载图当'生成的设计图'mock。
    style 取值：新中式 / 日式原木 / 极简自然风 / 法式中古风"""
    style_dir = MATERIAL_DIR / style
    urls = [
        _local_image_to_data_uri(p)
        for p in sorted(style_dir.iterdir())
        if p.suffix.lower() in (".jpg", ".jpeg", ".png")
    ]
    return GeneratedImages(
        image_urls=urls,
        prompts_used=ImagePromptBundle(positive_prompt="[mock]", negative_prompt="[mock]"),
    )
```

> `material/毛坯房/` 不是设计图，**跳过**（和 analyzer 一致）。

---

## 5. 错误处理矩阵

| 错误源 | 处置 |
|---|---|
| `.env` 没有 `OPENAI_API_KEY` | `tools/llm.py` 启动期直接 raise（analyzer 已处理） |
| HTTP 4xx/5xx | httpx 抛 → copywriter 捕获 → 重试 1 次 → 仍失败用 MOCK_COPY |
| LLM 输出带 ```` ```json ```` 包裹 | 解析前 strip（复用 analyzer） |
| LLM 输出 JSON 格式错 / 字段缺失 | 重试 1 次（带 error_hint）→ 失败 MOCK_COPY |
| LLM 输出 body 过短（<20 字） | 校验失败 → 走兜底 |
| 图片 URL 无法访问 | LLM 拒绝/乱猜 → 校验失败走兜底；**根本解法见 §8** |
| 调用超时（90s 多模态） | 走兜底 |

---

## 6. 代码组织（新增 / 修改文件清单）

```
core/agents/copywriter/
├── SKILL.md              # 已有，可小改（更新 status: skeleton → live，补实现细节）
├── agent.py              # ★ 重写：run + _build_style_brief + _extract_floorplan_text + _parse_copy_json + _call_with_retry
├── _prompts.py           # ★ 新增：COPYWRITER_SYSTEM_PROMPT + COPYWRITER_USER_PROMPT_TEMPLATE
├── _mocks.py             # ★ 新增：MOCK_COPY 兜底文案
└── __init__.py           # 已有，不动

tests/
├── test_copywriter_live.py  # ★ 新增：吃真 LLM 跑一次（4 风格可切）
└── _material_helpers.py     # ☆ 可选：把 analyzer + copywriter 共用的预压缩 helper 抽公共（见 §11）

不动的文件：tools/llm.py、.env、.env.example、core/schemas.py
```

---

## 7. 开发顺序（checklist）

**阶段 1 · Prompt + 兜底（20 分钟）**
- [x] 7.1 写 `_prompts.py`（SYSTEM + USER template）
- [x] 7.2 写 `_mocks.py`（MOCK_COPY）
- [x] 7.3 写 `_parse_copy_json` + `_strip_markdown_fence`
- [x] 7.4 写 `_call_with_retry`（抄 analyzer）

**阶段 2 · 主逻辑（20 分钟）**
- [x] 7.5 写 `_build_style_brief` + `_extract_floorplan_text`
- [x] 7.6 重写 `run()`（单次多模态调用 + 兜底）
- [x] 7.7 5 行小脚本调通"日式原木"一例

**阶段 3 · 测试 + 交叉验证（20 分钟）**
- [x] 7.8 写 `test_copywriter_live.py`（4 套 STYLE_DNA_MOCKS + material 设计图 + 编的户型）
- [x] 7.9 跑 4 风格交叉验证（文案风格 ↔ 设计图 ↔ StyleDNA 三者自洽）

**阶段 4 · 联调（5 分钟）**
- [x] 7.10 跑 `make smoke` 确认 orchestrator 能消费
- [ ] 7.11 commit（**等你明确说 push 再 push**）

**总预算：65 分钟内出 v1**（比 analyzer 快——基础设施已铺好）

---

## 8. 已知风险 & 兜底

| 风险 | 概率 | 影响 | 处置 |
|---|---|---|---|
| generator 返回 `/static/generated/...` 本地静态路径 | **已解决** | 中 | copywriter 自动映射到 `data/generated/<file>`，压缩并转 data URI 后给多模态 LLM |
| 单元测试期使用 material mock 图 | **已保留** | - | `test_copywriter_live.py` 继续用 `material/<style>/` 设计图做独立验证（见 §4.7.3） |
| LLM 输出 JSON 不严格 | 中 | 校验炸 | 解析层 strip + 重试 + MOCK_COPY 兜底 |
| doubao 限流 / 抖动 | 中 | 偶发 5xx | 90s 超时 + 兜底（analyzer 已验证 HTTP backoff 有效） |
| 单张设计图过大 | **已解决** | - | helper 预压缩（Pillow 长边 1024 + JPEG 75），复用 analyzer 修复 |
| LLM 文案和图对不上（瞎编家具） | 中 | 完成度扣分 | Prompt 强约束"必须描述图里真实元素"+ D1 看图；交叉验证时人工抽查 |
| `CopyContent` 字段名 `hashtags` vs 输入 `hashtag_pattern` 混淆 | 低 | AttributeError | §3 已标注，代码里注意 |

### 测试数据策略（已定）

- **测试期**：`test_copywriter_live.py` 维护 `STYLE_DNA_MOCKS`（4 风格手写 StyleDNA）+ 调 helper 从 `material/<style>/` 加载设计图 + `MOCK_USER_REQUEST`（编的户型）。三者同风格联动
- **生产期**：analyzer 真实产出 StyleDNA、generator 真实产出设计图、前端传真实 UserRequest，copywriter 透传，**业务代码零修改**
- **`python -m tests.smoke_from_collect`**：orchestrator 用 `data/collect/厚来设计` 跳过 collector，真实串联 analyzer / prompter / generator / copywriter；copywriter 会读取 generator 生成的本地效果图并输出最终营销文案

**测试风格清单**（复用 analyzer）：

| 风格 | 设计图目录 | 期望文案语气 |
|------|-----------|-------------|
| 日式原木（默认） | `material/日式原木/` | 治愈、原木藤编亚麻、漫射光 |
| 新中式 | `material/新中式/` | 雅致、黑胡桃月白黄铜、茶室留白 |
| 极简自然风 | `material/极简自然风/` | 克制、雾灰白微水泥、少即是多 |
| 法式中古风 | `material/法式中古风/` | 浪漫、人字拼脏粉天鹅绒、氛围感 |

---

## 9. 测试入口

```python
# tests/test_copywriter_live.py
"""真实跑 copywriter（吃真 doubao 多模态），打印 CopyContent。
开发期数据：手写 STYLE_DNA_MOCKS（风格）+ material/<style>/ 设计图（视觉）+ 编的户型。
三者风格严格联动，验证"文案复刻账号语气 + 描述了图里真实元素"。
"""
import asyncio
from pathlib import Path

from core.agents.copywriter.agent import run
from core.schemas import (
    GeneratedImages, ImagePromptBundle, StyleDNA, UserRequest,
)

MATERIAL_DIR = Path(
    "/Users/kafka/Desktop/files/bussiness_test/Hackathon/Beyond Prompt: Agents in Action/material"
)
TEST_STYLE = "日式原木"  # 可切换：新中式 / 极简自然风 / 法式中古风

# ============================================================
# 4 套 StyleDNA mock（见 §4.7.1，此处省略完整定义，开发时从文档拷）
# ============================================================
STYLE_DNA_MOCKS = { ... }

# ============================================================
# 编的户型（见 §4.7.2）
# ============================================================
def _build_mock_request(style: str) -> UserRequest:
    return UserRequest(
        target_account_id=STYLE_DNA_MOCKS[style].target_account_id,
        floorplan_image_url="",
        floorplan_meta={"area_sqm": 89, "layout": "两室一厅", "orientation": "南向"},
        user_notes=(
            "89㎡ 两室一厅，南北通透，南向主卧。"
            "常住一对年轻夫妻 + 一只猫，近一两年准备要小孩。"
            "希望整体温馨治愈、收纳充足、给猫留活动空间，预算 12-15 万。"
        ),
    )


# ============================================================
# 设计图 mock（预压缩，见 §4.7.3）
# ============================================================
def _build_mock_design_images(style: str) -> GeneratedImages: ...


# ============================================================
# 主入口
# ============================================================
async def main():
    style_dna = STYLE_DNA_MOCKS[TEST_STYLE]
    images = _build_mock_design_images(TEST_STYLE)
    request = _build_mock_request(TEST_STYLE)

    copy = await run(style_dna, images, request)
    print(f"=== 测试风格：{TEST_STYLE} ===")
    print(f"标题：{copy.title}")
    print(f"\n正文：\n{copy.body}")
    print(f"\n话题：{' '.join(copy.hashtags)}")


if __name__ == "__main__":
    asyncio.run(main())
```

跑：`python -m tests.test_copywriter_live`

**预期（4 风格交叉验证）**：
1. **文案语气 ↔ StyleDNA 自洽**：日式原木出治愈系文案、新中式出雅致文案……切风格语气明显不同
2. **文案 ↔ 设计图自洽**：文案里提到的家具/材质/色彩，在 `material/<style>/` 图里**能真实看到**（不瞎编）
3. **hashtag 复刻**：话题词和 StyleDNA.copy.hashtag_pattern 风格一致

> 如果某风格跑出来文案讲日式但图是法式，说明 `STYLE_DNA_MOCKS[style]` 和 `_build_mock_design_images(style)` 没联动好——回去检查 TEST_STYLE 是否一致传入两处。

---

## 10. 为什么这么设计（一句话理由）

- **文案是营销获客内容，不是自嗨种草** —— 核心 = 展示「我们针对客户 query 生成的效果图」多好，帮家装公司获客；风格 DNA 只是语气外衣（见开头★产品定位）
- **多模态看图（D1）** —— 评委看的就是"文案配不配图"，看图让文案言之有物，是企业客户最看重的
- **单次调用（不分 title/body）** —— 标题正文话题是一个整体，一次产出最自洽
- **风格 DNA 拼成"人话简报"** —— LLM 对结构化人话理解比原始 JSON 准
- **JSON 输出（D3）** —— 跟 analyzer 一致、解析可靠、可校验
- **3 级兜底** —— 主链路永不挂（hackathon demo 关键）
- **手写 StyleDNA mock** —— 测试快、独立、可复现，不耦合 analyzer
- **零新增基础设施** —— llm.py / doubao / .env / 踩坑修复全是 analyzer 铺好的，copywriter 只写自己目录

---

## 11. 与 analyzer 的复用关系（本次零新增基础设施）

| analyzer 已铺好 | copywriter 如何用 |
|----------------|------------------|
| `tools/llm.py`（`chat_with_images` + `trust_env=False`） | 直接 import，零修改 |
| doubao 多模态 API 联通验证 | 直接用，已验证可用 |
| `.env`（OPENAI_API_KEY） | 直接读，已配好 |
| 大图预压缩踩坑修复 | helper 复用同样逻辑 |
| 3 级兜底链模式（`_call_with_retry`） | 抄同构实现 |
| `_strip_markdown_fence` | 抄 / 抽公共（见下） |

**可选重构（推荐，但需你点头）**：`_strip_markdown_fence` 和预压缩 helper 在 analyzer 和 copywriter 都要用。建议抽到：
- `_strip_markdown_fence` → `tools/llm.py` 或新建 `tools/json_utils.py`
- 预压缩 helper → `tests/_material_helpers.py`

这样需改 `analyzer/agent.py` 和 `test_analyzer_live.py` 各 1 行 import。**改动可控、不破坏已通过测试**。若你想稳，copywriter 先各自复制一份（标 `# TODO 抽公共`），hackathon 后再重构。
