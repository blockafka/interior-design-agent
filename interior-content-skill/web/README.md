# AI 家装内容生成引擎 - Frontend & API Server

> Beyond Prompt: Agents in Action 黑客松项目
> 团队成员：caonan（前端）、kafka（风格分析）、A（Agent 工程）

## 项目简介

多 Agent 协同的 AI 家装内容生成工具：输入户型需求 → 克隆对标账号风格 → 自动生成 3 张设计效果图 + 小红书营销文案。

### Pipeline

```
采集 Agent → 风格分析 Agent → 提示词 Agent → 图片生成 Agent → 文案 Agent
```

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vite + React + Tailwind CSS 4 |
| 后端 API | FastAPI + SSE 流式推送 |
| LLM | OpenAI-compatible API (doubao / gemini) |
| 生图 | OpenAI Images API (gemini-3.1-flash-image-preview) |
| 数据契约 | Pydantic v2 Schemas |

## 快速启动

### 1. 安装依赖

```bash
cd interior-content-skill

# Python 依赖
pip install -e .

# 前端依赖
cd web && npm install && cd ..
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入 OPENAI_API_KEY
```

### 3. 启动服务

```bash
# 终端 1：后端 (端口 8000)
cd interior-content-skill
python -m server.main

# 终端 2：前端 (端口 5173)
cd interior-content-skill/web
npm run dev
```

### 4. 访问

浏览器打开 http://localhost:5173

## 前端设计

- **InputView**：两步表单（对标账号选择 + 户型需求填写），预填 demo 数据一键生成
- **GeneratingView**：5 Agent Pipeline 实时可视化，SSE 推送中间结果，蓝色脉冲动画
- **ResultView**：左图右文布局，模拟小红书卡片，一键复制文案

### SSE 事件协议

```
event: step_start   → Agent 开始执行
event: step_done    → Agent 完成，附带中间结果
event: complete     → 全部完成，附带 FinalPost
event: error        → Pipeline 异常
```

## 目录结构

```
interior-content-skill/
├── server/main.py          # FastAPI + SSE 端点
├── core/
│   ├── schemas.py          # Pydantic 数据契约
│   ├── agents/             # 5 个 Agent 实现
│   └── collect_loader.py   # 本地采集数据加载
├── tools/
│   ├── llm.py              # LLM 调用封装
│   └── image_gen.py        # 文生图 API 封装
├── web/                    # 前端项目
│   ├── src/
│   │   ├── App.jsx         # 三态状态机
│   │   └── components/     # UI 组件
│   └── vite.config.js      # 代理 + Tailwind 配置
└── examples/collect-sample/ # 采集样本数据
```

## 演示效果

1. 暗色科技风 UI，路演展示效果最大化
2. 5 个 Agent 实时亮灯，评委可看到协作过程
3. 中间结果实时展示（StyleDNA 摘要）
4. 最终产出：3 张高质量效果图 + 可直接发布的小红书文案
