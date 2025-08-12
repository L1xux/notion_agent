from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from service.tools.block_tool import (
    # Core content blocks (unified: accept text or rich_text_array)
    add_heading_tool,
    add_paragraph_tool,
    add_callout_tool,
    add_quote_tool,
    add_divider_tool,
    add_toggle_tool,

    # Code and lists
    add_code_tool,
    add_todo_tool,
    add_bulleted_list_tool_obj,
    add_numbered_list_tool_obj,

    # Navigation and structure
    add_table_of_contents_tool_obj,
    add_breadcrumb_tool_obj,
    add_equation_tool_obj,
    add_table_tool_obj,

    # Media blocks
    add_image_tool,
    add_video_tool,

    # Web content
    add_embed_tool,
    add_url_tool,
    add_bookmark_tool,
)
from config.env_config import get_openai_api_key

load_dotenv()


def _create_common_prompt_template() -> str:
    """Create common prompt template to avoid duplication"""
    return """You are an expert Notion content architect.

CRITICAL RULES:
1. NEVER send raw text without JSON wrapping
2. ALWAYS include "page_id": "{page_id}" in every tool call
3. Use double quotes for all JSON strings
4. If a tool fails, DO NOT retry the same input - move to next content
5. Create content systematically from top to bottom
6. For images: Use Unsplash URLs (https://images.unsplash.com/...) or direct image URLs
7. For videos: Use YouTube URLs (https://www.youtube.com/watch?v=...)
8. SAFETY FIRST: If you encounter any errors, fall back to creating a Paragraph block

CONTENT MAPPING:
- Titles/Headlines → Add Heading Block
- Body text → Add Paragraph Block  
- Code examples → Add Code Block
- Math formulas → Add Equation Block
- Tasks → Add Todo Block
- Lists → Add Bulleted List or Add Numbered List
- Important notes → Add Callout Block
- Quotes → Add Quote Block
- Separators → Add Divider Block
- Images → Add Image Block
- Videos → Add Video Block
- Links → Add URL Block or Add Bookmark Block
- Tables → Add Table Block (extract dimensions from text)
- Navigation → Add Table of Contents, Breadcrumb

Execute content creation now using ONLY valid JSON format."""


def call_block_agent(page_id: str, block_request: str) -> Dict[str, Any]:
    """
    Block agent that handles Notion block creation operations using LangChain tools
    
    Args:
        page_id: Target Notion page ID
        block_request: Block creation request
        
    Returns:
        Dictionary containing block creation results
    """
    
    logger.info(f"✍️ Text agent called with page_id: '{page_id}', request: '{block_request[:100]}...'")
    
    # Initialize LLM
    llm = ChatOpenAI(
        temperature=0,
        model="gpt-4o-mini",
        api_key=get_openai_api_key()
    )
    
    # Use standard ReAct prompt
    react_prompt = hub.pull("hwchase17/react")
    
    # Create comprehensive block creation template with strict JSON enforcement
    text_template = f"""{{_create_common_prompt_template()}}

PAGE ID: {{page_id}}
CONTENT REQUEST: {{block_request}}

MANDATORY JSON FORMAT - ALL TOOLS REQUIRE VALID JSON INPUT:

WRONG: "파이썬 기초 학습 가이드"
CORRECT: {{"page_id": "{{page_id}}", "text": "파이썬 기초 학습 가이드", "level": 1}}

TOOL SPECIFICATIONS:

HEADING: {{"page_id": "{{page_id}}", "text": "title", "level": 1}}
PARAGRAPH: {{"page_id": "{{page_id}}", "text": "content"}}
CODE: {{"page_id": "{{page_id}}", "text": "code", "language": "python"}}
EQUATION: {{"page_id": "{{page_id}}", "expression": "2 + 2 = 4"}}
TODO: {{"page_id": "{{page_id}}", "text": "task", "checked": false}}
BULLETED LIST: {{"page_id": "{{page_id}}", "text": "item"}}
NUMBERED LIST: {{"page_id": "{{page_id}}", "text": "item"}}
CALLOUT: {{"page_id": "{{page_id}}", "text": "note", "icon": "💡"}}
QUOTE: {{"page_id": "{{page_id}}", "text": "quote"}}
DIVIDER: {{"page_id": "{{page_id}}"}}
TOGGLE: {{"page_id": "{{page_id}}", "text": "title"}}
IMAGE: {{"page_id": "{{page_id}}", "image_url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4", "caption": ""}}
VIDEO: {{"page_id": "{{page_id}}", "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "caption": ""}}
EMBED: {{"page_id": "{{page_id}}", "embed_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "caption": ""}}
URL: {{"page_id": "{{page_id}}", "url": "https://oracle.com/java", "title": "Oracle Java"}}
BOOKMARK: {{"page_id": "{{page_id}}", "bookmark_url": "https://docs.oracle.com/javase", "caption": ""}}
TABLE OF CONTENTS: {{"page_id": "{{page_id}}"}}
BREADCRUMB: {{"page_id": "{{page_id}}"}}
TABLE: {{"page_id": "{{page_id}}", "table_width": 3, "table_height": 3, "has_column_header": true, "has_row_header": false}}"""

    # Define all tools from text_tool
    tools = [
        # Core content blocks
        add_heading_tool,
        add_paragraph_tool,
        add_callout_tool,
        add_quote_tool,
        add_divider_tool,
        add_toggle_tool,
        
        # Code and lists
        add_code_tool,
        add_todo_tool,
        add_bulleted_list_tool_obj,
        add_numbered_list_tool_obj,
        
        # Navigation and structure
        add_table_of_contents_tool_obj,
        add_breadcrumb_tool_obj,
        add_equation_tool_obj,
        add_table_tool_obj,
        
        # Media blocks
        add_image_tool,
        add_video_tool,
        
        # Web content
        add_embed_tool,
        add_url_tool,
        add_bookmark_tool
    ]
    
    # Create agent with standard ReAct prompt
    agent = create_react_agent(llm=llm, tools=tools, prompt=react_prompt)
    
    # Create agent executor with strict error handling
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=50,  # Increased to 50 for more comprehensive content creation
        max_execution_time=300,  # Increased timeout for more blocks (5 minutes)
        return_intermediate_steps=True,
        handle_parsing_errors=True,
        early_stopping_method="force"  # Force stop on repeated failures
    )
    
    try:
        # Create formatted input for the agent
        formatted_input = text_template.format(
            page_id=page_id,
            block_request=block_request
        )
        
        logger.info(f"🚀 Executing agent...")
        
        # Execute agent
        result = agent_executor.invoke({"input": formatted_input})
        
        logger.info(f"🔧 Agent called {len(result.get('intermediate_steps', []))} tool(s)")
        
        # Check intermediate steps
        intermediate_steps = result.get('intermediate_steps', [])
        if len(intermediate_steps) >= 1:
            return {
                "success": True,
                "message": f"Successfully created content using {len(intermediate_steps)} tools",
                "page_id": page_id,
                "tools_called": len(intermediate_steps),
                "agent_output": result.get("output", "")
            }
        else:
            return {
                "success": False,
                "error": "No tools were called",
                "message": "Agent did not create any content"
            }
        
    except Exception as e:
        logger.error(f"❌ Text agent error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Text agent failed: {str(e)}"
        }


def call_block_agent_with_rich_text(page_id: str, block_instructions: str, rich_text_array: list) -> Dict[str, Any]:
    """
    Block agent that processes rich text objects and creates formatted Notion blocks using ReAct pattern
    
    Args:
        page_id: Target Notion page ID
        block_instructions: Instructions for what type of blocks to create
        rich_text_array: Array of formatted rich text objects from rich_text_llm
        
    Returns:
        Dictionary containing block creation results
    """
    
    logger.info(f"🎨 Rich text block agent called with page_id: '{page_id}', rich_text segments: {len(rich_text_array)}")
    logger.info(f"📋 Block instructions: {block_instructions}")
    
    # Initialize LLM
    llm = ChatOpenAI(
        temperature=0,
        model="gpt-4o",
        api_key=get_openai_api_key()
    )
    
    # Use standard ReAct prompt
    react_prompt = hub.pull("hwchase17/react")
    
    # Create rich text processing template
    rich_text_template = """You are an expert Notion block architect that processes formatted rich text objects into appropriate Notion blocks.

PAGE ID: {page_id}
BLOCK INSTRUCTIONS: {block_instructions}
RICH TEXT OBJECTS: {rich_text_array}

YOUR TASK:
1. Analyze the block_instructions to understand what type of content structure is needed
2. Parse the provided rich_text_array CONTENT into logical sections (split by blank lines / headings / lists / markers)
3. Map each section to the correct Notion block type and create the blocks in order
4. Use Rich Text tools to preserve formatting (bold, italic, colors, etc.) for text blocks. NEVER replace with plain text.

AVAILABLE RICH TEXT TOOLS:

ADD PARAGRAPH WITH RICH TEXT:
{{"page_id": "{page_id}", "rich_text_array": [rich_text_objects]}}

ADD HEADING WITH RICH TEXT:
{{"page_id": "{page_id}", "rich_text_array": [rich_text_objects], "level": 1}}

ADD CALLOUT WITH RICH TEXT:
{{"page_id": "{page_id}", "rich_text_array": [rich_text_objects], "icon": "💡"}}

ADD QUOTE WITH RICH TEXT:
{{"page_id": "{page_id}", "rich_text_array": [rich_text_objects]}}

ADD TODO WITH RICH TEXT:
{{"page_id": "{page_id}", "rich_text_array": [rich_text_objects], "checked": false}}

ADD BULLETED LIST WITH RICH TEXT:
{{"page_id": "{page_id}", "rich_text_array": [rich_text_objects]}}

ADD NUMBERED LIST WITH RICH TEXT:
{{"page_id": "{page_id}", "rich_text_array": [rich_text_objects]}}

ADD TABLE BLOCK:
{{"page_id": "{page_id}", "table_width": 3, "table_height": 4, "has_column_header": true, "has_row_header": false}}

RICH TEXT OBJECT FORMAT:
Each rich_text object has:
- "type": "text"
- "text": {{"content": "text_content"}}
- "annotations": {{"bold": true/false, "italic": true/false, "color": "red/blue/default", etc.}}

STRATEGY (GENERIC, PATTERN-BASED):
1. Sectioning: Split content by blank lines, headings, list markers ("- ", "* ", digit+"."), code fences, and standalone link/media lines.
2. Heading: Short standalone lines without ending punctuation and with title-like semantics → Heading (default level 1 unless specified in instructions).
3. Paragraph: Multi-sentence prose → Paragraph.
4. Emphasis Note: Sections explicitly marked as important/emphasized → Callout.
5. Quote: Quoted lines or well-known quotations → Quote.
6. Lists: Consecutive lines with list markers → Bulleted/Numbered List (one item per line).
7. Code: Text inside code fences (```...```) → Code block; apply language if specified.
8. Lists (CRITICAL): Never send multiple list items in ONE tool call. Create ONE tool call PER ITEM. If the content chunk represents several items (by markers, newlines, commas, or separate phrases), split and call the list tool individually per item.
9. Links/Media: SAFELY recognize URLs. If the line is primarily an image/video/embed/link → use Image/Video/Embed/URL/Bookmark blocks. IMPORTANT: Only extract URLs if they are clearly visible in the text content (e.g., "https://example.com"). If URL extraction fails or is unclear, keep as paragraph text with links preserved.
10. Structure: Recognize generic navigation/separator intents from instructions context (e.g., table of contents, breadcrumb, divider) without relying on specific keywords.
11. Equations: If an inline or block formula is detected (e.g., "Load Time = (File Size) / (Connection Speed)" or math-like expressions) and the intent suggests a formula, prefer Equation block over Paragraph.
12. Tables: If block_instructions mention "표", "테이블", "table", "주차별", "로드맵", "체크리스트" or content contains table structure info (e.g., "4 rows, 3 columns", "주차별로 목표, 내용, 완료여부") → Create Table Block with appropriate dimensions.
13. Default: If none apply, use Paragraph.

CRITICAL RULES:
1. For TEXT blocks, use ONLY the provided rich_text_array content (do not invent new text)
2. For NON-TEXT/STRUCTURAL blocks (images, videos, URLs, dividers, table of contents, breadcrumbs), you MAY extract URLs/markers from the text content and call the appropriate tools ONLY if the URLs are clearly visible and extractable
3. ALWAYS include "page_id": "{page_id}" in every tool call
4. Use appropriate block types based on block_instructions and detected patterns
5. Preserve all formatting from rich_text_array for text sections
6. Split large content into multiple blocks based on logical section boundaries; do not dump everything into one paragraph
7. For table creation: Extract table dimensions from text (e.g., "4 rows, 3 columns" → table_width: 3, table_height: 4) and set has_column_header: true, has_row_header: false as defaults
8. SAFETY FIRST: If you encounter any errors with URL extraction or media block creation, fall back to creating a Paragraph block with the rich text content instead
9. TEXT BLOCKS MUST USE RICH TEXT: Always pass "rich_text_array" (not "text") to Heading/Paragraph/Callout/Quote/Todo/List/Code tools. Do not alter annotations or concatenate into plain strings.

TABLE CREATION INSTRUCTIONS:
When creating tables, analyze the text content for:
- Dimension patterns: "4 rows, 3 columns" → table_width: 3, table_height: 4
- Korean patterns: "4행 3열" → table_width: 3, table_height: 4
- Content hints: "주차별로 목표, 내용, 완료여부" → has_column_header: true
- Default values: If no dimensions found, use table_width: 3, table_height: 4

EXAMPLE:
If rich_text_array contains formatted text about "Java programming":
{{"page_id": "{page_id}", "rich_text_array": {rich_text_array}}}

Execute block creation now using the rich text objects."""
    
    # Unified tools: each accepts text or rich_text_array
    rich_text_tools = [
        add_heading_tool,
        add_paragraph_tool,
        add_callout_tool,
        add_quote_tool,
        add_todo_tool,
        add_bulleted_list_tool_obj,
        add_numbered_list_tool_obj,
        add_code_tool,
        add_divider_tool,
        add_toggle_tool,
        add_table_of_contents_tool_obj,
        add_breadcrumb_tool_obj,
        add_equation_tool_obj,
        add_table_tool_obj,
        add_image_tool,
        add_video_tool,
        add_embed_tool,
        add_url_tool,
        add_bookmark_tool
    ]
    
    # Create agent with rich text tools
    agent = create_react_agent(llm=llm, tools=rich_text_tools, prompt=react_prompt)
    
    # Create agent executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=rich_text_tools,
        verbose=True,
        max_iterations=100,
        max_execution_time=300,
        return_intermediate_steps=True,
        handle_parsing_errors=True,
        early_stopping_method="force"
    )
    
    try:
        # Create formatted input for the agent
        formatted_input = rich_text_template.format(
            page_id=page_id,
            block_instructions=block_instructions,
            rich_text_array=rich_text_array
        )
        
        logger.info(f"🚀 Executing rich text block agent...")
        
        # Execute agent
        result = agent_executor.invoke({"input": formatted_input})
        
        logger.info(f"🔧 Agent called {len(result.get('intermediate_steps', []))} tool(s)")
        
        # Check intermediate steps
        intermediate_steps = result.get('intermediate_steps', [])
        if len(intermediate_steps) >= 1:
            return {
                "success": True,
                "message": f"Successfully created {len(intermediate_steps)} formatted blocks from rich text objects",
                "page_id": page_id,
                "blocks_created": len(intermediate_steps),
                "rich_text_segments_processed": len(rich_text_array),
                "agent_output": result.get("output", ""),
                "workflow": "rich_text_array → formatted_notion_blocks"
            }
        else:
            return {
                "success": False,
                "error": "No blocks were created",
                "message": "Agent did not create any formatted blocks from rich text objects"
            }
        
    except Exception as e:
        logger.error(f"❌ Rich text block agent error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Rich text block agent failed: {str(e)}"
        }
