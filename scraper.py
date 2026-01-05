# -*- coding: utf-8 -*-
"""
백준 문제 크롤링 모듈

백준 온라인 저지 페이지에서 문제 정보를 추출합니다.
"""

import re
import requests
from bs4 import BeautifulSoup


def get_problem_id(url):
    """URL에서 문제 번호 추출"""
    match = re.search(r'/problem/(\d+)', url)
    if match:
        return int(match.group(1))
    return None


def clean_text(text):
    """
    텍스트 정리: 과도한 줄바꿈 제거
    연속된 줄바꿈을 하나로 줄이고, 불필요한 공백 정리
    """
    if not text:
        return ""
    
    # 연속된 줄바꿈을 하나로
    text = re.sub(r'\n\s*\n', '\n\n', text)
    # 3개 이상 연속 줄바꿈을 2개로
    text = re.sub(r'\n{3,}', '\n\n', text)
    # 앞뒤 공백 제거
    return text.strip()


def extract_images(element):
    """
    HTML 요소에서 이미지 URL 추출
    
    Args:
        element: BeautifulSoup 요소
    
    Returns:
        list: 이미지 URL 리스트
    """
    if not element:
        return []
    
    images = []
    for img in element.find_all("img"):
        src = img.get("src", "")
        if src:
            # 상대 경로를 절대 경로로 변환
            if src.startswith("//"):
                src = "https:" + src
            elif src.startswith("/"):
                src = "https://www.acmicpc.net" + src
            elif not src.startswith("http"):
                src = "https://www.acmicpc.net/" + src
            images.append(src)
    
    return images


def get_solved_ac_info(problem_id):
    """
    solved.ac API에서 문제 정보 가져오기
    
    Returns:
        dict: {tier: str, tier_level: int, tags: list}
    """
    result = {
        "tier": "Unknown",
        "tier_level": 0,
        "tags": []
    }
    
    try:
        response = requests.get(
            f"https://solved.ac/api/v3/problem/show",
            params={"problemId": problem_id},
            headers={"Accept": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            level = data.get("level", 0)
            
            tier_names = {
                0: "Unrated",
                1: "Bronze V", 2: "Bronze IV", 3: "Bronze III", 4: "Bronze II", 5: "Bronze I",
                6: "Silver V", 7: "Silver IV", 8: "Silver III", 9: "Silver II", 10: "Silver I",
                11: "Gold V", 12: "Gold IV", 13: "Gold III", 14: "Gold II", 15: "Gold I",
                16: "Platinum V", 17: "Platinum IV", 18: "Platinum III", 19: "Platinum II", 20: "Platinum I",
                21: "Diamond V", 22: "Diamond IV", 23: "Diamond III", 24: "Diamond II", 25: "Diamond I",
                26: "Ruby V", 27: "Ruby IV", 28: "Ruby III", 29: "Ruby II", 30: "Ruby I"
            }
            
            result["tier"] = tier_names.get(level, "Unknown")
            result["tier_level"] = level
            
            # 알고리즘 태그 추출
            tags = data.get("tags", [])
            for tag in tags:
                # 한국어 태그명 우선, 없으면 영어
                display_names = tag.get("displayNames", [])
                ko_name = None
                en_name = None
                for name in display_names:
                    if name.get("language") == "ko":
                        ko_name = name.get("name")
                    elif name.get("language") == "en":
                        en_name = name.get("name")
                result["tags"].append(ko_name or en_name or tag.get("key", ""))
                
    except Exception as e:
        print(f"⚠️ solved.ac 정보를 가져올 수 없습니다: {e}")
    
    return result


def scrape_problem(url):
    """
    백준 문제 페이지 크롤링
    
    Args:
        url: 백준 문제 URL (예: https://www.acmicpc.net/problem/14716)
    
    Returns:
        dict: 문제 정보 딕셔너리
    """
    # 문제 번호 추출
    problem_id = get_problem_id(url)
    if not problem_id:
        raise ValueError(f"올바른 백준 URL이 아닙니다: {url}")
    
    # Selenium으로 페이지 로드 (AWS WAF 우회)
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 브라우저 창 숨김
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        driver.get(url)
        
        # 페이지 로드 대기 (문제 제목이 나타날 때까지)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "problem_title"))
        )
        
        # HTML 파싱
        soup = BeautifulSoup(driver.page_source, 'html.parser')
    finally:
        driver.quit()
    
    # 제목 추출
    title_elem = soup.select_one("#problem_title")
    title = title_elem.text.strip() if title_elem else "제목 없음"
    
    # 문제 정보 테이블 추출
    info_table = soup.select_one("#problem-info tbody tr")
    if info_table:
        cells = info_table.find_all("td")
        time_limit = cells[0].text.strip() if len(cells) > 0 else ""
        memory_limit = cells[1].text.strip() if len(cells) > 1 else ""
        submissions = cells[2].text.strip() if len(cells) > 2 else ""
        accepted = cells[3].text.strip() if len(cells) > 3 else ""
        users = cells[4].text.strip() if len(cells) > 4 else ""
        accuracy = cells[5].text.strip() if len(cells) > 5 else ""
    else:
        time_limit = memory_limit = submissions = accepted = users = accuracy = ""
    
    # 문제 설명 추출
    description_elem = soup.select_one("#problem_description")
    description = clean_text(description_elem.get_text(separator="\n")) if description_elem else ""
    description_images = extract_images(description_elem)
    
    # 입력 설명 추출
    input_elem = soup.select_one("#problem_input")
    input_desc = clean_text(input_elem.get_text(separator="\n")) if input_elem else ""
    input_images = extract_images(input_elem)
    
    # 출력 설명 추출
    output_elem = soup.select_one("#problem_output")
    output_desc = clean_text(output_elem.get_text(separator="\n")) if output_elem else ""
    output_images = extract_images(output_elem)
    
    # 예제 입출력 추출
    examples = []
    example_num = 1
    while True:
        sample_input = soup.select_one(f"#sample-input-{example_num}")
        sample_output = soup.select_one(f"#sample-output-{example_num}")
        
        if not sample_input:
            break
        
        examples.append({
            "input": sample_input.text.strip() if sample_input else "",
            "output": sample_output.text.strip() if sample_output else ""
        })
        example_num += 1
    
    # solved.ac 정보 가져오기 (티어 + 알고리즘 태그)
    solved_info = get_solved_ac_info(problem_id)
    
    return {
        "problem_id": problem_id,
        "title": title,
        "tier": solved_info["tier"],
        "tier_level": solved_info["tier_level"],
        "tags": solved_info["tags"],
        "url": url,
        "time_limit": time_limit,
        "memory_limit": memory_limit,
        "submissions": submissions,
        "accepted": accepted,
        "users": users,
        "accuracy": accuracy,
        "description": description,
        "description_images": description_images,
        "input": input_desc,
        "input_images": input_images,
        "output": output_desc,
        "output_images": output_images,
        "examples": examples
    }


# 테스트용 코드
if __name__ == "__main__":
    import json
    
    test_url = "https://www.acmicpc.net/problem/14716"
    print(f"🔍 크롤링 테스트: {test_url}\n")
    
    try:
        result = scrape_problem(test_url)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ 오류: {e}")
