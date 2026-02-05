# LLM 클라이언트 가이드

이 문서는 `src/base_template/integrations/llm/client.py`의 `LLMClient` 사용 방법을 설명합니다.

**목적**
- LangChain의 `BaseChatModel`을 상속해 기존 메서드(`invoke`, `ainvoke`, `stream`, `astream`)를 그대로 제공합니다.
- 호출 로깅과 예외 래핑을 공통 정책으로 처리합니다.
- 필요하면 DB 저장소를 로깅 백엔드로 사용할 수 있습니다.

**핵심 구성**
- 클래스: `LLMClient`
- 베이스: `BaseChatModel`
- 예외: `BaseAppException`, `ExceptionDetail`

**기본 사용법**

```python
from base_template.integrations.llm import LLMClient
from base_template.shared.logging import create_default_logger

logger = create_default_logger("llm")
client = LLMClient(model=langchain_chat_model, name="llm-main", logger=logger)

result = client.invoke("간단한 질문")
```

**비동기/스트리밍 사용법**

```python
# 비동기 호출
result = await client.ainvoke("질문")

# 스트리밍 호출
for chunk in client.stream("질문"):
    print(chunk)
```

**로깅 정책**
- 호출 시작/성공/실패 로그를 자동으로 기록합니다.
- 기본 메타데이터: 액션, 모델 이름, 메시지 수, stop 여부, 스트리밍 여부
- `log_payload=True`이면 메시지 내용을 로그에 포함합니다.
- `log_response=True`이면 결과를 로그에 포함합니다.

**로깅 엔진 주입 규칙**
- `logging_engine`에는 다음 타입만 허용됩니다.
- DB 엔진: `BaseDBEngine` 구현체
- 로거: `Logger` 구현체
- 저장소: `LogRepository` 구현체
- 기본 컬렉션 이름은 `llm_logs`입니다.
- 내부적으로 `LLMLogRepository`가 사용됩니다.
- 기본 스키마는 컬럼 분리 방식으로 저장됩니다.

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

```python
from base_template.integrations.db.engines.postgres import PostgresEngine

engine = PostgresEngine(dsn="postgresql://user:pass@localhost:5432/app")
client = LLMClient(
    model=langchain_chat_model,
    logging_engine=engine,
)
```

**자동 연결 규칙**
- `LLMClient`가 DB 엔진을 통해 로깅할 때는 자동으로 `connect()`를 호출합니다.
- 파일/메모리 로깅에는 DB 연결이 필요하지 않습니다.

**파일 로깅 예시**
```python
from base_template.integrations.fs import FileLogRepository

file_repo = FileLogRepository(base_dir="data/logs")
client = LLMClient(
    model=langchain_chat_model,
    logging_engine=file_repo,
)
```

**메모리 로깅 예시**
```python
from base_template.shared.logging import InMemoryLogger

memory_logger = InMemoryLogger(name="llm")
client = LLMClient(
    model=langchain_chat_model,
    logging_engine=memory_logger,
)
```

**LLM 메타데이터 표준화**
- `usage_metadata`는 LangSmith 표준 스키마를 따른다고 가정합니다.
- 기본 필드 예시: `input_tokens`, `output_tokens`, `total_tokens`, `input_cost`, `output_cost`, `total_cost`
- 상세 필드는 `input_token_details`, `output_token_details`, `input_cost_details`, `output_cost_details`로 저장합니다.
- 값이 없으면 `None`으로 저장되며 이후 보강 가능합니다.

**컨텍스트 자동 주입**
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

**오류 처리 규칙**
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

**주의 사항**
- DB 저장소를 사용할 경우 DB 연결/스키마 준비가 필요합니다.
- 민감한 데이터는 `log_payload`/`log_response`를 비활성화한 상태로 운영하는 것을 권장합니다.
