import os
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# .env 파일 로드 (통합 환경 설정 파일 경로 지정)
dotenv_path = r"c:\ICB7\.venv\.env"
load_dotenv(dotenv_path=dotenv_path)

# 환경 변수에서 토큰 가져오기
slack_token = os.environ.get("SLACK_BOT_TOKEN")
channel_id = os.environ.get("SLACK_CHANNEL_ID")

def test_slack_connection():
    # 토큰 확인
    if not slack_token or "your_xoxb_token" in slack_token:
        print("[오류] .env 파일에 올바른 SLACK_BOT_TOKEN을 입력해 주세요.")
        return

    # 클라이언트 초기화
    client = WebClient(token=slack_token)

    try:
        # 1. 연결 테스트 (auth.test)
        response = client.auth_test()
        bot_name = response["user"]
        print(f"[성공] 슬랙 연결 완료! 봇 이름: {bot_name}")

        # 2. 메시지 전송 테스트 (chat.postMessage)
        if channel_id and "your_channel_id" not in channel_id:
            print(f"채널({channel_id})로 테스트 메시지를 전송합니다...")
            client.chat_postMessage(
                channel=channel_id,
                text=f"안녕하세요! {bot_name}이(가) 성공적으로 가동되었습니다. 🚀"
            )
            print("[성공] 테스트 메시지가 전송되었습니다.")
        else:
            print("[알림] SLACK_CHANNEL_ID가 설정되지 않아 메시지 전송 테스트는 건너뜁니다.")

    except SlackApiError as e:
        print(f"[오류] 슬랙 API 에러 발생: {e.response['error']}")
    except Exception as e:
        print(f"[오류] 예상치 못한 오류 발생: {e}")

if __name__ == "__main__":
    test_slack_connection()
