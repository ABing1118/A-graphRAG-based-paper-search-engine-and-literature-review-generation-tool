# routers/paper.py

from fastapi import APIRouter, HTTPException
import logging

from app.services.fetcher import get_client, fetch_papers

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/paper/{paper_id}/citations")
async def get_paper_citations(paper_id: str):
    """获取引用了该论文的文章列表（即被引用信息）"""
    logger.info(f"正在获取引用了论文 {paper_id} 的文章列表")
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
            logger.info(f"成功获取到 {len(citations)} 篇引用了该论文的文章")
            return citations
    except Exception as e:
        logger.error(f"获取引用数据时发生错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取引用数据时发生错误: {str(e)}")

@router.get("/paper/{paper_id}/references")
async def get_paper_references(paper_id: str):
    """获取该论文引用的文章列表（即参考文献）"""
    logger.info(f"正在获取论文 {paper_id} 的参考文献列表")
    try:
        async with await get_client() as client:
            response = await fetch_papers(
                client,
                f"/paper/{paper_id}/references",  # 使用 references 端点
                params={
                    "fields": "title,authors,year,citationCount",
                    "limit": 100
                }
            )
            data = response.json()
            # 添加详细的数据结构日志
            logger.info(f"references API 返回的完整数据结构: {data}")
            if data.get('data'):
                logger.info(f"第一条参考文献示例: {data['data'][0]}")
            
            references = data.get('data', [])
            logger.info(f"成功获取到 {len(references)} 篇参考文献")
            return references
    except Exception as e:
        logger.error(f"获取参考文献数据时发生错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取参考文献数据时发生错误: {str(e)}")
