# routers/paper.py

from fastapi import APIRouter, HTTPException
import logging

from app.services.fetcher import get_elsevier_client

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/paper/{paper_id}/citations")
async def get_paper_citations(paper_id: str):
    try:
        async with await get_elsevier_client() as client:
            response = await client.get(
                f"/paper/{paper_id}/citations",
                params={"limit": 100, "fields": "title,authors,year,citationCount"}
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"获取引用数据失败: {response.status_code}"}
    except Exception as e:
        logger.error(f"获取引用数据时发生错误: {str(e)}", exc_info=True)
        return {"error": f"获取引用数据时发生错误: {str(e)}"}
