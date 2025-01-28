# routers/paper.py

from fastapi import APIRouter, HTTPException
import logging
from typing import List
import httpx
from config import SEMANTIC_SCHOLAR_API_URL

from app.services.fetcher import get_client, fetch_papers

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/paper/{paper_id}/citations")
async def get_paper_citations(paper_id: str) -> List[dict]:
    """获取引用了该论文的文章列表"""
    try:
        async with httpx.AsyncClient() as client:
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
        logger.error(f"获取论文 {paper_id} 的引用网络失败: {str(e)}")
        return []

@router.get("/paper/{paper_id}/references")
async def get_paper_references(paper_id: str) -> List[dict]:
    """获取论文的参考文献列表"""
    try:
        async with httpx.AsyncClient() as client:
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
            
    except Exception as e:
        logger.error(f"获取论文 {paper_id} 的参考文献失败: {str(e)}")
        return []
