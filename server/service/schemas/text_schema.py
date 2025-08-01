from pydantic import BaseModel, Field

# ========== Agent Result Schema ==========

class TextResult(BaseModel):
    """Pydantic model for text operation result"""
    success: bool = Field(description="Whether the text operation was successful")
    message: str = Field(description="Result message")
    page_id: str = Field(description="Target page ID")
    blocks_added: int = Field(default=0, description="Number of blocks added")
    error: str = Field(default="", description="Error message if operation failed") 