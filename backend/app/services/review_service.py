import websockets
import asyncio
import logging
import ssl
import time
from config import WS_REVIEW_URL

logger = logging.getLogger(__name__)

class ReviewService:
    def __init__(self):
        # WebSocket URL 已经在配置中
        self.ws_url = WS_REVIEW_URL  # 直接使用配置的 URL，不需要替换
        self.review_listeners = []
        self.current_review = None  # 存储最新的 review 内容
        self.last_update_time = None  # 添加时间戳
        
        # 创建 SSL 上下文
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
    def add_review_listener(self, callback):
        """添加回调函数，当收到新的review时会被调用"""
        self.review_listeners.append(callback)
        
    async def start_websocket_client(self):
        """启动WebSocket客户端来监听review更新"""
        while True:
            try:
                # 添加心跳超时和其他WebSocket选项
                async with websockets.connect(
                    self.ws_url,
                    ssl=self.ssl_context,
                    ping_interval=20,  # 每20秒发送一次ping
                    ping_timeout=10,   # ping超时时间
                    close_timeout=10    # 关闭超时时间
                ) as websocket:
                    logger.info("Connected to review websocket")
                    
                    # 发送初始消息
                    try:
                        await websocket.send("connect")
                    except Exception as e:
                        logger.error(f"Failed to send initial message: {str(e)}")
                        continue
                        
                    while True:
                        try:
                            review_content = await websocket.recv()
                            self.current_review = review_content
                            self.last_update_time = int(time.time() * 1000)  # 更新时间戳
                            # 通知所有监听器
                            for listener in self.review_listeners:
                                await listener(review_content)
                        except websockets.exceptions.ConnectionClosed:
                            logger.error("WebSocket connection closed")
                            break
                        except Exception as e:
                            logger.error(f"Error receiving message: {str(e)}")
                            break
                            
            except Exception as e:
                logger.error(f"WebSocket connection error: {str(e)}")
                
            # 连接断开后等待一段时间再重试
            logger.info("Waiting 5 seconds before reconnecting...")
            await asyncio.sleep(5)
                
    async def get_current_review(self):
        """获取当前的review内容"""
        return self.current_review 