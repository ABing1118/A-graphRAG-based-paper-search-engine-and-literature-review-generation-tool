from fastapi import APIRouter, HTTPException, Query
import logging
import json
import os
from typing import List, Dict, Set
from config import QUERIES_DIR, MIN_SCORE_THRESHOLD

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