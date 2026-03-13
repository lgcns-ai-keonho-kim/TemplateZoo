# Shared Logging 레퍼런스

`src/chatbot/shared/logging`은 로거 인터페이스와 로그 저장소 구현을 제공한다.

## 1. 구성 요소

핵심 타입:

1. 모델: `LogLevel`, `LogContext`, `LogRecord`
2. 인터페이스: `Logger`, `LogRepository`
3. 기본 구현: `InMemoryLogger`
4. 내부 기본 저장소: `InMemoryLogRepository`
5. DB 저장소: `DBLogRepository`
6. LLM 전용 저장소: `LLMLogRepository`

## 2. 기본 로거 동작

`create_default_logger(name)`는 `InMemoryLogger`를 반환한다.

특징:

1. 저장소를 주입하지 않으면 내부 `InMemoryLogRepository`를 사용한다.
2. `LOG_STDOUT`가 없으면 stdout 출력은 기본적으로 꺼져 있다.
3. `LOG_STDOUT=1`, `true`, `yes`, `on`일 때 JSON 로그를 stdout에 출력한다.
4. `with_context()`는 기존 컨텍스트를 병합한 새 로거를 만든다.

## 3. DB 저장소 계열

### 3-1. `DBLogRepository`

1. 일반 로그 레코드를 DB 컬럼 구조로 저장한다.
2. 손상된 문서를 읽으면 조용히 건너뛴다.

### 3-2. `LLMLogRepository`

1. `metadata["usage_metadata"]`를 컬럼으로 분해해 저장한다.
2. 모델명, provider, 토큰, 비용 메타데이터를 함께 다룬다.
3. LLM 호출 메타데이터 키가 바뀌면 비용/사용량 추적이 깨질 수 있다.

## 4. 유지보수 포인트

1. 로그 필드를 늘릴 때는 모델, 직렬화, 역직렬화를 같이 수정해야 한다.
2. `LogContext.tags`는 병합 가능한 자유형 태그 집합이다.
3. 기본 로거와 저장소 fallback은 조용하지만, DB/LLM 저장소는 스키마와 DBClient 계약에 의존한다.

## 5. 관련 문서

- `docs/integrations/fs/overview.md`
- `docs/integrations/llm/overview.md`
