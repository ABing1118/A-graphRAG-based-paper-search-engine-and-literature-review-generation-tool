import asyncio
import logging
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException
from typing import List
import json
import os

# 这里的 import 需要根据你的项目实际结构做调整
from config import (
    MIN_SCORE_THRESHOLD,
    DEFAULT_FETCH_SIZE,
    MAX_PARALLEL_REQUESTS,
    SEARCH_MODE,
    QUERIES_DIR,
    SearchMode,  # 添加这个导入
    NETWORK_CACHE_SIZE,
    NETWORK_MINIMUM_REQUIRED
)
from app.services.fetcher import (
    get_client,
    fetch_papers_from_multiple_sources,
    # 如果你还用到了 fetch_paper_details 等，可一并导入
)
from app.services.scorer import calculate_paper_score
from app.routers.paper import get_paper_citations, get_paper_references  # 添加 get_paper_references

logger = logging.getLogger(__name__)
router = APIRouter()

async def save_search_results(query: str, papers: list, paper_networks: dict = None):
    """保存所有搜索结果，不考虑筛选条件"""
    # 1. 保存所有论文数据
    papers_file = os.path.join(QUERIES_DIR, query, "papers.json")
    with open(papers_file, 'w', encoding='utf-8') as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)
    
    # 2. 获取评分最高的N篇论文（不考虑筛选条件）
    all_scored_papers = []
    for paper in papers:
        try:
            score = calculate_paper_score(paper)
            paper["score"] = score
            all_scored_papers.append(paper)
        except Exception as e:
            continue
            
    # 按评分排序，取前N篇
    all_scored_papers.sort(key=lambda x: x["score"], reverse=True)
    top_papers = all_scored_papers[:NETWORK_CACHE_SIZE]
    
    # 3. 获取这些论文的引用网络
    networks_to_fetch = []
    for paper in top_papers:
        paper_id = paper.get('paperId')
        if paper_id not in (paper_networks or {}):
            networks_to_fetch.append(paper)
    
    if networks_to_fetch:
        logger.info(f"需要获取额外 {len(networks_to_fetch)} 篇高分论文的引用网络")
        # 获取这些论文的引用网络
        # ... 获取逻辑 ...

async def check_local_data(query: str) -> tuple[bool, set, int]:
    """检查本地数据完整性"""
    try:
        query_dir = os.path.join(QUERIES_DIR, query)
        papers_file = os.path.join(query_dir, "papers.json")
        networks_dir = os.path.join(query_dir, "networks")
        
        if not all(os.path.exists(p) for p in [query_dir, papers_file, networks_dir]):
            return False, set(), 0
            
        # 1. 读取并筛选论文
        with open(papers_file, 'r', encoding='utf-8') as f:
            all_papers = json.load(f)
            
        # 计算合格论文数量
        qualified_papers = []
        for paper in all_papers:
            try:
                score = calculate_paper_score(paper)
                if score >= MIN_SCORE_THRESHOLD:
                    qualified_papers.append(paper)
            except Exception:
                continue
                
        total_qualified = len(qualified_papers)  # 合格论文总数
        
        # 2. 检查引用网络完整性
        existing_ids = {
            f.replace('.json', '') 
            for f in os.listdir(networks_dir) 
            if f.endswith('.json')
        }
        
        # 3. 判断完整性：
        # - 如果合格论文数 < NETWORK_MINIMUM_REQUIRED，需要所有合格论文的引用网络
        # - 否则需要至少 NETWORK_MINIMUM_REQUIRED 篇
        required_count = min(NETWORK_MINIMUM_REQUIRED, total_qualified)
        is_complete = len(existing_ids) >= required_count
        
        if is_complete:
            logger.info(f"""
            本地数据检查完成:
            总论文数: {len(all_papers)}
            合格论文数: {total_qualified}
            已有引用网络数: {len(existing_ids)}
            状态: 完整
            """)
            
        return is_complete, existing_ids, total_qualified
        
    except Exception as e:
        logger.error(f"检查本地数据时出错: {str(e)}")
        return False, set(), 0

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
        logger.info(f"""
====== 搜索配置 ======
模式: {SEARCH_MODE.value}
关键词: {query}
数据目录: {QUERIES_DIR}
""")
        logger.info(f"收到搜索请求，关键词: {query}")
        logger.info(f"搜索模式: {SEARCH_MODE.value}")

        # hybrid模式下先检查本地数据
        if SEARCH_MODE == SearchMode.HYBRID:
            is_complete, existing_ids, total_papers = await check_local_data(query)
            
            if is_complete:
                logger.info(f"找到完整的本地数据（主题总论文数: {total_papers}），使用离线模式")
                return await search_papers_offline(
                    query=query,
                    min_year=min_year,
                    min_citations=min_citations,
                    top_k=top_k,  # 确保传入用户指定的 top_k
                    min_score=min_score
                )
            elif existing_ids:
                logger.info(f"找到部分本地数据({len(existing_ids)}/{total_papers}篇)，将混合使用本地和在线数据")
            else:
                logger.info("本地无数据，使用在线模式")
        
        # 在线模式或本地数据不完整时的处理
        if SEARCH_MODE in [SearchMode.ONLINE, SearchMode.HYBRID]:
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
                        # 年份和引用量筛选
                        paper_year = paper.get("year")
                        if paper_year is not None:
                            try:
                                paper_year = int(paper_year)
                            except (ValueError, TypeError):
                                continue
                        
                        citations = paper.get("citationCount", 0)
                        try:
                            citations = int(citations)
                        except (ValueError, TypeError):
                            citations = 0
                        
                        # 筛选条件
                        if min_year and (paper_year is None or paper_year < min_year):
                            continue
                        if min_citations and citations < min_citations:
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

                # 在获取引用网络的部分
                paper_networks = await get_citation_networks(
                    query=query,
                    papers=qualified_papers,  # 传入已经排序的合格论文
                    required_count=NETWORK_CACHE_SIZE
                )

                # 如果获取的数据不够，记录警告但不中断流程
                if len(paper_networks) < NETWORK_MINIMUM_REQUIRED:
                    logger.warning(f"未能获取足够的引用网络数据: {len(paper_networks)}/{NETWORK_MINIMUM_REQUIRED}")

                # 保存所有数据
                await save_search_results(query, all_papers, paper_networks)
                logger.info(f"已将搜索结果保存到本地: {query}")

                processed_papers.sort(key=lambda x: x.get("score", 0), reverse=True)

                # 返回搜索结果
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

async def search_papers_offline(
    query: str,
    min_year: int = None,
    min_citations: int = None,
    top_k: int = 60,
    min_score: float = MIN_SCORE_THRESHOLD
) -> dict:
    """
    从本地数据中检索论文
    
    Args:
        query: 搜索关键词
        min_year: 最早年份
        min_citations: 最少引用数
        top_k: 返回结果数量
        min_score: 最低质量分数
    """
    try:
        logger.info(f"""
        开始从本地数据检索: 
        关键词: {query}
        显示数量: {top_k}
        最早年份: {min_year}
        最少引用: {min_citations}
        最低分数: {min_score}
        """)
        
        # 1. 读取基础论文数据
        papers_file = os.path.join(QUERIES_DIR, query, "papers.json")
        with open(papers_file, 'r', encoding='utf-8') as f:
            all_papers = json.load(f)
            
        # 2. 评分和筛选（与在线模式相同的逻辑）
        qualified_papers = []
        for paper in all_papers:
            try:
                # 年份和引用量筛选
                paper_year = paper.get("year")
                if paper_year is not None:
                    try:
                        paper_year = int(paper_year)
                    except (ValueError, TypeError):
                        continue
                
                citations = paper.get("citationCount", 0)
                try:
                    citations = int(citations)
                except (ValueError, TypeError):
                    citations = 0
                
                # 筛选条件
                if min_year and (paper_year is None or paper_year < min_year):
                    continue
                if min_citations and citations < min_citations:
                    continue
                    
                # 计算分数
                score = calculate_paper_score(paper)
                paper["score"] = score
                
                if score >= min_score:
                    qualified_papers.append(paper)
                    
            except Exception as e:
                logger.warning(f"处理论文时出错: {str(e)}, paper: {paper.get('paperId', 'unknown')}")
                continue
                
        # 3. 排序和截取
        qualified_papers.sort(key=lambda x: x["score"], reverse=True)
        
        # 添加日志，显示排序后的论文及其评分
        logger.info("\n====== 论文排序和评分 ======")
        for i, paper in enumerate(qualified_papers[:20]):  # 只显示前20篇，避免日志太长
            logger.info(f"""
            论文 {i+1}:
            标题: {paper.get('title', '无标题')}
            评分: {paper.get('score', 0):.2f}
            年份: {paper.get('year', '未知')}
            引用数: {paper.get('citationCount', 0)}
            """)
            
        processed_papers = qualified_papers[:top_k]
        
        # 4. 格式化输出数据
        results = []
        for paper in processed_papers:
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
                "score": paper.get("score", 0),
                "source": paper.get("source", "unknown")
            }
            results.append(paper_data)
            
        # 5. 读取引用网络数据（如果需要）
        networks_dir = os.path.join(QUERIES_DIR, query, "networks")
        if os.path.exists(networks_dir):
            for paper in results:
                paper_id = paper["id"]
                network_file = os.path.join(networks_dir, f"{paper_id}.json")
                if os.path.exists(network_file):
                    with open(network_file, 'r', encoding='utf-8') as f:
                        network = json.load(f)
                        paper["citations_list"] = network.get("citations", [])
                        paper["references"] = network.get("references", [])
                        
        logger.info(f"""
        离线检索完成:
        总论文数: {len(all_papers)}
        符合条件数: {len(qualified_papers)}
        返回结果数: {len(results)}
        """)
        
        return {
            "query": query,
            "total_available": len(all_papers),
            "qualified_papers": len(qualified_papers),
            "showing": len(results),
            "min_score": min_score,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"离线检索出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"离线检索失败: {str(e)}")

async def get_citation_networks(query: str, papers: list, required_count: int = NETWORK_CACHE_SIZE) -> dict:
    """渐进式获取引用网络数据"""
    paper_networks = {}
    networks_dir = os.path.join(QUERIES_DIR, query, "networks")
    os.makedirs(networks_dir, exist_ok=True)
    
    # 1. 先读取本地已有的网络数据
    existing_networks = {}
    if os.path.exists(networks_dir):
        for filename in os.listdir(networks_dir):
            if filename.endswith('.json'):
                paper_id = filename.replace('.json', '')
                network_path = os.path.join(networks_dir, filename)
                try:
                    with open(network_path, 'r', encoding='utf-8') as f:
                        existing_networks[paper_id] = json.load(f)
                except Exception as e:
                    logger.warning(f"读取网络数据文件出错: {filename}, {str(e)}")

    logger.info(f"本地已有 {len(existing_networks)} 篇论文的引用网络")

    # 2. 确定需要在线获取的论文
    top_papers = papers[:required_count]
    papers_to_fetch = []
    
    for paper in top_papers:
        paper_id = paper.get('paperId')
        if paper_id in existing_networks:
            paper_networks[paper_id] = existing_networks[paper_id]
        else:
            papers_to_fetch.append(paper)
            
    logger.info(f"""
    引用网络数据状态:
    需要的总量: {required_count}
    本地已有: {len(paper_networks)}
    需要获取: {len(papers_to_fetch)}
    """)

    # 3. 在线获取缺失的数据
    if papers_to_fetch:
        max_retries = 3
        logger.info(f"需要在线获取 {len(papers_to_fetch)} 篇论文的引用网络")
        
        for i, paper in enumerate(papers_to_fetch, 1):
            try:
                paper_id = paper.get('paperId')
                if not paper_id:
                    continue
                    
                logger.info(f"正在获取第 {i}/{len(papers_to_fetch)} 篇论文的引用网络")
                network = {'citations': [], 'references': []}
                
                # 获取引用信息（带重试）
                for attempt in range(max_retries):
                    try:
                        citations = await get_paper_citations(paper_id)
                        if citations:
                            network['citations'] = citations
                            logger.info(f"获取到 {len(citations)} 条引用信息")
                        break
                    except HTTPException as e:
                        if e.status_code == 429 and attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 2
                            logger.warning(f"遇到429，等待{wait_time}秒后重试...")
                            await asyncio.sleep(wait_time)
                        else:
                            raise
                            
                # 获取参考文献（带重试）
                for attempt in range(max_retries):
                    try:
                        references = await get_paper_references(paper_id)
                        if references:
                            network['references'] = references
                            logger.info(f"获取到 {len(references)} 条参考文献")
                        break
                    except HTTPException as e:
                        if e.status_code == 429 and attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 2
                            logger.warning(f"遇到429，等待{wait_time}秒后重试...")
                            await asyncio.sleep(wait_time)
                        else:
                            raise
                
                # 保存和添加到结果中
                network_file = os.path.join(networks_dir, f"{paper_id}.json")
                with open(network_file, 'w', encoding='utf-8') as f:
                    json.dump(network, f, ensure_ascii=False, indent=2)
                    
                paper_networks[paper_id] = network
                
            except Exception as e:
                logger.error(f"获取论文引用网络失败: {str(e)}")
                continue
                
    # 即使本地数据够用，也尝试获取更多数据（后台进行）
    if papers_to_fetch and len(paper_networks) >= NETWORK_MINIMUM_REQUIRED:
        logger.info(f"后台获取额外的引用网络数据: {len(papers_to_fetch)} 篇")
        try:
            for paper in papers_to_fetch:
                # ... 获取和保存新数据 ...
                pass
        except Exception as e:
            logger.warning(f"获取额外数据时出错: {str(e)}")
    
    return paper_networks
