#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
백준 문제 Notion 자동 정리 도구

사용법:
    python main.py <백준 문제 URL>

예시:
    python main.py https://www.acmicpc.net/problem/14716
"""

import sys
import argparse

from config import validate_config
from scraper import scrape_problem
from notion_api import create_problem_page, test_connection


def main():
    # 명령행 인자 파싱
    parser = argparse.ArgumentParser(
        description="백준 문제를 Notion에 자동으로 정리합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
    python main.py https://www.acmicpc.net/problem/14716
    python main.py https://www.acmicpc.net/problem/1000 --test
        """
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="백준 문제 URL (예: https://www.acmicpc.net/problem/14716)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Notion 연결만 테스트합니다"
    )
    
    args = parser.parse_args()
    
    # 환경 변수 검증
    if not validate_config():
        sys.exit(1)
    
    # 연결 테스트 모드
    if args.test:
        print("🔌 Notion 연결 테스트 중...")
        if test_connection():
            print("✅ 연결 테스트 성공!")
        sys.exit(0)
    
    # URL 필수 확인
    if not args.url:
        parser.print_help()
        print("\n❌ 오류: 백준 문제 URL을 입력해주세요.")
        sys.exit(1)
    
    # URL 유효성 검사
    if "acmicpc.net/problem/" not in args.url:
        print(f"❌ 오류: 올바른 백준 URL이 아닙니다: {args.url}")
        print("   예시: https://www.acmicpc.net/problem/14716")
        sys.exit(1)
    
    print(f"🔍 문제 크롤링 중: {args.url}")
    
    try:
        # 1. 백준 문제 크롤링
        problem_data = scrape_problem(args.url)
        print(f"   ✓ 문제: {problem_data['title']}")
        print(f"   ✓ 난이도: {problem_data['tier']}")
        if problem_data.get("tags"):
            print(f"   ✓ 태그: {', '.join(problem_data['tags'][:5])}")  # 최대 5개만 표시
        
        # 2. Notion 페이지 생성
        print("📝 Notion 페이지 생성 중...")
        page_url = create_problem_page(problem_data)
        
        print("\n" + "=" * 50)
        if "(이미 존재)" in page_url:
            print("⚠️ 이미 등록된 문제입니다!")
            print(f"📄 기존 페이지: {page_url.replace('(이미 존재) ', '')}")
        else:
            print("✅ 완료!")
            print(f"📄 Notion 페이지: {page_url}")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
