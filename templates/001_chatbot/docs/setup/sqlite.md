# SQLite 구성 가이드

이 문서는 현재 프로젝트에서 SQLite를 기본 CRUD 저장소로 사용하는 방법을 정리한다.
이 문서의 범위는 Chat 이력/세션 저장이며, 벡터 검색은 포함하지 않는다.

## 1. 적용 범위

1. 로컬 단일 노드 기본 실행
2. Chat 세션/메시지/커밋 저장
3. SQLite 파일 경로/권한/잠금 설정 점검

## 2. 관련 스크립트

| 경로 | 역할 |
| --- | --- |
| `src/chatbot/core/chat/const/settings.py` | Chat 기본 DB 경로(`CHAT_DB_PATH`) |
| `src/chatbot/shared/chat/repositories/history_repository.py` | 기본 저장소 조립 |
| `src/chatbot/integrations/db/engines/sqlite/engine.py` | SQLite CRUD/일반 조회 |
| `src/chatbot/integrations/db/engines/sqlite/connection.py` | 연결/PRAGMA/timeout 처리 |
| `src/chatbot/integrations/db/engines/sqlite/schema_manager.py` | 테이블/컬럼 관리 |

## 3. 핵심 정책

1. SQLite는 기본 저장소이며 벡터 검색은 지원하지 않는다.
2. `SQLiteEngine.vector_search()` 호출 시 런타임 오류를 발생시킨다.
3. 벡터 검색이 필요하면 LanceDB 또는 다른 벡터 지원 엔진을 사용한다.

## 4. 환경 변수

```env
CHAT_DB_PATH=data/db/chat/chat_history.sqlite
SQLITE_BUSY_TIMEOUT_MS=5000
```

설명:

1. `CHAT_DB_PATH`: Chat 이력 SQLite 파일 경로
2. `SQLITE_BUSY_TIMEOUT_MS`: 잠금 대기 시간(ms)

## 5. 빠른 점검 절차

1. 경로 확인:

```bash
printf 'CHAT_DB_PATH=%s\n' "$CHAT_DB_PATH"
```

2. 파일/디렉터리 권한 확인:

```bash
mkdir -p "$(dirname "$CHAT_DB_PATH")"
ls -ld "$(dirname "$CHAT_DB_PATH")"
```

3. 서버 기동 후 생성 확인:

```bash
ls -l "$CHAT_DB_PATH"
```

기대 결과:

1. 서버 동작 후 SQLite 파일이 생성된다.
2. 권한 문제 없이 쓰기가 가능하다.

## 6. 운영 권장사항

1. `CHAT_DB_PATH`는 절대경로 사용을 권장한다.
2. 다중 프로세스 동시 쓰기가 증가하면 PostgreSQL 전환을 우선 검토한다.
3. 백업은 `.sqlite` 파일 단위로 수행한다.

## 7. 장애 대응

| 증상 | 원인 후보 | 확인 경로 | 조치 |
| --- | --- | --- | --- |
| DB 파일 생성 실패 | 상위 디렉터리 권한 부족 | `CHAT_DB_PATH`, OS 권한 | 디렉터리 생성 및 권한 수정 |
| SQLite 잠금 오류 빈발 | timeout 과소, 동시성 과다 | `SQLITE_BUSY_TIMEOUT_MS` | timeout 상향, 쓰기 패턴 조정 |
| 벡터 검색 호출 실패 | SQLite 엔진 정책상 미지원 | `sqlite/engine.py` | LanceDB/Elasticsearch 등 벡터 지원 엔진 사용 |

## 8. 관련 문서

- `docs/setup/env.md`
- `docs/setup/lancedb.md`
- `docs/setup/postgresql_pgvector.md`
- `docs/integrations/db.md`
