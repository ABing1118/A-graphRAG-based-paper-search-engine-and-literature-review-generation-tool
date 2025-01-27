import asyncio
import logging
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException
from typing import List

# 这里的 import 需要根据你的项目实际结构做调整
from config import (
    MIN_SCORE_THRESHOLD,
    DEFAULT_FETCH_SIZE,
    MAX_PARALLEL_REQUESTS
)
from app.services.fetcher import (
    get_client,
    fetch_papers_from_multiple_sources,
    # 如果你还用到了 fetch_paper_details 等，可一并导入
)
from app.services.scorer import calculate_paper_score
from app.routers.paper import get_paper_citations  # 添加这行导入

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/search_papers")
async def search_papers(
    query: str = Query(..., description="搜索关键词"),
    min_year: int = Query(None, description="最早年份"),
    min_citations: int = Query(None, description="最少引用数"),
    top_k: int = Query(60, description="返回结果数量"),
    fetch_size: int = Query(DEFAULT_FETCH_SIZE, description="实际获取的论文数量"),
    min_score: float = Query(MIN_SCORE_THRESHOLD, description="最低质量分数")
):
    """
    这是重构后的搜索路由，核心逻辑与原先相同，只做了以下改动：
    1. 在对论文进行打分时，保证每篇进入 qualified_papers 的论文都拥有 'score'。
    2. 当某批次返回 429 或其他异常时，进行异常处理，避免把不完整数据加入 all_papers。
    """
    try:
        logger.info(f"收到搜索请求，关键词: {query}")

        async with await get_client() as client:
            # 用于收集所有论文
            all_papers = []
            batch_size = 100
            total_fetched = 0

            # 暂存一批批 fetch 的协程
            fetch_tasks = []

            # 1. 分批创建并行任务
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

                # 每到达 MAX_PARALLEL_REQUESTS 就并行执行一批，防止过多并发
                if len(fetch_tasks) >= MAX_PARALLEL_REQUESTS:
                    batch_results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
                    # 检查结果
                    for res in batch_results:
                        if isinstance(res, Exception):
                            # 如果是 HTTPException，可能是 429/4xx/5xx
                            if isinstance(res, HTTPException):
                                logger.error(f"出现 HTTP 错误: {res.status_code}, {res.detail}")
                                # 你可以选择直接 raise，让前端收到对应状态码
                                raise res
                            else:
                                # 其他异常，记录日志后可跳过
                                logger.error(f"fetch error: {str(res)}")
                            continue
                        # 如果是正常的返回 (list of papers)
                        all_papers.extend(res)
                    # 清空本批次任务
                    fetch_tasks = []

            # 处理剩余的任务（不足 MAX_PARALLEL_REQUESTS 的最后一批）
            if fetch_tasks:
                batch_results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
                for res in batch_results:
                    if isinstance(res, Exception):
                        if isinstance(res, HTTPException):
                            logger.error(f"出现 HTTP 错误: {res.status_code}, {res.detail}")
                            raise res
                        else:
                            logger.error(f"fetch error: {str(res)}")
                        continue
                    all_papers.extend(res)

            # 2. 评分和筛选
            qualified_papers = []
            for paper in all_papers:
                try:
                    # 合理处理年份和引用量
                    paper_year = paper.get("year")
                    if paper_year is not None:
                        try:
                            paper_year = int(paper_year)
                        except (ValueError, TypeError):
                            continue  # 跳过无效年份

                    citations = paper.get("citationCount", 0)
                    if citations is not None:
                        try:
                            citations = int(citations)
                        except (ValueError, TypeError):
                            citations = 0

                    # 筛选条件
                    if min_year and (paper_year is None or paper_year < min_year):
                        continue
                    if min_citations and (citations is None or citations < min_citations):
                        continue

                    # 计算分数 -> 先赋值
                    score = calculate_paper_score(paper)
                    paper["score"] = score  # 给每篇paper都添加score

                    # 如果分数>=阈值，则加入合格列表
                    if score >= min_score:
                        qualified_papers.append(paper)

                except Exception as e:
                    logger.warning(f"处理论文时出错: {str(e)}, paper: {paper.get('paperId', 'unknown')}")
                    continue

            # 按score排序（一定不会再KeyError了）
            qualified_papers.sort(key=lambda x: x["score"], reverse=True)
            top_papers = qualified_papers[:top_k]

            # 3. (可选) 并行获取每篇论文的引用信息
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
                    "score": paper["score"],      # 我们已经赋值了
                    "source": paper.get("source", "unknown")
                }

                # 如果还想获取更多引用信息，可以和 fetch_paper_details(client, paperId) 结合
                # citation_tasks.append(fetch_paper_details(client, paper.get("paperId")))

                processed_papers.append(paper_data)

            # 如果你开启了 citation_tasks，这里就 await 结果
            # citation_results = await asyncio.gather(*citation_tasks, return_exceptions=True)
            # 处理引用信息 -> 略

            # 2. 搜索结果统计
            logger.info(f"""
            ====== 搜索结果统计 ======
            关键词: {query}
            检索到的总论文数: {len(all_papers)}
            符合质量要求的论文数: {len(qualified_papers)}
            实际展示的论文数: {len(processed_papers)}
            最低分数要求: {min_score}
            """)

            # 3. 前5篇论文示例
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

            # 4. 分数分布统计
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

            # 5. 年份分布
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

            # 获取前N篇论文的引用信息
            logger.info("====== 获取引用网络 ======")
            for paper in processed_papers[:5]:
                try:
                    paper_id = paper.get('id')  # 改用 'id' 而不是 'paperId'
                    logger.info(f"论文: {paper.get('title')}")
                    logger.info(f"尝试获取论文ID: {paper_id} 的引用信息")
                    if paper_id:
                        citations = await get_paper_citations(paper_id)
                        if citations:
                            logger.info(f"""
                            引用数量: {len(citations)}
                            前5篇引用论文:
                            {', '.join([cite['citingPaper']['title'] for cite in citations[:5]])}
                            """)
                except Exception as e:
                    logger.error(f"获取论文 {paper.get('title')} 的引用信息失败: {str(e)}")
                    continue

            return {
                "query": query,
                "total_available": len(all_papers),
                "qualified_papers": len(qualified_papers),
                "showing": len(processed_papers),
                "min_score": min_score,
                "results": processed_papers,
                "total_fetched": total_fetched,
                "sources_stats": {
                    source: len([pp for pp in qualified_papers if pp.get("source") == source])
                    for source in set(pp.get("source", "unknown") for pp in qualified_papers)
                },
                "stats": {
                    "score_distribution": {
                        "max": max(scores) if scores else 0,
                        "min": min(scores) if scores else 0,
                        "avg": sum(scores)/len(scores) if scores else 0
                    },
                    "year_distribution": {
                        "latest": max(years) if years else None,
                        "earliest": min(years) if years else None,
                        "last_year": len([y for y in years if y >= datetime.now().year - 1]) if years else 0,
                        "last_3_years": len([y for y in years if y >= datetime.now().year - 3]) if years else 0,
                        "last_5_years": len([y for y in years if y >= datetime.now().year - 5]) if years else 0,
                    }
                }
            }

    except Exception as e:
        logger.error(f"搜索过程中发生错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
