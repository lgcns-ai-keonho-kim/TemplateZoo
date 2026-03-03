# Setup 가이드 개요

이 문서는 `docs/setup` 하위의 인프라/환경 설정 문서를 빠르게 탐색하기 위한 인덱스다.
애플리케이션 코드 구조(`src/chatbot/*`) 문서와 달리, 이 폴더는 실행 환경 구성과 외부 시스템 준비 절차를 다룬다.

범위 기준:

1. DB 설치/서비스 기동 예시는 Ubuntu 환경 기준으로 설명한다.

## 1. 문서 구성

| 문서 | 목적 | 열어야 하는 시점 |
| --- | --- | --- |
| `docs/setup/env.md` | `.env` 키 상세, 반영 위치, 장애 징후 점검 | 초기 부트스트랩, 배포 전 변수 검증 |
| `docs/setup/sqlite.md` | SQLite 기본 저장소(CRUD) 구성 | 로컬 기본 실행/파일 저장소 점검 |
| `docs/setup/lancedb.md` | LanceDB 벡터 검색 구성 | 벡터 검색 테스트/로컬 실험 |
| `docs/setup/postgresql_pgvector.md` | PostgreSQL + pgvector 구성 | 운영형 DB/벡터 인프라 전환 |
| `docs/setup/mongodb.md` | MongoDB 인증/연동 구성 | MongoDB 엔진 검증/전환 |
| `docs/setup/filesystem.md` | 파일 로그 저장소 구성 | 파일 기반 로깅/아카이빙 |
| `docs/setup/troubleshooting.md` | 반복 장애 복구 허브 | 장애 발생 시 즉시 확인 |

## 2. 권장 읽기 순서

1. `docs/setup/env.md`
2. `docs/setup/sqlite.md`
3. `docs/setup/lancedb.md`
4. `docs/setup/postgresql_pgvector.md`
5. `docs/setup/mongodb.md`
6. `docs/setup/filesystem.md`
7. `docs/setup/troubleshooting.md`

## 3. 최소 실행 경로 (로컬 단일 노드)

1. `.env`를 생성하고 `GEMINI_MODEL`, `GEMINI_PROJECT`, `CHAT_DB_PATH`를 설정한다.
2. SQLite 기본 저장 경로(`CHAT_DB_PATH`) 접근 권한을 확인한다.
3. 서버를 실행하고 `/health`, `/docs`, `/ui`를 순서대로 점검한다.

## 4. 확장 실행 경로

### 4-1. LanceDB 벡터 검색

1. `LANCEDB_URI` 경로를 준비한다.
2. 임베딩 공급자 상태를 확인한다.
3. 벡터 검색 테스트를 통해 차원/검색 결과를 검증한다.

### 4-2. PostgreSQL + pgvector

1. PostgreSQL 서버와 pgvector 확장을 설치한다.
2. DB/계정/권한을 준비하고 `.env`에 `POSTGRES_*` 값을 입력한다.
3. `runtime.py` 저장소 조립을 PostgreSQL 주입 방식으로 변경한다.

### 4-3. MongoDB

1. MongoDB 서버와 계정/인증 DB(`authSource`)를 준비한다.
2. `.env`에 `MONGODB_*` 값을 설정한다.
3. `runtime.py`에서 MongoDB 엔진을 주입해 저장소를 교체한다.

### 4-4. 파일 시스템 로그 저장

1. 로그 기준 디렉터리(`data/logs` 등)를 설계한다.
2. `FileLogRepository(base_dir=...)`를 주입해 로그 저장소를 활성화한다.
3. 운영 정책(보관 기간, 아카이빙 경로, 접근 권한)을 확정한다.

## 5. 코드 매핑

| 설정 영역 | 관련 코드 |
| --- | --- |
| 런타임 환경 로딩 | `src/chatbot/shared/config/runtime_env_loader.py`, `src/chatbot/api/main.py` |
| Chat 런타임 변수 소비 | `src/chatbot/api/chat/services/runtime.py`, `src/chatbot/shared/chat/services/chat_service.py` |
| 기본 SQLite 저장소 | `src/chatbot/shared/chat/repositories/history_repository.py`, `src/chatbot/core/chat/const/settings.py` |
| LanceDB 벡터 엔진 | `src/chatbot/integrations/db/engines/lancedb/*.py` |
| PostgreSQL/pgvector | `src/chatbot/integrations/db/engines/postgres/*.py` |
| MongoDB | `src/chatbot/integrations/db/engines/mongodb/*.py` |
| 파일 시스템 연동 | `src/chatbot/integrations/fs/*.py`, `src/chatbot/shared/logging/logger.py` |

## 6. 문서 동기화 체크리스트

1. 문서의 환경 변수 키가 `.env.sample` 또는 코드(`os.getenv`)와 일치하는지 확인한다.
2. 설치 문서의 경로/명령이 실제 런타임 조립 지점(`runtime.py`)과 연결되는지 확인한다.
3. SQLite 설명이 CRUD 전용 정책(벡터 미지원)과 일치하는지 확인한다.
4. LanceDB 문서가 벡터 테스트 경로와 일치하는지 확인한다.
5. 트러블슈팅 항목이 실제 장애 로그 메시지와 동일한 문자열을 포함하는지 확인한다.
