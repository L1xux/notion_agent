# Notion API Tools for FastAPI

A comprehensive collection of modular utility tools for integrating Notion API with FastAPI applications.

## File Structure

```
server/service/tools/
├── tool.py              # Main import file (exports all tools)
├── page_tool.py         # Page-related tools
├── block_tool.py        # Block-related tools + block creation utilities
├── database_tool.py     # Database-related tools
├── search_tool.py       # Search-related tools
├── text_tool.py         # Text formatting and rich text tools
├── user_tool.py         # User management tools
├── comment_tool.py      # Comment management tools
└── file_tool.py         # File upload and management tools
```

## Installation

```bash
pip install notion-client
```

Set your Notion API key as an environment variable:
```bash
export NOTION_API_KEY="your_notion_api_key_here"
```

## Usage

### Import All Tools
```python
from server.service.tools.tool import *
```

### Import Specific Tools
```python
from server.service.tools.page_tool import create_page_tool
from server.service.tools.block_tool import create_callout_block_tool
from server.service.tools.text_tool import create_bold_text_tool
```

## Available Tools

### Page Tools (`page_tool.py`)
- `create_page_tool` - Create new pages
- `update_page_tool` - Update existing pages
- `retrieve_page_tool` - Get page details

### Block Tools (`block_tool.py`)
**Block API Operations:**
- `append_block_children_tool` - Add blocks to pages
- `retrieve_block_children_tool` - Get block children
- `delete_block_tool` - Delete blocks
- `retrieve_block_tool` - Get block details
- `update_block_tool` - Update blocks

**Block Creation Tools:**
- `create_callout_block_tool` - Callout blocks with icons
- `create_child_page_block_tool` - Child page blocks
- `create_code_block_tool` - Code blocks with language support
- `create_divider_block_tool` - Divider blocks
- `create_file_block_tool` - File blocks
- `create_image_block_tool` - Image blocks with captions
- `create_mention_block_tool` - User mention blocks
- `create_bulleted_list_block_tool` - Bulleted lists
- `create_numbered_list_block_tool` - Numbered lists
- `create_toggle_block_tool` - Toggle blocks
- `create_quote_block_tool` - Quote blocks
- `create_table_block_tool` - Table blocks
- `create_bookmark_block_tool` - Bookmark blocks
- `create_equation_block_tool` - Equation blocks
- `create_synced_block_block_tool` - Synced blocks

### Database Tools (`database_tool.py`)
- `query_database_tool` - Query databases
- `create_database_tool` - Create databases
- `update_database_tool` - Update databases
- `retrieve_database_tool` - Get database details

### Search Tools (`search_tool.py`)
- `search_tool` - Search in Notion

### Text Tools (`text_tool.py`)
**Text Formatting:**
- `create_bold_text_tool` - Create bold text
- `create_italic_text_tool` - Create italic text
- `create_code_text_tool` - Create code text
- `create_strikethrough_text_tool` - Create strikethrough text
- `create_underlined_text_tool` - Create underlined text
- `create_colored_text_tool` - Create colored text
- `create_linked_text_tool` - Create linked text with URLs

**Special Text Types:**
- `create_mention_text_tool` - Create user mention text
- `create_equation_text_tool` - Create equation text
- `create_date_text_tool` - Create date text objects

**Utility Tools:**
- `format_text_with_annotations_tool` - Format text with custom annotations
- `create_rich_text_array_tool` - Create rich text arrays

### User Tools (`user_tool.py`)
- `retrieve_user_tool` - Get user details by ID
- `list_users_tool` - List all users
- `retrieve_me_tool` - Get current user (bot) details

### Comment Tools (`comment_tool.py`)
- `create_comment_tool` - Create comments
- `retrieve_comment_tool` - Get comment details
- `list_comments_tool` - List comments for blocks/pages

### File Tools (`file_tool.py`)
- `create_file_block_from_url_tool` - Create file blocks from URLs
- `create_file_block_from_base64_tool` - Create file blocks from base64 data
- `create_image_block_from_url_tool` - Create image blocks from URLs
- `create_image_block_from_base64_tool` - Create image blocks from base64 data
- `encode_file_to_base64_tool` - Encode files to base64
- `get_file_content_type_tool` - Get file content type

## Response Format

All tools return a consistent response format:
```python
{
    "success": True/False,
    "data": {...},  # On success
    "error": "error_message"  # On failure
}
```

## Example Usage

### Create a Page with Rich Content
```python
from server.service.tools import *

# Create a page
page_data = {
    "parent": {"database_id": "your_database_id"},
    "properties": {
        "Title": {"title": [{"text": {"content": "My New Page"}}]}
    }
}
page_result = create_page_tool(page_data)

if page_result["success"]:
    page_id = page_result["data"]["id"]
    
    # Add rich content
    blocks = [
        create_callout_block_tool("Important note!", "⚠️", "yellow"),
        create_bold_text_tool("This is bold text"),
        create_code_block_tool("print('Hello World')", "python")
    ]
    
    # Append blocks to page
    append_result = append_block_children_tool({
        "block_id": page_id,
        "children": [block["data"] for block in blocks]
    })
```

### Search and Query
```python
# Search for content
search_result = search_tool({
    "query": "important",
    "filter": {"property": "object", "value": "page"}
})

# Query a database
query_result = query_database_tool({
    "database_id": "your_database_id",
    "filter": {"property": "Status", "select": {"equals": "Done"}}
})
```

### File Upload
```python
# Encode a file for upload
file_result = encode_file_to_base64_tool("/path/to/file.pdf")
if file_result["success"]:
    file_block = create_file_block_from_base64_tool(
        file_result["data"], 
        "My Document.pdf", 
        "application/pdf"
    )
```

## Error Handling

All tools include comprehensive error handling and return structured error responses:

```python
result = create_page_tool(invalid_data)
if not result["success"]:
    print(f"Error: {result['error']}")
```

## Dependencies

- `notion-client` - Official Notion Python SDK
- `fastapi` - For FastAPI integration
- `python-dotenv` - For environment variable management (optional)

## Environment Variables

- `NOTION_API_KEY` - Your Notion API integration token

## License

This project is part of the Notion Agent FastAPI application. 