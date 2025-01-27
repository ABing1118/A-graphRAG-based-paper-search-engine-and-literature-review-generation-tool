# services/scorer.py

import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def calculate_paper_score(paper: dict) -> float:
    """
    新版论文评分逻辑：
    
    1) 基础分: 40
    2) 引用量 (最高40分):
       - citations = 0 => -5 (显性惩罚)
       - 1~10 => +0
       - 11~50 => +5
       - 51~100 => +10
       - 101~500 => +20
       - 501~1000 => +30
       - 1001+ => +40
       
    3) 年份 (最高25分):
       - 近 5 年 => +25
       - 5~10 年 => +10
       - 10~15 年 => +5
       - 15+ 年 => +0
       
    4) 期刊/会议质量 (最高15分):
       - 如果在 top_venues => +15
       - 否则如果在 good_venues => +10
       
    5) 开放获取 => +5
    
    最终分数不超过100
    """

    score = 40.0  # 基础分

    try:
        # ========== (1) 引用数评分 (最高40分) ========== 
        citations = int(paper.get("citationCount", 0))

        if citations == 0:
            # 对 0 引用做显式惩罚
            score -= 5
        elif 1 <= citations <= 10:
            # 不加不减
            pass
        elif 11 <= citations <= 50:
            score += 5
        elif 51 <= citations <= 100:
            score += 10
        elif 101 <= citations <= 500:
            score += 20
        elif 501 <= citations <= 1000:
            score += 30
        else:  # citations > 1000
            score += 40

        # ========== (2) 年份评分 (最高25分) ========== 
        pub_date = paper.get("publicationDate", "")
        if pub_date:
            current_year = datetime.now().year
            try:
                year = int(pub_date.split("-")[0])
            except:
                year = 0

            age = current_year - year
            if age <= 5:
                # 近5年 => +25
                score += 25
            elif age <= 10:
                # 5~10年 => +10
                score += 10
            elif age <= 15:
                # 10~15年 => +5
                score += 5
            else:
                # 15年以上 => +0
                pass

        # ========== (3) 期刊/会议质量评分 (最高15分) ========== 
        venue = paper.get("venue", "").lower()

        top_venues = {
            "nature", "science", "cell",  
            "neural information processing systems",
            "icml", "iclr", "aaai", "ijcai",
            "ieee transactions on pattern analysis and machine intelligence",
            "artificial intelligence"
        }

        good_venues = {
            "ieee", "acm", "elsevier", "springer",
            "neurocomputing", "neural networks",
            "expert systems with applications"
        }

        if any(v in venue for v in top_venues):
            score += 15
        elif any(v in venue for v in good_venues):
            score += 10

        # ========== (4) 开放获取加分 (最高5分) ========== 
        if paper.get("openAccessPdf"):
            score += 5

    except Exception as e:
        logger.warning(f"计算论文分数时出错: {str(e)}, paper_id: {paper.get('paperId', 'unknown')}")

    # 最终不超100
    return min(100, score)
