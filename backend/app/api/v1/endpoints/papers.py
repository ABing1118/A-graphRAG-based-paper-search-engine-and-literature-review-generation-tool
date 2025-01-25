from fastapi import APIRouter, Query
from typing import Optional
from app.services.paper_service import PaperService
from app.models.paper import Paper

router = APIRouter()

@router.get("/search")
async def search_papers(
    query: Optional[str] = Query(None, description="要搜索的论文关键词")
) -> dict:
    if not query:
        return {"error": "请提供 query 参数，例如 ?query=人工智能"}
    
    results = await PaperService.search_papers(query)
    return {
        "query": query,
        "results": results
    } 