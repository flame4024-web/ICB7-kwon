import imaplib
import os
import sys
import base64
from dotenv import load_dotenv

# UTF-8 출력 설정
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def decode_imap_utf7(s):
    # 간단한 IMAP-UTF7 디코더 (필요 부분만)
    if not s.startswith('&') or not s.endswith('-'):
        return s
    try:
        inner = s[1:-1].replace(',', '/')
        # Padding
        res = base64.b64decode(inner + '=' * (-len(inner) % 4))
        return res.decode('utf-16-be')
    except:
        return s

# 환경 변수 로드
load_dotenv(r"c:\mskwon_data\.venv\.env")

email_user = os.getenv("NAVER_EMAIL")
email_pass = os.getenv("NAVER_APP_PW")

try:
    mail = imaplib.IMAP4_SSL("imap.naver.com")
    mail.login(email_user, email_pass)
    
    status, folders = mail.list()
    print("--- Decoding Folders ---")
    for f in folders:
        parts = f.decode('utf-8').split('"')
        if len(parts) >= 4:
            f_name = parts[-2]
            # 인코딩된 부분 찾기
            import re
            decoded = f_name
            matches = re.findall(r'&[^-]+-', f_name)
            for m in matches:
                d = decode_imap_utf7(m)
                decoded = decoded.replace(m, d)
            print(f"Encoded: {f_name} -> Decoded: {decoded}")
            
    mail.logout()
except Exception as e:
    print(f"Error: {str(e)}")
