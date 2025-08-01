from typing import Dict, Any, List, Optional
from datetime import datetime
from notion_client import Client
from config.env_config import get_notion_api_key
from service.schemas.search_schema import PageInfo, SearchData, SearchResult
from service.schemas.tool_schema import NotionSearchFilter, NotionSearchRequest
from langchain_core.tools import Tool
import re

# Initialize Notion client
notion: Client = Client(auth=get_notion_api_key())

# ===================== UTILITY FUNCTIONS =====================

def extract_page_title(page_data: Dict[str, Any]) -> str:
    """Extract page title from Notion page data"""
    page_title_text: str = ""
    
    if "properties" in page_data and "title" in page_data["properties"]:
        title_property: Dict[str, Any] = page_data["properties"]["title"]
        if "title" in title_property:
            title_parts: List[Dict[str, Any]] = title_property["title"]
            for title_part in title_parts:
                if "plain_text" in title_part:
                    page_title_text += title_part["plain_text"]
    
    return page_title_text

def create_page_info_from_data(page_data: Dict[str, Any], page_title: str) -> PageInfo:
    """Create PageInfo Pydantic model from raw page data"""
    return PageInfo(
        id=page_data["id"],
        title=page_title,
        url=page_data.get("url", ""),
        created_time=page_data.get("created_time", ""),
        last_edited_time=page_data.get("last_edited_time", "")
    )

def filter_matching_pages(pages: List[Dict[str, Any]], search_term: str) -> List[PageInfo]:
    """Filter pages that match the search term using regex"""
    matching_pages: List[PageInfo] = []
    
    # Clean search term - remove quotes and whitespace
    cleaned_search_term: str = search_term.strip().strip('"').strip("'").strip()
    
    # Create regex pattern with case insensitive and unicode support
    escaped_search_term: str = re.escape(cleaned_search_term)
    pattern: re.Pattern[str] = re.compile(escaped_search_term, re.IGNORECASE | re.UNICODE)

    for page in pages:
        raw_page_title: str = extract_page_title(page)
        cleaned_page_title: str = raw_page_title.strip().strip('"').strip("'").strip()

        if pattern.search(cleaned_page_title):
            page_info: PageInfo = create_page_info_from_data(page, cleaned_page_title)
            matching_pages.append(page_info)
            print(f"✅ Matched page: {cleaned_page_title} (created: {page.get('created_time', '')})")
        else:
            print(f"❌ No match: {cleaned_page_title}")
    
    return matching_pages

def get_most_recent_page(pages: List[PageInfo]) -> Optional[PageInfo]:
    """Get the most recently created page from a list of pages"""
    if not pages:
        return None
    
    # Sort by created_time in descending order (most recent first)
    sorted_pages: List[PageInfo] = sorted(
        pages, 
        key=lambda page: datetime.fromisoformat(page.created_time.replace('Z', '+00:00')), 
        reverse=True
    )
    
    # Return only the most recent page
    most_recent_page: PageInfo = sorted_pages[0]
    print(f"🎯 Selected most recent page: {most_recent_page.title} (created: {most_recent_page.created_time})")
    
    return most_recent_page

# ===================== SEARCH TOOL DECORATOR =====================

def search_operation(success_message: str = "Search completed successfully", error_prefix: str = "Search failed"):
    """
    Decorator for search operations with automatic error handling and result formatting
    
    Args:
        success_message: Success message for logging
        error_prefix: Error message prefix for failures
    """
    def decorator(func):
        def wrapper(page_title: str) -> SearchResult:
            print(f"🔍 {func.__name__} called with: '{page_title}'")
            
            try:
                result = func(page_title)
                print(f"✅ {success_message}: {result}")
                return result
                
            except Exception as e:
                error_result: SearchResult = SearchResult(
                    success=False,
                    data=SearchData(pages=[], total_found=0),
                    error=f"{error_prefix}: {str(e)}"
                )
                print(f"❌ {func.__name__} error: {error_result}")
                return error_result
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    
    return decorator

# ===================== SEARCH TOOL FUNCTIONS =====================

@search_operation("Search completed successfully", "Search failed")
def search_tool(page_title: str) -> SearchResult:
    """Search for pages by title in Notion and return the most recently created page"""
    # Create search request
    search_filter: NotionSearchFilter = NotionSearchFilter(
        property="object",
        value="page"
    )
    
    search_request: NotionSearchRequest = NotionSearchRequest(
        query=page_title,
        filter=search_filter
    )
    
    # Search for pages with the given title
    response: Dict[str, Any] = notion.search(
        query=search_request.query,
        filter=search_request.filter.model_dump()
    )
    
    print(f"📊 Notion API response: {response}")
    
    pages: List[Dict[str, Any]] = response.get("results", [])
    
    # Filter pages that match the title using regex
    matching_pages: List[PageInfo] = filter_matching_pages(pages, page_title)
    
    # Get the most recent page
    most_recent_page: Optional[PageInfo] = get_most_recent_page(matching_pages)
    
    # Create final pages list
    final_pages: List[PageInfo] = [most_recent_page] if most_recent_page else []
    
    # Create and return SearchResult
    return SearchResult(
        success=True,
        data=SearchData(pages=final_pages, total_found=len(final_pages)),
        error=""
    )

# ===================== LANGCHAIN TOOL DEFINITIONS =====================

search_notion_pages_tool = Tool(
    name="Search Notion pages",
    func=search_tool,
    description="Search for pages in Notion workspace by title. Use when you need to find pages. Input should be a page title (e.g., 'Test').",
) 