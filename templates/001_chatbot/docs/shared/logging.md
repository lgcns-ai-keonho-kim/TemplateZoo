# Shared Logging 레퍼런스

`src/chatbot/shared/logging`은 로거 인터페이스와 로그 저장소 구현을 제공한다. 현재 기본 로거는 인메모리 저장소 기반이며, 필요하면 DB 저장소를 주입할 수 있다.

## 1. 코드 설명

핵심 구성:

1. 모델: `LogLevel`, `LogContext`, `LogRecord`
2. 인터페이스: `Logger`, `LogRepository`
3. 기본 구현: `InMemoryLogger`, `InMemoryLogRepository`
4. DB 저장소: `DBLogRepository`
5. LLM 전용 저장소: `LLMLogRepository`

기본 로거 생성:

1. `create_default_logger(name)` -> `InMemoryLogger`
2. `LOG_STDOUT`가 없으면 stdout 출력은 기본적으로 꺼져 있다
3. `LOG_STDOUT`가 `1`, `true`, `yes`, `on`이면 JSON 로그 출력

`DBLogRepository`는 일반 로그 컬럼 스키마를, `LLMLogRepository`는 모델명/토큰/비용 컬럼을 포함한 스키마를 사용한다.

## 2. 유지보수 포인트

1. `InMemoryLogger.with_context()`는 기존 컨텍스트와 새 컨텍스트를 병합한 새 로거를 반환한다.
2. DB 저장소는 손상된 레코드를 조회 시 조용히 건너뛴다. 저장 포맷이 틀어졌을 때 일부 로그가 사라진 것처럼 보일 수 있다.
3. `LLMLogRepository`는 `metadata["usage_metadata"]`를 컬럼으로 분해한다. LLM 호출 메타데이터 키를 바꾸면 비용 추적이 깨질 수 있다.

## 3. 추가 개발/확장 가이드

1. 로그 필드를 더 늘릴 때는 모델, 저장소 직렬화, 역직렬화 세 군데를 같이 수정해야 한다.
2. 운영 로그와 LLM 사용량 로그를 분리하고 싶다면 현재처럼 저장소 레벨에서 컬렉션을 나누는 구조를 유지하는 편이 명확하다.

## 4. 관련 코드

- `src/chatbot/shared/logging/logger.py`
- `src/chatbot/shared/logging/db_repository.py`
- `src/chatbot/shared/logging/llm_repository.py`
- `src/chatbot/integrations/llm/client.py`
