import os
import sys
import re
import webbrowser
import subprocess
from datetime import datetime

# 1. 설정 및 경로 정의
ANALYSIS_ROOT = r"C:\Users\역량평가 운영파트\OneDrive\1. 권민섭\2. 개인 관리\1. 업무처리\3. 2026\1. 데이터분석"
DOWNLOADS_PATH = os.path.join(os.path.expanduser("~"), "Downloads")

CHROME_URLS = [
    "https://gemini.google.com/gem/9e29b16951fb",
    "https://gemini.google.com/gem/88cf3cd62385",
    "https://docs.google.com/spreadsheets/u/0/",
    "https://www.notion.so/INNER-CIRCLE-Course-7-2e7d5beeb0c0808783cbce4847daca5b"
]

ZOOM_LINK = "https://us06web.zoom.us/j/83054584885?pwd=dRnP7ruvduHVQYP05UhRazn29b5BRT.1"

def get_next_folder_info(root_path):
    """기존 폴더 목록에서 다음 번호와 형식을 결정합니다."""
    if not os.path.exists(root_path):
        return 1, datetime.now().strftime("%y%m%d")
    
    dirs = [d for d in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, d))]
    
    max_num = 0
    for d in dirs:
        # '번호. 날짜' 또는 '번호 날짜' 형식에서 번호 추출
        match = re.match(r"(\d+)", d)
        if match:
            num = int(match.group(1))
            if num > max_num:
                max_num = num
                
    next_num = max_num + 1
    today_yymmdd = datetime.now().strftime("%y%m%d")
    return next_num, today_yymmdd

def register_command():
    """현재 스크립트 위치를 기준으로 'lecture' 명령어를 시스템에 등록합니다."""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.abspath(__file__)
        bat_path = os.path.join(current_dir, "lecture.bat")
        
        # 1. lecture.bat 파일 생성 (ANSI/CP949 인코딩으로 CMD 호환성 확보)
        bat_content = f'@python "{script_path}" %*'
        with open(bat_path, "w", encoding="cp949") as f:
            f.write(bat_content)
        
        # 2. PATH 환경 변수 확인 및 등록 (PowerShell 이용)
        # 인코딩 문제를 방지하기 위해 bytes로 받고 강제 디코딩하거나 utf-8 지정
        check_path_cmd = f'[Environment]::GetEnvironmentVariable("Path", "User")'
        ps_check = subprocess.run(["powershell", "-Command", check_path_cmd], capture_output=True, encoding='utf-8', errors='ignore')
        
        user_path = ps_check.stdout if ps_check.stdout else ""
        
        if current_dir.lower() not in user_path.lower():
            print(f"새로운 환경에서 명령어를 등록합니다: {current_dir}")
            add_path_cmd = f'$oldPath = [Environment]::GetEnvironmentVariable("Path", "User"); [Environment]::SetEnvironmentVariable("Path", "$oldPath;{current_dir}", "User")'
            subprocess.run(["powershell", "-Command", add_path_cmd], capture_output=True)
            print(">>> 'lecture' 명령어가 성공적으로 등록되었습니다. (새로운 CMD 창에서 적용됩니다)")
    except Exception as e:
        print(f"명령어 등록 중 알림: {e}")

def setup_lecture():
    # 실행 시마다 명령어 등록 상태 확인 및 갱신
    register_command()
    
    print("강의 세팅 자동화를 시작합니다...")

    # 1. 폴더 생성
    next_num, yymmdd = get_next_folder_info(ANALYSIS_ROOT)
    # 세팅 가이드 예시(1.260321)에 맞춰 번호.날짜 형식으로 생성
    new_folder_name = f"{next_num}. {yymmdd}"
    new_folder_path = os.path.join(ANALYSIS_ROOT, new_folder_name)
    
    try:
        if not os.path.exists(new_folder_path):
            os.makedirs(new_folder_path)
            print(f"새 폴더 생성 완료: {new_folder_path}")
        else:
            print(f"폴더가 이미 존재합니다: {new_folder_path}")
    except Exception as e:
        print(f"폴더 생성 중 오류 발생: {e}")

    # 2. 탐색기 실행
    print("탐색기를 실행합니다...")
    try:
        os.startfile(new_folder_path)
        os.startfile(DOWNLOADS_PATH)
    except Exception as e:
        print(f"탐색기 실행 중 오류 발생: {e}")

    # 3. 크롬 탭 활성화
    print("크롬 브라우저 탭을 엽니다...")
    try:
        # 기본 브라우저(크롬 권장)로 URL 오픈
        for url in CHROME_URLS:
            webbrowser.open(url)
    except Exception as e:
        print(f"브라우저 실행 중 오류 발생: {e}")

    # 4. 줌 회의 시작
    print("줌 회의에 접속합니다...")
    try:
        webbrowser.open(ZOOM_LINK)
    except Exception as e:
        print(f"줌 접속 중 오류 발생: {e}")

    # 5. antigravity 실행
    print("Antigravity를 실행합니다...")
    try:
        # 시스템 PATH에 있는 antigravity 명령어 호출
        subprocess.Popen(["antigravity"], shell=True)
    except Exception as e:
        print(f"Antigravity 실행 중 오류 발생: {e}")

    # 6. onenote 실행
    print("OneNote를 실행합니다...")
    try:
        os.startfile("onenote:")
    except Exception as e:
        print(f"OneNote 실행 중 오류 발생: {e}")

    print("모든 세팅이 완료되었습니다. 즐거운 강의 되세요!")

if __name__ == "__main__":
    # 터미널 한글 깨짐 방지 (Windows)
    os.system("chcp 65001 > nul")
    setup_lecture()
