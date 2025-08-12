import json
import re
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from config.env_config import get_openai_api_key


def create_formatted_rich_text_array(format_instructions: str, result_text: str) -> Dict[str, Any]:
    """
    Create formatted rich text array by applying multiple format instructions to result text.
    
    Args:
        format_instructions (str): Multiple format instructions separated by sentences
                                 (e.g., "중요한 부분을 빨간색으로 칠해줘. 자바를 굵게 만들어줘. 프로그래밍을 밑줄 쳐줘.")
        result_text (str): The actual text content to be formatted
        
    Returns:
        Dict[str, Any]: Formatted rich text result with array of rich text objects
    """
    try:
        # If no format instructions, return plain text
        if not format_instructions.strip():
            plain_rich_text = [{
                "type": "text",
                "text": {"content": result_text},
                "annotations": {
                    "bold": False,
                    "italic": False,
                    "strikethrough": False,
                    "underline": False,
                    "code": False,
                    "color": "default"
                }
            }]
            return {
                "success": True,
                "rich_text_array": plain_rich_text,
                "message": "Plain text without formatting created.",
                "segments_count": 1
            }
        
        # Use LLM to analyze format instructions and apply to text
        llm = ChatOpenAI(temperature=0, model="gpt-4o", api_key=get_openai_api_key())
        
        system_prompt = """You are a text formatting expert. Analyze MULTIPLE format instructions and apply them to specific parts of text.

FORMAT MAPPING:
- "빨간색", "red" → color: "red"
- "파란색", "blue" → color: "blue"
- "녹색", "green" → color: "green"
- "노란색", "yellow" → color: "yellow"
- "보라색", "purple" → color: "purple"
- "분홍색", "pink" → color: "pink"
- "회색", "gray" → color: "gray"
- "굵게", "bold", "볼드" → bold: true
- "기울임", "italic", "이탤릭" → italic: true
- "밑줄", "underline" → underline: true
- "취소선", "strikethrough" → strikethrough: true
- "코드", "code" → code: true

TABLE PROCESSING:
- When format instructions mention "표", "테이블", "table", "주차별", "로드맵", "체크리스트" → Keep the text as-is for table content
- Do NOT try to format table structure instructions - these will be handled by block creation
- Table-related text should remain as plain text segments that can be processed later
- Examples: "4 rows, 3 columns", "주차별로 목표, 내용, 완료여부" → Keep as plain text

TASK:
1. Parse ALL format instructions (multiple instructions may be given)
2. Identify which parts of the text should be formatted for EACH instruction
3. Apply MULTIPLE formats to the same text segment if needed (e.g., bold AND red)
4. Split text into segments and create rich text objects
5. For table-related content, preserve the text without applying formatting

COMBINING FORMATS:
- If multiple formats apply to the same text segment, combine them
- Example: "자바를 굵게 하고 빨간색으로 칠해줘" → bold: true, color: "red"

OUTPUT: JSON array of rich text objects

EXAMPLES:

Example 1 - Single Format:
Format: "중요한 부분을 빨간색으로 칠해줘"
Text: "자바(Java)는 객체지향 프로그래밍 언어입니다."
Output:
[
  {
    "type": "text",
    "text": {"content": "자바(Java)는 "},
    "annotations": {"bold": false, "italic": false, "strikethrough": false, "underline": false, "code": false, "color": "default"}
  },
  {
    "type": "text", 
    "text": {"content": "객체지향 프로그래밍 언어"},
    "annotations": {"bold": false, "italic": false, "strikethrough": false, "underline": false, "code": false, "color": "red"}
  },
  {
    "type": "text",
    "text": {"content": "입니다."},
    "annotations": {"bold": false, "italic": false, "strikethrough": false, "underline": false, "code": false, "color": "default"}
  }
]

Example 2 - Multiple Formats:
Format: "자바를 굵게 만들어줘. 프로그래밍을 밑줄 쳐줘. 언어를 파란색으로 칠해줘."
Text: "자바는 프로그래밍 언어입니다."
Output:
[
  {
    "type": "text",
    "text": {"content": "자바"},
    "annotations": {"bold": true, "italic": false, "strikethrough": false, "underline": false, "code": false, "color": "default"}
  },
  {
    "type": "text",
    "text": {"content": "는 "},
    "annotations": {"bold": false, "italic": false, "strikethrough": false, "underline": false, "code": false, "color": "default"}
  },
  {
    "type": "text",
    "text": {"content": "프로그래밍"},
    "annotations": {"bold": false, "italic": false, "strikethrough": false, "underline": true, "code": false, "color": "default"}
  },
  {
    "type": "text",
    "text": {"content": " "},
    "annotations": {"bold": false, "italic": false, "strikethrough": false, "underline": false, "code": false, "color": "default"}
  },
  {
    "type": "text",
    "text": {"content": "언어"},
    "annotations": {"bold": false, "italic": false, "strikethrough": false, "underline": false, "code": false, "color": "blue"}
  },
  {
    "type": "text",
    "text": {"content": "입니다."},
    "annotations": {"bold": false, "italic": false, "strikethrough": false, "underline": false, "code": false, "color": "default"}
  }
]

Example 3 - Combined Formats on Same Text:
Format: "자바를 굵게 하고 빨간색으로 칠해줘."
Text: "자바는 프로그래밍 언어입니다."
Output:
[
  {
    "type": "text",
    "text": {"content": "자바"},
    "annotations": {"bold": true, "italic": false, "strikethrough": false, "underline": false, "code": false, "color": "red"}
  },
  {
    "type": "text",
    "text": {"content": "는 프로그래밍 언어입니다."},
    "annotations": {"bold": false, "italic": false, "strikethrough": false, "underline": false, "code": false, "color": "default"}
  }
]

Example 4 - Table Content (No Formatting):
Format: "중요한 부분을 빨간색으로 칠해줘"
Text: "웹 개발 마스터하기. 4 rows, 3 columns (주차별로 목표, 내용, 완료여부)"
Output:
[
  {
    "type": "text",
    "text": {"content": "웹 개발 마스터하기. "},
    "annotations": {"bold": false, "italic": false, "strikethrough": false, "underline": false, "code": false, "color": "default"}
  },
  {
    "type": "text",
    "text": {"content": "4 rows, 3 columns (주차별로 목표, 내용, 완료여부)"},
    "annotations": {"bold": false, "italic": false, "strikethrough": false, "underline": false, "code": false, "color": "default"}
  }
]

Return ONLY the JSON array."""

        prompt = f"""{system_prompt}

Format Instructions: {format_instructions}
Text Content: {result_text}

Output:"""

        response = llm.invoke(prompt)
        raw_text = getattr(response, "content", "") if not isinstance(response, str) else response
        
        # Clean and parse response
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\n", "", cleaned)
            cleaned = re.sub(r"\n```$", "", cleaned)
        
        rich_text_array = json.loads(cleaned.strip())
        
        # Validate response format
        if not isinstance(rich_text_array, list):
            raise ValueError("Invalid response format - expected array")
        
        return {
            "success": True,
            "rich_text_array": rich_text_array,
            "message": f"Formatted rich text array created with {len(rich_text_array)} segments.",
            "segments_count": len(rich_text_array),
            "format_instructions": format_instructions,
            "result_text": result_text
        }
        
    except Exception as e:
        # Return plain text as fallback
        try:
            plain_rich_text = [{
                "type": "text",
                "text": {"content": result_text},
                "annotations": {
                    "bold": False,
                    "italic": False,
                    "strikethrough": False,
                    "underline": False,
                    "code": False,
                    "color": "default"
                }
            }]
            
            return {
                "success": True,
                "rich_text_array": plain_rich_text,
                "message": f"Formatting failed, returned plain text. Error: {str(e)}",
                "segments_count": 1,
                "fallback": True,
                "format_instructions": format_instructions,
                "result_text": result_text
            }
        except:
            return {
                "success": False,
                "error": str(e),
                "message": "Critical error in rich text formatting"
            }