# SQLite 구성 레퍼런스

이 문서는 현재 기본 채팅 런타임이 사용하는 SQLite 저장 경로와 유지보수 포인트를 정리한다.

## 1. 현재 기본 런타임

1. `ChatHistoryRepository`는 `db_client=None`일 때 내부에서 `SQLiteEngine`을 생성한다.
2. `api/chat/services/runtime.py`는 기본 생성자의 `ChatHistoryRepository`를 그대로 사용하므로 현재 서비스 기본 저장소는 SQLite다.
3. 이 경로는 세션, 메시지, request commit 저장까지 모두 담당한다.

## 2. 관련 코드

- `src/chatbot/shared/chat/repositories/history_repository.py`
- `src/chatbot/integrations/db/engines/sqlite/engine.py`
- `src/chatbot/integrations/db/engines/sqlite/connection.py`
- `src/chatbot/integrations/db/engines/sqlite/schema_manager.py`
- `src/chatbot/core/chat/const/settings.py`

## 3. 필요한 환경 변수

```env
CHAT_DB_PATH=data/db/chat/chat_history.sqlite
SQLITE_BUSY_TIMEOUT_MS=5000
```

## 4. 운영 점검 포인트

1. 상위 디렉터리 쓰기 권한이 있어야 한다.
2. 파일 단일 노드 저장소이므로 다중 프로세스/고부하 쓰기 환경에서는 잠금 경합이 생길 수 있다.
3. 벡터 검색은 기본 SQLite 엔진의 책임이 아니다.

## 5. 추가 개발과 확장 시 주의점

1. SQLite를 다른 엔진으로 교체하려면 setup 문서만 바꾸는 것이 아니라 `runtime.py` 조립 코드를 함께 변경해야 한다.
2. 스키마를 추가할 때는 `build_chat_*_schema()`와 `document_mapper.py`를 같이 검토해야 한다.
3. 백업/이관은 파일 복사보다 애플리케이션 중지 시점과 잠금 상태를 먼저 고려해야 한다.

## 6. 관련 문서

- `docs/integrations/db/overview.md`
- `docs/integrations/db/engines/sqlite/engine.md`
- `docs/setup/env.md`
- `docs/setup/postgresql_pgvector.md`
