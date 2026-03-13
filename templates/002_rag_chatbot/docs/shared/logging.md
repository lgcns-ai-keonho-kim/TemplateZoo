# Shared Logging 가이드

이 문서는 `src/rag_chatbot/shared/logging`의 로거, 저장소, 로그 모델이 현재 어떻게 쓰이는지 설명한다.

## 1. 현재 구성

- `Logger`, `InMemoryLogger`: 애플리케이션 로그 인터페이스와 기본 구현
- `LogRepository`, `InMemoryLogRepository`: 저장소 포트와 메모리 구현
- `DBLogRepository`, `LLMLogRepository`, `EmbeddingLogRepository`: DB 기반 로그 저장소
- `create_default_logger()`: `LOG_STDOUT` 환경 변수에 따라 stdout 출력 여부를 결정한다.

## 2. 현재 사용 경로

- Chat runtime 조립 시 `service_logger`, `llm_logger`가 생성된다.
- LLMClient와 EmbeddingClient는 선택적으로 저장소/DB 엔진을 받아 호출 로그를 남길 수 있다.
- 파일 기반 로그가 필요하면 `FileLogRepository`를 별도로 조립한다.

## 3. 유지보수/추가개발 포인트

- 로그 저장소를 바꿀 때는 logger 인터페이스보다 repository 계약을 먼저 유지하는 편이 안전하다.
- payload/response 전문 저장은 비용이 크므로 운영 환경에서는 수집 범위를 구분하는 편이 좋다.
- `request_id`, `session_id` 같은 컨텍스트 키를 일관되게 넘겨야 장애 추적이 쉬워진다.

## 4. 관련 문서

- `docs/integrations/llm/client.md`
- `docs/integrations/embedding/client.md`
- `docs/setup/filesystem.md`
