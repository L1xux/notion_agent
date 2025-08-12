
from fastapi import FastAPI
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables from .env file at the very beginning
load_dotenv(dotenv_path="config/.env")

from service.llm.rich_text_llm import create_formatted_rich_text_array
from service.preprocessing import call_preprocessing_agent
from service.agents.block_agent import call_block_agent_with_rich_text

app = FastAPI()

# Hardcoded page ID for testing
TEST_PAGE_ID = "23f625eb-5879-8056-aa11-ca93a8d9227f"

# ---------------- Orchestration (pure function, no endpoint) ---------------- #
# (Removed run_master_workflow as requested)
@app.get("/test_block_creation")
async def test_block_creation() -> Dict[str, Any]:
    """
    End-to-end pipeline test with a comprehensive request that includes
    both structural and formatting instructions.
    Workflow: preprocessing → rich_text_llm → block_agent → Notion
    """
    
    # Comprehensive request covering block types and explicit formatting asks
    test_request = """안녕하세요! 웹 개발 초보자들을 위한 완전한 학습 가이드를 만들어주세요.

제목은 "웹 개발 마스터하기"로 H1(가장 큰 제목)으로 작성해주시고, 그 밑에 소제목으로 "HTML/CSS 기초부터 React까지"라고 넣어주세요.

포맷 지시사항: HTML은 굵게, CSS는 파란색, JavaScript는 초록색으로, "반응형 디자인"은 밑줄과 초록색으로, 중요한 개념들은 빨간색으로 표시해주세요. 오래된 기술은 취소선을 적용해주세요. 코드 관련된 부분은 코드 형태로 표시해주세요.

기본 설명은 간단하게 몇 문단 정도 써주시고, 중요한 부분은 💡 아이콘과 함께 콜아웃으로 강조해주세요. 특히 "반응형 디자인은 필수입니다!"라는 문장은 빨간색으로 칠해주세요.

스티브 잡스가 말했던 "Design is not just what it looks like and feels like. Design is how it works."라는 명언도 인용구로 넣어주시고요.

### 기초 단계

학습 순서는 이렇게 해주세요:
- HTML 구조 이해하기
- CSS 스타일링 배우기  
- JavaScript 기초 문법
- 프레임워크 선택하기
- 실전 프로젝트 만들기

그리고 번호 리스트로는:
1. 환경 설정 (VS Code 설치)
2. Git/GitHub 사용법 익히기
3. 배포 방법 학습하기

### 실습 체크리스트

할 일 목록도 만들어주세요:
□ HTML 기본 태그 연습
□ CSS 플렉스박스 마스터
☑ JavaScript 변수/함수 이해 (이건 체크된 상태로)
□ React 컴포넌트 만들기

---

코드 예제는 이런 식으로:

```html
<!DOCTYPE html>
<html>
  <head><title>Hello World</title></head>
  <body><h1>안녕하세요!</h1></body>
</html>
```

수식도 하나 넣어볼까요? 웹 성능 계산할 때 쓰는 공식: `Load Time = (File Size) / (Connection Speed)`

더 자세한 내용을 보려면 여기를 클릭하세요 [펼치기/접기]

### 학습 로드맵

진도 관리표도 필요할 것 같은데, 4주 계획으로 만들어주세요. 주차별로 목표, 내용, 완료여부 이런 식으로 컬럼 3개 정도면 될 것 같아요.

### 참고 자료들

유용한 이미지 하나 넣어주세요: https://images.unsplash.com/photo-1461749280684-dccba630e2f6
동영상 강의도 추천해주세요: https://www.youtube.com/watch?v=UB1O30fR-EE

Mozilla 개발자 문서 링크도 걸어주시고: https://developer.mozilla.org/ko/
W3Schools 북마크: https://www.w3schools.com/
CodePen 사이트도 임베드해주세요: https://codepen.io/

마지막으로 목차랑 브레드크럼 네비게이션도 넣어주시면 완벽할 것 같아요! 

아 맞다, 중간중간에 구분선도 넣어주시면 내용이 더 정리된 느낌일 거예요."""

    print("🧪 Running full pipeline with comprehensive request...")
    print(f"📝 Request length: {len(test_request)} characters")

    # Step 1: Preprocessing
    pre = call_preprocessing_agent(user_input=test_request)
    if not pre.get("success"):
        return {
            "success": False,
            "error": f"Preprocessing failed: {pre.get('error')}",
            "step_failed": "preprocessing"
        }

    block_instructions = pre.get("block_instructions", "")
    format_instructions = pre.get("format_instructions", "")
    result_text = pre.get("result_text", "")

    print("📋 Preprocessing done.")
    print(f"   Block: {block_instructions[:120]}...")
    print(f"   Format: {format_instructions[:120]}...")
    print(f"   Result text: {result_text[:120]}...")

    # Step 2: Rich Text Formatting
    rt = create_formatted_rich_text_array(format_instructions, result_text)
    if not rt.get("success"):
        return {
            "success": False,
            "error": f"Rich text formatting failed: {rt.get('error')}",
            "step_failed": "rich_text_formatting",
            "preprocessing": pre
        }

    rich_text_array = rt.get("rich_text_array", [])
    segments_count = rt.get("segments_count", 0)

    print(f"🎨 Rich text created: {segments_count} segments")

    # Step 3: Create Notion Blocks via Block Agent
    br = call_block_agent_with_rich_text(
        page_id=TEST_PAGE_ID,
        block_instructions=block_instructions,
        rich_text_array=rich_text_array
    )

    if not br.get("success"):
        return {
            "success": False,
            "error": f"Block creation failed: {br.get('error')}",
            "step_failed": "block_creation",
            "preprocessing": pre,
            "rich_text": rt
        }

    blocks_created = br.get("blocks_created", 0)

    return {
        "success": True,
        "message": "Complete pipeline executed successfully",
        "pipeline": {
            "page_id": TEST_PAGE_ID,
            "blocks_created": blocks_created,
            "rich_text_segments": segments_count
        },
        "step1_preprocessing": pre,
        "step2_rich_text_formatting": rt,
        "step3_notion_blocks": br
    }


@app.get("/test_simple_instruction")
async def test_simple_instruction() -> Dict[str, Any]:
    """
    Test preprocessing agent with a simple example to demonstrate block/format separation.
    """
    
    # Simple test case
    simple_request = """제목은 안녕하세요, 인사하는 방법들을 길게 작성하고 중간마다 중요한 부분들을 빨간색으로 색칠해주세요. 중간마다 구분선을 작성해주세요."""
    
    print("🧪 Testing simple instruction separation...")
    print(f"📝 Request: {simple_request}")
    
    # Call preprocessing agent
    result = call_preprocessing_agent(user_input=simple_request)
    
    # Simple response format
    response: Dict[str, Any] = {
        "success": result.get("success", False),
        "user_input": simple_request,
        "block_instructions": result.get("block_instructions", ""),
        "format_instructions": result.get("format_instructions", ""),
        "error": result.get("error", "")
    }
    
    print(f"📋 Block: {response['block_instructions']}")
    print(f"🎨 Format: {response['format_instructions']}")
    
    return response


## Removed deprecated endpoint /test_rich_text_processing


@app.get("/test_rich_text_formatting")
async def test_rich_text_formatting() -> Dict[str, Any]:
    """
    Test complete workflow: preprocessing → rich text formatting
    Shows how format_instructions and result_text are processed into formatted rich text objects
    """
    
    # Test cases with different formatting scenarios
    test_cases = [
        {
            "name": "Single Format",
            "input": "자바에 대해서 알려주고, 중요한 부분을 빨간색으로 칠해줘"
        },
        {
            "name": "Multiple Formats", 
            "input": "파이썬에 대해 설명해줘. 파이썬을 굵게 만들어줘. 프로그래밍을 밑줄 쳐줘. 언어를 파란색으로 칠해줘."
        },
        {
            "name": "Combined Formats",
            "input": "자바스크립트에 대해 알려줘. 자바스크립트를 굵게 하고 초록색으로 칠해줘."
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n🧪 Testing: {test_case['name']}")
        print(f"Input: {test_case['input']}")
        
        # Step 1: Preprocessing - Extract block_instructions, format_instructions, result_text
        print("📋 Step 1: Preprocessing...")
        preprocessing_result = call_preprocessing_agent(test_case['input'])
        
        if not preprocessing_result.get("success"):
            results.append({
                "test_case": test_case['name'],
                "success": False,
                "error": f"Preprocessing failed: {preprocessing_result.get('error')}",
                "input": test_case['input']
            })
            continue
        
        block_instructions = preprocessing_result.get("block_instructions", "")
        format_instructions = preprocessing_result.get("format_instructions", "")
        result_text = preprocessing_result.get("result_text", "")
        
        print(f"   Block instructions: {block_instructions}")
        print(f"   Format instructions: {format_instructions}")
        print(f"   Result text: {result_text[:100]}...")
        
        # Step 2: Rich Text Formatting - Apply format_instructions to result_text
        print("🎨 Step 2: Rich Text Formatting...")
        rich_text_result = create_formatted_rich_text_array(format_instructions, result_text)
        
        if not rich_text_result.get("success"):
            results.append({
                "test_case": test_case['name'],
                "success": False,
                "error": f"Rich text formatting failed: {rich_text_result.get('error')}",
                "input": test_case['input'],
                "preprocessing_result": preprocessing_result
            })
            continue
        
        rich_text_array = rich_text_result.get("rich_text_array", [])
        segments_count = rich_text_result.get("segments_count", 0)
        
        print(f"   Created {segments_count} text segments")
        print(f"   First segment: {rich_text_array[0] if rich_text_array else 'None'}")
        
        # Step 3: Compile complete result
        results.append({
            "test_case": test_case['name'],
            "success": True,
            "input": test_case['input'],
            "preprocessing": {
                "block_instructions": block_instructions,
                "format_instructions": format_instructions,
                "result_text": result_text
            },
            "rich_text_formatting": {
                "segments_count": segments_count,
                "rich_text_array": rich_text_array,
                "message": rich_text_result.get("message", "")
            },
            "workflow_summary": f"Processed '{test_case['input'][:50]}...' → {segments_count} formatted segments"
        })
        
        print(f"✅ {test_case['name']} completed successfully!")
    
    # Generate overall summary
    successful_tests = [r for r in results if r.get("success")]
    failed_tests = [r for r in results if not r.get("success")]
    
    return {
        "success": True,
        "message": f"Rich text formatting workflow test completed. {len(successful_tests)}/{len(test_cases)} tests passed.",
        "workflow_description": "preprocessing (extract format_instructions + result_text) → rich_text_llm (create formatted rich text objects)",
        "test_results": results,
        "summary": {
            "total_tests": len(test_cases),
            "successful": len(successful_tests),
            "failed": len(failed_tests),
            "test_cases_covered": [
                "Single format instruction",
                "Multiple format instructions", 
                "Combined formats on same text"
            ]
        },
        "sample_output": {
            "description": "Example of rich text object with formatting",
            "example": {
                "type": "text",
                "text": {"content": "자바"},
                "annotations": {
                    "bold": True,
                    "italic": False,
                    "strikethrough": False,
                    "underline": False,
                    "code": False,
                    "color": "red"
                }
            }
        }
    }


@app.get("/test_single_example")
async def test_single_example() -> Dict[str, Any]:
    """
    Comprehensive example demonstrating the full preprocessing → rich text formatting workflow
    Shows multiple format types: bold, italic, colors, underline, strikethrough, code formatting
    """
    
    # Comprehensive example with multiple formatting requirements
    user_input = """웹 개발에 대해서 자세히 설명해주세요. HTML을 굵게 만들어주고, CSS는 파란색으로 칠해주세요. 
    JavaScript는 기울임체로 만들고, 중요한 포인트들은 빨간색으로 강조해주세요. 
    그리고 deprecated된 기술들은 취소선을 그어주시고, 코드 예제 부분은 코드 형태로 표시해주세요. 
    특히 '반응형 디자인'이라는 단어는 밑줄을 그어주시고 초록색으로 칠해주세요."""
    
    print(f"🔍 Comprehensive Example Test")
    print(f"📝 Input: {user_input}")
    print(f"🎯 Expected formats: HTML(bold), CSS(blue), JavaScript(italic), important points(red), deprecated(strikethrough), code examples(code), 반응형 디자인(underline+green)")
    
    # Step 1: Preprocessing
    print("\n📋 Step 1: Preprocessing...")
    preprocessing_result = call_preprocessing_agent(user_input)
    
    if not preprocessing_result.get("success"):
        return {
            "success": False,
            "error": f"Preprocessing failed: {preprocessing_result.get('error')}",
            "input": user_input
        }
    
    block_instructions = preprocessing_result.get("block_instructions", "")
    format_instructions = preprocessing_result.get("format_instructions", "")
    result_text = preprocessing_result.get("result_text", "")
    
    print(f"   📄 Block instructions: {block_instructions}")
    print(f"   🎨 Format instructions: {format_instructions}")
    print(f"   📝 Result text: {result_text}")
    
    # Step 2: Rich Text Formatting
    print("\n🎨 Step 2: Rich Text Formatting...")
    rich_text_result = create_formatted_rich_text_array(format_instructions, result_text)
    
    if not rich_text_result.get("success"):
        return {
            "success": False,
            "error": f"Rich text formatting failed: {rich_text_result.get('error')}",
            "input": user_input,
            "preprocessing_result": preprocessing_result
        }
    
    rich_text_array = rich_text_result.get("rich_text_array", [])
    segments_count = rich_text_result.get("segments_count", 0)
    
    print(f"   📊 Created {segments_count} formatted segments")
    
    # Detailed segment analysis
    formatting_stats = {"bold": 0, "italic": 0, "underline": 0, "strikethrough": 0, "code": 0, "colored": 0, "plain": 0}
    
    for i, segment in enumerate(rich_text_array):
        content = segment.get("text", {}).get("content", "").strip()
        annotations = segment.get("annotations", {})
        formatting = []
        
        # Collect formatting types
        if annotations.get("bold"): 
            formatting.append("bold")
            formatting_stats["bold"] += 1
        if annotations.get("italic"): 
            formatting.append("italic")
            formatting_stats["italic"] += 1
        if annotations.get("underline"): 
            formatting.append("underline")
            formatting_stats["underline"] += 1
        if annotations.get("strikethrough"): 
            formatting.append("strikethrough")
            formatting_stats["strikethrough"] += 1
        if annotations.get("code"): 
            formatting.append("code")
            formatting_stats["code"] += 1
        if annotations.get("color") and annotations.get("color") != "default": 
            formatting.append(f"color:{annotations.get('color')}")
            formatting_stats["colored"] += 1
        
        if not formatting:
            formatting_stats["plain"] += 1
            
        format_desc = f" → [{', '.join(formatting)}]" if formatting else " → [plain]"
        print(f"      📝 Segment {i+1}: '{content}'{format_desc}")
    
    # Summary of applied formatting
    print(f"\n📈 Formatting Summary:")
    print(f"   🔢 Total segments: {segments_count}")
    print(f"   💪 Bold segments: {formatting_stats['bold']}")
    print(f"   ↗️ Italic segments: {formatting_stats['italic']}")
    print(f"   📏 Underlined segments: {formatting_stats['underline']}")
    print(f"   ❌ Strikethrough segments: {formatting_stats['strikethrough']}")
    print(f"   💻 Code segments: {formatting_stats['code']}")
    print(f"   🎨 Colored segments: {formatting_stats['colored']}")
    print(f"   📄 Plain segments: {formatting_stats['plain']}")
    
    # Check if expected formats were applied
    found_html_bold = any("HTML" in seg.get("text", {}).get("content", "") and seg.get("annotations", {}).get("bold") for seg in rich_text_array)
    found_css_blue = any("CSS" in seg.get("text", {}).get("content", "") and seg.get("annotations", {}).get("color") == "blue" for seg in rich_text_array)
    found_js_italic = any("JavaScript" in seg.get("text", {}).get("content", "") and seg.get("annotations", {}).get("italic") for seg in rich_text_array)
    found_responsive_underline_green = any("반응형 디자인" in seg.get("text", {}).get("content", "") and seg.get("annotations", {}).get("underline") and seg.get("annotations", {}).get("color") == "green" for seg in rich_text_array)
    
    expectations_met = [found_html_bold, found_css_blue, found_js_italic, found_responsive_underline_green]
    met_count = sum(expectations_met)
    
    print(f"\n🎯 Expected Format Verification:")
    print(f"   {'✅' if found_html_bold else '❌'} HTML bold formatting")
    print(f"   {'✅' if found_css_blue else '❌'} CSS blue color")
    print(f"   {'✅' if found_js_italic else '❌'} JavaScript italic")
    print(f"   {'✅' if found_responsive_underline_green else '❌'} 반응형 디자인 underline + green")
    print(f"   📊 Expectations met: {met_count}/4")
    
    print(f"\n✅ Comprehensive workflow completed successfully!")
    
    return {
        "success": True,
        "message": "Single example workflow completed successfully",
        "workflow_steps": [
            "1. User input → preprocessing (extract block_instructions, format_instructions, result_text)",
            "2. format_instructions + result_text → rich_text_llm (create formatted rich text objects)"
        ],
        "input": user_input,
        "step1_preprocessing": {
            "block_instructions": block_instructions,
            "format_instructions": format_instructions,
            "result_text": result_text
        },
        "step2_rich_text_formatting": {
            "segments_count": segments_count,
            "rich_text_array": rich_text_array,
            "message": rich_text_result.get("message", "")
        },
        "final_result": {
            "description": f"Generated {segments_count} text segments with proper formatting applied",
            "rich_text_objects": rich_text_array
        },
        "detailed_analysis": {
            "formatting_statistics": formatting_stats,
            "expected_formats_verification": {
                "html_bold": found_html_bold,
                "css_blue": found_css_blue,
                "javascript_italic": found_js_italic,
                "responsive_design_underline_green": found_responsive_underline_green,
                "expectations_met_count": f"{met_count}/4"
            },
            "sample_segments": [
                {
                    "content": seg.get("text", {}).get("content", ""),
                    "annotations": seg.get("annotations", {}),
                    "applied_formatting": [fmt for fmt in ["bold", "italic", "underline", "strikethrough", "code"] if seg.get("annotations", {}).get(fmt)] + 
                                        ([f"color:{seg.get('annotations', {}).get('color')}" for color in [seg.get("annotations", {}).get("color")] if color and color != "default"])
                }
                for seg in rich_text_array[:3]  # Show first 3 segments as examples
            ]
        },
        "formatting_requirements": {
            "input_requirements": "HTML(bold), CSS(blue), JavaScript(italic), important points(red), deprecated(strikethrough), code examples(code), 반응형 디자인(underline+green)",
            "total_format_types_requested": 7,
            "successfully_applied_formats": met_count
        }
    }


@app.get("/test_complete_pipeline")
async def test_complete_pipeline() -> Dict[str, Any]:
    """
    Test the complete pipeline: preprocessing → rich_text_llm → block_agent → Notion
    Demonstrates the full workflow from user input to formatted Notion blocks
    """
    
    # Test input with rich formatting requirements
    user_input = """웹 개발 가이드라는 제목으로 만들어주세요. 
    HTML을 굵게 강조하고, CSS는 파란색으로, JavaScript는 초록색으로 칠해주세요.
    중요한 개념들은 빨간색으로 표시해주세요."""
    
    print(f"🌟 Complete Pipeline Test Started")
    print(f"📝 User Input: {user_input}")
    print(f"🎯 Target Page: {TEST_PAGE_ID}")
    
    try:
        # Step 1: Preprocessing
        print(f"\n📋 Step 1: Preprocessing...")
        preprocessing_result = call_preprocessing_agent(user_input)
        
        if not preprocessing_result.get("success"):
            return {
                "success": False,
                "error": f"Preprocessing failed: {preprocessing_result.get('error')}",
                "step_failed": "preprocessing",
                "user_input": user_input
            }
        
        block_instructions = preprocessing_result.get("block_instructions", "")
        format_instructions = preprocessing_result.get("format_instructions", "")
        result_text = preprocessing_result.get("result_text", "")
        
        print(f"   ✅ Block instructions: {block_instructions}")
        print(f"   ✅ Format instructions: {format_instructions}")
        print(f"   ✅ Result text: {result_text[:100]}...")
        
        # Step 2: Rich Text Formatting
        print(f"\n🎨 Step 2: Rich Text Formatting...")
        rich_text_result = create_formatted_rich_text_array(format_instructions, result_text)
        
        if not rich_text_result.get("success"):
            return {
                "success": False,
                "error": f"Rich text formatting failed: {rich_text_result.get('error')}",
                "step_failed": "rich_text_formatting",
                "preprocessing_result": preprocessing_result
            }
        
        rich_text_array = rich_text_result.get("rich_text_array", [])
        segments_count = rich_text_result.get("segments_count", 0)
        
        print(f"   ✅ Created {segments_count} formatted text segments")
        for i, segment in enumerate(rich_text_array[:3]):  # Show first 3 segments
            content = segment.get("text", {}).get("content", "")
            annotations = segment.get("annotations", {})
            formatting = []
            if annotations.get("bold"): formatting.append("bold")
            if annotations.get("italic"): formatting.append("italic")
            if annotations.get("color") != "default": formatting.append(f"color:{annotations.get('color')}")
            format_desc = f" [{', '.join(formatting)}]" if formatting else " [plain]"
            print(f"      Segment {i+1}: '{content[:30]}...'{format_desc}")
        
        # Step 3: Block Agent (Create Notion Blocks)
        print(f"\n🏗️ Step 3: Creating Notion Blocks...")
        block_result = call_block_agent_with_rich_text(
            page_id=TEST_PAGE_ID,
            block_instructions=block_instructions,
            rich_text_array=rich_text_array
        )
        
        if not block_result.get("success"):
            return {
                "success": False,
                "error": f"Block creation failed: {block_result.get('error')}",
                "step_failed": "block_creation",
                "preprocessing_result": preprocessing_result,
                "rich_text_result": rich_text_result
            }
        
        blocks_created = block_result.get("blocks_created", 0)
        print(f"   ✅ Created {blocks_created} Notion blocks")
        print(f"   ✅ Processed {block_result.get('rich_text_segments_processed', 0)} rich text segments")
        
        # Final Success Result
        print(f"\n🎉 Complete Pipeline Success!")
        
        return {
            "success": True,
            "message": "Complete pipeline executed successfully: User Input → Preprocessing → Rich Text Formatting → Notion Blocks",
            "pipeline_summary": {
                "user_input": user_input,
                "page_id": TEST_PAGE_ID,
                "steps_completed": 3,
                "final_result": f"Created {blocks_created} formatted Notion blocks from {segments_count} rich text segments"
            },
            "step1_preprocessing": {
                "block_instructions": block_instructions,
                "format_instructions": format_instructions,
                "result_text": result_text
            },
            "step2_rich_text_formatting": {
                "segments_count": segments_count,
                "rich_text_array": rich_text_array,
                "message": rich_text_result.get("message", "")
            },
            "step3_notion_blocks": {
                "blocks_created": blocks_created,
                "page_id": TEST_PAGE_ID,
                "message": block_result.get("message", ""),
                "agent_output": block_result.get("agent_output", "")
            },
            "workflow_diagram": [
                f"📝 User Input: '{user_input[:50]}...'",
                f"📋 Preprocessing: Extract instructions and content",
                f"🎨 Rich Text: Create {segments_count} formatted segments",
                f"🏗️ Block Agent: Create {blocks_created} Notion blocks",
                f"📄 Result: Formatted content added to Notion page {TEST_PAGE_ID}"
            ]
        }
        
    except Exception as e:
        print(f"❌ Complete pipeline error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Complete pipeline failed: {str(e)}",
            "user_input": user_input
        }
