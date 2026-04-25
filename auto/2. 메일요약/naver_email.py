import os
import imaplib
import email
from email.header import decode_header
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import sys

# 터미널 출력 인코딩 설정 (한글 및 이모지 깨짐 방지)
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python 3.7 미만 버전 대응
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# [1단계] 환경 및 인증 검증
# 프로젝트 루트의 .venv/.env 파일을 참조하도록 설정
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
env_path = os.path.join(root_path, '.venv', '.env')
load_dotenv(dotenv_path=env_path)

USER_EMAIL = os.getenv("NAVER_EMAIL")
USER_PASSWORD = os.getenv("NAVER_APP_PW")

if not USER_EMAIL or not USER_PASSWORD:
    print("❌ 오류: .env 파일에 계정 정보가 없습니다.")
    exit()

def summarize_text(text, limit=120):
    """
    외부 API 없이 단어 빈도수 기반으로 핵심 문장을 추출하는 요약 함수
    """
    if not text or len(text) <= limit:
        return text.strip()

    import re
    from collections import Counter

    # 1. 문장 분리 (마침표, 물음표 등 기준)
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(sentences) <= 1:
        return text[:limit] + "..."

    # 2. 단어 빈도수 계산 (간이 토큰화: 2글자 이상 단어만 대상)
    words = re.findall(r'[가-힣A-Za-z0-9]{2,}', text)
    word_freq = Counter(words)
    
    if not word_freq:
        return text[:limit] + "..."

    # 3. 문장별 점수 계산 (포함된 단어의 빈도수 합계)
    sentence_scores = {}
    for i, sent in enumerate(sentences):
        sent_words = re.findall(r'[가-힣A-Za-z0-9]{2,}', sent)
        score = sum(word_freq.get(w, 0) for w in sent_words)
        # 문장 위치에 따른 가중치 (앞쪽 문장에 약간의 가중치)
        sentence_scores[i] = score * (1 + 0.1 / (i + 1))

    # 4. 상위 문장 선택 (가장 점수가 높은 문장부터 정해진 글자수까지)
    sorted_indices = sorted(sentence_scores, key=sentence_scores.get, reverse=True)
    
    # 핵심 문장 1~2개 선택 (순서는 원문 순서 유지)
    best_indices = sorted(sorted_indices[:2])
    summary = " ".join([sentences[i] for i in best_indices])
    
    # 5. 최종 글자 수 조정
    if len(summary) > limit:
        summary = summary[:limit].rsplit(' ', 1)[0] + "..."
    
    return summary.strip()

def get_decoded_string(encoded_str):
    """이메일 헤더의 인코딩된 문자열을 사람이 읽을 수 있게 디코딩하는 헬퍼 함수"""
    if not encoded_str: return ""
    decoded_fragments = decode_header(encoded_str)
    decoded_string = ""
    for string, charset in decoded_fragments:
        if isinstance(string, bytes):
            decoded_string += string.decode(charset or 'utf-8', errors='replace')
        else:
            decoded_string += string
    return decoded_string

try:
    # 네이버 IMAP 서버 연결
    mail = imaplib.IMAP4_SSL("imap.naver.com")
    
    # 로그인 아이디 형식 처리 (이메일 전체 또는 아이디만 시도)
    login_id = USER_EMAIL.split("@")[0] if USER_EMAIL else ""
    try:
        mail.login(login_id, USER_PASSWORD)
    except Exception:
        # 아이디만으로 실패할 경우 전체 이메일로 재시도
        mail.login(USER_EMAIL, USER_PASSWORD)
        
    mail.select("INBOX") # 수신함 선택

    # [2단계] 모든 폴더에서 메일 통합 수집 (누락 방지)
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    today_str = f"{now.day:02d}-{months[now.month-1]}-{now.year}"
    
    print(f"🔍 검색 기준 날짜 (KST): {today_str}")
    
    # 제외할 폴더 목록 (보낸메일함, 휴지통, 스팸 등)
    exclude_keywords = ["Sent", "Drafts", "Deleted", "Trash", "Junk", "스팸", "&v6vS6LGms7E-"] # "전체메일"은 중복 방지를 위해 제외하거나 이것만 쓰거나 선택
    
    status, folders_list = mail.list()
    all_mail_ids = {} # {msg_id: (folder, mail_id)} 형식으로 중복 방지
    
    print("📂 메일 수집 중 (여러 폴더 확인)...")
    
    for f_info in folders_list:
        parts = f_info.decode().split('"')
        if len(parts) >= 4:
            folder_name = parts[-2]
        else:
            continue
            
        # 제외 폴더 스킵
        if any(kw.lower() in folder_name.lower() for kw in exclude_keywords):
            continue
            
        try:
            mail.select(folder_name, readonly=True)
            # SINCE가 더 안정적이므로 SINCE 사용 후 Python에서 날짜 재검증하거나,
            # 네이버에서는 ON이 잘 작동하므로 ON으로 우선 시도.
            status, messages = mail.search(None, f'(ON "{today_str}")')
            ids = messages[0].split()
            
            for m_id in ids:
                # 메일의 고유 Message-ID를 가져오기 위해 일단 fetch
                # (중복 제거를 위해 Message-ID나 내용을 키로 사용)
                # 여기서는 간단히 folder_name과 m_id 조합을 사용하되, 
                # 같은 내용의 메일이 여러 폴더에 보일 수 있으므로 주의.
                all_mail_ids[(folder_name, m_id)] = m_id
        except:
            continue

    # [3단계] 데이터 데이터 추출 및 구조화
    mail_list = []
    print(f"\n📊 띠링! 오늘 도착한 메일 요약 리포트입니다. (총 {len(all_mail_ids)}개)\n" + "-"*50)
    
    idx = 1
    for (folder, m_id) in all_mail_ids.keys():
        try:
            mail.select(folder, readonly=True)
            status, msg_data = mail.fetch(m_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # 제목과 발신자 추출
                    subject = get_decoded_string(msg.get("Subject"))
                    sender = get_decoded_string(msg.get("From"))
                    
                    # 제목/발신자/날짜 전수 검사 (중복 메일 방지: 제목이 같고 발신자가 같으면 스킵)
                    if any(m['subject'] == subject and m['sender'] == sender for m in mail_list):
                        continue
                        
                    # 본문 추출 (텍스트 우선, 없으면 HTML에서 추출)
                    body_plain = ""
                    body_html = ""
                    
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            if content_type == "text/plain":
                                try:
                                    body_plain = part.get_payload(decode=True).decode('utf-8', errors='replace')
                                except: pass
                            elif content_type == "text/html":
                                try:
                                    body_html = part.get_payload(decode=True).decode('utf-8', errors='replace')
                                except: pass
                    else:
                        content_type = msg.get_content_type()
                        if content_type == "text/plain":
                            try:
                                body_plain = msg.get_payload(decode=True).decode('utf-8', errors='replace')
                            except: pass
                        elif content_type == "text/html":
                            try:
                                body_html = msg.get_payload(decode=True).decode('utf-8', errors='replace')
                            except: pass
                    
                    # 텍스트가 있으면 텍스트 사용, 없으면 HTML에서 태그 제거 후 사용
                    final_body = body_plain.strip()
                    if not final_body and body_html:
                        import re
                        # <style>, <script> 태그와 그 내용 삭제
                        clean_text = re.sub(r'<(style|script)[^>]*>.*?</\1>', ' ', body_html, flags=re.DOTALL | re.IGNORECASE)
                        # 나머지 모든 HTML 태그 삭제
                        clean_text = re.sub(r'<[^>]+>', ' ', clean_text)
                        # HTML 엔티티 간소화 (예: &nbsp; -> 공백)
                        clean_text = re.sub(r'&[a-z0-9#]+;', ' ', clean_text, flags=re.IGNORECASE)
                        # 연속된 공백 및 줄바꿈 정리
                        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                        final_body = clean_text
                    
                    body_preview = summarize_text(final_body, limit=120) if final_body else "본문 내용 없음"
                    
                    # 결과 저장
                    mail_list.append({
                        "no": idx,
                        "sender": sender,
                        "subject": subject,
                        "body": body_preview
                    })
                    
                    # 출력 포맷팅
                    print(f"{idx}. [{sender}] {subject}")
                    print(f"   ↳ 📝 내용: {mail_list[-1]['body']}\n")
                    idx += 1
        except:
            continue

    # [4단계] 마크다운 파일로 저장
    if mail_list:
        report_dir = os.path.join(os.path.dirname(__file__), "reports")
        os.makedirs(report_dir, exist_ok=True)
        
        # 파일명 생성 (오늘 날짜)
        file_date = datetime.now(kst).strftime("%Y%m%d")
        report_filename = f"mail_summary_{file_date}.md"
        report_path = os.path.join(report_dir, report_filename)
        
        # 마크다운 내용 구성
        md_content = f"# 📊 네이버 메일 요약 리포트 ({datetime.now(kst).strftime('%Y-%m-%d')})\n\n"
        md_content += f"**오늘 도착한 메일:** 총 {len(mail_list)}개\n\n"
        md_content += "---\n\n"
        
        for mail_item in mail_list:
            md_content += f"### {mail_item['no']}. {mail_item['subject']}\n"
            md_content += f"- **발신자:** {mail_item['sender']}\n"
            md_content += f"- **내용 요약:** {mail_item['body']}\n\n"
        
        # 파일 저장
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        
        print(f"✅ 마크다운 리포트가 생성되었습니다: {report_path}")
    else:
        print("📭 오늘 도착한 메일이 없습니다.")
                
except Exception as e:
    print(f"❌ 작업 중 오류가 발생했습니다: {str(e)}")
finally:
    # 안전하게 연결 종료
    try:
        mail.logout()
    except:
        pass
