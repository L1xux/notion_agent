from pydantic import BaseModel, Field

# ===================== SEARCH TOOL SCHEMAS =====================

class NotionSearchFilter(BaseModel):
    """Pydantic model for Notion search filter"""
    property: str = Field(description="Property to filter by")
    value: str = Field(description="Value to filter")

class NotionSearchRequest(BaseModel):
    """Pydantic model for Notion search request"""
    query: str = Field(description="Search query")
    filter: NotionSearchFilter = Field(description="Search filter") 