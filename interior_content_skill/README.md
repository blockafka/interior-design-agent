# interior-content-skill

家装内容生成的非采集链路。可作厚 Claude Code Skill 复制到 `~/.claude/skills/`，也可直接在本仓库内开发运行。

```text
collector 输出目录
  → analyzer（风格 DNA）
  → prompter（生图 prompt）
  → generator（3 张效果图）
  → copywriter（小红书文案）
  → final_post.json
```

不包含真实采集 Agent。采集由另一个 collector skill 完成，本 skill 只读取其输出目录。

提供两种运行方式：

| 方式 | 入口 | 适合 |
|------|------|------|
| Web | `server/`（FastAPI）+ `web/`（React） | 浏览器演示、SSE 实时进度 |
| CLI | `python -m scripts.run_from_collect` | 命令行、写文件、调试 |

## 安装

```bash
cd interior-content-skill
python -m pip install -e .
cp .env.example .env      # 然后填入 OPENAI_API_KEY
```

`.env`：

```env
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://api.openai-next.com/v1
IMAGE_GEN_PROVIDER=openai_image
IMAGE_GEN_MODEL=gemini-3.1-flash-image-preview
```

## 输入目录格式

按账号组织，一次分析一个账号。`--collect-dir` 指到**账号目录**：

```text
examples/collect-sample/<账号>/
└── <单篇笔记>/
    ├── metadata.json
    ├── body.txt
    ├── image_urls.txt
    └── images/
```

内置示例账号（`examples/collect-sample/` 下，共 11 个）：

```
厚来设计  上海设计师  六伊设计  刘思彤设计师  境一所  宸白空间
成都宏福樘  成都山顶设计  杭州上北设计  海狸酱  飞墨设计
```

## 运行：Web（推荐演示用）

两个终端分别起后端和前端：

```bash
# 终端 1：后端（:8000）
python -m server.main

# 终端 2：前端（:5173）
cd web
npm install                 # 首次需安装依赖
./node_modules/.bin/vite    # ⚠️ 不要用 npm run dev，见下方说明
```

浏览器打开 **http://localhost:5173** → 选对标账号 + 填户型需求 → 生成。前端 `/api`、`/static` 自动代理到后端 :8000。

> ⚠️ **关于 `npm run dev`**：本项目路径 `Beyond Prompt: Agents in Action` 含**冒号**，会污染 npm 的 PATH 解析，报 `sh: vite: command not found`。装好依赖后用 `./node_modules/.bin/vite` 直调即可。最干净的根治办法是把项目移到无冒号的路径。

生成会调真实 doubao / gemini（`.env` 的 key），约 1–3 分钟，generator 阶段最慢。

## 运行：CLI

```bash
python -m scripts.run_from_collect \
  --collect-dir examples/collect-sample/厚来设计 \
  --target-account-id 厚来设计 \
  --area-sqm 180 \
  --layout 四室两厅 \
  --orientation 南北通透 \
  --target-customer 三代同堂改善型家庭 \
  --pain-points 高级感不能冰冷，要兼顾长辈孩子和年轻夫妻互动 \
  --notes "180㎡四室两厅，三代同堂改善住宅。客户希望有静奢老钱风的高级感，但不要酒店样板间式的冰冷；需要开放客餐厨、充足收纳、儿童活动空间，并照顾长辈日常动线。"
```

换账号改 `--collect-dir` 路径即可。

## 输出

CLI 每次运行在终端打印完整小红书成稿，并把结构化结果写入：

```text
data/runs/<request_id>/
├── xiaohongshu_post.md      # 最方便直接查看 / 复制发布的最终成稿
├── request.json             # 本次用户户型需求
├── collected_content.json   # 从 collector 目录读取并转换后的内容
├── style_dna.json           # analyzer 输出：视觉 / 文案风格 DNA
├── prompt_bundle.json       # prompter 输出：生图 prompt
├── generated_images.json    # generator 输出：图片路径
├── copy_content.json        # copywriter 输出：标题 / 正文 / 话题
└── final_post.json          # 最终聚合结果
```

运行结束时终端会打印 `Run directory`。Web 端结果直接在浏览器展示，图片通过 `/static/generated/` 回显。

图片生成结果写入：

```text
data/generated/<uuid>.png
```
