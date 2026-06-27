"""
Cloudsway 三件套 API 封装

提供：
- smart_search(query) → 搜索结果 dict
- read(url)            → markdown + image_list dict
- agent_call(...)      → 复杂研究类子任务兜底

环境变量：
- CLOUDSWAY_API_KEY
- AGENT_API_KEY
- AGENT_API_BASE_URL（默认 https://api.agentsway.dev）

负责人：A · Agent 工程师
"""

import os

import httpx

SMART_SEARCH_URL = "https://aisearchapi.cloudsway.net/api/search/smart"
READER_URL = "https://aisearchapi.cloudsway.net/api/search/read"
AGENT_URL_DEFAULT = "https://api.agentsway.dev/v1/agent"


async def smart_search(query: str, count: int = 10) -> dict:
    """
    TODO 真实实现：
      POST SMART_SEARCH_URL with {"q": query, "count": count}
      返回 {"webPages": {"value": [...]}}
    """
    # api_key = os.getenv("CLOUDSWAY_API_KEY")
    # headers = {"Authorization": f"Bearer {api_key}"}
    # async with httpx.AsyncClient(timeout=30) as client:
    #     resp = await client.post(SMART_SEARCH_URL, json={"q": query, "count": count}, headers=headers)
    #     resp.raise_for_status()
    #     return resp.json()
    return {"webPages": {"value": []}}  # MOCK


async def read(url: str) -> dict:
    """
    TODO 真实实现：
      POST READER_URL with {"url": url}
      返回 {"markdown": ..., "image_list": [...], "metadata": {...}}
    """
    return {"markdown": "", "image_list": [], "metadata": {}}  # MOCK


async def agent_call(preset: str, user_input: str) -> str:
    """
    TODO 真实实现：
      POST {AGENT_API_BASE_URL}/v1/agent with {"preset": preset, "input": user_input}
      用于复杂开放研究类子任务兜底
    """
    return ""  # MOCK
