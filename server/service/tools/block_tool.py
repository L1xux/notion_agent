from typing import Dict, Any
import json
from notion_client import Client
from config.env_config import get_notion_api_key
from langchain.tools import Tool

# Initialize Notion client
notion = Client(auth=get_notion_api_key())

# ===================== HELPER FUNCTIONS =====================

def _clean_json_input(input_str: str) -> str:
    """Clean JSON input by removing markdown code blocks"""
    cleaned = input_str.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()

# Optimized block creation using dictionaries for configuration
BLOCK_CONFIGS = {
    "heading_1": {"is_toggleable": False, "color": "default"},
    "heading_2": {"is_toggleable": False, "color": "default"},
    "heading_3": {"is_toggleable": False, "color": "default"},
    "to_do": {"checked": False, "color": "default"},
    "code": {"language": "python", "caption": []},
    "callout": {"icon": {"emoji": "💡"}, "color": "default"},
    "toggle": {"color": "default"}
}

def _create_simple_block(block_type: str, content: str, **kwargs) -> Dict[str, Any]:
    """Create a simple Notion block with basic text content"""
    block = {
        "object": "block",
        "type": block_type,
        block_type: {"rich_text": [{"type": "text", "text": {"content": content}}]}
    }
    
    # Apply type-specific configuration
    if block_type in BLOCK_CONFIGS:
        config = BLOCK_CONFIGS[block_type].copy()
        config.update({k: v for k, v in kwargs.items() if k in config})
        block[block_type].update(config)
    
    return block

def _create_structural_block(block_type: str, **kwargs) -> Dict[str, Any]:
    """Create structural blocks without text content"""
    configs = {
        "divider": {},
        "table_of_contents": {"color": "default"},
        "breadcrumb": {},
        "equation": {"expression": kwargs.get("expression", "E = mc^2")}
    }
    
    return {
        "object": "block",
        "type": block_type,
        block_type: configs.get(block_type, {})
    }

def _create_media_block(block_type: str, url: str, **kwargs) -> Dict[str, Any]:
    """Create media blocks with URL"""
    # Clean URL - remove any whitespace and ensure it's a valid URL format
    url = url.strip()
    
    block = {
        "object": "block",
        "type": block_type,
        block_type: {"type": "external", "external": {"url": url}}
    }
    
    if caption := kwargs.get("caption"):
        block[block_type]["caption"] = [{"type": "text", "text": {"content": caption}}]
    
    return block

def _append_block_to_page(page_id: str, block: Dict[str, Any]) -> Dict[str, Any]:
    """Append a single block to a Notion page"""
    return notion.blocks.children.append(block_id=page_id, children=[block])

# ===================== BLOCK CREATION FUNCTIONS =====================

def add_notion_heading_block(page_id: str, text: str, level: int = 1) -> Dict[str, Any]:
    """Add heading block to Notion page"""
    block_type = f"heading_{level}" if 1 <= level <= 3 else "heading_1"
    block = _create_simple_block(block_type, text)
    return _append_block_to_page(page_id, block)

def add_notion_paragraph_block(page_id: str, text: str) -> Dict[str, Any]:
    """Add paragraph block to Notion page"""
    block = _create_simple_block("paragraph", text)
    return _append_block_to_page(page_id, block)

def add_notion_callout_block(page_id: str, text: str, icon: str = "💡") -> Dict[str, Any]:
    """Add callout block to Notion page"""
    block = _create_simple_block("callout", text, icon=icon)
    return _append_block_to_page(page_id, block)

def add_notion_quote_block(page_id: str, text: str) -> Dict[str, Any]:
    """Add quote block to Notion page"""
    block = _create_simple_block("quote", text)
    return _append_block_to_page(page_id, block)

def add_notion_divider_block(page_id: str) -> Dict[str, Any]:
    """Add divider block to Notion page"""
    block = _create_structural_block("divider")
    return _append_block_to_page(page_id, block)

def add_notion_toggle_block(page_id: str, text: str) -> Dict[str, Any]:
    """Add toggle block to Notion page"""
    block = _create_simple_block("toggle", text)
    return _append_block_to_page(page_id, block)

def add_notion_code_block(page_id: str, text: str, language: str = "python") -> Dict[str, Any]:
    """Add code block to Notion page"""
    block = _create_simple_block("code", text, language=language)
    return _append_block_to_page(page_id, block)

def add_notion_to_do_block(page_id: str, text: str, checked: bool = False) -> Dict[str, Any]:
    """Add to-do block to Notion page"""
    block = _create_simple_block("to_do", text, checked=checked)
    return _append_block_to_page(page_id, block)

def add_notion_bulleted_list_block(page_id: str, text: str) -> Dict[str, Any]:
    """Add bulleted list block to Notion page"""
    block = _create_simple_block("bulleted_list_item", text)
    return _append_block_to_page(page_id, block)

def add_notion_numbered_list_block(page_id: str, text: str) -> Dict[str, Any]:
    """Add numbered list block to Notion page"""
    block = _create_simple_block("numbered_list_item", text)
    return _append_block_to_page(page_id, block)

def add_notion_table_of_contents_block(page_id: str) -> Dict[str, Any]:
    """Add table of contents block to Notion page"""
    block = _create_structural_block("table_of_contents")
    return _append_block_to_page(page_id, block)

def add_notion_breadcrumb_block(page_id: str) -> Dict[str, Any]:
    """Add breadcrumb block to Notion page"""
    block = _create_structural_block("breadcrumb")
    return _append_block_to_page(page_id, block)

def add_notion_equation_block(page_id: str, expression: str) -> Dict[str, Any]:
    """Add equation block to Notion page"""
    block = _create_structural_block("equation", expression=expression)
    return _append_block_to_page(page_id, block)

def add_notion_table_block(page_id: str, table_width: int = 3, table_height: int = 3, has_column_header: bool = True, has_row_header: bool = False) -> Dict[str, Any]:
    """Add table block to Notion page"""
    children = []
    
    # Create all rows (header + data rows)
    for row in range(table_height):
        row_cells = []
        for col in range(table_width):
            # Determine cell content
            if has_column_header and row == 0:
                content = f"Header {col + 1}"
            elif has_row_header and col == 0:
                content = f"Row {row + 1}" if not (has_column_header and row == 0) else "Header 1"
            else:
                content = ""
            
            row_cells.append([{"type": "text", "text": {"content": content}}])
        
        children.append({
            "type": "table_row", 
            "table_row": {"cells": row_cells}
        })
    
    block = {
        "object": "block",
        "type": "table",
        "table": {
            "table_width": table_width,
            "has_column_header": has_column_header,
            "has_row_header": has_row_header,
            "children": children
        }
    }
    
    return _append_block_to_page(page_id, block)

def add_notion_image_block(page_id: str, image_url: str, caption: str = "") -> Dict[str, Any]:
    """Add image block to Notion page"""
    block = _create_media_block("image", image_url, caption=caption)
    return _append_block_to_page(page_id, block)

def add_notion_video_block(page_id: str, video_url: str, caption: str = "") -> Dict[str, Any]:
    """Add video block to Notion page"""
    block = _create_media_block("video", video_url, caption=caption)
    return _append_block_to_page(page_id, block)

def add_notion_embed_block(page_id: str, embed_url: str, caption: str = "") -> Dict[str, Any]:
    """Add embed block to Notion page"""
    block = _create_media_block("embed", embed_url, caption=caption)
    return _append_block_to_page(page_id, block)

def add_notion_url_block(page_id: str, url: str, title: str = "") -> Dict[str, Any]:
    """Add URL link as paragraph block to Notion page"""
    text = title if title else url
    block = {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{
                "type": "text",
                "text": {"content": text, "link": {"url": url}}
            }]
        }
    }
    return _append_block_to_page(page_id, block)

def add_notion_bookmark_block(page_id: str, bookmark_url: str, caption: str = "") -> Dict[str, Any]:
    """Add bookmark block to Notion page"""
    block = {
        "object": "block",
        "type": "bookmark",
        "bookmark": {"url": bookmark_url}
    }
    if caption:
        block["bookmark"]["caption"] = [{"type": "text", "text": {"content": caption}}]
    return _append_block_to_page(page_id, block)

# ===================== LANGCHAIN TOOL WRAPPERS =====================

def notion_tool(required_params=None, optional_params=None, success_message="Added block"):
    """
    Decorator for creating Notion block tools with automatic JSON parsing and error handling
    
    Args:
        required_params: List of required parameter names
        optional_params: Dict of optional parameters with defaults
        success_message: Success message string or callable
    """
    def decorator(func):
        def wrapper(input_str: str) -> str:
            try:
                cleaned = _clean_json_input(input_str)
                data = json.loads(cleaned)
                
                # Validate required parameters
                req_params = required_params or []
                missing = [p for p in req_params if not data.get(p)]
                if missing:
                    raise ValueError(f"{', '.join(missing)} are required")
                
                # Extract parameters
                args = [data.get(p) for p in req_params]
                kwargs = {k: data.get(k, v) for k, v in (optional_params or {}).items()}
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Generate message
                message = success_message(data) if callable(success_message) else success_message
                
                return json.dumps({
                    "success": True,
                    "message": message,
                    "block_id": result["results"][0]["id"] if result.get("results") else None
                }, ensure_ascii=False)
                
            except Exception as e:
                block_type = func.__name__.replace('add_notion_', '').replace('_block', '')
                return json.dumps({
                    "success": False,
                    "error": f"Failed to add {block_type} block: {str(e)}"
                })
        
        wrapper.__name__ = f"{func.__name__}_tool"
        wrapper.__doc__ = f"Tool: {func.__doc__ or 'Add block to Notion page'}"
        return wrapper
    
    return decorator

# Clean decorator-based tool definitions
@notion_tool(["page_id", "text"], {"level": 1}, lambda d: f"Added heading_{d.get('level', 1)} block")
def add_heading_block_tool(page_id: str, text: str, level: int = 1) -> Dict[str, Any]:
    return add_notion_heading_block(page_id, text, level)

@notion_tool(["page_id", "text"], success_message="Added paragraph block")
def add_paragraph_block_tool(page_id: str, text: str) -> Dict[str, Any]:
    return add_notion_paragraph_block(page_id, text)

@notion_tool(["page_id", "text"], {"icon": "💡"}, lambda d: f"Added callout block with {d.get('icon', '💡')} icon")
def add_callout_block_tool(page_id: str, text: str, icon: str = "💡") -> Dict[str, Any]:
    return add_notion_callout_block(page_id, text, icon)

@notion_tool(["page_id", "text"], success_message="Added quote block")
def add_quote_block_tool(page_id: str, text: str) -> Dict[str, Any]:
    return add_notion_quote_block(page_id, text)

@notion_tool(["page_id"], success_message="Added divider block")
def add_divider_block_tool(page_id: str) -> Dict[str, Any]:
    return add_notion_divider_block(page_id)

@notion_tool(["page_id", "text"], success_message="Added toggle block")
def add_toggle_block_tool(page_id: str, text: str) -> Dict[str, Any]:
    return add_notion_toggle_block(page_id, text)

@notion_tool(["page_id", "text"], {"language": "python"}, lambda d: f"Added {d.get('language', 'python')} code block")
def add_code_block_tool(page_id: str, text: str, language: str = "python") -> Dict[str, Any]:
    return add_notion_code_block(page_id, text, language)

@notion_tool(["page_id", "text"], {"checked": False}, lambda d: f"Added to-do block ({'checked' if d.get('checked', False) else 'unchecked'})")
def add_todo_block_tool(page_id: str, text: str, checked: bool = False) -> Dict[str, Any]:
    return add_notion_to_do_block(page_id, text, checked)

@notion_tool(["page_id", "text"], success_message="Added bulleted list item")
def add_bulleted_list_tool(page_id: str, text: str) -> Dict[str, Any]:
    return add_notion_bulleted_list_block(page_id, text)

@notion_tool(["page_id", "text"], success_message="Added numbered list item")
def add_numbered_list_tool(page_id: str, text: str) -> Dict[str, Any]:
    return add_notion_numbered_list_block(page_id, text)

@notion_tool(["page_id"], success_message="Added table of contents")
def add_table_of_contents_tool(page_id: str) -> Dict[str, Any]:
    return add_notion_table_of_contents_block(page_id)

@notion_tool(["page_id"], success_message="Added breadcrumb")
def add_breadcrumb_tool(page_id: str) -> Dict[str, Any]:
    return add_notion_breadcrumb_block(page_id)

@notion_tool(["page_id"], {"expression": "E = mc^2"}, lambda d: f"Added equation: {d.get('expression', 'E = mc^2')}")
def add_equation_tool(page_id: str, expression: str = "E = mc^2") -> Dict[str, Any]:
    return add_notion_equation_block(page_id, expression)

@notion_tool(["page_id"], {"table_width": 1, "table_height": 1, "has_column_header": False, "has_row_header": False}, 
             lambda d: f"Added table ({d.get('table_width', 1)}x{d.get('table_height', 1)})")
def add_table_tool(page_id: str, table_width: int = 1, table_height: int = 1, has_column_header: bool = False, has_row_header: bool = False) -> Dict[str, Any]:
    return add_notion_table_block(page_id, table_width, table_height, has_column_header, has_row_header)

@notion_tool(["page_id", "image_url"], {"caption": ""}, success_message="Added image block")
def add_image_block_tool(page_id: str, image_url: str, caption: str = "") -> Dict[str, Any]:
    return add_notion_image_block(page_id, image_url, caption)

@notion_tool(["page_id", "video_url"], {"caption": ""}, success_message="Added video block")
def add_video_block_tool(page_id: str, video_url: str, caption: str = "") -> Dict[str, Any]:
    return add_notion_video_block(page_id, video_url, caption)

@notion_tool(["page_id", "embed_url"], {"caption": ""}, success_message="Added embed block")
def add_embed_block_tool(page_id: str, embed_url: str, caption: str = "") -> Dict[str, Any]:
    return add_notion_embed_block(page_id, embed_url, caption)

@notion_tool(["page_id", "url"], {"title": ""}, success_message="Added URL block")
def add_url_block_tool(page_id: str, url: str, title: str = "") -> Dict[str, Any]:
    return add_notion_url_block(page_id, url, title)

@notion_tool(["page_id", "bookmark_url"], {"caption": ""}, success_message="Added bookmark block")
def add_bookmark_block_tool(page_id: str, bookmark_url: str, caption: str = "") -> Dict[str, Any]:
    return add_notion_bookmark_block(page_id, bookmark_url, caption)

# ===================== LANGCHAIN TOOL DEFINITIONS =====================

add_heading_tool = Tool(
    name="Add Heading Block",
    description="Add heading block (h1/h2/h3) to Notion page with text",
    func=add_heading_block_tool
)

add_paragraph_tool = Tool(
    name="Add Paragraph Block", 
    description="Add paragraph block to Notion page with text",
    func=add_paragraph_block_tool
)

add_callout_tool = Tool(
    name="Add Callout Block",
    description="Add callout block to Notion page with icon (for important notes)",
    func=add_callout_block_tool
)

add_quote_tool = Tool(
    name="Add Quote Block",
    description="Add quote block to Notion page for highlighting quotes",
    func=add_quote_block_tool
)

add_divider_tool = Tool(
    name="Add Divider Block",
    description="Add divider line block to Notion page for section separation",
    func=add_divider_block_tool
)

add_toggle_tool = Tool(
    name="Add Toggle Block",
    description="Add toggle block to Notion page for collapsible content",
    func=add_toggle_block_tool
)

add_code_tool = Tool(
    name="Add Code Block",
    description="Add code block to Notion page with syntax highlighting",
    func=add_code_block_tool
)

add_todo_tool = Tool(
    name="Add Todo Block",
    description="Add to-do checklist item to Notion page with checked/unchecked state",
    func=add_todo_block_tool
)

add_bulleted_list_tool_obj = Tool(
    name="Add Bulleted List",
    description="Add bulleted list item to Notion page",
    func=add_bulleted_list_tool
)

add_numbered_list_tool_obj = Tool(
    name="Add Numbered List", 
    description="Add numbered list item to Notion page",
    func=add_numbered_list_tool
)

add_table_of_contents_tool_obj = Tool(
    name="Add Table of Contents",
    description="Add table of contents block to Notion page for navigation",
    func=add_table_of_contents_tool
)

add_breadcrumb_tool_obj = Tool(
    name="Add Breadcrumb Block",
    description="Add breadcrumb navigation block to Notion page",
    func=add_breadcrumb_tool
)

add_equation_tool_obj = Tool(
    name="Add Equation Block",
    description="Add mathematical equation block to Notion page with LaTeX expressions",
    func=add_equation_tool
)

add_table_tool_obj = Tool(
    name="Add Table Block",
    description="Add table block to Notion page with customizable columns and headers",
    func=add_table_tool
)

add_image_tool = Tool(
    name="Add Image Block",
    description="Add image block to Notion page with URL and optional caption",
    func=add_image_block_tool
)

add_video_tool = Tool(
    name="Add Video Block",
    description="Add video block to Notion page (YouTube, Vimeo, etc.)",
    func=add_video_block_tool
)

add_embed_tool = Tool(
    name="Add Embed Block",
    description="Add embed block to Notion page for external content",
    func=add_embed_block_tool
)

add_url_tool = Tool(
    name="Add URL Block",
    description="Add URL link block to Notion page with optional title",
    func=add_url_block_tool
)

add_bookmark_tool = Tool(
    name="Add Bookmark Block", 
    description="Add bookmark preview block to Notion page with URL and optional caption",
    func=add_bookmark_block_tool
)



