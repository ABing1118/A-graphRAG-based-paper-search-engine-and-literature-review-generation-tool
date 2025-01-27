# services/scorer.py
import numpy as np
from datetime import datetime

def calculate_paper_score(paper):
    """
    计算论文的重要性分数
    
    评分标准：
    1. 年份权重：越新的文章分数越高
    2. 引用量权重：使用对数计算，避免引用差异过大
    3. 期刊/会议权重：顶级期刊和会议有额外加分
    4. 摘要加分：有摘要的论文额外加分
    
    Args:
        paper (dict): 包含论文信息的字典
    
    Returns:
        float: 论文的综合评分
    """
    current_year = datetime.now().year
    score = 0

    # 1. 年份权重 (最近5年权重最高)
    year = paper.get("year")
    if year and isinstance(year, (int, float)):
        year_diff = current_year - int(year)
        if year_diff <= 5:
            score += 30
        elif year_diff <= 10:
            score += 20
        else:
            score += 10
    
    # 2. 引用量权重 (使用对数平滑)
    citations = paper.get("citationCount", 0)
    if citations and isinstance(citations, (int, float)):
        score += np.log1p(float(citations)) * 10
    
    # 3. 期刊/会议权重
    venue = paper.get("venue", "").lower() if paper.get("venue") else ""
    top_venues = {
        "nature": 50, "science": 50,    # 顶级期刊
        "cell": 40,
        "neural information processing systems": 35,  # 顶级会议
        "icml": 35, "iclr": 35,
        "ieee": 30, "acm": 30
    }
    for top_venue, weight in top_venues.items():
        if venue and top_venue in venue:
            score += weight
            break

    # 4. 摘要加分 (新增)
    abstract = paper.get("abstract", "").strip()
    if abstract and abstract.lower() not in ["no abstract", "暂无摘要"]:
        score += 10  # 有摘要加10分

    return score
