from typing import Dict, Any, List, Optional
from datetime import datetime
from notion_client import Client
from config.env_config import get_notion_api_key
from service.schemas.search_schema import PageInfo, SearchData, SearchResult
from pydantic import BaseModel, Field
import re

# Initialize Notion client
notion: Client = Client(auth=get_notion_api_key())

class NotionSearchFilter(BaseModel):
    """Pydantic model for Notion search filter"""
    property: str = Field(description="Property to filter by")
    value: str = Field(description="Value to filter")

class NotionSearchRequest(BaseModel):
    """Pydantic model for Notion search request"""
    query: str = Field(description="Search query")
    filter: NotionSearchFilter = Field(description="Search filter")

class NotionTitleProperty(BaseModel):
    """Pydantic model for Notion title property"""
    plain_text: str = Field(description="Plain text content")

class NotionPageResponse(BaseModel):
    """Pydantic model for Notion page response"""
    id: str = Field(description="Page ID")
    url: Optional[str] = Field(default=None, description="Page URL")
    created_time: Optional[str] = Field(default=None, description="Creation time")
    last_edited_time: Optional[str] = Field(default=None, description="Last edit time")
    properties: Dict[str, Any] = Field(description="Page properties")

def extract_page_title(page_data: Dict[str, Any]) -> str:
    """
    Extract page title from Notion page data
    
    Args:
        page_data: Raw page data from Notion API
        
    Returns:
        Extracted page title as string
    """
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
    """
    Create PageInfo Pydantic model from raw page data
    
    Args:
        page_data: Raw page data from Notion API
        page_title: Extracted page title
        
    Returns:
        PageInfo Pydantic model
    """
    return PageInfo(
        id=page_data["id"],
        title=page_title,
        url=page_data.get("url", ""),
        created_time=page_data.get("created_time", ""),
        last_edited_time=page_data.get("last_edited_time", "")
    )

def filter_matching_pages(pages: List[Dict[str, Any]], search_term: str) -> List[PageInfo]:
    """
    Filter pages that match the search term using regex
    
    Args:
        pages: List of raw page data from Notion API
        search_term: Search term to match against
        
    Returns:
        List of matching PageInfo models
    """
    matching_pages: List[PageInfo] = []
    
    # Clean search term - remove quotes and whitespace
    cleaned_search_term: str = search_term.strip().strip('"').strip("'").strip()
    
    # Create regex pattern with case insensitive and unicode support
    # Escape special regex characters in search term for safety
    escaped_search_term: str = re.escape(cleaned_search_term)
    pattern: re.Pattern[str] = re.compile(escaped_search_term, re.IGNORECASE | re.UNICODE)
    

    for page in pages:
        raw_page_title: str = extract_page_title(page)
        # Clean page title - remove quotes and whitespace
        cleaned_page_title: str = raw_page_title.strip().strip('"').strip("'").strip()

        # Use regex search on cleaned page title
        if pattern.search(cleaned_page_title):
            page_info: PageInfo = create_page_info_from_data(page, cleaned_page_title)
            matching_pages.append(page_info)
            print(f"✅ Matched page: {cleaned_page_title} (created: {page.get('created_time', '')})")
        else:
            print(f"❌ No match: {cleaned_page_title}")
    
    return matching_pages

def get_most_recent_page(pages: List[PageInfo]) -> Optional[PageInfo]:
    """
    Get the most recently created page from a list of pages
    
    Args:
        pages: List of PageInfo models
        
    Returns:
        Most recent PageInfo model, or None if no pages provided
    """
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

def search_tool(page_title: str) -> SearchResult:
    """
    Search for pages by title in Notion and return the most recently created page
    
    Args:
        page_title: Title of the page to search for (can be partial match)
    
    Returns:
        SearchResult BaseModel with search results (only the most recent page if multiple matches)
    """
    print(f"🔍 search_tool called with: '{page_title}'")
    
    try:
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
        
        # Filter pages that match the title using regex (cleaning happens inside)
        matching_pages: List[PageInfo] = filter_matching_pages(pages, page_title)
        
        # Get the most recent page (returns single PageInfo or None)
        most_recent_page: Optional[PageInfo] = get_most_recent_page(matching_pages)
        
        # Create final pages list
        final_pages: List[PageInfo] = [most_recent_page] if most_recent_page else []
        
        # Create SearchData BaseModel
        search_data: SearchData = SearchData(
            pages=final_pages,
            total_found=len(final_pages)
        )
        
        # Create and return SearchResult BaseModel
        result: SearchResult = SearchResult(
            success=True,
            data=search_data,
            error=""
        )
        
        print(f"✅ search_tool result: {result}")
        return result
        
    except Exception as e:
        # Create error SearchResult BaseModel
        error_result: SearchResult = SearchResult(
            success=False,
            data=SearchData(pages=[], total_found=0),
            error=str(e)
        )
        print(f"❌ search_tool error: {error_result}")
        return error_result 