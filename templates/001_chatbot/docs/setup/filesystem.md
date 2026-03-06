# 파일 시스템 연동 레퍼런스

이 문서는 `src/chatbot/integrations/fs`를 이용해 로그를 파일로 저장하는 방법과,
원격 스토리지 엔진으로 확장할 때 필요한 구현 포인트를 정리한다.

## 1. 적용 범위

1. 로컬 디스크 로그 영속 저장
2. 파일 기반 로그 파이프라인(수집/백업/분석)
3. `BaseFSEngine` 기반 커스텀 스토리지 연동

## 2. 관련 스크립트

| 경로 | 역할 |
| --- | --- |
| `src/chatbot/integrations/fs/base/engine.py` | 파일 엔진 인터페이스 |
| `src/chatbot/integrations/fs/engines/local.py` | 로컬 파일 시스템 구현 |
| `src/chatbot/integrations/fs/file_repository.py` | 로그 파일 저장소 |
| `src/chatbot/integrations/llm/client.py` | LLM 로그 저장소 주입 가능 |

## 3. 기본 동작 구조

`FileLogRepository` 저장 동작:

1. 경로: `<base_dir>/<YYYYMMDD>/<uuid>.log`
2. 내용: `LogRecord` JSON 문자열
3. 인코딩: `utf-8`

조회 동작:

1. `.log` 파일 재귀 탐색
2. JSON 파싱/모델 검증 성공 레코드 수집
3. timestamp 오름차순 정렬
4. 손상 파일은 WARNING fallback 레코드로 대체

## 4. 로컬 연동 예시

```python
from chatbot.integrations.fs import FileLogRepository
from chatbot.shared.logging import InMemoryLogger

file_repository = FileLogRepository(base_dir="data/logs")
logger = InMemoryLogger(name="app-logger", repository=file_repository)

logger.info("서비스 시작")
```

## 5. LLM 로그 저장 예시(Gemini)

```python
from langchain_google_genai import ChatGoogleGenerativeAI

from chatbot.integrations.fs import FileLogRepository
from chatbot.integrations.llm import LLMClient

repo = FileLogRepository(base_dir="data/logs/llm")
model = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    project="your-project",
    thinking_level="minimal",  # 정책 기준
)

client = LLMClient(
    model=model,
    name="chat-response-llm",
    log_repository=repo,
    log_payload=True,
    log_response=True,
)
```

## 6. 장애 대응

| 증상 | 원인 후보 | 확인 경로 | 조치 |
| --- | --- | --- | --- |
| 로그 파일 미생성 | 디렉터리 권한/경로 오류 | `base_dir`, OS 권한 | 디렉터리 생성/권한 수정 |
| 조회 시 WARNING 다수 | 파일 손상/중간 쓰기 실패 | `_fallback_record` | 생성 경로/쓰기 실패 원인 점검 |
| 로그 목록 누락 | suffix/recursive 조건 오류 | `list_files` 구현 | 조건값 점검 |

## 7. 관련 문서

- `docs/integrations/fs.md`
- `docs/integrations/llm.md`
- `docs/setup/env.md`
- `docs/setup/troubleshooting.md`
