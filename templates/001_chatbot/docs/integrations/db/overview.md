# Integrations DB 모듈 레퍼런스

`src/chatbot/integrations/db`는 공통 DB 계약 위에 여러 엔진 구현을 올려서 상위 계층이 엔진 교체 비용을 낮출 수 있게 만든 계층이다.

## 1. 현재 기본 경로

| 구분 | 현재 상태 | 코드 기준 |
| --- | --- | --- |
| 기본 저장소 | SQLite | `ChatHistoryRepository(db_client=None)` |
| 선택 확장 | PostgreSQL, MongoDB, Redis, Elasticsearch, LanceDB | 별도 조립 또는 테스트 경로 |

현재 서비스 기본 조립은 `src/chatbot/api/chat/services/runtime.py`에서 `ChatHistoryRepository()`만 생성하므로 실제 서비스 경로의 기본 저장소는 SQLite다.

## 2. 구조

| 경로 | 역할 |
| --- | --- |
| `base` | 엔진/세션/모델/쿼리 계약 |
| `client.py` | `DBClient` 퍼사드 |
| `query_builder` | 읽기/쓰기/삭제 DSL |
| `engines/*` | 엔진별 연결, 스키마, 문서 변환, 필터/검색 구현 |

## 3. 유지보수 포인트

1. `CollectionSchema`, `Query`, 벡터 검색 모델 의미를 바꾸면 전체 엔진에 파급된다.
2. 새 엔진을 추가해도 `runtime.py`를 바꾸지 않으면 기본 런타임 동작은 바뀌지 않는다.
3. 엔진별 제한사항은 숨기기보다 문서에 분리해서 적는 편이 낫다.

## 4. 관련 문서

- `docs/shared/chat/repositories/history_repository.md`
- `docs/setup/overview.md`
