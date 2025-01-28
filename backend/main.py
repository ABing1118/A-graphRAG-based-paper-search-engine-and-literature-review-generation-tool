# main.py
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.search import router as search_router
from app.routers.paper import router as paper_router
from app.routers.network import router as network_router
# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# 配置CORS中间件，允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 允许的前端域名
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有请求头
)

# 注册路由模块
app.include_router(search_router)  # 搜索相关的路由
app.include_router(paper_router)   # 论文详情相关的路由
app.include_router(network_router) # 引用网络相关的路由

# 如果还有其他全局事件，如 on_startup, on_shutdown 等也可以放在这里
# ...
