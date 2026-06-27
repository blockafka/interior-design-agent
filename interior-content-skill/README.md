# interior-content-skill

可复制到 `~/.claude/skills/` 的厚 Claude Code Skill。

它包含家装内容生成的非采集链路：

```text
collector 输出目录
  → analyzer
  → prompter
  → generator
  → copywriter
  → final_post.json
```

不包含真实采集 Agent。采集由另一个 collector skill 完成，本 skill 只读取其输出目录。

## 安装

```bash
cd ~/.claude/skills/interior-content-skill
python -m pip install -e .
cp .env.example .env
```

填写 `.env`：

```env
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://api.openai-next.com/v1
IMAGE_GEN_PROVIDER=openai_image
IMAGE_GEN_MODEL=gemini-3.1-flash-image-preview
```

## 输入目录格式

```text
<collect-dir>/
└── <post-folder>/
    ├── metadata.json
    ├── body.txt
    ├── image_urls.txt
    └── images/
```

## 运行示例

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

## 输出

每次运行都会在终端直接打印完整小红书成稿（标题、正文、话题、图片）。同时会把结构化结果写入：

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

运行结束时终端会打印 `Run directory`，直接打开这个目录即可找到所有结果。

图片生成结果写入：

```text
data/generated/<uuid>.png
```
