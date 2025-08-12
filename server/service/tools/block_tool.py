from typing import Dict, Any, Union, List
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
    # Handle inline backticks
    if cleaned.startswith("`") and cleaned.endswith("`") and len(cleaned) >= 2:
        cleaned = cleaned[1:-1]
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

def _create_block(block_type: str, content: Union[str, List[Dict]], **kwargs) -> Dict[str, Any]:
    """Create a unified Notion block that handles both text and rich_text_array"""
    # Handle rich text content
    if isinstance(content, list):
        rich_text = content
    else:
        rich_text = [{"type": "text", "text": {"content": str(content)}}]
    
    block = {
        "object": "block",
        "type": block_type,
        block_type: {"rich_text": rich_text}
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
    """Create media blocks with correct Notion API structure"""
    url = url.strip()
    
    # Adjust structure based on Notion API requirements for different media types
    if block_type in ["image", "video"]:
        block_content = {"type": "external", "external": {"url": url}}
    elif block_type in ["embed", "bookmark", "link_preview"]:
        block_content = {"url": url}
    else:
        raise ValueError(f"Unsupported media block type: {block_type}")
    
    block = {
        "object": "block",
        "type": block_type,
        block_type: block_content
    }
    
    if caption := kwargs.get("caption"):
        block[block_type]["caption"] = [{"type": "text", "text": {"content": caption}}]
    
    return block


def _append_block_to_page(page_id: str, block: Dict[str, Any]) -> Dict[str, Any]:
    """Append a single block to a Notion page"""
    return notion.blocks.children.append(block_id=page_id, children=[block])

# ===================== UNIFIED BLOCK CREATION FUNCTIONS =====================

def add_notion_heading_block(page_id: str, content: Union[str, List[Dict]], level: int = 1) -> Dict[str, Any]:
    """Add heading block to Notion page (supports both text and rich_text_array)"""
    block_type = f"heading_{level}" if 1 <= level <= 3 else "heading_1"
    block = _create_block(block_type, content)
    return _append_block_to_page(page_id, block)

def add_notion_paragraph_block(page_id: str, content: Union[str, List[Dict]]) -> Dict[str, Any]:
    """Add paragraph block to Notion page (supports both text and rich_text_array)"""
    block = _create_block("paragraph", content)
    return _append_block_to_page(page_id, block)

def add_notion_callout_block(page_id: str, content: Union[str, List[Dict]], icon: str = "💡") -> Dict[str, Any]:
    """Add callout block to Notion page (supports both text and rich_text_array)"""
    block = _create_block("callout", content, icon={"emoji": icon})
    return _append_block_to_page(page_id, block)

def add_notion_quote_block(page_id: str, content: Union[str, List[Dict]]) -> Dict[str, Any]:
    """Add quote block to Notion page (supports both text and rich_text_array)"""
    block = _create_block("quote", content)
    return _append_block_to_page(page_id, block)

def add_notion_toggle_block(page_id: str, content: Union[str, List[Dict]]) -> Dict[str, Any]:
    """Add toggle block to Notion page (supports both text and rich_text_array)"""
    block = _create_block("toggle", content)
    return _append_block_to_page(page_id, block)

def add_notion_to_do_block(page_id: str, content: Union[str, List[Dict]], checked: bool = False) -> Dict[str, Any]:
    """Add to-do block to Notion page (supports both text and rich_text_array)"""
    block = _create_block("to_do", content, checked=checked)
    return _append_block_to_page(page_id, block)

def add_notion_bulleted_list_block(page_id: str, content: Union[str, List[Dict]]) -> Dict[str, Any]:
    """Add bulleted list block to Notion page (supports both text and rich_text_array)"""
    block = _create_block("bulleted_list_item", content)
    return _append_block_to_page(page_id, block)

def add_notion_numbered_list_block(page_id: str, content: Union[str, List[Dict]]) -> Dict[str, Any]:
    """Add numbered list block to Notion page (supports both text and rich_text_array)"""
    block = _create_block("numbered_list_item", content)
    return _append_block_to_page(page_id, block)

def add_notion_code_block(page_id: str, content: Union[str, List[Dict]], language: str = "python") -> Dict[str, Any]:
    """Add code block to Notion page (supports both text and rich_text_array)"""
    block = _create_block("code", content, language=language)
    return _append_block_to_page(page_id, block)

# Structural blocks (no text content)
def add_notion_divider_block(page_id: str) -> Dict[str, Any]:
    """Add divider block to Notion page"""
    block = _create_structural_block("divider")
    return _append_block_to_page(page_id, block)

def add_notion_table_of_contents_block(page_id: str) -> Dict[str, Any]:
    """Add table of contents block to Notion page"""
    block = _create_structural_block("table_of_contents")
    return _append_block_to_page(page_id, block)

def add_notion_breadcrumb_block(page_id: str) -> Dict[str, Any]:
    """Add breadcrumb block to Notion page"""
    block = _create_structural_block("breadcrumb")
    return _append_block_to_page(page_id, block)

def add_notion_equation_block(page_id: str, expression: str = "E = mc^2") -> Dict[str, Any]:
    """Add equation block to Notion page"""
    block = _create_structural_block("equation", expression=expression)
    return _append_block_to_page(page_id, block)

# Media blocks
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
    """Add URL block to Notion page"""
    block = _create_media_block("link_preview", url, title=title)
    return _append_block_to_page(page_id, block)

def add_notion_bookmark_block(page_id: str, bookmark_url: str, caption: str = "") -> Dict[str, Any]:
    """Add bookmark block to Notion page"""
    block = _create_media_block("bookmark", bookmark_url, caption=caption)
    return _append_block_to_page(page_id, block)

# Table creation function
def add_notion_table_block(page_id: str, table_width: int = 1, table_height: int = 1, 
                          has_column_header: bool = False, has_row_header: bool = False) -> Dict[str, Any]:
    """Add table block to Notion page"""
    # Create empty table data
    children = []
    for row in range(table_height):
        row_cells = []
        for col in range(table_width):
            row_cells.append([{"type": "text", "text": {"content": ""}}])
        
        children.append({
            "type": "table_row",
            "table_row": {"cells": row_cells}
        })
    
    table_block = {
        "type": "table",
        "table": {
            "table_width": table_width,
            "has_column_header": has_column_header,
            "has_row_header": has_row_header,
            "children": children
        }
    }
    
    return notion.blocks.children.append(block_id=page_id, children=[table_block])

# ===================== UNIFIED TOOL WRAPPER FUNCTIONS =====================

def create_unified_tool_func(block_func, required_params, optional_params=None, success_message="Block added successfully"):
    """Create a unified tool wrapper function"""
    def tool_func(input_str: str) -> str:
        try:
            data = json.loads(_clean_json_input(input_str))

            # Handle both text and rich_text_array
            if "rich_text_array" in data:
                content = data["rich_text_array"]
                content_provided = True
            elif "text" in data:
                content = data["text"]
                content_provided = True
            else:
                content = ""
                content_provided = False

            # Validate required parameters (excluding text since we handle text/rich_text_array above)
            content_required = "text" in required_params
            other_required_params = [p for p in required_params if p != "text"]
            missing = [p for p in other_required_params if not data.get(p)]

            # Check if content is needed: either "text" is required OR rich_text_array is provided
            needs_content = content_required or "rich_text_array" in data
            if needs_content and not content_provided:
                missing.append("text or rich_text_array")
            if missing:
                raise ValueError(f"{', '.join(missing)} are required")

            # Prepare arguments
            args = [data["page_id"]]
            if content_provided:
                args.append(content)

            # Add other required params (excluding page_id and text)
            for param in required_params:
                if param not in ["page_id", "text"]:
                    args.append(data[param])

            # Add optional parameters
            kwargs = {}
            if optional_params:
                for k, default_val in optional_params.items():
                    if k in data:
                        kwargs[k] = data[k]
                    elif default_val is not None:
                        kwargs[k] = default_val
            # Execute function
            result = block_func(*args, **kwargs)

            return json.dumps({
                "success": True,
                "message": success_message,
                "block_id": result["results"][0]["id"] if result.get("results") else None
            })

        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e)
            })
    
    return tool_func

# ===================== TOOL FUNCTIONS =====================

add_heading_block_tool_func = create_unified_tool_func(
    add_notion_heading_block, ["page_id"], {"level": 1}, "Added heading block"
)

add_paragraph_block_tool_func = create_unified_tool_func(
    add_notion_paragraph_block, ["page_id"], None, "Added paragraph block"
)

add_callout_block_tool_func = create_unified_tool_func(
    add_notion_callout_block, ["page_id"], {"icon": "💡"}, "Added callout block"
)

add_quote_block_tool_func = create_unified_tool_func(
    add_notion_quote_block, ["page_id"], None, "Added quote block"
)

add_toggle_block_tool_func = create_unified_tool_func(
    add_notion_toggle_block, ["page_id"], None, "Added toggle block"
)

add_todo_block_tool_func = create_unified_tool_func(
    add_notion_to_do_block, ["page_id"], {"checked": False}, "Added todo block"
)

add_bulleted_list_tool_func = create_unified_tool_func(
    add_notion_bulleted_list_block, ["page_id"], None, "Added bulleted list item"
)

add_numbered_list_tool_func = create_unified_tool_func(
    add_notion_numbered_list_block, ["page_id"], None, "Added numbered list item"
)

add_code_block_tool_func = create_unified_tool_func(
    add_notion_code_block, ["page_id"], {"language": "python"}, "Added code block"
)

add_divider_block_tool_func = create_unified_tool_func(
    add_notion_divider_block, ["page_id"], None, "Added divider block"
)

add_table_of_contents_tool_func = create_unified_tool_func(
    add_notion_table_of_contents_block, ["page_id"], None, "Added table of contents"
)

add_breadcrumb_tool_func = create_unified_tool_func(
    add_notion_breadcrumb_block, ["page_id"], None, "Added breadcrumb"
)

add_equation_tool_func = create_unified_tool_func(
    add_notion_equation_block, ["page_id"], {"expression": "E = mc^2"}, "Added equation"
)

add_image_block_tool_func = create_unified_tool_func(
    add_notion_image_block, ["page_id", "image_url"], {"caption": ""}, "Added image block"
)

add_video_block_tool_func = create_unified_tool_func(
    add_notion_video_block, ["page_id", "video_url"], {"caption": ""}, "Added video block"
)

add_embed_block_tool_func = create_unified_tool_func(
    add_notion_embed_block, ["page_id", "embed_url"], {"caption": ""}, "Added embed block"
)

add_url_block_tool_func = create_unified_tool_func(
    add_notion_url_block, ["page_id", "url"], {"title": ""}, "Added URL block"
)

add_bookmark_block_tool_func = create_unified_tool_func(
    add_notion_bookmark_block, ["page_id", "bookmark_url"], {"caption": ""}, "Added bookmark block"
)

add_table_tool_func = create_unified_tool_func(
    add_notion_table_block,
    ["page_id"],
    {"table_width": 1, "table_height": 1, "has_column_header": False, "has_row_header": False},
    "Added table block"
)

# ===================== LANGCHAIN TOOL DEFINITIONS =====================

add_heading_tool = Tool(
    name="Add Heading Block",
    description="Add heading block (h1/h2/h3) to Notion page. Supports both text and rich_text_array. Input: JSON with page_id, text/rich_text_array, and optional level (1-3)",
    func=add_heading_block_tool_func
)

add_paragraph_tool = Tool(
    name="Add Paragraph Block", 
    description="Add paragraph block to Notion page. Supports both text and rich_text_array. Input: JSON with page_id and text/rich_text_array",
    func=add_paragraph_block_tool_func
)

add_callout_tool = Tool(
    name="Add Callout Block",
    description="Add callout block to Notion page. Supports both text and rich_text_array. Input: JSON with page_id, text/rich_text_array, and optional icon",
    func=add_callout_block_tool_func
)

add_quote_tool = Tool(
    name="Add Quote Block",
    description="Add quote block to Notion page. Supports both text and rich_text_array. Input: JSON with page_id and text/rich_text_array",
    func=add_quote_block_tool_func
)

add_divider_tool = Tool(
    name="Add Divider Block",
    description="Add divider line block to Notion page. Input: JSON with page_id",
    func=add_divider_block_tool_func
)

add_toggle_tool = Tool(
    name="Add Toggle Block",
    description="Add toggle block to Notion page. Supports both text and rich_text_array. Input: JSON with page_id and text/rich_text_array",
    func=add_toggle_block_tool_func
)

add_code_tool = Tool(
    name="Add Code Block",
    description="Add code block to Notion page. Supports both text and rich_text_array. Input: JSON with page_id, text/rich_text_array, and optional language",
    func=add_code_block_tool_func
)

add_todo_tool = Tool(
    name="Add Todo Block",
    description="Add todo/checkbox block to Notion page. Supports both text and rich_text_array. Input: JSON with page_id, text/rich_text_array, and optional checked boolean",
    func=add_todo_block_tool_func
)

add_bulleted_list_tool_obj = Tool(
    name="Add Bulleted List Block",
    description="Add bulleted list item to Notion page. Supports both text and rich_text_array. Input: JSON with page_id and text/rich_text_array",
    func=add_bulleted_list_tool_func
)

add_numbered_list_tool_obj = Tool(
    name="Add Numbered List Block",
    description="Add numbered list item to Notion page. Supports both text and rich_text_array. Input: JSON with page_id and text/rich_text_array",
    func=add_numbered_list_tool_func
)

add_table_of_contents_tool_obj = Tool(
    name="Add Table of Contents Block",
    description="Add table of contents block to Notion page. Input: JSON with page_id",
    func=add_table_of_contents_tool_func
)

add_breadcrumb_tool_obj = Tool(
    name="Add Breadcrumb Block",
    description="Add breadcrumb navigation block to Notion page. Input: JSON with page_id",
    func=add_breadcrumb_tool_func
)

add_equation_tool_obj = Tool(
    name="Add Equation Block",
    description="Add mathematical equation block to Notion page. Input: JSON with page_id and optional expression",
    func=add_equation_tool_func
)

add_table_tool_obj = Tool(
    name="Add Table Block",
    description="Add table block to Notion page. Input: JSON with page_id and optional table_width, table_height, has_column_header, has_row_header",
    func=add_table_tool_func
)

add_image_tool = Tool(
    name="Add Image Block",
    description="Add image block to Notion page. Input: JSON with page_id, image_url, and optional caption",
    func=add_image_block_tool_func
)

add_video_tool = Tool(
    name="Add Video Block",
    description="Add video block to Notion page. Input: JSON with page_id, video_url, and optional caption",
    func=add_video_block_tool_func
)

add_embed_tool = Tool(
    name="Add Embed Block",
    description="Add embed block to Notion page. Input: JSON with page_id, embed_url, and optional caption",
    func=add_embed_block_tool_func
)

add_url_tool = Tool(
    name="Add URL Block",
    description="Add URL link block to Notion page. Input: JSON with page_id, url, and optional title",
    func=add_url_block_tool_func
)

add_bookmark_tool = Tool(
    name="Add Bookmark Block", 
    description="Add bookmark preview block to Notion page. Input: JSON with page_id, bookmark_url, and optional caption",
    func=add_bookmark_block_tool_func
)

## Removed rich-text-specific duplicate tools. Unified tools below accept either "text" or "rich_text_array".