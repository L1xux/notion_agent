import json
import re
from typing import Any, Dict, List

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from config.env_config import get_openai_api_key

load_dotenv()


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\n", "", cleaned)
        cleaned = re.sub(r"\n```$", "", cleaned)
    return cleaned.strip()


def extract_result_text(user_input: str) -> str:
    """
    Extract pure text content from user input or generate complete answers for questions
    
    Args:
        user_input: User's free-form request
        
    Returns:
        Plain text content or generated answer
    """
    llm = ChatOpenAI(temperature=0.3, model="gpt-4o", api_key=get_openai_api_key())
    
    system_prompt = """Extract or generate the actual text content that should appear in the final document based on user input.

FOR FORMATTING INSTRUCTIONS:
- Extract actual text content, ignoring structural and formatting instructions
- IGNORE: structural instructions (create heading, add paragraph, etc.)
- IGNORE: formatting instructions (make bold, italic, color red, etc.)
- INTELLIGENTLY EXPAND any vague or generic terms into specific, detailed content

FOR QUESTIONS OR CONTENT REQUESTS:
- Generate complete, informative answers to the user's questions
- Provide comprehensive content that directly answers what was asked
- Write in a natural, educational style

UNIVERSAL PLACEHOLDER EXPANSION STRATEGY:
When you encounter vague or generic terms, apply contextual expansion:

1. IDENTIFY CONTEXT: Determine the main topic/subject from the input
2. DETECT GENERIC TERMS: Look for patterns like:
   - Abstract concepts (important things, key points, main ideas, etc.)
   - Incomplete references (such features, these aspects, those concepts, etc.) 
   - Placeholder language (various topics, several examples, many benefits, etc.)
   - Any language: 중요한/핵심/주요 + 개념들/내용/특징들, important/key/main + concepts/ideas/features, etc.

3. CONTEXTUAL EXPANSION: Replace generic terms with specific, relevant content based on the topic:
   - For technical topics → Generate specific technical concepts, methods, features
   - For educational content → Generate specific learning points, principles, examples
   - For general topics → Generate specific facts, characteristics, applications

4. MAINTAIN AUTHENTICITY: Ensure expanded content is accurate and relevant to the context

Examples:

Input: "제목은 '안녕하세요'로 하고, console.log('Hello World') 코드를 넣어주세요. 중요한 부분은 빨간색으로 칠해주세요."
Output: "안녕하세요, console.log('Hello World')"

Input: "웹 개발 가이드라는 제목으로 만들어주세요. HTML을 굵게 강조하고, CSS는 파란색으로, JavaScript는 초록색으로 칠해주세요. 중요한 개념들은 빨간색으로 표시해주세요."
Output: "웹 개발 가이드

HTML은 웹페이지의 구조를 정의하는 마크업 언어입니다. CSS는 웹페이지의 스타일과 레이아웃을 담당합니다. JavaScript는 웹페이지에 동적인 기능을 추가하는 프로그래밍 언어입니다. DOM 조작, 반응형 디자인, 비동기 프로그래밍, 이벤트 처리는 웹 개발의 핵심 개념들입니다."

Input: "Machine Learning guide with key algorithms and important concepts highlighted."
Output: "Machine Learning

Machine Learning is a subset of artificial intelligence that enables computers to learn from data. Supervised learning, unsupervised learning, neural networks, decision trees, regression analysis, clustering algorithms are fundamental concepts in this field."

Input: "Create content about Python with various features and main advantages."
Output: "Python

Python is a high-level programming language known for its simplicity and versatility. Object-oriented programming, dynamic typing, extensive standard library, cross-platform compatibility, readable syntax, strong community support are its key features and advantages."

Return the complete text content with all generic terms expanded into specific, contextually relevant information."""

    try:
        response = llm.invoke(f"{system_prompt}\n\nUser input:\n{user_input}\n\nOutput:")
        raw_text: str = getattr(response, "content", "") if not isinstance(response, str) else response
        return raw_text.strip()
    except Exception:
        return ""


def call_preprocessing_agent(user_input: str) -> Dict[str, Any]:
    """
    PREPROCESSING_LLM: Separates user input into block structure instructions, text formatting instructions, and extracts pure text content
    
    Args:
        user_input: User's free-form request
        
    Returns:
        {"block_instructions": "...", "format_instructions": "...", "result_text": "...", "success": True/False}
    """
    llm = ChatOpenAI(temperature=0, model="gpt-4o", api_key=get_openai_api_key())

    system_prompt = """Analyze the user input and separate it into two DISTINCT types of instructions while PRESERVING ALL ORIGINAL CONTENT:

1) BLOCK_INSTRUCTIONS: ONLY document structure and block creation (NO styling)
   What to include:
   - Headings/Titles (heading_1/2/3), Paragraphs
   - Lists (bulleted/numbered), Todos
   - Quotes, Callouts
   - Code blocks (include language if specified), Equations
   - Media: Images, Videos, Embeds, URLs/Bookmarks (include the actual URL)
   - Navigation/Structure: Dividers, Table of Contents, Breadcrumbs, Tables (with basic dimensions)
   - Content placement and ordering (top → bottom)
   - Preserve EXACT text content, code samples, and URLs in the relevant sections
   What to exclude:
   - Any visual styling (colors, bold, italic, underline, strikethrough)

   SECTIONING GUIDELINES (very important):
   - Split content into logical sections by headings, blank lines, list markers (-, *, 1.), code fences ```...```, and link/media lines
   - For each section, indicate the intended block type and a short description of the content that belongs to it
   - Do NOT convert everything into one paragraph
   - If a title is requested (제목/heading/title), mark it as a Heading level 1
   - If links, images, or video URLs are present, note them explicitly for separate blocks

2) FORMAT_INSTRUCTIONS: ONLY text styling/formatting
   - Text formatting: bold, italic, underline, strikethrough, code
   - Color changes (red/blue/green/...) with EXACT target text phrases
   - Link connections: specify link text and target URL
   - Multiple and combined formats are allowed (e.g., bold + red)
   - EXCLUDE all structural elements and content placement

CRITICAL SEPARATION RULES:
- WHAT/WHERE (structure, block types, order, URLs, code sections) → BLOCK_INSTRUCTIONS
- HOW IT LOOKS (styling, colors, emphasis, links on text) → FORMAT_INSTRUCTIONS
- NEVER mix styling into block_instructions
- NEVER put structure into format_instructions

Response must be ONLY this JSON:
{
  "block_instructions": "Clear structural plan with sections and block types, without any styling",
  "format_instructions": "All formatting rules mapped to exact phrases to style"
}

Example:
Input: "제목은 '안녕하세요'로 하고, console.log('Hello World') 코드를 넣어주세요. 중요한 부분은 빨간색으로 칠해주세요."

Output:
{
  "block_instructions": "Heading 1: '안녕하세요'. Add Code block with console.log('Hello World').",
  "format_instructions": "'중요한'이라는 단어를 빨간색으로 칠하기."
}

Input: "웹 개발 가이드라는 제목으로 만들어주세요. HTML은 굵게, CSS는 파란색, JavaScript는 초록색으로. 이미지: https://images.unsplash.com/... 유튜브: https://www.youtube.com/watch?v=UB1O30fR-EE 목차와 구분선도 넣어주세요."

Output:
{
  "block_instructions": "Heading 1: '웹 개발 가이드'. Paragraph: 개요 텍스트. Bulleted list: 학습 항목들. Add Image block (https://images.unsplash.com/...). Add Video block (https://www.youtube.com/watch?v=UB1O30fR-EE). Add Table of Contents. Add Divider.",
  "format_instructions": "'HTML'은 bold. 'CSS'는 color: blue. 'JavaScript'는 color: green."
}

REMEMBER: Color/Emphasis = FORMAT, Structure/Blocks/URLs = BLOCK. Keep them strictly separated."""

    try:
        response = llm.invoke(f"{system_prompt}\n\nUser input:\n{user_input}\n\nGenerate JSON response:")
        raw_text: str = getattr(response, "content", "") if not isinstance(response, str) else response
        cleaned = _strip_code_fences(raw_text)
        parsed = json.loads(cleaned)
        
        # Validate response format
        if not isinstance(parsed, dict) or "block_instructions" not in parsed or "format_instructions" not in parsed:
            raise ValueError("Invalid response format")
        
        # Extract pure text content using the new function
        result_text = extract_result_text(user_input)
            
        return {
            "success": True,
            "block_instructions": parsed["block_instructions"],
            "format_instructions": parsed["format_instructions"],
            "result_text": result_text,
            "error": ""
        }
        
    except Exception as e:
        return {
            "success": False,
            "block_instructions": "",
            "format_instructions": "",
            "result_text": "",
            "error": str(e)
        }
