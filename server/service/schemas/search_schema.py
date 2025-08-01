from typing import List, Dict, Any
from pydantic import BaseModel, Field

class PageInfo(BaseModel):
    id: str = Field(description="Page ID")
    title: str = Field(description="Page title")
    url: str = Field(description="Page URL")
    created_time: str = Field(description="Page creation time")
    last_edited_time: str = Field(description="Page last edited time")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "created_time": self.created_time,
            "last_edited_time": self.last_edited_time
        }

class SearchData(BaseModel):
    pages: List[PageInfo] = Field(description="List of found pages")
    total_found: int = Field(description="Total number of pages found")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pages": [page.to_dict() for page in self.pages],
            "total_found": self.total_found
        }

class SearchResult(BaseModel):
    success: bool = Field(description="Whether the search was successful")
    data: SearchData = Field(description="Search data containing pages and total count")
    error: str = Field(description="Error message if search failed", default="")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data.to_dict(),
            "error": self.error
        }

 