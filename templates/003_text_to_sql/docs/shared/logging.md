# Shared Logging 가이드

이 문서는 `src/text_to_sql/shared/logging`의 로깅 인터페이스와 저장소 구현을 코드 기준으로 정리한다.

## 1. 용어 정리

| 용어 | 의미 | 관련 스크립트 |
| --- | --- | --- |
| Logger | 로그 기록 인터페이스 | `logger.py` |
| LogRepository | 로그 저장소 인터페이스 | `logger.py` |
| InMemoryLogger | 기본 로거 구현체 | `logger.py` |
| LogRecord | 단일 로그 레코드 모델 | `models.py` |
| LogContext | trace/span/request/user 정보를 담는 컨텍스트 | `models.py` |
| DBLogRepository | 일반 로그 DB 저장소 | `db_repository.py` |
| LLMLogRepository | LLM 메타데이터 전용 DB 저장소 | `llm_repository.py` |

## 2. 관련 스크립트

| 파일 | 역할 |
| --- | --- |
| `src/text_to_sql/shared/logging/models.py` | `LogLevel`, `LogContext`, `LogRecord` 정의 |
| `src/text_to_sql/shared/logging/logger.py` | Logger/Repository 인터페이스, InMemory 구현, 기본 로거 팩토리 |
| `src/text_to_sql/shared/logging/db_repository.py` | 일반 로그 DB 저장 구현 |
| `src/text_to_sql/shared/logging/llm_repository.py` | LLM 로그 DB 저장 구현 |
| `src/text_to_sql/shared/logging/__init__.py` | 공개 API 제공 |

## 3. 인터페이스 정의

## 3-1. LogLevel

지원 레벨:

1. `DEBUG`
2. `INFO`
3. `WARNING`
4. `ERROR`
5. `CRITICAL`

## 3-2. LogRecord

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `level` | `LogLevel` | 로그 레벨 |
| `message` | `str` | 로그 메시지 |
| `timestamp` | `datetime` | 기록 시각 |
| `logger_name` | `str` | 로거 이름 |
| `context` | `LogContext \| None` | 호출 컨텍스트 |
| `metadata` | `dict[str, Any]` | 부가 메타데이터 |

## 3-3. Logger 메서드

핵심 메서드:

1. `log(level, message, context, metadata)`
2. `with_context(context)`
3. 편의 메서드: `debug`, `info`, `warning`, `error`, `critical`

## 4. 기본 구현 동작

## 4-1. InMemoryLogger

1. 기본 저장소는 `InMemoryLogRepository`다.
2. `with_context`는 base context를 병합한 새 로거를 반환한다.
3. `LOG_STDOUT=true`이면 JSON 로그를 stdout으로 출력한다.

stdout JSON 출력 필드:

1. `timestamp`
2. `level`
3. `logger`
4. `message`
5. `context` 선택
6. `metadata` 선택

## 4-2. DBLogRepository

1. `LogRecord`를 DB Document로 변환해 `upsert`한다.
2. `auto_create`면 기본 `logs` 스키마를 생성한다.
3. 손상된 레코드는 조회 시 스킵한다.

## 4-3. LLMLogRepository

1. LLM 사용량 메타데이터를 전용 컬럼으로 분해한다.
2. `usage_metadata` 하위 필드를 토큰/비용 컬럼에 저장한다.
3. DB 조회 시 다시 `LogRecord` 구조로 복원한다.

## 5. 선택 기준

1. 빠른 개발/테스트: `create_default_logger` + InMemory
2. 일반 운영 로그 적재: `DBLogRepository`
3. LLM 호출 비용/사용량 추적: `LLMLogRepository`

## 6. 연동 규칙

1. 호출 측은 `Logger` 인터페이스에만 의존한다.
2. 저장소 예외가 나도 핵심 비즈니스 흐름을 과도하게 중단하지 않도록 설계한다.
3. 컨텍스트는 `request_id`, `trace_id` 중심으로 일관되게 전달한다.

## 7. 트러블슈팅

| 증상 | 원인 후보 | 확인 스크립트 | 조치 |
| --- | --- | --- | --- |
| 로그가 메모리에만 쌓임 | DB 저장소 미주입 | `logger.py` 초기화 지점 | repository 주입 경로 확인 |
| stdout 로그 미출력 | `LOG_STDOUT` 값 미설정 | `_read_emit_stdout_env` | 환경 변수값 확인 |
| LLM 비용 필드가 비어 있음 | usage_metadata 누락 | `llm_repository.py` | metadata 수집 경로 점검 |
| 조회 시 일부 로그가 사라짐 | 손상 레코드 스킵 | `db_repository.py`/`llm_repository.py` | 저장 포맷/파싱 오류 점검 |

## 8. 관련 문서

- `docs/shared/overview.md`
- `docs/shared/exceptions.md`
- `docs/shared/runtime.md`
