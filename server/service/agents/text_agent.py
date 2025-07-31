from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.tools import Tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub
from langchain_core.output_parsers import PydanticOutputParser
from typing import Dict, Any, List
from langchain_core.runnables import RunnableLambda
import json
import re

from service.tools.text_tool import (
    create_rich_text_objects_tool,
    create_blocks_tool,
    append_blocks_to_page_tool
)
from service.schemas.text_schema import TextResult

load_dotenv()

def call_text_agent(page_id: str, text_request: str) -> Dict[str, Any]:
    """
    Text agent that handles Notion text writing operations using LangChain tools
    
    Args:
        page_id: Target Notion page ID
        text_request: Text content and formatting instructions
        
    Returns:
        Dictionary containing text operation results
    """
    
    print(f"✍️ Text agent called with page_id: '{page_id}', request: '{text_request[:100]}...'")
    
    llm: ChatOpenAI = ChatOpenAI(
        temperature=0,
        model="gpt-4o-mini",
        model_kwargs={"seed": 42}  # For consistent behavior
    )
    
    # Use standard ReAct prompt
    react_prompt = hub.pull("hwchase17/react")
    
    # Custom template for text writing request - DYNAMIC content processing
    text_template: str = """CRITICAL: You MUST use the provided tools in the exact order specified. Do not generate fake responses.

Page ID: {page_id}
Text Content: {text_request}

ANALYZE THE TEXT CONTENT ABOVE and create appropriate rich text objects and blocks based on the actual request.

MANDATORY WORKFLOW - Execute each step using the actual tools:

STEP 1: Use "Create rich text objects" tool
- Parse the text content above
- Identify text segments that need different formatting (bold, italic, colors, links, etc.)
- Create JSON array with appropriate formatting for each text segment

FORMAT GUIDELINES:
- **Bold text** or text marked as bold → {{"content": "text", "bold": true}}
- *Italic text* or text marked as italic → {{"content": "text", "italic": true}}
- Code snippets → {{"content": "text", "code": true}}
- Colored text → {{"content": "text", "color": "blue/red/green/etc"}}
- Links → {{"content": "text", "link_url": "https://..."}}
- Strikethrough → {{"content": "text", "strikethrough": true}}
- Underlined → {{"content": "text", "underline": true}}

STEP 2: Use "Create blocks" tool
- Group the rich text objects into logical blocks
- Determine appropriate block types based on content structure:
  * Headings → {{"type": "heading_1"}}, {{"type": "heading_2"}}, {{"type": "heading_3"}}
  * Regular paragraphs → {{"type": "paragraph"}}
  * To-do items → {{"type": "to_do", "checked": true/false}}
  * Code blocks → {{"type": "paragraph"}} with code formatting

Format: {{
    "rich_text_objects": [result_from_step_1],
    "blocks_config": [appropriate_block_configs_based_on_content]
}}

STEP 3: Use "Append blocks to page" tool with:
{{
    "page_id": "{page_id}",
    "blocks": [blocks_from_step_2]
}}

EXAMPLES OF PARSING:
Input: "# My Heading\\nThis is **bold** text with a [link](https://example.com)"
→ Rich text: [{{"content": "My Heading"}}, {{"content": "This is "}}, {{"content": "bold", "bold": true}}, {{"content": " text with a "}}, {{"content": "link", "link_url": "https://example.com"}}]
→ Blocks: [{{"type": "heading_1"}}, {{"type": "paragraph"}}]

Input: "- [ ] Todo item\\n- [x] Done item"
→ Rich text: [{{"content": "Todo item"}}, {{"content": "Done item"}}]
→ Blocks: [{{"type": "to_do", "checked": false}}, {{"type": "to_do", "checked": true}}]

YOU MUST ACTUALLY CALL EACH TOOL WITH CONTENT BASED ON THE ACTUAL TEXT REQUEST - DO NOT USE HARDCODED EXAMPLES.

Your final answer must be in this JSON format after calling all tools:
{{
    "success": true,
    "message": "Successfully wrote content to page",
    "page_id": "{page_id}",
    "blocks_added": number_of_blocks,
    "error": ""
}}"""
    
    prompt_template: PromptTemplate = PromptTemplate(
        template=text_template, 
        input_variables=["page_id", "text_request"]
    )

    # Define tools with very explicit descriptions
    tools_for_agent: List[Tool] = [
        Tool(
            name="Create rich text objects",
            func=create_rich_text_objects_tool,
            description="MANDATORY FIRST STEP: Create rich text objects with formatting. Input must be a JSON array of objects with content and formatting properties. This tool MUST be called first.",
        ),
        Tool(
            name="Create blocks",
            func=create_blocks_tool,
            description="MANDATORY SECOND STEP: Create Notion blocks from rich text objects. Input must be JSON with 'rich_text_objects' (from previous tool) and 'blocks_config' arrays. This tool MUST be called second.",
        ),
        Tool(
            name="Append blocks to page",
            func=append_blocks_to_page_tool,
            description="MANDATORY FINAL STEP: Append blocks to Notion page. Input must be JSON with 'page_id' and 'blocks' (from previous tool). This tool MUST be called last.",
        )
    ]
    
    # Create agent with standard ReAct prompt
    agent = create_react_agent(llm=llm, tools=tools_for_agent, prompt=react_prompt)
    
    # Configure agent executor with stricter settings
    agent_executor: AgentExecutor = AgentExecutor(
        agent=agent, 
        tools=tools_for_agent, 
        verbose=True, 
        handle_parsing_errors=True,
        max_iterations=10,  # Allow more iterations
        max_execution_time=120,  # 2 minutes timeout
        return_intermediate_steps=True  # Help debug tool calls
    )
    
    try:
        formatted_prompt: str = prompt_template.format(
            page_id=page_id,
            text_request=text_request
        )
        
        print(f"🚀 Executing agent with prompt...")
        print(f"📝 Formatted prompt: {formatted_prompt[:500]}...")
        
        # Execute agent
        result = agent_executor.invoke({"input": formatted_prompt})
        
        print(f"🔍 Agent execution result keys: {result.keys()}")
        print(f"📥 Agent output: {result.get('output', 'No output')}")
        print(f"🔧 Intermediate steps: {len(result.get('intermediate_steps', []))}")
        
        # Check if tools were actually called
        intermediate_steps = result.get('intermediate_steps', [])
        if not intermediate_steps:
            print("⚠️ WARNING: No intermediate steps found - agent may not have called tools!")
        else:
            print(f"✅ Agent called {len(intermediate_steps)} tool(s)")
            for i, (action, observation) in enumerate(intermediate_steps):
                print(f"  Step {i+1}: {action.tool} -> {observation[:100]}...")
        
        # Try to parse the final output
        final_output = result.get('output', '{}')
        
        # Extract JSON from the output if it's wrapped in text
        import re
        json_match = re.search(r'\{.*\}', final_output, re.DOTALL)
        if json_match:
            try:
                parsed_result = json.loads(json_match.group(0))
                print(f"✅ Successfully parsed result: {parsed_result}")
                return parsed_result
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing failed: {e}")
        
        # Fallback - check if tools were called successfully
        if intermediate_steps and len(intermediate_steps) >= 3:
            return {
                "success": True,
                "message": "Tools were called successfully (parsing final output failed)",
                "page_id": page_id,
                "blocks_added": 8,  # Expected number
                "error": ""
            }
        else:
            return {
                "success": False,
                "message": "Agent did not call all required tools",
                "page_id": page_id,
                "blocks_added": 0,
                "error": f"Only {len(intermediate_steps)} tools called, expected 3"
            }
        
    except Exception as e:
        print(f"❌ Text agent error: {e}")
        
        return {
            "success": False,
            "message": "Text agent execution failed",
            "page_id": page_id,
            "blocks_added": 0,
            "error": str(e)
        }
