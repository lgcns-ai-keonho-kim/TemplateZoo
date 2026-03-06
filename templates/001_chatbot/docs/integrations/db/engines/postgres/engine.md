# `db/engines/postgres/engine.py` 레퍼런스

## 1. 모듈 목적

- 목적: PostgreSQL 기반 DB 엔진을 제공한다.
- 설명: 컬렉션 스키마 기반 CRUD와 PGVector 벡터 검색을 처리한다.
- 디자인 패턴: 어댑터 패턴

## 2. 핵심 심볼

- `class PostgresEngine`

## 3. 입력/출력 관점

- 엔진 구현체가 실제 저장소 CRUD/검색/스키마 동작을 수행한다.
- 소스 경로: `src/chatbot/integrations/db/engines/postgres/engine.py`
- 문서 경로: `docs/integrations/db/engines/postgres/engine.md`

## 4. 실패 경로

- 이 파일에서 명시적으로 선언한 `ExceptionDetail.code` 문자열은 없다.

## 5. 연계 모듈

- `src/chatbot/integrations/db/base/engine.py`

## 6. 변경 영향 범위

- 엔진별 동작 변경 시 setup 문서와 shared 저장소 동작 결과를 함께 점검해야 한다.
- 변경 후에는 `docs/integrations/overview.md` 및 해당 하위 `overview.md`와 동기화한다.
