# -*- coding: utf-8 -*-
"""
Notion API 연동 모듈

크롤링한 백준 문제를 Notion 페이지로 생성합니다.
"""

from notion_client import Client
from config import NOTION_TOKEN, NOTION_PARENT_PAGE_ID


# 티어별 아이콘 매핑
TIER_ICONS = {
    "Unrated": "❓",
    "Bronze": "🥉",
    "Silver": "🥈", 
    "Gold": "🥇",
    "Platinum": "💎",
    "Diamond": "💠",
    "Ruby": "💎"
}

# 티어별 색상 매핑 (Notion API 지원 색상)
TIER_COLORS = {
    "Unrated": "default",
    "Bronze": "brown",
    "Silver": "gray",
    "Gold": "yellow",
    "Platinum": "green",
    "Diamond": "blue",
    "Ruby": "red"
}

# 백준 관련 커버 이미지 URL
COVER_IMAGE_URL = "https://d2gd6pc034wcta.cloudfront.net/images/logo@2x.png"


def get_notion_client():
    """Notion 클라이언트 생성"""
    if not NOTION_TOKEN:
        raise ValueError("NOTION_TOKEN이 설정되지 않았습니다.")
    return Client(auth=NOTION_TOKEN)


def get_tier_base(tier):
    """티어에서 기본 이름 추출 (예: 'Silver I' -> 'Silver')"""
    for base in ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Ruby"]:
        if base in tier:
            return base
    return "Unrated"


def get_tier_icon(tier):
    """티어에 맞는 아이콘 반환"""
    base = get_tier_base(tier)
    return TIER_ICONS.get(base, "🥚")


def get_tier_color(tier):
    """티어에 맞는 색상 반환"""
    base = get_tier_base(tier)
    return TIER_COLORS.get(base, "default")


def check_duplicate(client, problem_id):
    """
    이미 등록된 문제인지 확인
    
    Args:
        client: Notion 클라이언트
        problem_id: 백준 문제 번호
    
    Returns:
        str or None: 중복된 페이지 URL (없으면 None)
    """
    try:
        # 부모 페이지의 하위 페이지들 검색
        response = client.blocks.children.list(block_id=NOTION_PARENT_PAGE_ID)
        
        for block in response.get("results", []):
            if block.get("type") == "child_page":
                page_title = block.get("child_page", {}).get("title", "")
                # 문제 번호가 제목에 포함되어 있는지 확인
                if f"] {problem_id}:" in page_title:
                    # 페이지 ID로 URL 생성
                    page_id = block.get("id", "").replace("-", "")
                    return f"https://www.notion.so/{page_id}"
        
        return None
    except Exception as e:
        print(f"⚠️ 중복 체크 실패: {e}")
        return None


def test_connection():
    """Notion API 연결 테스트"""
    try:
        client = get_notion_client()
        # 사용자 정보 조회로 연결 테스트
        response = client.users.me()
        print(f"✅ Connected to Notion!")
        print(f"   Bot: {response.get('name', 'Unknown')}")
        return True
    except Exception as e:
        print(f"❌ Notion 연결 실패: {e}")
        return False


def create_problem_page(problem_data, skip_duplicate=True):
    """
    백준 문제를 Notion 페이지로 생성
    
    Args:
        problem_data: scraper.py에서 반환한 문제 딕셔너리
        skip_duplicate: True면 중복 시 스킵, False면 그래도 생성
    
    Returns:
        str: 생성된 페이지 URL (또는 기존 페이지 URL)
    """
    client = get_notion_client()
    
    # 중복 체크
    if skip_duplicate:
        existing_url = check_duplicate(client, problem_data["problem_id"])
        if existing_url:
            return f"(이미 존재) {existing_url}"
    
    # 한국어 티어 변환
    tier_korean = problem_data["tier"].replace("Bronze", "브론즈").replace("Silver", "실버").replace("Gold", "골드").replace("Platinum", "플래티넘").replace("Diamond", "다이아몬드").replace("Ruby", "루비")
    
    # 페이지 제목 생성: [백준 실버 1] 14716: 현수막
    page_title = f"[백준 {tier_korean}] {problem_data['problem_id']}: {problem_data['title']}"
    
    # 티어별 아이콘 및 색상
    tier_icon = get_tier_icon(problem_data["tier"])
    tier_color = get_tier_color(problem_data["tier"])
    
    # Notion 블록 구성
    children = []
    
    # 0. 알고리즘 태그 섹션 (태그가 있을 때만)
    tags = problem_data.get("tags", [])
    if tags:
        tag_text = " | ".join([f"#{tag}" for tag in tags])
        children.append({
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": tag_text}}],
                "icon": {"type": "emoji", "emoji": "🏷️"},
                "color": "purple_background"
            }
        })
    
    # 1. 링크 섹션 (Callout)
    children.append({
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": [
                {"type": "text", "text": {"content": "www.acmicpc.net\n"}},
                {"type": "text", "text": {"content": problem_data["url"], "link": {"url": problem_data["url"]}}}
            ],
            "icon": {"type": "emoji", "emoji": "🔗"},
            "color": "gray_background"
        }
    })
    
    # 2. 구분선
    children.append({"object": "block", "type": "divider", "divider": {}})
    
    # 3. 문제 정보 테이블
    children.append({
        "object": "block",
        "type": "table",
        "table": {
            "table_width": 6,
            "has_column_header": True,
            "has_row_header": False,
            "children": [
                {
                    "object": "block",
                    "type": "table_row",
                    "table_row": {
                        "cells": [
                            [{"type": "text", "text": {"content": "시간 제한"}}],
                            [{"type": "text", "text": {"content": "메모리 제한"}}],
                            [{"type": "text", "text": {"content": "제출"}}],
                            [{"type": "text", "text": {"content": "정답"}}],
                            [{"type": "text", "text": {"content": "맞힌 사람"}}],
                            [{"type": "text", "text": {"content": "정답 비율"}}]
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "table_row",
                    "table_row": {
                        "cells": [
                            [{"type": "text", "text": {"content": problem_data.get("time_limit", "")}}],
                            [{"type": "text", "text": {"content": problem_data.get("memory_limit", "")}}],
                            [{"type": "text", "text": {"content": problem_data.get("submissions", "")}}],
                            [{"type": "text", "text": {"content": problem_data.get("accepted", "")}}],
                            [{"type": "text", "text": {"content": problem_data.get("users", "")}}],
                            [{"type": "text", "text": {"content": problem_data.get("accuracy", "")}}]
                        ]
                    }
                }
            ]
        }
    })
    
    # 4. 문제 섹션
    children.append({"object": "block", "type": "divider", "divider": {}})
    children.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{
                "type": "text", 
                "text": {"content": "📋 문제"},
                "annotations": {"color": "blue"}
            }]
        }
    })
    
    # 문제 설명 (길이 제한: Notion API는 블록당 2000자)
    description = problem_data.get("description", "")
    for chunk in split_text(description, 2000):
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": chunk}}]}
        })
    

    # 5. 입력 섹션
    children.append({"object": "block", "type": "divider", "divider": {}})
    children.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{
                "type": "text", 
                "text": {"content": "📥 입력"},
                "annotations": {"color": "blue"}
            }]
        }
    })
    
    input_desc = problem_data.get("input", "")
    for chunk in split_text(input_desc, 2000):
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": chunk}}]}
        })
    

    # 6. 출력 섹션
    children.append({"object": "block", "type": "divider", "divider": {}})
    children.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{
                "type": "text", 
                "text": {"content": "📤 출력"},
                "annotations": {"color": "blue"}
            }]
        }
    })
    
    output_desc = problem_data.get("output", "")
    for chunk in split_text(output_desc, 2000):
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": chunk}}]}
        })
    

    # 7. 예제 섹션
    children.append({"object": "block", "type": "divider", "divider": {}})
    children.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{
                "type": "text", 
                "text": {"content": "💻 예제"},
                "annotations": {"color": "blue"}
            }]
        }
    })
    
    examples = problem_data.get("examples", [])
    for i, example in enumerate(examples, 1):
        # 예제 입력
        children.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {"rich_text": [{"type": "text", "text": {"content": f"예제 입력 {i}"}}]}
        })
        children.append({
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": [{"type": "text", "text": {"content": example.get("input", "")}}],
                "language": "plain text"
            }
        })
        
        # 예제 출력
        children.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {"rich_text": [{"type": "text", "text": {"content": f"예제 출력 {i}"}}]}
        })
        children.append({
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": [{"type": "text", "text": {"content": example.get("output", "")}}],
                "language": "plain text"
            }
        })
    
    # 8. 풀이 섹션 (빈 공간)
    children.append({"object": "block", "type": "divider", "divider": {}})
    children.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{
                "type": "text", 
                "text": {"content": "✏️ 풀이"},
                "annotations": {"color": "blue"}
            }]
        }
    })
    children.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": "여기에 풀이를 작성하세요..."}}]}
    })
    
    # 페이지 생성 (부모 페이지 아래에 하위 페이지로)
    new_page = client.pages.create(
        parent={"page_id": NOTION_PARENT_PAGE_ID},
        icon={"type": "emoji", "emoji": tier_icon},
        properties={
            "title": {
                "title": [{"type": "text", "text": {"content": page_title}}]
            }
        },
        children=children
    )
    
    return new_page.get("url", "URL 없음")


def split_text(text, max_length):
    """
    텍스트를 최대 길이로 분할
    Notion API는 한 블록에 2000자 제한이 있음
    """
    if not text:
        return [""]
    
    chunks = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break
        
        # 줄바꿈 기준으로 자르기
        split_point = text.rfind('\n', 0, max_length)
        if split_point == -1:
            split_point = max_length
        
        chunks.append(text[:split_point])
        text = text[split_point:].lstrip('\n')
    
    return chunks


# 테스트용 코드
if __name__ == "__main__":
    test_connection()
