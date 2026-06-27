---
name: collector
description: 采集对标账号的 5-10 篇代表作笔记（标题 / 正文 / 图片 URL / 互动数）
order: 1
input_schema: UserRequest
output_schema: CollectedContent
tools:
  - tools.cloudsway.smart_search
  - tools.cloudsway.read
owner: TBD
status: skeleton
---

# Step 1 · 采集 Agent

## 一句话职责
吃进 `UserRequest`（包含 `target_account_id`），吐出该账号最近 5-10 篇高质量笔记的结构化内容（文本 + 图片 URL）。

## 输入：UserRequest
schema 定义见 `core/schemas.py::UserRequest`，关键字段：
- `target_account_id`: 对标账号唯一标识

## 输出：CollectedContent
schema 定义见 `core/schemas.py::CollectedContent`，包含一个 `posts: list[CollectedPost]`。
每个 `CollectedPost` 必含：`post_id` / `title` / `body` / `image_urls` / `metadata`。

## 实现步骤（TODO 填实现）
1. 用 `cloudsway.smart_search` 查找该账号最近 5-10 篇代表作（按互动数排）
2. 每个 URL 调 `cloudsway.read` 拿正文 markdown + 图片列表
3. 组装 `CollectedPost` 列表

## 失败兜底
若搜索返回 < 3 条，回退到 `data/samples/` 下的本地账号数据。

## 联调约定
- **下游**（analyzer）：要求 `posts` 长度 ≥ 3，否则 analyzer 会报错
