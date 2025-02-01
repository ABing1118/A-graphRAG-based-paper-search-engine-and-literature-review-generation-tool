from fastapi import APIRouter, HTTPException, Query, Request
from starlette.background import BackgroundTasks
import logging
import json
import os
from typing import List, Dict, Set
from config import QUERIES_DIR, MIN_SCORE_THRESHOLD
from app.routers.paper import get_paper_citations, get_paper_references  # 确保添加这行导入
import asyncio  # 添加这个导入

logger = logging.getLogger(__name__)
router = APIRouter()

def load_paper_network(query: str, paper_id: str) -> Dict:
    """加载单个论文的引用网络数据"""
    try:
        network_file = os.path.join(QUERIES_DIR, query, "networks", f"{paper_id}.json")
        with open(network_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载论文 {paper_id} 的网络数据失败: {str(e)}")
        return {"citations": [], "references": []}

def load_paper_info(query: str) -> Dict:
    """加载查询相关的所有论文基础信息"""
    try:
        papers_file = os.path.join(QUERIES_DIR, query, "papers.json")
        with open(papers_file, 'r', encoding='utf-8') as f:
            papers = json.load(f)
            return {paper["paperId"]: paper for paper in papers}
    except Exception as e:
        logger.error(f"加载论文基础信息失败: {str(e)}")
        return {}

@router.get("/citation_network/{query}")
async def get_citation_network(
    query: str,
    top_k: int = Query(None, description="展示论文数量"),  # 改为 None，表示必须由用户提供
    min_score: float = Query(MIN_SCORE_THRESHOLD)
) -> dict:
    """
    构建论文引用关系网络
    返回适合可视化的节点和边数据
    """
    try:
        # 1. 加载所有论文信息
        paper_info = load_paper_info(query)
        if not paper_info:
            raise HTTPException(status_code=404, detail="未找到相关论文数据")
            
        # 2. 获取评分最高的K篇论文
        qualified_papers = [
            paper for paper in paper_info.values()
            if paper.get("score", 0) >= min_score
        ]
        qualified_papers.sort(key=lambda x: x.get("score", 0), reverse=True)
        top_papers = qualified_papers[:top_k]  # 与 search_papers 中的 processed_papers 对应
        
        # 3. 构建节点集合
        nodes = []
        paper_ids = set()  # 跟踪已添加的论文ID
        
        # 添加top_k论文作为主要节点
        for paper in top_papers:
            paper_id = paper["paperId"]
            paper_ids.add(paper_id)
            nodes.append({
                "id": paper_id,
                "title": paper.get("title", "Unknown"),
                "year": paper.get("year", "Unknown"),
                "authors": [author.get("name", "") for author in paper.get("authors", [])],
                "citations_count": paper.get("citationCount", 0),
                "score": paper.get("score", 0),
                "type": "main"  # 标记为主要节点
            })
        
        # 4. 构建边（引用关系）
        edges = []
        edge_set = set()  # 避免重复边
        
        # 遍历top_k论文的引用网络
        for paper in top_papers:
            paper_id = paper["paperId"]
            network = load_paper_network(query, paper_id)
            
            # 处理引用关系
            for citation in network.get("citations", []):
                citing_id = citation.get("paperId")
                if citing_id in paper_ids:  # 只添加top_k论文之间的引用关系
                    edge_key = f"{citing_id}->{paper_id}"
                    if edge_key not in edge_set:
                        edges.append({
                            "source": citing_id,
                            "target": paper_id,
                            "type": "citation"
                        })
                        edge_set.add(edge_key)
            
            # 处理参考文献
            for reference in network.get("references", []):
                ref_id = reference.get("paperId")
                if ref_id in paper_ids:  # 只添加top_k论文之间的引用关系
                    edge_key = f"{paper_id}->{ref_id}"
                    if edge_key not in edge_set:
                        edges.append({
                            "source": paper_id,
                            "target": ref_id,
                            "type": "reference"
                        })
                        edge_set.add(edge_key)
        
        # 5. 返回网络数据
        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "query": query,
                "top_k": top_k
            }
        }
        
    except Exception as e:
        logger.error(f"构建引用网络失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/paper_network/{paper_id}")
async def get_paper_sub_network(paper_id: str, request: Request):
    """获取单篇论文的引用网络（包括引用关系最多的5篇论文以及它们之间的关系）"""
    try:
        logger.info(f"开始获取论文 {paper_id} 的子网络")
        
        # 1. 获取中心论文的引用和被引用信息
        citations = await get_paper_citations(paper_id)
        logger.info(f"获取到中心论文引用数: {len(citations)}")
        
        # 检查客户端是否还连接
        if await request.is_disconnected():
            logger.info("Client disconnected after getting citations")
            return None
        
        references = await get_paper_references(paper_id)
        logger.info(f"获取到中心论文参考文献数: {len(references)}")
        
        # 确保是列表并处理None值
        if not isinstance(citations, list):
            citations = []
        if not isinstance(references, list):
            references = []
            
        # 2. 按引用量排序并只取前5篇
        def safe_get_citation_count(paper):
            try:
                return int(paper.get('citationCount', 0) or 0)
            except (TypeError, ValueError):
                return 0
            
        top_citations = sorted(citations, key=safe_get_citation_count, reverse=True)[:5]
        top_references = sorted(references, key=safe_get_citation_count, reverse=True)[:5]
        
        logger.info(f"选取了 {len(top_citations)} 篇高引用论文和 {len(top_references)} 篇高引用参考文献")
        
        # 3. 构建节点集合
        nodes = []
        edges = []
        edge_set = set()
        paper_ids = set()
        
        # 4. 添加中心论文节点
        nodes.append({
            "id": paper_id,
            "title": "Center Paper",
            "type": "center"
        })
        paper_ids.add(paper_id)
        
        # 5. 添加引用论文节点和边
        for paper in top_citations:
            paper_id_cite = paper.get('paperId')
            if paper_id_cite:
                paper_ids.add(paper_id_cite)
                nodes.append({
                    "id": paper_id_cite,
                    "title": paper.get('title', 'Unknown Title'),
                    "citations_count": safe_get_citation_count(paper),
                    "year": paper.get('year'),
                    "type": "citation"
                })
                edge_key = f"{paper_id_cite}->{paper_id}"
                if edge_key not in edge_set:
                    edges.append({
                        "source": paper_id_cite,
                        "target": paper_id,
                        "type": "citation"
                    })
                    edge_set.add(edge_key)
        
        # 6. 添加被引用论文节点和边
        for paper in top_references:
            paper_id_ref = paper.get('paperId')
            if paper_id_ref:
                paper_ids.add(paper_id_ref)
                nodes.append({
                    "id": paper_id_ref,
                    "title": paper.get('title', 'Unknown Title'),
                    "citations_count": safe_get_citation_count(paper),
                    "year": paper.get('year'),
                    "type": "reference"
                })
                edge_key = f"{paper_id}->{paper_id_ref}"
                if edge_key not in edge_set:
                    edges.append({
                        "source": paper_id,
                        "target": paper_id_ref,
                        "type": "reference"
                    })
                    edge_set.add(edge_key)
        
        logger.info(f"初始节点数: {len(nodes)}, 初始边数: {len(edges)}")
        
        # 7. 遍历论文获取它们之间的引用关系
        logger.info("开始获取论文间的引用关系...")
        processed_count = 0
        
        for source_paper in top_citations + top_references:
            if await request.is_disconnected():
                logger.info("Client disconnected during paper processing")
                return None
                
            source_id = source_paper.get('paperId')
            if not source_id:
                continue
                
            try:
                logger.info(f"处理论文 {processed_count + 1}/10: {source_id}")
                
                paper_citations = await get_paper_citations(source_id)
                logger.info(f"获取到引用数: {len(paper_citations) if isinstance(paper_citations, list) else 0}")

                
                paper_references = await get_paper_references(source_id)
                logger.info(f"获取到参考文献数: {len(paper_references) if isinstance(paper_references, list) else 0}")

                
                old_edge_count = len(edges)
                
                # 处理引用关系
                if isinstance(paper_citations, list):
                    for citation in paper_citations:
                        citing_id = citation.get('paperId')
                        if citing_id in paper_ids:  # 只添加选中论文之间的引用关系
                            edge_key = f"{citing_id}->{source_id}"
                            if edge_key not in edge_set:
                                edges.append({
                                    "source": citing_id,
                                    "target": source_id,
                                    "type": "citation"
                                })
                                edge_set.add(edge_key)
                
                # 处理参考文献
                if isinstance(paper_references, list):
                    for reference in paper_references:
                        ref_id = reference.get('paperId')
                        if ref_id in paper_ids:  # 只添加选中论文之间的引用关系
                            edge_key = f"{source_id}->{ref_id}"
                            if edge_key not in edge_set:
                                edges.append({
                                    "source": source_id,
                                    "target": ref_id,
                                    "type": "reference"
                                })
                                edge_set.add(edge_key)
                                
                logger.info(f"新增边数: {len(edges) - old_edge_count}")
                processed_count += 1
                
            except Exception as e:
                logger.error(f"处理论文 {source_id} 失败: {str(e)}")
                continue
        
        logger.info(f"处理完成。最终节点数: {len(nodes)}, 最终边数: {len(edges)}")
        
        result = {
            "nodes": nodes,
            "edges": edges
        }
        logger.info(f"成功返回子网络数据，状态码: 200")
        return result
        
    except Exception as e:
        logger.error(f"获取论文 {paper_id} 的子网络失败: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"获取子网络失败: {str(e)}"
        ) 