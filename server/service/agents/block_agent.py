from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub
from typing import Dict, Any


from service.tools.block_tool import (
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
)
from config.env_config import get_openai_api_key

load_dotenv()

def call_block_agent(page_id: str, block_request: str) -> Dict[str, Any]:
    """
    Block agent that handles Notion block creation operations using LangChain tools
    
    Args:
        page_id: Target Notion page ID
        block_request: Block creation request
        
    Returns:
        Dictionary containing block creation results
    """
    
    print(f"✍️ Text agent called with page_id: '{page_id}', request: '{block_request[:100]}...'")
    
    # Initialize LLM
    llm = ChatOpenAI(
        temperature=0,
        model="gpt-4o-mini",
        api_key=get_openai_api_key()
    )
    
    # Use standard ReAct prompt
    react_prompt = hub.pull("hwchase17/react")
    
    # Create comprehensive block creation template with strict JSON enforcement
    text_template = """You are an expert Notion content architect. Create content for: {block_request}

PAGE ID: {page_id}

MANDATORY JSON FORMAT - ALL TOOLS REQUIRE VALID JSON INPUT:

WRONG: "파이썬 기초 학습 가이드"
CORRECT: {{"page_id": "{page_id}", "text": "파이썬 기초 학습 가이드", "level": 1}}

TOOL SPECIFICATIONS:

HEADING: {{"page_id": "{page_id}", "text": "title", "level": 1}}
PARAGRAPH: {{"page_id": "{page_id}", "text": "content"}}
CODE: {{"page_id": "{page_id}", "text": "code", "language": "python"}}
EQUATION: {{"page_id": "{page_id}", "expression": "2 + 2 = 4"}}
TODO: {{"page_id": "{page_id}", "text": "task", "checked": false}}
BULLETED LIST: {{"page_id": "{page_id}", "text": "item"}}
NUMBERED LIST: {{"page_id": "{page_id}", "text": "item"}}
CALLOUT: {{"page_id": "{page_id}", "text": "note", "icon": "💡"}}
QUOTE: {{"page_id": "{page_id}", "text": "quote"}}
DIVIDER: {{"page_id": "{page_id}"}}
TOGGLE: {{"page_id": "{page_id}", "text": "title"}}
IMAGE: {{"page_id": "{page_id}", "image_url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4", "caption": ""}}
VIDEO: {{"page_id": "{page_id}", "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "caption": ""}}
EMBED: {{"page_id": "{page_id}", "embed_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "caption": ""}}
URL: {{"page_id": "{page_id}", "url": "https://oracle.com/java", "title": "Oracle Java"}}
BOOKMARK: {{"page_id": "{page_id}", "bookmark_url": "https://docs.oracle.com/javase", "caption": ""}}
TABLE OF CONTENTS: {{"page_id": "{page_id}"}}
BREADCRUMB: {{"page_id": "{page_id}"}}
TABLE: {{"page_id": "{page_id}", "table_width": 3, "table_height": 3, "has_column_header": true, "has_row_header": false}}

CRITICAL RULES:
1. NEVER send raw text without JSON wrapping
2. ALWAYS include "page_id": "{page_id}" in every tool call
3. Use double quotes for all JSON strings
4. If a tool fails, DO NOT retry the same input - move to next content
5. Create content systematically from top to bottom
6. For images: Use Unsplash URLs (https://images.unsplash.com/...) or direct image URLs
7. For videos: Use YouTube URLs (https://www.youtube.com/watch?v=...)

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

Execute content creation now using ONLY valid JSON format."""

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
        
        print(f"🚀 Executing agent...")
        
        # Execute agent
        result = agent_executor.invoke({"input": formatted_input})
        
        print(f"🔧 Agent called {len(result.get('intermediate_steps', []))} tool(s)")
        
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
        print(f"❌ Text agent error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Text agent failed: {str(e)}"
        }
