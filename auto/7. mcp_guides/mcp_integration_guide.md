# 🚀 dbt, Slack, GitHub 통합 MCP 설정 과업지시서

이 문서는 다른 PC 환경에서도 **dbt, Slack, GitHub MCP 서버** 3개를 동시에 충돌 없이 설정하고 동기화하기 위한 종합 가이드입니다. 안티그래비티 환경의 `mcp_config.json`을 수정할 때 발생할 수 있는 잠재적인 인코딩 및 경로 오류를 방지하는 모범 사례(Best Practices)를 포함합니다.

---

## 🛑 1. 충돌 방지를 위한 핵심 준수 사항 (Troubleshooting)

이전 통합 과정에서 발생했던 "Failed to load MCP servers" 및 기타 충돌 사례를 바탕으로 다음 규칙을 반드시 지켜야 합니다.

### ① 경로에 공백 포함 금지
- `DBT_PROJECT_DIR` 등 경로 설정에 사용되는 폴더명 안에는 **공백이나 특수 문자가 없어야 합니다.** 
- ❌ Bad: `C:/path/to/6. dbt project`
- ✅ Good: `C:/path/to/dbt_project`

### ② Python CP949 인코딩 오류 방지 (`PYTHONUTF8`)
- 윈도우 환경에서 `uvx`를 통해 파이썬 플러그인(dbt-mcp 등)을 실행할 때, 내부적으로 파일을 읽으면서 `UnicodeDecodeError`가 발생할 수 있습니다.
- 이를 방지하기 위해 `mcp_config.json`의 `env` 설정에 반드시 `"PYTHONUTF8": "1"`을 추가해야 합니다.

### ③ 슬래시(`/`) 기반 경로 사용
- 윈도우의 기본 백슬래시(`\`) 대신, JSON 표준에 부합하고 이스케이프 문자 오류를 일으키지 않는 **정방향 슬래시(`/`)**를 사용하여 모든 경로를 작성합니다.

### ④ 설명(`description`) 필드의 영문화 권장
- 한글 인코딩 깨짐 현상으로 인한 JSON 파싱 오류를 최소화하기 위해, `description` 등의 필드는 가급적 영문자로 작성하거나 완전히 오류가 검증된 환경에서만 한글을 사용합니다.

---

## ⚙️ 2. 환경 사전 설정 (새 PC용)

### 가. dbt 패키지 설치 (`uv` 기반)
로컬 파이썬 가상환경에 `uv`를 이용하여 dbt를 설치합니다. (프로젝트 폴더 내 `.venv` 환경 사용)
```powershell
# 가상환경 활성화가 되어 있는 상태에서 패키지 설치
uv pip install dbt-core dbt-postgres
```

### 나. dbt 프로젝트 생성
공백이 없는 이름으로 dbt 기초 프로젝트 폴더를 생성합니다. (예: `dbt_project`)
해당 폴더 안에는 반드시 `dbt_project.yml` 파일이 위치해야 합니다.

---

## 📝 3. `mcp_config.json` 설정 전문

안티그래비티 MCP의 메인 설정 파일인 `mcp_config.json`에 반영해야 할 최종 템플릿입니다. 자신의 환경에 맞게 토큰과 절대 경로만 수정하여 복사/붙여넣기 하십시오.

```json
{
  "mcpServers": {
    "slack": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-slack"
      ],
      "env": {
        "SLACK_BOT_TOKEN": "xoxb-[여기에_봇_토큰_입력]",
        "SLACK_TEAM_ID": "[여기에_팀_ID_입력]"
      },
      "description": "Slack MCP Server"
    },
    "github-mcp-server": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-github"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "github_pat_[여기에_깃허브_토큰_입력]"
      },
      "description": "GitHub MCP Server"
    },
    "dbt": {
      "command": "uvx",
      "args": [
        "dbt-mcp"
      ],
      "env": {
        "DBT_PROJECT_DIR": "C:/실제/경로/dbt_project",
        "DBT_PATH": "C:/실제/경로/.venv/Scripts/dbt.exe",
        "PYTHONUTF8": "1"
      },
      "description": "dbt MCP Server"
    }
  }
}
```

---
**작성일**: 2026-04-25
**작성자**: Antigravity AI
