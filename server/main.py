from fastapi import FastAPI
from dotenv import load_dotenv
from typing import Dict, Any
import os
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from service.agents.search_agent import call_search_agent
from service.schemas.search_schema import SearchResult
from service.agents.text_agent import call_text_agent

app = FastAPI()

class SearchRequest(BaseModel):
    """Pydantic model for search request"""
    query: str = Field(description="Search query for finding pages")

class TextRequest(BaseModel):
    """Pydantic model for text writing request"""
    page_id: str = Field(description="Target Notion page ID")
    content: str = Field(description="Text content to write with formatting instructions")

def create_master_agent():
    """
    Create a master agent that coordinates between different specialized agents
    
    Returns:
        Composed agent pipeline
    """
   
    llm: ChatOpenAI = ChatOpenAI(
        temperature=0,
        model="gpt-4o-mini"
    )
    
    # Create master agent prompt
    master_template: str = """You are a master agent that coordinates between different specialized agents.

Available agents:
- search_agent: Finds pages in Notion workspace
- text_agent: Writes and formats text to Notion pages

Current situation:
- User request: {user_request}
- Found pages: {found_pages}

Your job is to decide which agent to use next, or if the task is complete.

Decision rules:
1. If the request involves finding pages, use "search_agent"
2. If pages have been found and the request involves writing text, use "text_agent"
3. If text has been successfully written to a page, respond with "finish"
4. If the task is complete, respond with "finish"

Respond with only one of:
- "search_agent" if you need to find pages
- "text_agent" if you need to write text to found pages
- "finish" if the task is complete

User request: {user_request}
Found pages: {found_pages}
"""

    prompt_template: PromptTemplate = PromptTemplate(
        input_variables=["user_request", "found_pages"],
        template=master_template
    )
    
    return prompt_template | llm

@app.get("/")
def read_root() -> Dict[str, str]:
    """Root endpoint"""
    return {"message": "Notion Agent API"}

@app.post("/test-search")
def test_search_agent(request: SearchRequest) -> Dict[str, Any]:
    """
    Test the search agent functionality
    
    Args:
        request: SearchRequest containing search query
        
    Returns:
        Dictionary with search results
    """
    load_dotenv()
    
    print(f"🎯 Testing Search Agent with query: '{request.query}'")
    
    try:
        # Call search agent
        result: SearchResult = call_search_agent(request.query)
        
        print(f"📥 Search agent result: {result}")
        
        # Process results for response
        if result.success and result.data.pages:
            pages_info = []
            for i, page in enumerate(result.data.pages, 1):
                page_info = {
                    "index": i,
                    "id": page.id,
                    "title": page.title,
                    "url": page.url,
                    "created_time": page.created_time,
                    "last_edited_time": page.last_edited_time
                }
                pages_info.append(page_info)
                
                print(f"📄 Page {i}:")
                print(f"   - ID: {page.id}")
                print(f"   - Title: {page.title}")
                print(f"   - URL: {page.url}")
                print(f"   - Created: {page.created_time}")
                print(f"   - Last Edited: {page.last_edited_time}")
            
            return {
                "status": "success",
                "message": f"Search agent found {len(result.data.pages)} page(s)",
                "query": request.query,
                "total_found": result.data.total_found,
                "pages": pages_info
            }
        else:
            error_msg = result.error if not result.success else "No pages found"
            print(f"❌ Search failed or no results: {error_msg}")
            
            return {
                "status": "no_results",
                "message": error_msg,
                "query": request.query,
                "total_found": 0,
                "pages": []
            }
            
    except Exception as e:
        print(f"❌ Search agent error: {e}")
        return {
            "status": "error",
            "message": f"Search agent test failed: {str(e)}",
            "query": request.query,
            "error": str(e)
        }

@app.get("/test-search-simple/{query}")
def test_search_simple(query: str) -> Dict[str, Any]:
    """
    Simple test endpoint for search agent (GET request with path parameter)
    
    Args:
        query: Search query string
        
    Returns:
        Dictionary with search results
    """
    search_request = SearchRequest(query=query)
    return test_search_agent(search_request)

@app.post("/test-text")
def test_text_agent(request: TextRequest) -> Dict[str, Any]:
    """
    Test the text agent functionality
    
    Args:
        request: TextRequest containing page_id and content
        
    Returns:
        Dictionary with text writing results
    """
    load_dotenv()
    
    print(f"✍️ Testing Text Agent with page_id: '{request.page_id}', content: '{request.content}'")
    
    try:
        # Call text agent
        result = call_text_agent(request.page_id, request.content)
        
        print(f"📥 Text agent result: {result}")
        
        if result.get("success", False):
            return {
                "status": "success",
                "message": result.get("message", "Successfully wrote content to page"),
                "page_id": result.get("page_id"),
                "blocks_added": result.get("blocks_added", 0),
                "details": result
            }
        else:
            error_msg = result.get("error", "Unknown error")
            print(f"❌ Text writing failed: {error_msg}")
            
            return {
                "status": "failed",
                "message": result.get("message", "Failed to write content"),
                "page_id": request.page_id,
                "error": error_msg,
                "details": result
            }
            
    except Exception as e:
        print(f"❌ Text agent error: {e}")
        return {
            "status": "error",
            "message": f"Text agent test failed: {str(e)}",
            "page_id": request.page_id,
            "error": str(e)
        }

@app.get("/test-text-simple")
def test_text_simple() -> Dict[str, Any]:
    """
    Simple test endpoint for text agent with predefined content and formatting
    Uses the page ID: 23f625eb-5879-8056-aa11-ca93a8d9227f
    
    Returns:
        Dictionary with text writing results
    """
    # Predefined test with various formatting options
    test_page_id = "23f625eb-5879-8056-aa11-ca93a8d9227f"
    test_content = """
    Write a test document with the following content:
    
    1. A heading that says "🚀 Test Document" (make it heading_2, bold, and blue color)
    2. A paragraph with "This is a **bold text** example with *italic text* and some blue colored text." 
    3. A to-do item that says "Complete the Notion agent testing" (unchecked)
    4. Another paragraph with a link: "Visit our website" linking to https://example.com
    
    Use different formatting for each element:
    - Bold text should be bold=true
    - Italic text should be italic=true  
    - Blue text should be color=blue
    - The link should have link_url
    """
    
    print(f"🎯 Testing Text Agent with predefined formatting examples")
    print(f"📄 Page ID: {test_page_id}")
    print(f"📝 Content: Various formatting examples")
    
    text_request = TextRequest(page_id=test_page_id, content=test_content)
    return test_text_agent(text_request)

@app.get("/test-text-examples/{page_id}")
def test_text_examples(page_id: str, example: str = "1") -> Dict[str, Any]:
    """
    Test endpoint with multiple text examples for different scenarios
    
    Args:
        page_id: Target Notion page ID
        example: Example number or type (1-8, default: "1")
        
    Returns:
        Dictionary with text writing results
    """
    
    # Define various text examples
    examples = {
        "1": {
            "name": "Simple Text",
            "content": "Hello **world**! This is a *simple* test with some basic formatting."
        },
        "2": {
            "name": "Markdown Style",
            "content": """# My Project Documentation

## Introduction
This project demonstrates **advanced formatting** capabilities.

### Features
- Support for *italic* and **bold** text
- Code snippets like `console.log('hello')`
- Links to [external resources](https://developers.notion.com)

## Todo List
- [ ] Write documentation
- [x] Test formatting
- [ ] Deploy application"""
        },
        "3": {
            "name": "Korean Text",
            "content": """# 한국어 테스트 문서

안녕하세요! 이것은 **한국어** 텍스트 테스트입니다.

## 주요 기능
- *기울임* 텍스트 지원
- **굵은** 텍스트 지원
- `코드` 블록 지원

## 할 일 목록
- [ ] 문서 작성하기
- [x] 테스트 완료
- [ ] 배포 준비"""
        },
        "4": {
            "name": "Code and Links",
            "content": """# Development Guide

Visit our main website at https://example.com for more information.

## Code Examples

Here's a simple JavaScript function:
`function greet(name) { return "Hello " + name; }`

And a Python example:
`print("Hello, World!")`

## Useful Links
Check out the [Notion API Documentation](https://developers.notion.com) for detailed guides."""
        },
        "5": {
            "name": "Task Management",
            "content": """# Project Tasks

## Completed Tasks
- [x] Setup development environment
- [x] Create project structure
- [x] Implement basic features

## In Progress
- [ ] Add user authentication
- [ ] Implement data validation
- [ ] Write unit tests

## Future Plans
- [ ] Performance optimization
- [ ] UI/UX improvements
- [ ] Documentation updates"""
        },
        "6": {
            "name": "Meeting Notes",
            "content": """# Team Meeting Notes - 2024/01/15

## Attendees
- **John Smith** (Project Manager)
- *Sarah Kim* (Developer)
- Emily Chen (Designer)

## Discussion Points
The main topic was about **project timeline** and *resource allocation*.

## Action Items
- [ ] Update project roadmap (John)
- [x] Review design mockups (Emily)  
- [ ] Prepare technical specifications (Sarah)

## Next Meeting
Schedule follow-up meeting for next week."""
        },
        "7": {
            "name": "Complex Formatting",
            "content": """# 🚀 Advanced Formatting Test

## 📝 Text Styles
This paragraph contains **bold text**, *italic text*, and ~~strikethrough~~ text.

## 💻 Code Examples
JavaScript: `const message = "Hello World";`
Python: `print("Hello World")`

## 🔗 Links and References
- Official documentation: https://notion.so
- API reference: [Notion API](https://developers.notion.com)

## ✅ Task Lists
### High Priority
- [x] Complete project setup
- [ ] Implement core features

### Medium Priority  
- [ ] Add error handling
- [ ] Write documentation"""
        },
                 "8": {
             "name": "Blog Post Style",
             "content": """# Building Better Web Applications

## Introduction
In today's fast-paced development environment, creating **robust** and *maintainable* web applications is more important than ever.

## Key Principles

### 1. Clean Code
Write code that is easy to read and understand. Use meaningful variable names and proper commenting.

### 2. Testing
Implement comprehensive testing strategies:
- [ ] Unit tests
- [ ] Integration tests  
- [x] End-to-end tests

### 3. Documentation
Maintain up-to-date documentation. Link to resources like [MDN Web Docs](https://developer.mozilla.org) for reference.

## Conclusion
Remember: `code is written once but read many times` - make it count!"""
         },
         "11": {
             "name": "Korean Color Mix",
             "content": "안녕하세요 (빨간), 제 이름은 (초록, 볼드), 이의진(파란, italic)입니다."
         }
    }
    
    # Get the selected example
    selected_example = examples.get(example, examples["1"])
    
    print(f"🎯 Text Examples test - Page: {page_id}")
    print(f"📝 Using example {example}: {selected_example['name']}")
    print(f"📄 Content preview: {selected_example['content'][:100]}...")
    
    text_request = TextRequest(page_id=page_id, content=selected_example['content'])
    result = test_text_agent(text_request)
    
    # Add example info to result
    if isinstance(result, dict):
        result["example_used"] = {
            "number": example,
            "name": selected_example['name'],
            "content_preview": selected_example['content'][:100] + "..."
        }
    
    return result

@app.get("/test-text-examples-list")
def test_text_examples_list() -> Dict[str, Any]:
    """
    List all available text examples
    
    Returns:
        Dictionary with available examples
    """
    examples_info = {
        "1": {"name": "Simple Text", "description": "Basic formatting with bold and italic"},
        "2": {"name": "Markdown Style", "description": "Complete document with headings, lists, and links"},
        "3": {"name": "Korean Text", "description": "Korean language content with formatting"},
        "4": {"name": "Code and Links", "description": "Code snippets and external links"},
        "5": {"name": "Task Management", "description": "Task lists with checked/unchecked items"},
        "6": {"name": "Meeting Notes", "description": "Meeting notes format with attendees and action items"},
        "7": {"name": "Complex Formatting", "description": "Advanced formatting with emojis and mixed styles"},
        "8": {"name": "Blog Post Style", "description": "Blog post format with sections and principles"},
        "11": {"name": "Korean Color Mix", "description": "Korean text with mixed colors and formatting"}
    }
    
    return {
        "message": "Available text examples for testing",
        "examples": examples_info,
        "usage": "GET /test-text-examples/{page_id}?example={number}",
        "default_page_id": "23f625eb-5879-8056-aa11-ca93a8d9227f"
    }

@app.get("/test-notion-direct/{page_id}")
def test_notion_direct(page_id: str) -> Dict[str, Any]:
    """
    Direct test of Notion API without LangChain agent
    Tests text_tool functions directly
    
    Args:
        page_id: Target Notion page ID
        
    Returns:
        Dictionary with direct API test results
    """
    from service.tools.text_tool import (
        create_rich_text_item, 
        create_paragraph_block, 
        create_heading_block,
        append_blocks_to_page
    )
    
    print(f"🧪 Direct Notion API test - Page: {page_id}")
    
    try:
        # Step 1: Create simple rich text items
        heading_rich_text = create_rich_text_item(
            content="🧪 Direct API Test", 
            bold=True, 
            color="red"
        )
        
        paragraph_rich_text = create_rich_text_item(
            content="This is a direct API test to verify Notion connection works.", 
            italic=True
        )
        
        print(f"✅ Created rich text items")
        
        # Step 2: Create blocks
        heading_block = create_heading_block([heading_rich_text], level=2)
        paragraph_block = create_paragraph_block([paragraph_rich_text])
        
        blocks = [heading_block, paragraph_block]
        print(f"✅ Created {len(blocks)} blocks")
        print(f"📋 Blocks: {blocks}")
        
        # Step 3: Append to Notion page
        result = append_blocks_to_page(page_id, blocks)
        
        print(f"📥 Append result: {result}")
        
        if result.success:
            return {
                "status": "success",
                "message": "Direct Notion API test successful",
                "page_id": page_id,
                "blocks_added": result.blocks_count,
                "details": {
                    "heading_content": "🧪 Direct API Test",
                    "paragraph_content": "This is a direct API test to verify Notion connection works.",
                    "append_result": result.model_dump()
                }
            }
        else:
            return {
                "status": "failed",
                "message": "Direct Notion API test failed",
                "page_id": page_id,
                "error": result.error,
                "details": result.model_dump()
            }
            
    except Exception as e:
        print(f"❌ Direct API test error: {e}")
        return {
            "status": "error",
            "message": f"Direct API test failed: {str(e)}",
            "page_id": page_id,
            "error": str(e)
        }