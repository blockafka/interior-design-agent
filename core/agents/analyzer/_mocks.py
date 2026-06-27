"""三级兜底链的最末级 fallback。

故意做成"显眼的失败标记"风格 —— 一旦在生产输出里看到这些字面值，
就说明真实 LLM 调用 + 重试都失败，分析没拿到结果。便于排查。
"""

MOCK_VISUAL = {
    "color_palette": ["未识别"],
    "material": ["未识别"],
    "composition": "视觉分析失败（兜底数据）",
    "lighting": "视觉分析失败（兜底数据）",
}

MOCK_COPY = {
    "voice": "文案分析失败（兜底数据）",
    "keywords": ["未识别"],
    "sentence_pattern": "文案分析失败（兜底数据）",
    "hashtag_pattern": ["#兜底"],
}
