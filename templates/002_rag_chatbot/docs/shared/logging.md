# Shared Logging

## 공개 구성

- `Logger`, `InMemoryLogger`
- `LogRepository`, `InMemoryLogRepository`
- `DBLogRepository`
- `LLMLogRepository`
- `EmbeddingLogRepository`
- `create_default_logger()`

## 기본 동작

- `create_default_logger()`는 `InMemoryLogger`를 만든다.
- `LOG_STDOUT`가 `1`, `true`, `yes`, `on`이면 stdout JSON 로그를 출력한다.
- Chat 기본 런타임은 `service_logger`, `llm_logger`를 생성해 실행 로그를 남긴다.

## 확장 경로

- LLM과 임베딩 로그는 DB 저장소로 분리할 수 있다.
- 파일 로그 저장이 필요하면 `src/rag_chatbot/integrations/fs/file_repository.py`의 `FileLogRepository`를 별도로 조립해 사용한다.
