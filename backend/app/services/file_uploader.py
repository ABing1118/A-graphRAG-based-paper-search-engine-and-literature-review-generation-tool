import requests
from pathlib import Path
import logging
import base64

logger = logging.getLogger(__name__)

class FileUploader:
    def __init__(self, server_url: str, access_token: str):
        self.server_url = server_url
        self.headers = {
            'Authorization': f'token {access_token}',
            'Content-Type': 'application/json'
        }
        
    def upload_file(self, local_file_path: Path, remote_folder: str) -> bool:
        """
        上传文件到远程服务器
        
        Args:
            local_file_path: 本地文件路径
            remote_folder: 远程服务器上的目标文件夹
            
        Returns:
            bool: 上传是否成功
        """
        try:
            # 修正远程路径
            if remote_folder.startswith('/home/jovyan'):
                remote_folder = remote_folder[11:]
            remote_folder = remote_folder.replace(' ', '%20')
            remote_path = f"{remote_folder}/{local_file_path.name}"
            if remote_path.startswith('/'):
                remote_path = remote_path[1:]
            
            logger.info(f"Uploading to path: {remote_path}")
            
            # 直接读取文本内容，不使用base64编码
            with open(local_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 构建JSON数据
            data = {
                'type': 'file',
                'format': 'text',
                'content': content
            }
            
            # 发送请求
            response = requests.put(
                f"{self.server_url}api/contents/{remote_path}",
                headers=self.headers,
                json=data
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"File uploaded successfully to {remote_path}")
                return True
            else:
                logger.error(f"Failed to upload file: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            return False 