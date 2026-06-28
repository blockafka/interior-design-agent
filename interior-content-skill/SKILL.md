---
name: interior-content-skill
description: Use when generating Xiaohongshu interior-design marketing content from an existing collector output directory, especially after a separate collector skill has written data/collect-style files.
---

# Interior Content Skill

## Overview

This is a thick Claude Code skill for the non-collector half of the interior design content pipeline. It reads a collector output directory, analyzes the target account style, generates image prompts, generates design renderings, and writes Xiaohongshu marketing copy for home-decoration lead generation.

It does not collect Xiaohongshu data. A separate collector skill must produce the input directory.

## Input Contract

The input is a collector output directory:

```text
<collect-dir>/
└── <post-folder>/
    ├── metadata.json
    ├── body.txt
    ├── full_text_snapshot.txt      # optional fallback
    ├── image_urls.txt              # optional if images/ exists
    └── images/                     # recommended
        ├── 01.webp
        └── ...
```

`metadata.json` should contain `title`, `note_id`, `liked_count`, and `collect_count` when available. Local images are compressed and converted to data URIs before multimodal analysis.

## Required Environment

The skill expects an `.env` file in this skill directory or the current working directory:

```env
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://api.openai-next.com/v1
IMAGE_GEN_PROVIDER=openai_image
IMAGE_GEN_MODEL=gemini-3.1-flash-image-preview
```

Never print secret values. Only report whether required keys are set.

## First-Time Setup

From the skill directory:

```bash
python -m pip install -e .
cp .env.example .env
```

Then fill `.env` locally.

## Run Pipeline

Use the stable script entrypoint:

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

## Output Contract

Each run writes artifacts to:

```text
data/runs/<request_id>/
├── xiaohongshu_post.md
├── request.json
├── collected_content.json
├── style_dna.json
├── prompt_bundle.json
├── generated_images.json
├── copy_content.json
└── final_post.json
```

`xiaohongshu_post.md` is the easiest file to inspect or copy into a demo: it contains the title, body, hashtags, and generated image paths.

Generated images are written to `data/generated/` and referenced as `/static/generated/<file>.png`.

## What To Report

After running, report:

- run directory and `xiaohongshu_post.md` path
- the full final post: title, body, hashtags, and generated image paths
- `style_dna.json` summary: visual style and copy voice
- `prompt_bundle.json` positive prompt summary

If a model call falls back because of rate limits or invalid JSON, say which step fell back and whether the final run still completed.

## Common Mistakes

- Do not run collector logic here. This skill starts from an existing collector output directory.
- Do not paste or expose `.env` values.
- Do not use `tests/` as the primary interface; use `python -m scripts.run_from_collect`.
- Do not require the original `interior-design-agent` repository. This thick skill includes the non-collector runtime code it needs.
