# config.py

# Semantic Scholar API的基础URL
SEMANTIC_SCHOLAR_API_URL = "https://api.semanticscholar.org/graph/v1"

# config.py 或 fetcher.py

ELSEVIER_BASE_URL = "https://api.elsevier.com/content/search/scopus"
ELSEVIER_API_KEY = "6d81cc97d6371359de0fcb147f214296"  # 你的 Elsevier key


# 论文质量评分的最低阈值，低于此分数的论文将被过滤
MIN_SCORE_THRESHOLD = 30

# 最大并行请求数，防止对API服务器造成过大压力
MAX_PARALLEL_REQUESTS = 10

# 默认获取的论文数量，用于确保有足够的论文进行筛选
DEFAULT_FETCH_SIZE = 1000
