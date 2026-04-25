import imaplib
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# UTF-8 출력 설정 (윈도우 터미널 한글 깨짐 방지)
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

def manage_mail():
    try:
        # IMAP 연결 및 로그인
        mail = imaplib.IMAP4_SSL("imap.naver.com")
        mail.login(email_user, email_pass)
        print(f"✅ [{email_user}] 네이버 메일 로그인 성공")

        # ---------------------------------------------------------
        # 0. 전체 메일함 목록 및 시스템 폴더 식별
        # ---------------------------------------------------------
        status, folders_data = mail.list()
        all_folders = []
        trash_folder = "Deleted Messages"
        junk_folder = "Junk"

        for f in folders_data:
            f_str = f.decode('utf-8')
            parts = f_str.split('"')
            if len(parts) >= 4:
                folder_name = parts[-2]
                all_folders.append(folder_name)
                # 시스템 속성 확인
                if '\\Trash' in f_str:
                    trash_folder = folder_name
                if '\\Junk' in f_str:
                    junk_folder = folder_name
        
        # ---------------------------------------------------------
        # 1. 메일함 전체 '읽음' 상태로 변경 (예외 폴더 제외)
        # ---------------------------------------------------------
        # 읽음 제외 폴더 (인코딩 명칭)
        # &rWyzxQ-/&rBzHeA- : 구독/개인
        # &xbTBOMKk0MA-/&yRHFWcE4uzTWjKzE- : 어세스타/중앙세무회계
        read_exclude_folders = ["&rWyzxQ-/&rBzHeA-", "&xbTBOMKk0MA-/&yRHFWcE4uzTWjKzE-"]
        
        print("\n📑 전체 메일함 읽음 처리를 시작합니다...")
        for folder in all_folders:
            if folder in read_exclude_folders:
                print(f"⏩ \"{folder}\" 폴더: 읽음 처리 제외")
                continue
                
            try:
                mail.select(f'"{folder}"')
                status, messages = mail.search(None, 'UNSEEN')
                if status == 'OK':
                    unseen_ids = messages[0].split()
                    if unseen_ids:
                        for m_id in unseen_ids:
                            mail.store(m_id, '+FLAGS', '\\Seen')
                        print(f"✅ \"{folder}\": {len(unseen_ids)}개 읽음 처리 완료")
            except Exception as e:
                print(f"❌ \"{folder}\" 읽음 처리 실패: {str(e)}")

        # ---------------------------------------------------------
        # 2. 휴지통 및 스팸 폴더 비우기
        # ---------------------------------------------------------
        print(f"\n🗑️ 휴지통/스팸함 정리를 시작합니다... (대상: \"{trash_folder}\", \"{junk_folder}\")")
        for folder in [junk_folder, trash_folder]:
            try:
                mail.select(f'"{folder}"')
                status, messages = mail.search(None, 'ALL')
                if status == 'OK':
                    ids = messages[0].split()
                    if ids:
                        for m_id in ids:
                            mail.store(m_id, '+FLAGS', '\\Deleted')
                        mail.expunge()
                        print(f"🗑️ \"{folder}\" 폴더: {len(ids)}개의 메일을 영구 삭제했습니다.")
                    else:
                        print(f"🗑️ \"{folder}\" 폴더: 이미 비어 있습니다.")
            except Exception as e:
                print(f"⚠️ \"{folder}\" 폴더 비우기 실패: {str(e)}")

        # ---------------------------------------------------------
        # 3. 6개월 이상 된 메일 정리 (특정 폴더 제외)
        # ---------------------------------------------------------
        # 정리 제외 폴더
        exclude_folders = ["&rWyzxQ-/&rBzHeA-", "&xbTBOMKk0MA-/&yRHFWcE4uzTWjKzE-", "Sent Messages", "Drafts"]
        
        # 6개월 전 날짜 계산
        six_months_ago = (datetime.now() - timedelta(days=180)).strftime("%d-%b-%Y")
        print(f"\n🔍 {six_months_ago} 이전 메일을 \"{trash_folder}\"로 이동합니다.")

        for folder in all_folders:
            # 제외 폴더 및 시스템 폴더 스킵
            if folder in exclude_folders or folder == trash_folder or folder == junk_folder:
                continue
                
            try:
                mail.select(f'"{folder}"')
                status, messages = mail.search(None, f'BEFORE {six_months_ago}')
                if status == 'OK':
                    old_ids = messages[0].split()
                    if old_ids:
                        print(f"📦 \"{folder}\" 폴더: {len(old_ids)}개의 메일 이동 중...", end=" ", flush=True)
                        for m_id in old_ids:
                            # 식별된 휴지통으로 복사 후 삭제
                            copy_res = mail.copy(m_id, f'"{trash_folder}"')
                            if copy_res[0] == 'OK':
                                mail.store(m_id, '+FLAGS', '\\Deleted')
                        mail.expunge()
                        print("✅ 완료")
            except Exception as e:
                print(f"❌ \"{folder}\" 정리 실패: {str(e)}")

        mail.logout()
        print("\n✨ 모든 메일 관리 작업이 완료되었습니다.")

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

if __name__ == "__main__":
    manage_mail()
