# services/fetcher.py

import httpx
import asyncio
import logging
from fastapi import HTTPException
from tenacity import retry, stop_after_attempt, wait_exponential
from asyncio import Semaphore
import time

from config import (
    SEMANTIC_SCHOLAR_API_URL,
    MAX_CONCURRENT_REQUESTS,
    REQUEST_INTERVAL
)

logger = logging.getLogger(__name__)

# 全局信号量和上次请求时间
API_SEMAPHORE = Semaphore(MAX_CONCURRENT_REQUESTS)
LAST_REQUEST_TIME = 0

async def get_client():
    """
    创建并返回一个配置好的HTTP客户端
    """
    return httpx.AsyncClient(
        base_url=SEMANTIC_SCHOLAR_API_URL,
        headers={"User-Agent": "Paper Insight Research Tool"},
        timeout=60.0
    )

async def wait_for_rate_limit():
    """确保请求间隔符合配置"""
    global LAST_REQUEST_TIME
    current_time = time.time()
    elapsed = current_time - LAST_REQUEST_TIME
    if elapsed < REQUEST_INTERVAL:
        await asyncio.sleep(REQUEST_INTERVAL - elapsed)
    LAST_REQUEST_TIME = time.time()

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=4, max=10),
    reraise=True
)
async def fetch_papers(client, url, params):
    """
    通用的论文获取函数，包含重试机制和错误处理
    """
    async with API_SEMAPHORE:  # 使用信号量控制并发
        await wait_for_rate_limit()  # 确保请求间隔
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response
        except httpx.TimeoutException as e:
            logger.error(f"请求超时: {str(e)}")
            raise HTTPException(status_code=504, detail="API请求超时")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP错误: {str(e)}")
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except Exception as e:
            logger.error(f"未知错误: {str(e)}")
            raise HTTPException(status_code=500, detail="服务器内部错误")

async def fetch_papers_batch(client, query: str, offset: int, limit: int):
    """
    批量获取论文数据
    """
    params = {
        "query": query,
        "offset": offset,
        "limit": limit,
        "fields": (
            "title,authors,abstract,year,citationCount,venue,url,"
            "openAccessPdf,fieldsOfStudy,publicationTypes,publicationDate"
        )
    }
    response = await fetch_papers(client, "/paper/search", params)
    return response.json()

async def fetch_paper_details(client, paper_id: str):
    """
    获取单篇论文的详细信息，包括引用关系
    """
    try:
        # 使用基础的 fetch_papers 函数来获取数据
        response = await fetch_papers(
            client,
            f"/paper/{paper_id}",
            params={"fields": "references,citations"}
        )
        return response.json()
    except Exception as e:
        logger.warning(f"获取论文 {paper_id} 的引用信息失败: {str(e)}")
        return None

async def fetch_papers_from_multiple_sources(client, query: str, offset: int, limit: int):
    """
    从多个数据源获取论文（目前仅实现了Semantic Scholar，后续可扩展）
    """
    sources = [
        ("semantic_scholar", fetch_papers_batch(client, query, offset, limit)),
    ]
    
    results = []
    tasks = [source[1] for source in sources]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    for (source_name, _), response in zip(sources, responses):
        if isinstance(response, Exception):
            logger.error(f"{source_name} API调用失败: {str(response)}")
            continue
        if response and isinstance(response, dict):
            papers = response.get("data", [])
            for paper in papers:
                paper["source"] = source_name
            results.extend(papers)
    return results
