import imaplib
import os
import sys
from dotenv import load_dotenv

# UTF-8 출력 설정
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 환경 변수 로드
load_dotenv(r"c:\mskwon_data\.venv\.env")

email_user = os.getenv("NAVER_EMAIL")
email_pass = os.getenv("NAVER_APP_PW")

try:
    mail = imaplib.IMAP4_SSL("imap.naver.com")
    mail.login(email_user, email_pass)
    
    # 모든 폴더 목록 가져오기
    status, folders = mail.list()
    print("--- Naver Mail Folders ---")
    for f in folders:
        # f는 b'(\\HasNoChildren) "/" "INBOX"' 형식
        print(f.decode('utf-8'))
        
    mail.logout()
except Exception as e:
    print(f"Error: {str(e)}")
