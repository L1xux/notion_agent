from typing import Dict, Any, List, Optional, Union, Literal
from notion_client import Client
from config.env_config import get_notion_api_key
import json
import re

from service.schemas.text_schema import (
    TextLink, TextContent, TextAnnotations, RichTextItem,
    ParagraphBlock, HeadingBlock, ToDoBlock, NotionBlock,
    AppendResult, RichTextResult, BlocksResult
)

# Initialize Notion client
notion: Client = Client(auth=get_notion_api_key())

# ========== Rich Text Creation Functions ==========

def create_rich_text_item(
    content: str,
    link_url: Optional[str] = None,
    bold: bool = False,
    italic: bool = False,
    underline: bool = False,
    strikethrough: bool = False,
    code: bool = False,
    color: str = "default"
) -> RichTextItem:
    """
    Create a rich text item with specified formatting
    
    Args:
        content: Text content
        link_url: Optional URL for link
        bold: Bold formatting
        italic: Italic formatting
        underline: Underline formatting
        strikethrough: Strikethrough formatting
        code: Code formatting
        color: Text color
        
    Returns:
        RichTextItem Pydantic model
    """
    text_content = TextContent(
        content=content,
        link=TextLink(url=link_url) if link_url else None
    )
    
    annotations = TextAnnotations(
        bold=bold,
        italic=italic,
        underline=underline,
        strikethrough=strikethrough,
        code=code,
        color=color
    )
    
    return RichTextItem(
        text=text_content,
        annotations=annotations
    )

def create_rich_text_list(items: List[Dict[str, Any]]) -> List[RichTextItem]:
    """
    Create a list of rich text items from configuration
    
    Args:
        items: List of dictionaries with rich text configuration
               Format: [{"content": "text", "bold": True, "color": "blue", ...}, ...]
               
    Returns:
        List of RichTextItem models
    """
    rich_text_items: List[RichTextItem] = []
    
    for item in items:
        rich_text_item = create_rich_text_item(
            content=item.get("content", ""),
            link_url=item.get("link_url"),
            bold=item.get("bold", False),
            italic=item.get("italic", False),
            underline=item.get("underline", False),
            strikethrough=item.get("strikethrough", False),
            code=item.get("code", False),
            color=item.get("color", "default")
        )
        rich_text_items.append(rich_text_item)
    
    return rich_text_items

# ========== Block Creation Functions ==========

def create_paragraph_block(
    rich_text: List[RichTextItem],
    color: str = "default"
) -> Dict[str, Any]:
    """
    Create a paragraph block dictionary
    
    Args:
        rich_text: List of rich text items
        color: Block color
        
    Returns:
        Dictionary representing paragraph block
    """
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [item.model_dump() for item in rich_text],
            "color": color
        }
    }

def create_heading_block(
    rich_text: List[RichTextItem],
    level: Literal[1, 2, 3] = 1,
    color: str = "default",
    is_toggleable: bool = False
) -> Dict[str, Any]:
    """
    Create a heading block dictionary
    
    Args:
        rich_text: List of rich text items
        level: Heading level (1, 2, or 3)
        color: Block color
        is_toggleable: Whether heading is toggleable
        
    Returns:
        Dictionary representing heading block
    """
    heading_type = f"heading_{level}"
    return {
        "object": "block",
        "type": heading_type,
        heading_type: {
            "rich_text": [item.model_dump() for item in rich_text],
            "color": color,
            "is_toggleable": is_toggleable
        }
    }

def create_todo_block(
    rich_text: List[RichTextItem],
    checked: bool = False,
    color: str = "default"
) -> Dict[str, Any]:
    """
    Create a to-do block dictionary
    
    Args:
        rich_text: List of rich text items
        checked: Whether to-do is checked
        color: Block color
        
    Returns:
        Dictionary representing to-do block
    """
    return {
        "object": "block",
        "type": "to_do",
        "to_do": {
            "rich_text": [item.model_dump() for item in rich_text],
            "checked": checked,
            "color": color
        }
    }

# ========== Page Append Function ==========

def append_blocks_to_page(
    page_id: str,
    blocks: List[Dict[str, Any]]
) -> AppendResult:
    """
    Append blocks to a Notion page using children list
    
    Args:
        page_id: Notion page ID
        blocks: List of block dictionaries
        
    Returns:
        AppendResult with operation result
    """
    try:
        print(f"📝 Appending {len(blocks)} blocks to page {page_id}")
        
        # Print each block type for debugging
        for i, block in enumerate(blocks):
            print(f"🔸 Block {i+1}: {block.get('type', 'unknown')}")
        
        # Append all blocks at once using children list
        response = notion.blocks.children.append(
            block_id=page_id,
            children=blocks
        )
        
        print(f"✅ Successfully appended {len(blocks)} blocks to page")
        print(f"📊 Response: {response}")
        
        return AppendResult(
            success=True,
            message=f"Successfully appended {len(blocks)} blocks to page",
            page_id=page_id,
            blocks_count=len(blocks)
        )
        
    except Exception as e:
        print(f"❌ Error appending blocks to page: {e}")
        
        return AppendResult(
            success=False,
            message="Failed to append blocks to page",
            error=str(e)
        )

# ========== Convenience Functions ==========

def create_simple_paragraph(text: str, **formatting) -> Dict[str, Any]:
    """
    Create a simple paragraph block with one text item
    
    Args:
        text: Text content
        **formatting: Formatting options (bold, italic, color, etc.)
        
    Returns:
        Dictionary representing paragraph block
    """
    rich_text_item = create_rich_text_item(text, **formatting)
    return create_paragraph_block([rich_text_item])

def create_simple_heading(text: str, level: Literal[1, 2, 3] = 1, **formatting) -> Dict[str, Any]:
    """
    Create a simple heading block with one text item
    
    Args:
        text: Text content
        level: Heading level
        **formatting: Formatting options (bold, italic, color, etc.)
        
    Returns:
        Dictionary representing heading block
    """
    rich_text_item = create_rich_text_item(text, **formatting)
    return create_heading_block([rich_text_item], level=level)

def create_simple_todo(text: str, checked: bool = False, **formatting) -> Dict[str, Any]:
    """
    Create a simple to-do block with one text item
    
    Args:
        text: Text content
        checked: Whether to-do is checked
        **formatting: Formatting options (bold, italic, color, etc.)
        
    Returns:
        Dictionary representing to-do block
    """
    rich_text_item = create_rich_text_item(text, **formatting)
    return create_todo_block([rich_text_item], checked=checked)

# ========== LangChain Tool Wrappers ==========

def create_rich_text_objects_tool(input_str: str) -> str:
    """
    LangChain tool for creating rich text objects
    
    Args:
        input_str: JSON string with format:
                  [{"content": "text", "bold": true, "color": "blue"}, ...]
    
    Returns:
        JSON string with rich text objects
    """
    try:
        print(f"🔧 Rich text tool called with: {input_str}")
        
        # Clean the input string - extract JSON from any text
        # Try to find JSON array in the input string
        json_pattern = r'\[[\s\S]*\]'
        json_match = re.search(json_pattern, input_str)
        
        if json_match:
            cleaned_input = json_match.group(0)
        else:
            # Fallback to basic cleaning
            cleaned_input = input_str.strip()
            if cleaned_input.startswith("```json"):
                cleaned_input = cleaned_input[7:]
            if cleaned_input.startswith("```"):
                cleaned_input = cleaned_input[3:]
            if cleaned_input.endswith("```"):
                cleaned_input = cleaned_input[:-3]
            cleaned_input = cleaned_input.strip()
        
        print(f"🧹 Cleaned input: {cleaned_input}")
        
        # Parse input JSON
        items_config = json.loads(cleaned_input)
        
        print(f"📝 Processing {len(items_config)} rich text item configs")
        
        # Create rich text items using the existing function
        rich_text_items = create_rich_text_list(items_config)
        
        # Convert to dictionaries for JSON serialization
        rich_text_dicts = [item.model_dump() for item in rich_text_items]
        
        result = {
            "success": True,
            "rich_text_objects": rich_text_dicts,
            "count": len(rich_text_dicts)
        }
        
        return json.dumps(result)
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"Rich text creation failed: {str(e)}"
        }
        return json.dumps(error_result)

def create_blocks_tool(input_str: str) -> str:
    """
    LangChain tool for creating Notion blocks
    
    Args:
        input_str: JSON string with format:
                  {
                    "rich_text_objects": [...],
                    "blocks_config": [
                      {"type": "paragraph", "color": "default"},
                      {"type": "heading_1", "is_toggleable": false},
                      {"type": "to_do", "checked": false}
                    ]
                  }
    
    Returns:
        JSON string with created blocks
    """
    try:
        print(f"🔧 Blocks creation tool called with: {input_str}")
        
        # Clean the input string - extract JSON from any text
        # Try to find JSON object in the input string
        json_pattern = r'\{[\s\S]*\}'
        json_match = re.search(json_pattern, input_str)
        
        if json_match:
            cleaned_input = json_match.group(0)
        else:
            # Fallback to basic cleaning
            cleaned_input = input_str.strip()
            if cleaned_input.startswith("```json"):
                cleaned_input = cleaned_input[7:]
            if cleaned_input.startswith("```"):
                cleaned_input = cleaned_input[3:]
            if cleaned_input.endswith("```"):
                cleaned_input = cleaned_input[:-3]
            cleaned_input = cleaned_input.strip()
        
        print(f"🧹 Cleaned input: {cleaned_input}")
        
        # Parse input JSON
        config = json.loads(cleaned_input)
        rich_text_objects_data = config.get("rich_text_objects", [])
        blocks_config = config.get("blocks_config", [])
        
        print(f"📋 Rich text objects data type: {type(rich_text_objects_data)}")
        print(f"📋 Rich text objects count: {len(rich_text_objects_data) if isinstance(rich_text_objects_data, list) else 'not a list'}")
        print(f"📋 Blocks config count: {len(blocks_config) if isinstance(blocks_config, list) else 'not a list'}")
        
        if rich_text_objects_data and len(rich_text_objects_data) > 0:
            print(f"📋 First rich text object: {rich_text_objects_data[0]}")
            print(f"📋 First rich text object type: {type(rich_text_objects_data[0])}")
        
        # Convert rich text objects back to Pydantic models
        rich_text_objects = []
        for item_data in rich_text_objects_data:
            # Handle both agent format and proper format
            if isinstance(item_data, dict):
                # Check if it's agent format: {"content": "text", "bold": true, ...}
                if "content" in item_data and "text" not in item_data:
                    print(f"🔄 Converting agent format to RichTextItem: {item_data}")
                    
                    # Extract content and link
                    content = item_data.get("content", "")
                    link_url = item_data.get("link_url")
                    
                    # Create text content
                    text_content = TextContent(
                        content=content,
                        link=TextLink(url=link_url) if link_url else None
                    )
                    
                    # Create annotations
                    annotations = TextAnnotations(
                        bold=item_data.get("bold", False),
                        italic=item_data.get("italic", False),
                        underline=item_data.get("underline", False),
                        strikethrough=item_data.get("strikethrough", False),
                        code=item_data.get("code", False),
                        color=item_data.get("color", "default")
                    )
                    
                    # Create RichTextItem
                    rich_text_item = RichTextItem(
                        text=text_content,
                        annotations=annotations
                    )
                else:
                    # Already in proper format
                    rich_text_item = RichTextItem(**item_data)
                
                rich_text_objects.append(rich_text_item)
            else:
                print(f"⚠️ Unexpected rich text item format: {type(item_data)}")
                continue
        
        # Create blocks - group rich text objects intelligently
        blocks = []
        
        # If number of blocks_config matches rich_text_objects, use 1:1 mapping
        if len(blocks_config) == len(rich_text_objects):
            for i, block_config in enumerate(blocks_config):
                block_type = block_config.get("type", "paragraph")
                block_rich_text = [rich_text_objects[i]]
                
                if block_type == "paragraph":
                    color = block_config.get("color", "default")
                    block = create_paragraph_block(block_rich_text, color)
                elif block_type.startswith("heading_"):
                    level = int(block_type.split("_")[1])
                    color = block_config.get("color", "default")
                    is_toggleable = block_config.get("is_toggleable", False)
                    block = create_heading_block(block_rich_text, level, color, is_toggleable)
                elif block_type == "to_do":
                    checked = block_config.get("checked", False)
                    color = block_config.get("color", "default")
                    block = create_todo_block(block_rich_text, checked, color)
                else:
                    # Default to paragraph
                    block = create_paragraph_block(block_rich_text)
                
                blocks.append(block)
        
        # If more rich text objects than blocks, group them intelligently
        elif len(rich_text_objects) > len(blocks_config):
            print(f"🔄 Grouping {len(rich_text_objects)} rich text objects into {len(blocks_config)} blocks")
            
            # Calculate how many rich text objects per block
            objects_per_block = len(rich_text_objects) // len(blocks_config)
            remainder = len(rich_text_objects) % len(blocks_config)
            
            rich_text_index = 0
            for i, block_config in enumerate(blocks_config):
                block_type = block_config.get("type", "paragraph")
                
                # Determine how many rich text objects for this block
                objects_for_this_block = objects_per_block
                if i < remainder:  # Distribute remainder among first blocks
                    objects_for_this_block += 1
                
                # Get rich text objects for this block
                end_index = rich_text_index + objects_for_this_block
                block_rich_text = rich_text_objects[rich_text_index:end_index]
                rich_text_index = end_index
                
                print(f"🔸 Block {i+1} ({block_type}): using {len(block_rich_text)} rich text objects")
                
                if block_type == "paragraph":
                    color = block_config.get("color", "default")
                    block = create_paragraph_block(block_rich_text, color)
                elif block_type.startswith("heading_"):
                    level = int(block_type.split("_")[1])
                    color = block_config.get("color", "default")
                    is_toggleable = block_config.get("is_toggleable", False)
                    # For headings, typically use only first rich text object
                    block = create_heading_block([block_rich_text[0]] if block_rich_text else [], level, color, is_toggleable)
                elif block_type == "to_do":
                    checked = block_config.get("checked", False)
                    color = block_config.get("color", "default")
                    # For to-dos, typically use only first rich text object
                    block = create_todo_block([block_rich_text[0]] if block_rich_text else [], checked, color)
                else:
                    # Default to paragraph
                    block = create_paragraph_block(block_rich_text)
                
                blocks.append(block)
        
        # If fewer rich text objects than blocks, create simple blocks
        else:
            print(f"🔄 Creating {len(blocks_config)} blocks with {len(rich_text_objects)} rich text objects")
            for i, block_config in enumerate(blocks_config):
                block_type = block_config.get("type", "paragraph")
                
                # Use available rich text objects or create empty blocks
                if i < len(rich_text_objects):
                    block_rich_text = [rich_text_objects[i]]
                else:
                    block_rich_text = []
                
                if block_type == "paragraph":
                    color = block_config.get("color", "default")
                    block = create_paragraph_block(block_rich_text, color)
                elif block_type.startswith("heading_"):
                    level = int(block_type.split("_")[1])
                    color = block_config.get("color", "default")
                    is_toggleable = block_config.get("is_toggleable", False)
                    block = create_heading_block(block_rich_text, level, color, is_toggleable)
                elif block_type == "to_do":
                    checked = block_config.get("checked", False)
                    color = block_config.get("color", "default")
                    block = create_todo_block(block_rich_text, checked, color)
                else:
                    # Default to paragraph
                    block = create_paragraph_block(block_rich_text)
                
                blocks.append(block)
        
        result = {
            "success": True,
            "blocks": blocks,
            "count": len(blocks)
        }
        
        # Validate JSON structure before returning
        try:
            json_result = json.dumps(result)
            # Test if it can be parsed back
            json.loads(json_result)
            return json_result
        except Exception as json_error:
            print(f"❌ JSON validation failed: {json_error}")
            # Try to fix the blocks structure
            cleaned_blocks = []
            for block in blocks:
                if isinstance(block, dict):
                    cleaned_blocks.append(block)
            
            fixed_result = {
                "success": True,
                "blocks": cleaned_blocks,
                "count": len(cleaned_blocks)
            }
            return json.dumps(fixed_result)
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"Block creation failed: {str(e)}"
        }
        return json.dumps(error_result)

def append_blocks_to_page_tool(input_str: str) -> str:
    """
    LangChain tool for appending blocks to a Notion page
    
    Args:
        input_str: JSON string with format:
                  {
                    "page_id": "page_id",
                    "blocks": [block_dict1, block_dict2, ...]
                  }
    
    Returns:
        JSON string with append result
    """
    try:
        print(f"🔧 Append blocks tool called with: {input_str}")
        
        # Clean the input string - extract JSON from any text
        # Try to find JSON object in the input string
        json_pattern = r'\{[\s\S]*\}'
        json_match = re.search(json_pattern, input_str)
        
        if json_match:
            cleaned_input = json_match.group(0)
        else:
            # Fallback to basic cleaning
            cleaned_input = input_str.strip()
            if cleaned_input.startswith("```json"):
                cleaned_input = cleaned_input[7:]
            if cleaned_input.startswith("```"):
                cleaned_input = cleaned_input[3:]
            if cleaned_input.endswith("```"):
                cleaned_input = cleaned_input[:-3]
            cleaned_input = cleaned_input.strip()
        
        print(f"🧹 Cleaned input: {cleaned_input}")
        
        # Parse input JSON
        config = json.loads(cleaned_input)
        page_id = config.get("page_id")
        blocks_data = config.get("blocks", [])
        
        if not page_id:
            raise ValueError("page_id is required")
        
        # Use blocks directly as they are already dictionaries
        append_result = append_blocks_to_page(page_id, blocks_data)
        
        result = {
            "success": append_result.success,
            "message": append_result.message,
            "page_id": append_result.page_id,
            "blocks_count": append_result.blocks_count,
            "error": append_result.error or ""
        }
        
        return json.dumps(result)
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"Append blocks failed: {str(e)}"
        }
        return json.dumps(error_result) 