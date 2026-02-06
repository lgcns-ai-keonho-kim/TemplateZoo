# LLM 클라이언트 가이드

이 문서는 `src/base_template/integrations/llm/client.py`의 `LLMClient` 사용 방법을 설명합니다.

**목적**

- LangChain의 `BaseChatModel`을 감싸 호출 로깅과 예외 처리를 표준화합니다.
- 기존 메서드(`invoke`, `ainvoke`, `stream`, `astream`)를 그대로 제공합니다.

**핵심 구성**

- 클래스: `LLMClient`
- 베이스: `BaseChatModel`
- 예외: `BaseAppException`, `ExceptionDetail`

## 기본 사용법

```python
from base_template.integrations.llm import LLMClient
from base_template.shared.logging import create_default_logger

logger = create_default_logger("llm")
client = LLMClient(model=langchain_chat_model, name="llm-main", logger=logger)

result = client.invoke("간단한 질문")
```

## 비동기/스트리밍 사용법

```python
# 비동기 호출
result = await client.ainvoke("질문")

# 스트리밍 호출
for chunk in client.stream("질문"):
    print(chunk)
```

## 로깅 정책

- 호출 시작/성공/실패 로그를 자동으로 기록합니다.
- 기본 메타데이터: 액션, 모델 이름, 메시지 수, stop 여부, 스트리밍 여부
- `log_payload=True`이면 메시지 내용을 로그에 포함합니다.
- `log_response=True`이면 결과를 로그에 포함합니다.

## 로깅 엔진 주입 규칙

`logging_engine`에는 다음 타입만 허용됩니다.

- DB 엔진: `BaseDBEngine` 구현체
- 로거: `Logger` 구현체
- 저장소: `LogRepository` 구현체

### DB 엔진 주입 예시

```python
from base_template.integrations.db.engines.sqlite import SqliteVectorEngine
from base_template.integrations.llm import LLMClient

engine = SqliteVectorEngine(database_path="data/db/app.sqlite")
client = LLMClient(
    model=langchain_chat_model,
    name="llm-main",
    logging_engine=engine,
    log_collection="llm_logs",
)
```

### 파일/메모리 로깅 예시

```python
from base_template.integrations.fs import FileLogRepository
from base_template.shared.logging import InMemoryLogger

file_repo = FileLogRepository(base_dir="data/logs")
client = LLMClient(model=langchain_chat_model, logging_engine=file_repo)

memory_logger = InMemoryLogger(name="llm")
client = LLMClient(model=langchain_chat_model, logging_engine=memory_logger)
```

## 백그라운드 러너

- 스트리밍 성공 로그는 `background_runner`로 실행됩니다.
- 함수 시그니처는 `fn, *args` 형태입니다.

```python
def inline_runner(fn, *args):
    fn(*args)

client = LLMClient(
    model=langchain_chat_model,
    background_runner=inline_runner,
)
```

## 컨텍스트 자동 주입

- `context_provider`를 주입하면 사용자 ID/요청 ID를 자동으로 로그에 포함합니다.

```python
from base_template.shared.logging import LogContext

def context_provider():
    return LogContext(request_id="req-123", user_id="user-1")

client = LLMClient(
    model=langchain_chat_model,
    context_provider=context_provider,
)
```

## 오류 처리 규칙

- 내부 호출 실패 시 `BaseAppException`으로 래핑합니다.
- 액션별 에러 코드 예시
  - `LLM_INVOKE_ERROR`
  - `LLM_AINVOKE_ERROR`
  - `LLM_STREAM_ERROR`
  - `LLM_ASTREAM_ERROR`

```python
from base_template.shared.exceptions import BaseAppException

try:
    client.invoke("질문")
except BaseAppException as exc:
    print(exc.message)
    print(exc.detail.code)
```

## 주의 사항

- DB 저장소를 사용할 경우 DB 연결/스키마 준비가 필요합니다.
- 민감한 데이터는 `log_payload`/`log_response`를 비활성화한 상태로 운영하는 것을 권장합니다.
