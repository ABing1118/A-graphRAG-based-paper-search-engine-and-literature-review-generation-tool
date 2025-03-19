import requests
from pathlib import Path
import logging
import urllib3
import urllib.parse

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class FileUploader:
    def __init__(self, server_url: str, access_token: str):
        self.server_url = server_url
        self.headers = {
            'Authorization': f'token {access_token}'
        }
        
    def upload_file(self, local_file_path: Path, query: str = None) -> bool:
        """
        通过 FastAPI 服务上传文件
        
        Args:
            local_file_path: 本地文件路径
            query: 搜索查询词
            
        Returns:
            bool: 上传是否成功
        """
        try:
            logger.info(f"Uploading file with query: {query}")
            
            # 构建上传URL，将查询词作为URL参数
            base_url = "https://hub.comp-teach.qmul.ac.uk/user/jp2021213177/proxy/8011/upload/"
            upload_url = f"{base_url}?token=789ffdb6ea3445dfa8e5cb036d535545"
            if query:
                # 对查询词进行URL编码
                encoded_query = urllib.parse.quote(query)
                upload_url = f"{upload_url}&query={encoded_query}"
            
            logger.info(f"Upload URL: {upload_url}")
            
            # 准备文件数据
            with open(local_file_path, 'rb') as f:
                files = {'file': (local_file_path.name, f)}
                
                # 发送POST请求
                response = requests.post(
                    upload_url,
                    files=files,
                    verify=False
                )
            
            if response.status_code == 200:
                logger.info(f"File uploaded successfully via FastAPI service")
                return True
            else:
                logger.error(f"Failed to upload file: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            return False 