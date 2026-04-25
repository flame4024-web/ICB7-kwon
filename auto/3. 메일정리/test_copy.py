import imaplib
import os
from dotenv import load_dotenv

load_dotenv(r"c:\mskwon_data\.venv\.env")
email_user = os.getenv("NAVER_EMAIL")
email_pass = os.getenv("NAVER_APP_PW")

try:
    mail = imaplib.IMAP4_SSL("imap.naver.com")
    mail.login(email_user, email_pass)
    
    # 1. Trash folder identification (server-side attributes)
    trash_folder = "Deleted Messages"
    status, folders_data = mail.list()
    for f in folders_data:
        f_str = f.decode('utf-8')
        if '\\Trash' in f_str:
            trash_folder = f_str.split('"')[-2]
            print(f"Server-side Trash Folder: {trash_folder}")
    
    # 2. Try selecting it with quotes
    # For some servers, we MUST use direct quotes or the exact IMAP string.
    # In python imaplib, if the name has spaces, it's often better to quote it if passing directly, 
    # but imaplib often quotes it for you IF you use the method correctly.
    # BUT if we are getting "Invalid arguments", let's try different forms.
    
    try:
        res = mail.select(f'"{trash_folder}"')
        print(f"Select with quotes: {res}")
    except Exception as e:
        print(f"Select with quotes failed: {str(e)}")
        
    try:
        res = mail.select(trash_folder)
        print(f"Select without quotes: {res}")
    except Exception as e:
        print(f"Select without quotes failed: {str(e)}")

    # 3. Try COPY 1 to trash
    mail.select("INBOX")
    status, messages = mail.search(None, 'ALL')
    if status == 'OK':
        ids = messages[0].split()
        if ids:
            m_id = ids[0]
            print(f"Try to copy ID {m_id} to {trash_folder}")
            # Try different combinations
            try:
                # Standard imaplib way (it should handle quoting)
                res = mail.copy(m_id, trash_folder)
                print(f"Standard copy: {res}")
            except Exception as e:
                print(f"Standard copy failed: {str(e)}")
                
            try:
                # Quoted destination name
                res = mail.copy(m_id, f'"{trash_folder}"')
                print(f"Quoted-dest copy: {res}")
            except Exception as e:
                print(f"Quoted-dest copy failed: {str(e)}")

    mail.logout()
except Exception as e:
    print(f"Initial connection failed: {str(e)}")
