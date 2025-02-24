# services/scorer.py
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def calculate_paper_score(paper: dict) -> float:
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
    try:
        # 1. 基础分数 (30分)
        base_score = 30
        
        # 2. 引用量权重 (最高40分) - 增加引用的权重
        citations = paper.get("citationCount", 0)
        if citations and isinstance(citations, (int, float)):
            citation_score = np.log1p(float(citations)) * 15  # 从10增加到15
        else:
            citation_score = 0
            
        # 3. 年份权重 (最高20分)
        current_year = datetime.now().year
        year = paper.get("year")
        if year and isinstance(year, (int, float)):
            year_diff = current_year - int(year)
            if year_diff <= 5:
                year_score = 20
            elif year_diff <= 10:
                year_score = 15
            else:
                year_score = 10
        else:
            year_score = 0
            
        # 4. 期刊/会议权重 (最高10分) - 大幅降低期刊权重
        venue_score = 0
        venue = paper.get("venue", "").lower() if paper.get("venue") else ""
        top_venues = {
            "nature": 10, "science": 10,    # 从50降到10
            "cell": 8,                      # 从40降到8
            "neural information processing systems": 7,  # 从35降到7
            "icml": 7, "iclr": 7,
            "ieee": 6, "acm": 6             # 从30降到6
        }
        for top_venue, weight in top_venues.items():
            if venue and top_venue in venue:
                venue_score = weight
                break
                
        # 5. 添加摘要评分 (10分)
        abstract_score = 0
        abstract = paper.get("abstract", "")
        if abstract and isinstance(abstract, str):
            abstract = abstract.strip()
            # 排除无效摘要
            if abstract.lower() not in ["no abstract", "暂无摘要"]:
                # 根据摘要长度和质量给分
                words = len(abstract.split())
                if words >= 100:  # 完整摘要
                    abstract_score = 20
                elif words >= 50:  # 较短摘要
                    abstract_score = 15
                else:  # 极短摘要
                    abstract_score = 10
                    
        return base_score + citation_score + year_score + venue_score + abstract_score
        
    except Exception as e:
        raise ValueError(f"计算论文评分时出错: {str(e)}")
