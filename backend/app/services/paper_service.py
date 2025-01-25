from app.models.paper import Paper
from typing import List

class PaperService:
    @staticmethod
    async def search_papers(query: str) -> List[Paper]:
        # 这里暂时返回模拟数据，后续可以替换为真实的数据库查询
        mock_results = [
            Paper(title="Paper about AI", authors=["Alice", "Bob"]),
            Paper(title="Paper about Machine Learning", authors=["Charlie"]),
            Paper(title="Paper about Deep Learning", authors=["Dave", "Eve"])
        ]
        return mock_results 