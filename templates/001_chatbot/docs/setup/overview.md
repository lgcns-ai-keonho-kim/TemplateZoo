# Setup 가이드 개요

이 문서는 `docs/setup` 하위의 인프라/환경 설정 문서를 빠르게 탐색하기 위한 인덱스다.
애플리케이션 코드 구조(`src/chatbot/*`)와 1:1로 대응되는 문서와 달리, 이 폴더는 실행 환경 구성과 외부 시스템 준비 절차를 다룬다.

## 1. 문서 구성

| 문서 | 목적 | 열어야 하는 시점 |
| --- | --- | --- |
| `docs/setup/env.md` | `.env` 키 전체 설명과 실제 반영 여부 확인 | 프로젝트 초기 부트스트랩, 배포 전 변수 점검 |
| `docs/setup/sqlite_vec.md` | sqlite-vec 구성과 SQLite 데이터 저장 위치 정리 | 로컬 단독 실행, SQLite 벡터 검색 실험 |
| `docs/setup/postgresql_pgvector.md` | PostgreSQL + pgvector 설치/초기화/연동 절차 | 운영형 DB로 전환할 때 |
| `docs/setup/mongodb.md` | MongoDB 설치, 인증, 엔진 연동 절차 | MongoDB 엔진 검증/전환 시 |
| `docs/setup/filesystem.md` | 파일 시스템 기반 로그 저장소 연동 방식 | 로그 영속화/파일 백엔드 확장 시 |

## 2. 권장 읽기 순서

1. `docs/setup/env.md`
2. `docs/setup/sqlite_vec.md`
3. `docs/setup/postgresql_pgvector.md`
4. `docs/setup/mongodb.md`
5. `docs/setup/filesystem.md`

## 3. 최소 실행 경로 (로컬 단일 노드)

1. `.env`를 생성하고 `OPENAI_API_KEY`, `OPENAI_MODEL`, `CHAT_DB_PATH`를 설정한다.
2. SQLite 기본 저장 경로(`data/db/chat/chat_history.sqlite`) 접근 권한을 확인한다.
3. 서버를 실행하고 `/health`, `/docs`, `/ui`를 순서대로 점검한다.

## 4. 확장 실행 경로

### 4-1. PostgreSQL + pgvector

1. PostgreSQL 서버와 pgvector 확장을 설치한다.
2. DB/계정/권한을 준비하고 `.env`에 `POSTGRES_*` 값을 넣는다.
3. `src/chatbot/api/chat/services/runtime.py`의 저장소 조립을 PostgreSQL 주입 방식으로 변경한다.

### 4-2. MongoDB

1. MongoDB 서버와 계정/인증 DB를 준비한다.
2. `.env`에 `MONGODB_*` 값을 설정한다.
3. `runtime.py`에서 MongoDB 엔진을 주입해 저장소를 교체한다.

### 4-3. 파일 시스템 로그 저장

1. 로그 기준 디렉터리(`data/logs` 등)를 설계한다.
2. `FileLogRepository(base_dir=...)`를 주입해 로그 저장소를 활성화한다.
3. 운영 정책(보관 기간, 아카이빙 경로, 접근 권한)을 확정한다.

## 5. 코드 매핑

| 설정 영역 | 관련 코드 |
| --- | --- |
| 런타임 환경 로딩 | `src/chatbot/shared/config/runtime_env_loader.py`, `src/chatbot/api/main.py` |
| Chat 런타임 변수 소비 | `src/chatbot/api/chat/services/runtime.py`, `src/chatbot/shared/chat/services/chat_service.py` |
| 기본 SQLite 저장소 | `src/chatbot/shared/chat/repositories/history_repository.py`, `src/chatbot/core/chat/const/settings.py` |
| sqlite-vec 로딩 | `src/chatbot/integrations/db/engines/sqlite/connection.py`, `src/chatbot/integrations/db/engines/sqlite/vector_store.py` |
| PostgreSQL/pgvector | `src/chatbot/integrations/db/engines/postgres/*.py` |
| MongoDB | `src/chatbot/integrations/db/engines/mongodb/*.py` |
| 파일 시스템 연동 | `src/chatbot/integrations/fs/*.py`, `src/chatbot/shared/logging/logger.py` |

## 6. 문서 동기화 체크리스트

1. 문서에 적힌 환경 변수 키가 `.env.sample` 또는 코드(`os.getenv`)와 일치하는지 확인한다.
2. 설치 문서의 경로/명령이 실제 런타임 조립 지점(`runtime.py`)과 연결되는지 확인한다.
3. SQLite 기본 경로 설명이 `CHAT_DB_PATH` 기본값과 일치하는지 확인한다.
4. PostgreSQL/MongoDB 전환 예시가 `ChatHistoryRepository(db_client=...)` 패턴과 일치하는지 확인한다.
5. 파일 시스템 저장 경로 규칙이 `FileLogRepository` 구현(`YYYYMMDD/<uuid>.log`)과 일치하는지 확인한다.
