# 로깅 아키텍처 명세

이 문서는 `src/base_template/shared/logging`의 모델, 로거, 저장소 계층을 정의한다.

## 구성 요소

| 계층 | 파일 | 역할 |
| --- | --- | --- |
| 로그 모델 | `shared/logging/models.py` | `LogLevel`, `LogContext`, `LogRecord` |
| 로거 인터페이스 | `shared/logging/logger.py` | `Logger`, `LogRepository` 추상 계약 |
| 기본 구현 | `shared/logging/logger.py` | `InMemoryLogger`, `InMemoryLogRepository` |
| DB 저장소 | `shared/logging/db_repository.py` | 일반 로그 DB 저장 |
| LLM 저장소 | `shared/logging/llm_repository.py` | LLM 전용 메타데이터 DB 저장 |

## 기본 동작

1. `create_default_logger(name)`는 `InMemoryLogger`를 생성한다.
2. `InMemoryLogger.log()`는 `LogRecord`를 생성해 `LogRepository.add()`로 전달한다.
3. `with_context()`는 기존 컨텍스트와 신규 컨텍스트를 병합한 새 로거를 반환한다.

## 저장소 확장 규칙

`LogRepository` 구현체는 아래 메서드를 반드시 구현한다.

- `add(record: LogRecord) -> None`
- `list() -> list[LogRecord]`

### DB 저장소

- `DBLogRepository`: 일반 로그 컬럼 스키마 사용
- `LLMLogRepository`: 모델명/토큰/비용 등 LLM 컬럼 스키마 사용
- 두 저장소 모두 내부에서 `DBClient`를 사용한다.

## 의존성

```text
shared/logging/logger
  -> shared/logging/models

shared/logging/db_repository
  -> shared/logging/logger
  -> integrations/db/client

shared/logging/llm_repository
  -> shared/logging/logger
  -> integrations/db/client
```

## 장애 처리 원칙

1. 로깅 저장소 오류는 비즈니스 로직 오류와 분리한다.
2. `LLMClient`는 로깅 실패가 본 호출을 중단시키지 않도록 보호한다.
3. 저장소 레코드 파싱 실패는 해당 레코드만 건너뛴다.

## 예시

```python
from base_template.shared.logging import create_default_logger, LogContext

logger = create_default_logger("app")
logger.info("start", context=LogContext(request_id="req-1"))
```
