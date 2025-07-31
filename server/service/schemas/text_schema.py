from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field

# ========== Rich Text Schemas ==========

class TextLink(BaseModel):
    """Pydantic model for text link"""
    url: str = Field(description="URL for the link")

class TextContent(BaseModel):
    """Pydantic model for text content"""
    content: str = Field(description="Text content")
    link: Optional[TextLink] = Field(default=None, description="Optional link")

class TextAnnotations(BaseModel):
    """Pydantic model for text annotations"""
    bold: bool = Field(default=False, description="Bold formatting")
    italic: bool = Field(default=False, description="Italic formatting")
    underline: bool = Field(default=False, description="Underline formatting")
    strikethrough: bool = Field(default=False, description="Strikethrough formatting")
    code: bool = Field(default=False, description="Code formatting")
    color: str = Field(default="default", description="Text color")

class RichTextItem(BaseModel):
    """Pydantic model for rich text item"""
    type: Literal["text"] = Field(default="text", description="Rich text type")
    text: TextContent = Field(description="Text content and link")
    annotations: TextAnnotations = Field(description="Text annotations")

# ========== Block Schemas ==========

class ParagraphBlock(BaseModel):
    """Pydantic model for paragraph block"""
    rich_text: List[RichTextItem] = Field(description="Rich text content")
    color: str = Field(default="default", description="Block color")

class HeadingBlock(BaseModel):
    """Pydantic model for heading block"""
    rich_text: List[RichTextItem] = Field(description="Rich text content")
    color: str = Field(default="default", description="Block color")
    is_toggleable: bool = Field(default=False, description="Whether heading is toggleable")

class ToDoBlock(BaseModel):
    """Pydantic model for to-do block"""
    rich_text: List[RichTextItem] = Field(description="Rich text content")
    checked: bool = Field(default=False, description="Whether to-do is checked")
    color: str = Field(default="default", description="Block color")

class NotionBlock(BaseModel):
    """Pydantic model for Notion block"""
    object: Literal["block"] = Field(default="block", description="Object type")
    type: str = Field(description="Block type")
    paragraph: Optional[ParagraphBlock] = Field(default=None, description="Paragraph block content")
    heading_1: Optional[HeadingBlock] = Field(default=None, description="Heading 1 block content")
    heading_2: Optional[HeadingBlock] = Field(default=None, description="Heading 2 block content")
    heading_3: Optional[HeadingBlock] = Field(default=None, description="Heading 3 block content")
    to_do: Optional[ToDoBlock] = Field(default=None, description="To-do block content")

# ========== Tool Result Schemas ==========

class AppendResult(BaseModel):
    """Pydantic model for append operation result"""
    success: bool = Field(description="Whether the operation was successful")
    message: str = Field(description="Result message")
    page_id: Optional[str] = Field(default=None, description="Page ID where blocks were appended")
    blocks_count: Optional[int] = Field(default=None, description="Number of blocks appended")
    error: Optional[str] = Field(default=None, description="Error message if operation failed")

class RichTextResult(BaseModel):
    """Pydantic model for rich text creation result"""
    success: bool = Field(description="Whether the operation was successful")
    rich_text_objects: List[Dict[str, Any]] = Field(description="Created rich text objects")
    count: int = Field(description="Number of rich text objects created")
    error: str = Field(default="", description="Error message if operation failed")

class BlocksResult(BaseModel):
    """Pydantic model for blocks creation result"""
    success: bool = Field(description="Whether the operation was successful")
    blocks: List[Dict[str, Any]] = Field(description="Created blocks")
    count: int = Field(description="Number of blocks created")
    error: str = Field(default="", description="Error message if operation failed")

# ========== Agent Result Schema ==========

class TextResult(BaseModel):
    """Pydantic model for text operation result"""
    success: bool = Field(description="Whether the text operation was successful")
    message: str = Field(description="Result message")
    page_id: str = Field(description="Target page ID")
    blocks_added: int = Field(default=0, description="Number of blocks added")
    error: str = Field(default="", description="Error message if operation failed") 