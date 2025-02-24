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
    try:
        logger.info(f"Starting to fetch paper network for {paper_id}...（开始获取论文 {paper_id} 的引文网络）")
        
        # 1. 获取中心论文的引用和被引用信息
        logger.info("====== First Layer - Center Paper ======（第一层 - 中心论文）")
        logger.info("Fetching citations for center paper...（正在获取中心论文的引用信息...）")
        citations = await get_paper_citations(paper_id)
        if await request.is_disconnected(): return None
        logger.info(f"Found {len(citations)} citing papers（获取到引用论文数量: {len(citations)}）")
        
        logger.info("Fetching references for center paper...（正在获取中心论文的参考文献...）")
        references = await get_paper_references(paper_id)
        logger.info(f"Found {len(references)} referenced papers（获取到参考文献数量: {len(references)}）")
        
        if not isinstance(citations, list): citations = []
        if not isinstance(references, list): references = []
            
        def safe_get_citation_count(paper):
            try:
                return int(paper.get('citationCount', 0) or 0)
            except (TypeError, ValueError):
                return 0
            
        # 2. 获取第一层的高引用论文
        top_citations = sorted(citations, key=safe_get_citation_count, reverse=True)[:2]
        top_references = sorted(references, key=safe_get_citation_count, reverse=True)[:2]
        logger.info(f"选取了 {len(top_citations)} 篇高引用论文和 {len(top_references)} 篇高引用参考文献")
        
        # 3. 初始化节点和边的集合
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
        
        # 5. 处理第一层论文
        logger.info("\n====== First Layer - Related Papers ======（第一层 - 相关论文）")
        first_layer_papers = []
        
        # 5.1 处理引用论文
        for idx, paper in enumerate(top_citations, 1):
            paper_id_cite = paper.get('paperId')
            if paper_id_cite:
                logger.info(f"Processing first layer citation {idx}/{len(top_citations)}: {paper.get('title', 'Unknown')[:50]}...（处理第一层引用论文 {idx}/{len(top_citations)}: {paper.get('title', 'Unknown')[:50]}...）")
                paper_ids.add(paper_id_cite)
                nodes.append({
                    "id": paper_id_cite,
                    "title": paper.get('title', 'Unknown Title'),
                    "citations_count": safe_get_citation_count(paper),
                    "year": paper.get('year'),
                    "type": "citation"
                })
                edges.append({
                    "source": paper_id_cite,
                    "target": paper_id,
                    "type": "citation"
                })
                first_layer_papers.append(paper_id_cite)
        
        # 5.2 处理参考文献
        for idx, paper in enumerate(top_references, 1):
            paper_id_ref = paper.get('paperId')
            if paper_id_ref:
                logger.info(f"Processing first layer citation {idx}/{len(top_references)}: {paper.get('title', 'Unknown')[:50]}...（处理第一层引用论文 {idx}/{len(top_references)}: {paper.get('title', 'Unknown')[:50]}...）")
                paper_ids.add(paper_id_ref)
                nodes.append({
                    "id": paper_id_ref,
                    "title": paper.get('title', 'Unknown Title'),
                    "citations_count": safe_get_citation_count(paper),
                    "year": paper.get('year'),
                    "type": "reference"
                })
                edges.append({
                    "source": paper_id,
                    "target": paper_id_ref,
                    "type": "reference"
                })
                first_layer_papers.append(paper_id_ref)
        
        # 6. 获取第二层引用关系
        logger.info("\n====== Second Layer - Extended Papers ======（第二层 - 扩展论文）")
        second_layer_papers = []
        second_layer_info = {}
        
        for idx1, first_layer_id in enumerate(first_layer_papers, 1):
            if await request.is_disconnected(): return None
            
            logger.info(f"Processing relationships for first layer paper {idx1}/{len(first_layer_papers)}...（处理第一层论文 {idx1}/{len(first_layer_papers)} 的扩展关系...）")
            
            # 6.1 获取第二层论文信息
            logger.info("正在获取引用信息...")
            second_citations = await get_paper_citations(first_layer_id)
            if await request.is_disconnected(): return None
            
            logger.info("正在获取参考文献...")
            second_references = await get_paper_references(first_layer_id)
            
            if not isinstance(second_citations, list): second_citations = []
            if not isinstance(second_references, list): second_references = []
            
            logger.info(f"获取到 {len(second_citations)} 篇引用论文和 {len(second_references)} 篇参考文献")
            
            # 6.2 获取第二层的高引用论文
            second_top_citations = sorted(second_citations, key=safe_get_citation_count, reverse=True)[:2]
            second_top_references = sorted(second_references, key=safe_get_citation_count, reverse=True)[:2]
            
            # 6.3 添加第二层节点和边
            for idx2, paper in enumerate(second_top_citations + second_top_references, 1):
                second_id = paper.get('paperId')
                if second_id and second_id not in paper_ids:
                    # 确定节点类型
                    parent_type = "citation" if paper in second_citations else "reference"
                    first_layer_type = "citation" if first_layer_id in [p.get('paperId') for p in top_citations] else "reference"
                    
                    # 根据父节点类型和一级节点类型确定二级节点类型
                    node_type = f"{parent_type}_to_{first_layer_type}"
                    
                    logger.info(f"Adding second layer paper {idx2}/{len(second_top_citations + second_top_references)}: {paper.get('title', 'Unknown')[:50]}... (type: {node_type})（添加第二层论文 {idx2}/{len(second_top_citations + second_top_references)}: {paper.get('title', 'Unknown')[:50]}... (类型: {node_type})）")
                    
                    paper_ids.add(second_id)
                    second_layer_papers.append(second_id)
                    second_layer_info[second_id] = paper
                    nodes.append({
                        "id": second_id,
                        "title": paper.get('title', 'Unknown Title'),
                        "citations_count": safe_get_citation_count(paper),
                        "year": paper.get('year'),
                        "type": node_type  # 使用新的节点类型
                    })
                    # 根据关系类型添加边
                    if paper in second_citations:
                        edges.append({
                            "source": second_id,
                            "target": first_layer_id,
                            "type": "citation"
                        })
                    else:
                        edges.append({
                            "source": first_layer_id,
                            "target": second_id,
                            "type": "reference"
                        })

        # 7. 获取第二层节点之间的引用关系
        logger.info("\n====== Processing Complete ======（处理完成）")
        logger.info(f"Final node count: {len(nodes)}（最终节点数: {len(nodes)}）")
        logger.info(f"Final edge count: {len(edges)}（最终边数: {len(edges)}）")
        
        return {
            "nodes": nodes,
            "edges": edges
        }
        
    except Exception as e:
        logger.error(f"获取论文 {paper_id} 的子网络失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取子网络失败: {str(e)}") 