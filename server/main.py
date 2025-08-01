from fastapi import FastAPI
from dotenv import load_dotenv
from typing import Dict, Any

from service.agents.block_agent import call_block_agent
    
load_dotenv()

app = FastAPI()

# Hardcoded page ID for testing
TEST_PAGE_ID = "23f625eb-5879-8056-aa11-ca93a8d9227f"

@app.get("/test_block_creation")
async def test_block_creation() -> Dict[str, Any]:
    """
    Test various Notion block creation using the block agent.
    Creates different types of blocks without formatting details.
    """
    
    # Natural Korean text with all block types - Java programming guide
    test_request = """
        자바 프로그래밍 학습 가이드를 작성해주세요. 
        메인 제목으로 "자바 기초 학습 가이드"를 헤딩1로 만들고, 자바는 객체지향 프로그래밍의 대표적인 언어로 안정성과 성능이 뛰어나다는 설명 문단을 추가해주세요. 
        "자바의 특징" 헤딩2를 만들고 자바는 플랫폼 독립적이며 강력한 메모리 관리 기능을 제공한다는 내용을 문단으로 작성하고, 
        ☕ 아이콘과 함께 "자바는 컴파일 언어로 JVM에서 실행되어 높은 성능과 보안성을 제공합니다"라는 중요한 정보를 콜아웃으로 강조해주세요. 
        "제임스 고슬링이 말했듯이, 한 번 작성하면 어디서든 실행된다"라는 인용구 블록을 추가하고 구분선을 넣어주세요. 
        "학습 순서" 헤딩3을 만들고 기본 문법 배우기, 객체지향 개념 이해하기, 클래스와 메서드 작성하기를 불릿 리스트로 나열하고, 
        1단계 자바 기초, 2단계 객체지향 프로그래밍, 3단계 고급 프레임워크를 번호 리스트로 만들어주세요. 할 일 목록으로 "JDK 설치하기"는 완료 상태로, 
        "첫 자바 프로그램 작성하기"는 미완료 상태로 체크박스를 만들고 다시 구분선을 추가해주세요. 
        "코드 예제" 헤딩을 만들고 System.out.println("Hello, Java!")라는 자바 코드 블록을 삽입하고, "더 많은 예제 보기"라는 토글 블록을 만들어주세요. 
        목차를 추가하고 현재 위치를 표시하는 브레드크럼을 넣어주세요. "학습 진도표" 헤딩을 만들고 3열의 표(헤더 포함)를 생성해서 학습 계획을 정리할 수 있게 해주세요.
        "수학과 미디어" 헤딩을 만들고 a² + b² = c²라는 수식 블록을 추가하고, 
        https://picsum.photos/400/200 이미지를 삽입하고 https://www.youtube.com/watch?v=dQw4w9WgXcQ 동영상을 넣어주세요. 
        마지막 구분선 후 "참고 자료" 헤딩을 만들고 https://oracle.com/java 자바 공식 사이트 URL을 링크로 걸고, 
        https://docs.oracle.com/javase 자바 문서를 북마크로 만들고, https://replit.com 온라인 자바 실행 환경을 임베드로 삽입해주세요."""

    
    print(f"🧪 Testing block creation with page ID: {TEST_PAGE_ID}")
    print(f"📝 Request: {test_request}")
    
    # Call block agent
    result = call_block_agent(
        page_id=TEST_PAGE_ID,
        block_request=test_request
    )
    
    return {
        "success": result.get("success", False),
        "message": result.get("message", ""),
        "page_id": TEST_PAGE_ID,
        "tools_called": result.get("tools_called", 0),
        "agent_output": result.get("agent_output", ""),
        "error": result.get("error", "")
    }