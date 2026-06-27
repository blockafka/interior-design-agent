# Web 前端

待 3 人开会选型后启动开发。

## 候选框架

- [ ] **Next.js + Tailwind**（推荐，专业感强，能讲"全栈"故事）
- [ ] **Streamlit**（最快，但简陋）
- [ ] **Gradio**（折中）

## 与后端约定

| 项 | 内容 |
|----|------|
| 后端 base URL | `http://localhost:8000`（开发期） |
| 主接口 | `POST /api/generate` |
| 健康检查 | `GET /health` |
| Swagger 文档 | `http://localhost:8000/docs` |
| 请求体类型 | `core/schemas.py::UserRequest` |
| 响应体类型 | `core/schemas.py::FinalPost` |

## UI 要做的事

- [ ] 对标账号选择器（16+ 账号下拉 / 卡片）
- [ ] 上传客户户型图（含 demo 户型一键选择）
- [ ] 户型元信息表单（面积 / 户型 / 朝向 / 备注）
- [ ] 一键「生成」按钮
- [ ] 5 Agent 工作过程可视化（loading 动画 + 进度提示）
- [ ] 结果展示：3 张图片 + 标题 + 正文 + Hashtag
- [ ] 一键复制 / 下载

## 负责人

C · 前端 + Demo
