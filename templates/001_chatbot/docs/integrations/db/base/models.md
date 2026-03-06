# `db/base/models.py` 레퍼런스

## 1. 모듈 목적

- 목적: DB 통합 인터페이스에서 공통으로 사용하는 모델을 정의한다.
- 설명: 컬렉션/문서/필터/정렬/페이지네이션/벡터 검색 모델을 제공한다.
- 디자인 패턴: 데이터 전송 객체(DTO)

## 2. 핵심 심볼

- `class ColumnSpec`
- `class CollectionSchema`
- `class Vector`
- `class Document`
- `class FieldSource`
- `class FilterOperator`
- `class FilterCondition`
- `class FilterExpression`
- `class SortOrder`
- `class SortField`
- `class Pagination`
- `class Query`
- `class VectorSearchRequest`
- `class VectorSearchResult`
- `class VectorSearchResponse`
- `class CollectionInfo`

## 3. 입력/출력 관점

- 스키마/문서/쿼리/벡터 검색 요청·응답 모델을 입출력 타입으로 사용한다.
- 소스 경로: `src/chatbot/integrations/db/base/models.py`
- 문서 경로: `docs/integrations/db/base/models.md`

## 4. 실패 경로

- 이 파일에서 명시적으로 선언한 `ExceptionDetail.code` 문자열은 없다.

## 5. 연계 모듈

- `src/chatbot/integrations/db/base/engine.py`

## 6. 변경 영향 범위

- 모델 필드 변경 시 DBClient, QueryBuilder, 엔진 구현체, 상위 저장소의 타입 계약이 함께 변경된다.
- 변경 후에는 `docs/integrations/overview.md` 및 해당 하위 `overview.md`와 동기화한다.
