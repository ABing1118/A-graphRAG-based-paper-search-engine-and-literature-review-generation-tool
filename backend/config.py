# config.py

import os
from enum import Enum

class SearchMode(Enum):
    ONLINE = "online"   # 实时API
    OFFLINE = "offline" # 本地数据
    HYBRID = "hybrid"   # 优先本地，本地没有再用API

# Semantic Scholar API的基础URL
SEMANTIC_SCHOLAR_API_URL = "https://api.semanticscholar.org/graph/v1"

# 论文质量评分的最低阈值，低于此分数的论文将被过滤
MIN_SCORE_THRESHOLD = 20

# 最大并行请求数，防止对API服务器造成过大压力
MAX_PARALLEL_REQUESTS = 5

# 默认获取的论文数量，用于确保有足够的论文进行筛选
DEFAULT_FETCH_SIZE = 1000

# API 限流配置
MAX_CONCURRENT_REQUESTS = 2  # 最大并发请求数
REQUEST_INTERVAL = 1.0      # 请求间隔（秒）

# 添加新的配置
SEARCH_MODE = SearchMode.HYBRID  # 默认使用混合模式
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")  # 数据存储目录
QUERIES_DIR = os.path.join(DATA_DIR, "queries")  # 按查询词存储的目录

# 创建必要的目录
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(QUERIES_DIR, exist_ok=True)

# 添加配置项
NETWORK_CACHE_SIZE = 200  # 存储更多的引用网络，比如200篇
NETWORK_MINIMUM_REQUIRED = 100  # 最少需要100篇才能离线使用
