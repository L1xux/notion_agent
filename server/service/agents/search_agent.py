from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.tools import Tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub
from langchain_core.output_parsers import PydanticOutputParser
from typing import Dict, Any, List
from langchain_core.runnables import RunnableLambda

from service.tools.search_tool import search_notion_pages_tool
from service.schemas.search_schema import SearchResult

load_dotenv()

def call_search_agent(search_request: str) -> SearchResult:
    """
    Search agent that handles Notion search operations and returns page information
    
    Args:
        search_request: Search query string
        
    Returns:
        SearchResult: Pydantic model containing search results
    """
    
    llm: ChatOpenAI = ChatOpenAI(
        temperature=0,
        model="gpt-4o-mini"
    )
    
    # Use standard ReAct prompt
    react_prompt = hub.pull("hwchase17/react")
    
    # Custom template for search request
    search_template: str = """given the search request {search_request} i want you to find pages in Notion workspace.
        Your answer must contain only the search results data in JSON format with this exact structure:
        {{
            "success": true,
            "data": {{
                "pages": [
                    {{
                        "id": "page_id",
                        "title": "page_title", 
                        "url": "page_url",
                        "created_time": "created_time",
                        "last_edited_time": "last_edited_time"
                    }}
                ],
                "total_found": number_of_pages
            }},
            "error": ""
        }}
        
        If no pages found, return:
        {{
            "success": false,
            "data": {{
                "pages": [],
                "total_found": 0
            }},
            "error": "No pages found"
        }}"""
    
    prompt_template: PromptTemplate = PromptTemplate(
        template=search_template, 
        input_variables=["search_request"]
    )

    tools_for_agent: List[Tool] = [search_notion_pages_tool]
    
    # Create agent with standard ReAct prompt
    agent = create_react_agent(llm=llm, tools=tools_for_agent, prompt=react_prompt)
    
    agent_executor: AgentExecutor = AgentExecutor(
        agent=agent, 
        tools=tools_for_agent, 
        verbose=True, 
        handle_parsing_errors=True
    )
    
    # Create parser for SearchResult
    search_result_parser: PydanticOutputParser[SearchResult] = PydanticOutputParser(pydantic_object=SearchResult)
    
    # Create chain: agent_executor | search_result_parser
    extract_output: RunnableLambda = RunnableLambda(lambda d: d["output"])
    chain = agent_executor | extract_output | search_result_parser
    
    formatted_prompt: str = prompt_template.format(search_request=search_request)
    result: SearchResult = chain.invoke({"input": formatted_prompt})

    print("result: ", result)
    print("✅ Search agent created and executed successfully")
    return result 