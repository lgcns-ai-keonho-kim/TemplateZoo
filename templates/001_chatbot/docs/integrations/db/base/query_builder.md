# `db/base/query_builder.py` 레퍼런스

## 1. 모듈 목적

- 목적: 공통 DSL 기반 QueryBuilder를 제공한다.
- 설명: 체이닝 방식으로 Filter/Sort/Pagination을 구성해 Query 모델을 생성한다.
- 디자인 패턴: 빌더 패턴

## 2. 핵심 심볼

- `class QueryBuilder`

## 3. 입력/출력 관점

- 공통 Query DSL 빌더를 제공해 필터/정렬/페이지네이션을 조합한다.
- 소스 경로: `src/chatbot/integrations/db/base/query_builder.py`
- 문서 경로: `docs/integrations/db/base/query_builder.md`

## 4. 실패 경로

- 이 파일에서 명시적으로 선언한 `ExceptionDetail.code` 문자열은 없다.

## 5. 연계 모듈

- `src/chatbot/integrations/db/base/models.py`

## 6. 변경 영향 범위

- DSL 메서드 동작 변경 시 read/write/delete 빌더와 엔진별 query 처리 경로가 영향을 받는다.
- 변경 후에는 `docs/integrations/overview.md` 및 해당 하위 `overview.md`와 동기화한다.
