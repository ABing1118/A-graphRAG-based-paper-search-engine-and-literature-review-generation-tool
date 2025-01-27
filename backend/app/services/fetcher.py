# services/fetcher.py

import httpx
import asyncio
import logging
from fastapi import HTTPException
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

############################
# 1. Semantic Scholar 配置 #
############################

# 如果你需要 Semantic Scholar, 可以取消下面注释并在 config.py 里定义
# from config import SEMANTIC_SCHOLAR_API_URL
#
# async def get_semantic_client():
#     return httpx.AsyncClient(
#         base_url=SEMANTIC_SCHOLAR_API_URL,
#         headers={"User-Agent": "Paper Insight Research Tool"},
#         timeout=60.0
#     )
#
# @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=4, max=10), reraise=True)
# async def fetch_papers(client, url, params):
#     try:
#         response = await client.get(url, params=params)
#         response.raise_for_status()
#         return response
#     except httpx.TimeoutException as e:
#         logger.error(f"请求超时: {str(e)}")
#         raise HTTPException(status_code=504, detail="API请求超时")
#     except httpx.HTTPStatusError as e:
#         logger.error(f"HTTP错误: {str(e)}")
#         raise HTTPException(status_code=e.response.status_code, detail=str(e))
#     except Exception as e:
#         logger.error(f"未知错误: {str(e)}")
#         raise HTTPException(status_code=500, detail="服务器内部错误")

############################
# 2. Elsevier (Scopus) 配置 #
############################

from config import ELSEVIER_BASE_URL, ELSEVIER_API_KEY

async def get_elsevier_client():
    """为 Elsevier (Scopus) 创建一个专用的HTTP客户端"""
    return httpx.AsyncClient(
        base_url=ELSEVIER_BASE_URL,
        headers={
            "User-Agent": "Paper Insight Research Tool",
            "X-ELS-APIKey": ELSEVIER_API_KEY,
            "Accept": "application/json"
        },
        timeout=60.0
    )

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=4, max=10), reraise=True)
async def fetch_elsevier_papers_batch(client, query: str, offset: int, limit: int):
    """
    调用Elsevier(Scopus) Search API，返回与原先 search 逻辑兼容的结构。
    """
    # 限制单次请求数量
    actual_limit = min(limit, 25)  # Scopus 建议单次请求不超过25条
    
    params = {
        "query": f"TITLE-ABS-KEY({query})",
        "start": offset,
        "count": actual_limit,  # 使用较小的限制
        "view": "STANDARD"      # 使用 STANDARD 而不是 COMPLETE 来减少数据量
    }

    try:
        # 注意: 这里的 "" 指 base_url 后的相对路径, scopus接口 "/"
        response = await client.get("", params=params)
        response.raise_for_status()
    except httpx.TimeoutException as e:
        logger.error(f"请求超时: {str(e)}")
        raise HTTPException(status_code=504, detail="API请求超时")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP错误: {str(e)}")
        # 记录下 e.response.text 也许能查看具体400信息
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error(f"未知错误: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

    data = response.json()
    
    # 获取一个示例条目的详细信息
    search_results = data.get("search-results", {})
    entries = search_results.get("entry", [])
    if entries:
        logger.info("=" * 50)
        logger.info("示例论文的所有字段:")
        logger.info("=" * 50)
        example_paper = entries[0]
        for key, value in example_paper.items():
            logger.info(f"{key}: {value}")
        logger.info("=" * 50)

    papers_list = []
    for entry in entries:
        try:
            # 1. 解析作者信息
            authors = []
            # 优先使用 dc:creator 作为第一作者
            if entry.get("dc:creator"):
                authors.append({
                    "name": entry.get("dc:creator"),
                    "affiliation": ""  # 如果需要机构信息，可以从 affiliation 字段获取
                })
            # 如果没有 dc:creator，再尝试使用 author 字段
            elif "author" in entry:
                author = entry.get("author", [])[0] if entry.get("author") else {}  # 只取第一个作者
                author_name = author.get("authname", "Unknown")
                authors.append({
                    "name": author_name,
                    "affiliation": ""
                })
            else:
                authors.append({
                    "name": "Unknown",
                    "affiliation": ""
                })

            # 2. 解析链接
            links = entry.get("link", [])
            paper_url = next((link["@href"] for link in links if link.get("@ref") == "scopus"), "")
            pdf_url = next((link["@href"] for link in links if link.get("@ref") == "full-text"), "")
            
            # 3. 解析日期 - 使用完整的日期
            pub_date = entry.get("prism:coverDate", "")
            year = pub_date.split("-")[0] if pub_date else ""
            
            # 4. 解析引用数
            citations = int(entry.get("citedby-count", "0"))
            
            # 5. 解析研究领域
            subject_areas = entry.get("subject-area", [])
            fields = [area.get("$", "") for area in subject_areas if isinstance(area, dict)]
            
            # 6. 解析摘要 - 尝试获取不同字段的摘要
            abstract = (entry.get("dc:description", "") or 
                       entry.get("abstract", "") or 
                       entry.get("authkeywords", "") or 
                       "暂无摘要")

            paper_obj = {
                "paperId": entry.get("dc:identifier", "").replace("SCOPUS_ID:", ""),
                "title": entry.get("dc:title", "Unknown Title"),
                "authors": authors,  # 现在包含了作者的详细信息
                "abstract": abstract,
                "year": year,
                "citationCount": citations,
                "venue": entry.get("prism:publicationName", ""),
                "url": paper_url,
                "openAccessPdf": {"url": pdf_url} if pdf_url else None,
                "fieldsOfStudy": fields,
                "publicationTypes": [entry.get("prism:aggregationType", "")],
                "publicationDate": pub_date,  # 完整的发布日期
                "doi": entry.get("prism:doi", ""),
                "volume": entry.get("prism:volume", ""),
                "issue": entry.get("prism:issueIdentifier", ""),
                "pages": entry.get("prism:pageRange", ""),
                "publisher": entry.get("publisher", "")
            }
            papers_list.append(paper_obj)
            
        except Exception as e:
            logger.warning(f"处理论文数据时出错: {str(e)}, entry: {entry.get('dc:identifier', 'unknown')}")
            continue

    # 返回一个 { "data": [...], ... }，与Semantic Scholar风格对齐
    return {"data": papers_list}


############################
# 3. 多源聚合: 实际使用Elsevier #
############################

async def fetch_papers_from_multiple_sources(client, query: str, offset: int, limit: int):
    """
    从多个数据源获取论文。此处实际只启用Elsevier的那条源。
    如果想再启用Semantic Scholar, 可以取消注释相应行。
    """
    sources = [
        # 取消注释可启用Semantic:
        # ("semantic_scholar", fetch_papers_batch(client, query, offset, limit)),
        
        ("elsevier", fetch_elsevier_papers_batch(client, query, offset, limit)),
    ]
    
    results = []
    # 并行执行所有sources
    tasks = [ (src_name, src_task) for (src_name, src_task) in sources ]
    gather_tasks = [task for (_, task) in tasks]

    responses = await asyncio.gather(*gather_tasks, return_exceptions=True)
    
    # 遍历结果
    for (source_name, _), response in zip(sources, responses):
        if isinstance(response, Exception):
            logger.error(f"{source_name} API调用失败: {str(response)}")
            continue
        
        if response and isinstance(response, dict):
            papers = response.get("data", [])
            # 给每篇论文标记 source
            for paper in papers:
                paper["source"] = source_name
            results.extend(papers)
    
    return results
