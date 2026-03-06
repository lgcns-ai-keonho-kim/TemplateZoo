# models 모듈

이 문서는 `src/rag_chatbot/integrations/db/base/models.py`의 역할과 주요 구성을 설명한다.

## 1. 목적

DB 통합 인터페이스에서 공통으로 사용하는 모델을 정의한다.

## 2. 설명

컬렉션/문서/필터/정렬/페이지네이션/벡터 검색 모델을 제공한다.

## 3. 디자인 패턴

데이터 전송 객체(DTO)

## 4. 주요 구성

- 클래스 `ColumnSpec`
- 클래스 `CollectionSchema`
  주요 메서드: `has_payload`, `has_vector`, `column_names`, `resolve_vector_dimension`, `resolve_source`, `column_set`, `validate_document`, `validate_filter_expression`
- 클래스 `Vector`
- 클래스 `Document`
- 클래스 `FieldSource`
- 클래스 `FilterOperator`
- 클래스 `FilterCondition`
- 클래스 `FilterExpression`
- 클래스 `SortOrder`
- 클래스 `SortField`
- 클래스 `Pagination`
- 클래스 `Query`
- 클래스 `VectorSearchRequest`
- 클래스 `VectorSearchResult`
- 클래스 `VectorSearchResponse`
- 클래스 `CollectionInfo`

## 5. 연동 포인트

- `src/rag_chatbot/integrations/db/base/engine.py`

## 6. 관련 문서

- `docs/integrations/db/README.md`
- `docs/integrations/overview.md`
