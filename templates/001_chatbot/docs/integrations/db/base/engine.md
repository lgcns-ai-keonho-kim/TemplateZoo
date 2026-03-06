# `db/base/engine.py` 레퍼런스

## 1. 모듈 목적

- 목적: DB 엔진 추상 인터페이스를 정의한다.
- 설명: 컬렉션 관리, 문서 CRUD, 벡터 검색을 위한 표준 메서드를 제공한다.
- 디자인 패턴: 전략 패턴

## 2. 핵심 심볼

- `class BaseDBEngine`

## 3. 입력/출력 관점

- DB 엔진 구현체가 따라야 하는 공통 인터페이스를 정의한다.
- 소스 경로: `src/chatbot/integrations/db/base/engine.py`
- 문서 경로: `docs/integrations/db/base/engine.md`

## 4. 실패 경로

- 이 파일에서 명시적으로 선언한 `ExceptionDetail.code` 문자열은 없다.

## 5. 연계 모듈

- `src/chatbot/integrations/db/base/models.py`

## 6. 변경 영향 범위

- 메서드 계약 변경 시 모든 DB 엔진(SQLite/Redis/Postgres/MongoDB/Elasticsearch/LanceDB)에 영향을 준다.
- 변경 후에는 `docs/integrations/overview.md` 및 해당 하위 `overview.md`와 동기화한다.
