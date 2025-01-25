from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import httpx
import asyncio
from pydantic import BaseModel
from typing import List, Optional
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from datetime import datetime
import numpy as np
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SEMANTIC_SCHOLAR_API_URL = "https://api.semanticscholar.org/graph/v1"

# 定义一些常量
MIN_SCORE_THRESHOLD = 30  # 论文质量分数的最低阈值
MAX_PARALLEL_REQUESTS = 5  # 并行API请求的最大数量
DEFAULT_FETCH_SIZE = 500  # 默认获取的论文数量

async def get_client():
    return httpx.AsyncClient(
        base_url=SEMANTIC_SCHOLAR_API_URL,
        headers={
            "User-Agent": "Paper Insight Research Tool"
        },
        timeout=60.0  # 增加超时时间到60秒
    )

# 添加重试装饰器
@retry(
    stop=stop_after_attempt(3),  # 最多重试3次
    wait=wait_exponential(multiplier=1, min=4, max=10),  # 指数退避重试
    reraise=True
)
async def fetch_papers(client, url, params):
    try:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response
    except httpx.TimeoutException as e:
        logger.error(f"请求超时: {str(e)}")
        raise HTTPException(status_code=504, detail="API请求超时")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP错误: {str(e)}")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"未知错误: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True
)
async def fetch_papers_batch(client, query: str, offset: int, limit: int):
    """获取论文基本信息"""
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
    """获取单篇论文的详细信息，包括引用关系"""
    try:
        response = await client.get(
            f"/paper/{paper_id}",
            params={
                "fields": "references,citations"
            }
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.warning(f"获取论文 {paper_id} 的引用信息失败: {str(e)}")
        return None

def calculate_paper_score(paper):
    """计算论文的重要性分数"""
    current_year = datetime.now().year
    
    # 基础分数
    score = 0
    
    # 1. 年份权重 (最近5年权重最高)
    year = paper.get("year")
    if year and isinstance(year, (int, float)):  # 确保年份是有效的数字
        year_diff = current_year - int(year)
        if year_diff <= 5:
            score += 30
        elif year_diff <= 10:
            score += 20
        else:
            score += 10
    
    # 2. 引用量权重 (使用对数来平滑差异)
    citations = paper.get("citationCount", 0)
    if citations and isinstance(citations, (int, float)):  # 确保引用数是有效的数字
        score += np.log1p(float(citations)) * 10
    
    # 3. 期刊/会议权重
    venue = paper.get("venue", "").lower() if paper.get("venue") else ""
    top_venues = {
        "nature": 50, "science": 50, 
        "cell": 40,
        "neural information processing systems": 35,
        "icml": 35, "iclr": 35,
        "ieee": 30, "acm": 30
    }
    for top_venue, weight in top_venues.items():
        if venue and top_venue in venue:
            score += weight
            break
    
    return score

async def fetch_papers_from_multiple_sources(client, query: str, offset: int, limit: int):
    """从多个数据源并行获取论文"""
    # 这里可以添加更多的API源
    sources = [
        ("semantic_scholar", fetch_papers_batch(client, query, offset, limit)),
        # ("arxiv", fetch_arxiv_papers(query, offset, limit)),  # 示例：添加arXiv源
        # ("crossref", fetch_crossref_papers(query, offset, limit)),  # 示例：添加Crossref源
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

@app.get("/search_papers")
async def search_papers(
    query: str = Query(..., description="搜索关键词"),
    min_year: int = Query(None, description="最早年份"),
    min_citations: int = Query(None, description="最少引用数"),
    top_k: int = Query(60, description="返回结果数量"),
    fetch_size: int = Query(DEFAULT_FETCH_SIZE, description="实际获取的论文数量"),
    min_score: float = Query(MIN_SCORE_THRESHOLD, description="最低质量分数")
):
    try:
        logger.info(f"收到搜索请求，关键词: {query}")
        
        async with await get_client() as client:
            # 1. 并行获取大量论文数据
            all_papers = []
            batch_size = 100  # 增加每批次的大小
            total_fetched = 0
            
            # 创建并行任务
            fetch_tasks = []
            while total_fetched < fetch_size:
                current_limit = min(batch_size, fetch_size - total_fetched)
                task = fetch_papers_from_multiple_sources(
                    client,
                    query,
                    offset=total_fetched,
                    limit=current_limit
                )
                fetch_tasks.append(task)
                total_fetched += current_limit
                
                if len(fetch_tasks) >= MAX_PARALLEL_REQUESTS:
                    # 并行执行任务
                    batch_results = await asyncio.gather(*fetch_tasks)
                    for papers in batch_results:
                        all_papers.extend(papers)
                    fetch_tasks = []
            
            # 处理剩余的任务
            if fetch_tasks:
                batch_results = await asyncio.gather(*fetch_tasks)
                for papers in batch_results:
                    all_papers.extend(papers)
            
            # 2. 数据预处理和质量评分
            qualified_papers = []
            for paper in all_papers:
                try:
                    # 基础筛选 - 添加类型检查和错误处理
                    paper_year = paper.get("year")
                    if paper_year is not None:
                        try:
                            paper_year = int(paper_year)
                        except (ValueError, TypeError):
                            continue  # 跳过无效年份的论文
                    
                    citations = paper.get("citationCount", 0)
                    if citations is not None:
                        try:
                            citations = int(citations)
                        except (ValueError, TypeError):
                            citations = 0
                    
                    # 应用筛选条件
                    if min_year and (paper_year is None or paper_year < min_year):
                        continue
                    if min_citations and (citations is None or citations < min_citations):
                        continue
                    
                    # 计算论文分数
                    score = calculate_paper_score(paper)
                    if score >= min_score:  # 只保留高于阈值的论文
                        paper["score"] = score
                        qualified_papers.append(paper)
                except Exception as e:
                    logger.warning(f"处理论文时出错: {str(e)}, paper: {paper.get('paperId', 'unknown')}")
                    continue
            
            # 3. 按分数排序，选择最优的论文
            qualified_papers.sort(key=lambda x: x["score"], reverse=True)
            top_papers = qualified_papers[:top_k]
            
            # 4. 处理展示数据和引文网络
            processed_papers = []
            citation_tasks = []
            
            for paper in top_papers:
                paper_data = {
                    "id": paper.get("paperId", ""),
                    "title": paper.get("title", "无标题"),
                    "authors": [author.get("name", "") for author in paper.get("authors", [])],
                    "abstract": paper.get("abstract") or "暂无摘要",
                    "year": paper.get("year", "未知"),
                    "journal": paper.get("venue") or "未知期刊",
                    "citations": paper.get("citationCount", 0),
                    "url": paper.get("url", ""),
                    "pdf_url": (paper.get("openAccessPdf") or {}).get("url", ""),
                    "fields": paper.get("fieldsOfStudy", []),
                    "publication_types": paper.get("publicationTypes", []),
                    "publication_date": paper.get("publicationDate", ""),
                    "references": [],
                    "citations_list": [],
                    "keywords": [],
                    "score": paper["score"],
                    "source": paper.get("source", "unknown")
                }
                
                if paper.get("paperId"):
                    citation_tasks.append(fetch_paper_details(client, paper.get("paperId")))
                processed_papers.append(paper_data)
            
            # 5. 并行获取引文信息
            if citation_tasks:
                citation_results = await asyncio.gather(*citation_tasks, return_exceptions=True)
                
                # 更新论文的引用信息
                for i, citation_data in enumerate(citation_results):
                    if citation_data and not isinstance(citation_data, Exception):
                        processed_papers[i]["references"] = [
                            ref.get("paperId") for ref in citation_data.get("references", [])
                        ]
                        processed_papers[i]["citations_list"] = [
                            cit.get("paperId") for cit in citation_data.get("citations", [])
                        ]

            # 在处理数据后添加详细日志
            logger.info(f"""
            ====== 搜索结果统计 ======
            关键词: {query}
            检索到的总论文数: {len(all_papers)}
            符合质量要求的论文数: {len(qualified_papers)}
            实际展示的论文数: {len(processed_papers)}
            最低分数要求: {min_score}
            """)
            
            # 输出前5篇论文的详细信息作为样本
            logger.info("\n====== 前5篇论文示例 ======")
            for i, paper in enumerate(qualified_papers[:5]):
                try:
                    # 确保 fieldsOfStudy 是一个列表
                    fields = paper.get('fieldsOfStudy', [])
                    if not isinstance(fields, (list, tuple)):
                        fields = [str(fields)] if fields else []
                        
                    # 确保作者列表是可迭代的
                    authors = paper.get('authors', [])
                    if not isinstance(authors, (list, tuple)):
                        authors = [authors] if authors else []
                        
                    author_names = [
                        author.get('name', '') if isinstance(author, dict) else str(author)
                        for author in authors
                    ]
                    
                    logger.info(f"""
                    论文 {i+1}:
                    标题: {paper.get('title', '无标题')}
                    作者: {', '.join(filter(None, author_names))}
                    年份: {paper.get('year', '未知')}
                    期刊/会议: {paper.get('venue', '未知')}
                    引用数: {paper.get('citationCount', 0)}
                    评分: {paper.get('score', 0)}
                    来源: {paper.get('source', 'unknown')}
                    研究领域: {', '.join(filter(None, fields))}
                    """)
                except Exception as e:
                    logger.warning(f"处理论文信息时出错: {str(e)}, paper_id: {paper.get('paperId', 'unknown')}")
                    continue
            
            # 输出分数分布统计
            scores = [p.get('score', 0) for p in qualified_papers]
            if scores:
                logger.info(f"""
                ====== 分数统计 ======
                最高分: {max(scores):.2f}
                最低分: {min(scores):.2f}
                平均分: {sum(scores)/len(scores):.2f}
                分数分布:
                90-100: {len([s for s in scores if s >= 90])}篇
                80-90: {len([s for s in scores if 80 <= s < 90])}篇
                70-80: {len([s for s in scores if 70 <= s < 80])}篇
                60-70: {len([s for s in scores if 60 <= s < 70])}篇
                50-60: {len([s for s in scores if 50 <= s < 60])}篇
                <50: {len([s for s in scores if s < 50])}篇
                """)
            
            # 输出年份分布
            years = [p.get('year') for p in qualified_papers if p.get('year')]
            if years:
                current_year = datetime.now().year
                logger.info(f"""
                ====== 年份分布 ======
                最新: {max(years)}
                最早: {min(years)}
                近1年: {len([y for y in years if y >= current_year - 1])}篇
                近3年: {len([y for y in years if y >= current_year - 3])}篇
                近5年: {len([y for y in years if y >= current_year - 5])}篇
                5年以上: {len([y for y in years if y < current_year - 5])}篇
                """)

        # 修复这里的缩进，将 return 语句移到 try 块内
        return {
            "query": query,
            "total_available": len(all_papers),
            "qualified_papers": len(qualified_papers),
            "showing": len(processed_papers),
            "min_score": min_score,
            "results": processed_papers,
            "total_fetched": total_fetched,
            "sources_stats": {
                source: len([p for p in qualified_papers if p.get("source") == source])
                for source in set(p.get("source", "unknown") for p in qualified_papers)
            },
            "stats": {
                "score_distribution": {
                    "max": max(scores) if scores else 0,
                    "min": min(scores) if scores else 0,
                    "avg": sum(scores)/len(scores) if scores else 0,
                },
                "year_distribution": {
                    "latest": max(years) if years else None,
                    "earliest": min(years) if years else None,
                    "last_year": len([y for y in years if y >= current_year - 1]) if years else 0,
                    "last_3_years": len([y for y in years if y >= current_year - 3]) if years else 0,
                    "last_5_years": len([y for y in years if y >= current_year - 5]) if years else 0,
                }
            }
        }
                
    except Exception as e:
        logger.error(f"搜索过程中发生错误: {str(e)}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))

# 获取论文引用网络
@app.get("/paper/{paper_id}/citations")
async def get_paper_citations(paper_id: str):
    try:
        async with await get_client() as client:
            response = await client.get(
                f"/paper/{paper_id}/citations",
                params={
                    "limit": 100,
                    "fields": "title,authors,year,citationCount"
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"获取引用数据失败: {response.status_code}"}
                
    except Exception as e:
        return {"error": f"获取引用数据时发生错误: {str(e)}"}
