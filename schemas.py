from pydantic import BaseModel
from typing import Optional


class BlogCreate(BaseModel):
    title: str
    content: str
    author_id: int
    image_url: Optional[str] = None
    status: Optional[str] = "draft"
    tag_id: Optional[int] = int

class TagCreate(BaseModel):
    tag: str

class BlogUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    tag_id: Optional[int] = None
    image_url: Optional[str] = None