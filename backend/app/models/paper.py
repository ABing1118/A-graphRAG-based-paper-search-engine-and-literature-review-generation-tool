from pydantic import BaseModel
from typing import List

class Paper(BaseModel):
    title: str
    authors: List[str] 