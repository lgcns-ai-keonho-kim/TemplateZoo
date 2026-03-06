# connection 모듈

이 문서는 `src/rag_chatbot/integrations/db/engines/sqlite/connection.py`의 역할과 주요 구성을 설명한다.

## 1. 목적

SQLite 연결 관리 모듈을 제공한다.

## 2. 설명

연결 초기화/종료와 PRAGMA 적용을 담당한다.

## 3. 디자인 패턴

매니저 패턴

## 4. 주요 구성

- 클래스 `SqliteConnectionManager`
  주요 메서드: `supports_vector_search`, `connect`, `close`, `ensure_connection`

## 5. 연동 포인트

- `src/rag_chatbot/integrations/db/engines/sqlite/engine.py`

## 6. 관련 문서

- `docs/integrations/db/README.md`
- `docs/integrations/overview.md`
