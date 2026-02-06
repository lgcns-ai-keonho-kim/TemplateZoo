# 로깅 가이드

이 문서는 `src/base_template/shared/logging` 모듈을 설명합니다.

**목적**

- 로깅 인터페이스와 기본 저장소를 제공합니다.
- 실행 흐름과 컨텍스트를 구조화해 기록합니다.

**구성 요소**

- `Logger`: 로거 인터페이스
- `InMemoryLogger`: 기본 로거 구현체
- `LogRepository`: 저장소 인터페이스
- `InMemoryLogRepository`: 인메모리 저장소 (내부 구현)
- `DBLogRepository`: DB 기반 로그 저장소
- `LLMLogRepository`: LLM 로그 전용 DB 저장소
- `LogContext`, `LogRecord`, `LogLevel`: 로그 모델

## 기본 사용법

```python
from base_template.shared.logging import create_default_logger, LogContext

logger = create_default_logger("app")
logger.info("서비스 시작")

context = LogContext(trace_id="trace-1", request_id="req-1")
logger.info("요청 수신", context=context)
```

## 컨텍스트 병합

- `with_context()`는 기존 컨텍스트와 새 컨텍스트를 병합합니다.
- 같은 키는 새 컨텍스트가 우선합니다.

```python
logger = create_default_logger("app")
base = LogContext(trace_id="t1", tags={"env": "dev"})
child = logger.with_context(base)
child.info("컨텍스트 포함 로그")
```

## 저장소 접근

- 기본 로거는 인메모리 저장소를 사용합니다.
- `InMemoryLogger.repository.list()`로 로그 목록을 조회할 수 있습니다.

```python
records = logger.repository.list()
for record in records:
    print(record.level, record.message)
```

## DBLogRepository 사용

- `DBClient`를 주입해 로그를 DB에 저장할 수 있습니다.
- 기본 컬렉션 이름은 `logs`입니다.
- 기본 스키마는 모든 DB에서 동작하도록 `TEXT` 타입을 사용합니다.

```python
from base_template.integrations.db import DBClient
from base_template.integrations.db.engines.sqlite import SqliteVectorEngine
from base_template.shared.logging.db_repository import DBLogRepository
from base_template.shared.logging import InMemoryLogger

engine = SqliteVectorEngine(database_path="data/db/app.sqlite")
db_client = DBClient(engine)
db_client.connect()

repository = DBLogRepository(db_client, collection="app_logs")
logger = InMemoryLogger(name="app", repository=repository)
logger.info("DB 저장 로그")
```

## LLMLogRepository 사용

- LLM 전용 로그 컬럼 스키마를 제공합니다.
- `LLMClient`에서 자동으로 사용되며, 필요하면 직접 주입할 수도 있습니다.

## FileLogRepository 사용

- 파일 기반 로깅은 `base_template.integrations.fs` 모듈에 있습니다.
- 로그를 `base_dir/YYYYMMDD/UUID.log` 형식으로 저장합니다.

```python
from base_template.integrations.fs import FileLogRepository, LocalFSEngine
from base_template.shared.logging import InMemoryLogger

repository = FileLogRepository(base_dir="data/logs", engine=LocalFSEngine())
logger = InMemoryLogger(name="app", repository=repository)
logger.info("파일 저장 로그")
```

## 확장 포인트

- `LogRepository`를 구현하면 파일/DB/외부 로깅 시스템으로 확장할 수 있습니다.
- 커스텀 로거는 `Logger` 인터페이스만 만족하면 됩니다.
