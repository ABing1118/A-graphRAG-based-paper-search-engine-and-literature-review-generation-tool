# routers/paper.py

from fastapi import APIRouter, HTTPException
import logging
from typing import List
import httpx
from config import SEMANTIC_SCHOLAR_API_URL
import asyncio

from app.services.fetcher import get_client, fetch_papers

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/paper/{paper_id}/citations")
async def get_paper_citations(paper_id: str, max_retries: int = 3):
    """获取论文引用信息，使用指数退避的重试机制"""
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                if attempt > 0:  # 不是第一次请求才等待
                    await asyncio.sleep(0.5 * (2 ** (attempt - 1)))  # 0.5s, 1s, 2s
                    logger.warning(f"第{attempt + 1}次尝试获取引用...")
                
                response = await client.get(
                    f"{SEMANTIC_SCHOLAR_API_URL}/paper/{paper_id}/citations",
                    params={
                        "fields": "title,authors,year,citationCount",
                        "limit": 100
                    }
                )
                response.raise_for_status()
                
                data = response.json()
                citations = [item['citingPaper'] for item in data.get('data', [])]
                return citations
                
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                continue
            logger.error(f"获取论文 {paper_id} 的引用网络失败: {str(e)}")
            return []

@router.get("/paper/{paper_id}/references")
async def get_paper_references(paper_id: str, max_retries: int = 3):
    """获取论文参考文献，使用指数退避的重试机制"""
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                if attempt > 0:  # 不是第一次请求才等待
                    await asyncio.sleep(0.5 * (2 ** (attempt - 1)))  # 0.5s, 1s, 2s
                    logger.warning(f"第{attempt + 1}次尝试获取参考文献...")
                
                response = await client.get(
                    f"{SEMANTIC_SCHOLAR_API_URL}/paper/{paper_id}/references",
                    params={
                        "fields": "title,authors,year,citationCount",
                        "limit": 100
                    }
                )
                response.raise_for_status()
                
                data = response.json()
                references = [item['citedPaper'] for item in data.get('data', [])]
                return references
                
        except httpx.HTTPStatusError as e:
            # 处理HTTP状态错误
            if e.response.status_code == 429 and attempt < max_retries - 1:
                logger.warning(f"遇到限速 (429)，将在下次重试...")
                continue
            logger.error(f"获取论文 {paper_id} 的参考文献失败: HTTP {e.response.status_code}")
            return []
        except httpx.RequestError as e:
            # 处理请求错误（网络问题等）
            logger.error(f"获取论文 {paper_id} 的参考文献请求失败: {str(e)}")
            if attempt < max_retries - 1:
                continue
            return []
        except Exception as e:
            # 处理其他错误
            logger.error(f"获取论文 {paper_id} 的参考文献时发生未知错误: {str(e)}")
            if attempt < max_retries - 1:
                continue
            return []
