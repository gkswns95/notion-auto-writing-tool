# -*- coding: utf-8 -*-
"""
환경 변수 관리 모듈

.env 파일에서 Notion API 토큰과 데이터베이스 ID를 로드합니다.
"""

import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# Notion API 설정
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_PARENT_PAGE_ID = os.getenv("NOTION_PARENT_PAGE_ID")


def validate_config():
    """환경 변수가 제대로 설정되었는지 확인"""
    errors = []
    
    if not NOTION_TOKEN:
        errors.append("NOTION_TOKEN이 설정되지 않았습니다.")
    
    if not NOTION_PARENT_PAGE_ID:
        errors.append("NOTION_PARENT_PAGE_ID가 설정되지 않았습니다.")
    
    if errors:
        print("❌ 환경 변수 설정 오류:")
        for error in errors:
            print(f"   - {error}")
        print("\n📝 .env 파일을 확인해주세요.")
        print("   예시:")
        print("   NOTION_TOKEN=secret_xxxxxxxx")
        print("   NOTION_PARENT_PAGE_ID=xxxxxxxx")
        return False
    
    return True
