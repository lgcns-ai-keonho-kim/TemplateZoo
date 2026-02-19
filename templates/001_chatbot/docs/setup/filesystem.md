# 파일 시스템 연동 가이드

이 문서는 `src/chatbot/integrations/fs`를 이용해 로그를 파일로 저장하는 방법과,
원격 스토리지 엔진으로 확장할 때 필요한 구현 포인트를 정리한다.

## 1. 적용 범위

1. 로컬 디스크에 로그를 영속 저장
2. 파일 기반 로그 파이프라인(수집/백업/분석) 구성
3. `BaseFSEngine` 인터페이스를 구현한 커스텀 스토리지 연동

## 2. 관련 스크립트

| 경로 | 역할 |
| --- | --- |
| `src/chatbot/integrations/fs/base/engine.py` | 파일 엔진 인터페이스 |
| `src/chatbot/integrations/fs/engines/local.py` | 로컬 파일 시스템 구현 |
| `src/chatbot/integrations/fs/file_repository.py` | 로그 파일 저장소 |
| `src/chatbot/shared/logging/logger.py` | Logger/LogRepository 인터페이스 |
| `src/chatbot/integrations/llm/client.py` | 로깅 저장소를 주입해 LLM 호출 로그 저장 가능 |

## 3. 기본 동작 구조

`FileLogRepository`의 저장 규칙:

1. 기본 디렉터리: 생성자 인자로 받는 `base_dir`
2. 하위 경로: `<base_dir>/<YYYYMMDD>/<uuid>.log`
3. 파일 내용: `LogRecord` JSON 직렬화 문자열
4. 인코딩: 기본 `utf-8`

조회 규칙:

1. `base_dir` 하위 `.log` 파일을 재귀 탐색
2. JSON 파싱 + 모델 검증 성공 레코드 수집
3. `timestamp` 오름차순 정렬 후 반환
4. 손상 파일은 WARNING 레벨 fallback 레코드로 대체

## 4. 로컬 파일 시스템 연동 절차

### 4-1. 저장 디렉터리 설계

권장 예시:

1. 개발: `data/logs/dev`
2. 스테이징: `data/logs/stg`
3. 운영: `/var/log/<service>` 또는 마운트 볼륨 경로

### 4-2. 코드 조립 예시

```python
from chatbot.integrations.fs import FileLogRepository
from chatbot.shared.logging import InMemoryLogger

file_repository = FileLogRepository(base_dir="data/logs")
logger = InMemoryLogger(name="app-logger", repository=file_repository)

logger.info("서비스 시작")
logger.error("실패 시나리오 기록")
```

### 4-3. LLM 로그 저장소로 연결 예시

```python
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from chatbot.integrations.fs import FileLogRepository
from chatbot.integrations.llm import LLMClient

repo = FileLogRepository(base_dir="data/logs/llm")
model = ChatOpenAI(model="gpt-4o-mini", api_key=SecretStr("..."))

client = LLMClient(
    model=model,
    name="chat-response-llm",
    log_repository=repo,
    log_payload=True,
    log_response=True,
)
```

## 5. 커스텀 스토리지 엔진 확장

`BaseFSEngine`을 구현하면 저장소 교체가 가능하다.

필수 메서드:

1. `write_text`
2. `read_text`
3. `list_files`
4. `exists`
5. `mkdir`
6. `move`
7. `copy`

구현 예시 뼈대:

```python
from chatbot.integrations.fs.base import BaseFSEngine


class RemoteFSEngine(BaseFSEngine):
    @property
    def name(self) -> str:
        return "remote"

    def write_text(self, path: str, content: str, encoding: str) -> None:
        ...

    def read_text(self, path: str, encoding: str) -> str:
        ...

    def list_files(self, base_dir: str, recursive: bool = False, suffix: str | None = None) -> list[str]:
        ...

    def exists(self, path: str) -> bool:
        ...

    def mkdir(self, path: str, exist_ok: bool = True) -> None:
        ...

    def move(self, src: str, dst: str) -> None:
        ...

    def copy(self, src: str, dst: str) -> None:
        ...
```

주입:

```python
engine = RemoteFSEngine()
repository = FileLogRepository(base_dir="logs", engine=engine)
```

## 6. 운영 설계 포인트

1. `base_dir`는 로그 파일 증가량을 고려해 별도 볼륨으로 분리한다.
2. 날짜 디렉터리(`YYYYMMDD`) 단위 보관/삭제 정책을 정의한다.
3. 파일 권한(읽기/쓰기 사용자)을 서비스 계정 기준으로 고정한다.
4. 아카이빙 시 `move`/`copy` 동작이 원자성을 보장하는지 검토한다.

## 7. 장애 대응

| 증상 | 원인 후보 | 확인 경로 | 조치 |
| --- | --- | --- | --- |
| 로그 파일 미생성 | 디렉터리 권한/경로 오류 | `base_dir`, OS 권한 | 디렉터리 생성/권한 수정 |
| 같은 파일명 충돌 | 외부에서 고정 파일명 사용 | `engines/local.py` (`open(..., "x")`) | UUID 기반 파일명 유지 |
| 조회 시 WARNING 로그 다수 | 파일 손상/중간 쓰기 실패 | `FileLogRepository._fallback_record` | 파일 생성 경로/쓰기 실패 원인 점검 |
| 로그 목록 누락 | suffix/recursive 조건 오류 | `list_files` 구현 | 조건값 점검, 엔진 구현 보완 |

## 8. 소스 매칭 체크리스트

1. 인터페이스 메서드 목록이 `base/engine.py`와 일치하는가
2. 저장 경로 규칙이 `file_repository.py` 구현과 일치하는가
3. fallback 레코드 메타정보(`path`, `reason`)가 문서 설명과 일치하는가
4. 커스텀 엔진 주입 방식이 `FileLogRepository(engine=...)` 패턴과 일치하는가

## 9. 관련 문서

- `docs/setup/env.md`
- `docs/integrations/fs.md`
- `docs/shared/logging.md`
