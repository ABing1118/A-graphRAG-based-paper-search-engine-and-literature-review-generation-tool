# routers/paper.py

from fastapi import APIRouter, HTTPException
import logging

from app.services.fetcher import get_client, fetch_papers

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/paper/{paper_id}/citations")
async def get_paper_citations(paper_id: str):
    """获取论文的引用信息"""
    logger.info(f"正在获取论文 {paper_id} 的引用信息")
    try:
        async with await get_client() as client:
            response = await fetch_papers(
                client,
                f"/paper/{paper_id}/citations",
                params={
                    "fields": "title,authors,year,citationCount",
                    "limit": 100
                }
            )
            data = response.json()
            # 添加详细的数据结构日志
            logger.info(f"citations API 返回的完整数据结构: {data}")
            if data.get('data'):
                logger.info(f"第一条引用数据示例: {data['data'][0]}")
            
            citations = data.get('data', [])
            logger.info(f"成功获取到 {len(citations)} 条引用信息")
            return citations
    except Exception as e:
        logger.error(f"获取引用数据时发生错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取引用数据时发生错误: {str(e)}")
