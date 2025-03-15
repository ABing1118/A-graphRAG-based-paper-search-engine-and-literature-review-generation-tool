import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.review_service import ReviewService

async def test_review_listener(review_content):
    """测试用的回调函数"""
    print(f"收到新的 review 内容: {review_content[:100]}...")  # 只打印前100个字符

async def main():
    # 创建 ReviewService 实例
    service = ReviewService()
    
    # 添加测试监听器
    service.add_review_listener(test_review_listener)
    
    # 测试获取当前 review
    print("正在获取当前 review...")
    current_review = await service.get_current_review()
    if current_review:
        print(f"当前 review: {current_review[:100]}...")
    else:
        print("暂无 review")
    
    # 启动 WebSocket 客户端
    print("启动 WebSocket 监听...")
    try:
        await service.start_websocket_client()
    except KeyboardInterrupt:
        print("\n停止监听")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序已退出")
