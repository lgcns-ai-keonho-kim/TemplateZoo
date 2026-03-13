# ColumnSpec 가이드

이 문서는 `src/rag_chatbot/integrations/db/base/models.py`의 현재 구현을 기준으로 역할과 유지보수 포인트를 정리한다.

## 1. 역할

DB 계층 전체가 공유하는 스키마, 문서, 필터, 정렬, 벡터 검색 DTO를 정의한다.

## 2. 공개 구성

- 클래스 `ColumnSpec`
  공개 메서드: 없음
- 클래스 `CollectionSchema`
  공개 메서드: `has_payload`, `has_vector`, `column_names`, `resolve_vector_dimension`, `resolve_source`, `column_set`, `validate_document`, `validate_filter_expression`, `validate_query`, `default`
- 클래스 `Vector`
  공개 메서드: 없음
- 클래스 `Document`
  공개 메서드: 없음
- 클래스 `FieldSource`
  공개 메서드: 없음
- 클래스 `FilterOperator`
  공개 메서드: 없음
- 클래스 `FilterCondition`
  공개 메서드: 없음
- 클래스 `FilterExpression`
  공개 메서드: 없음
- 클래스 `SortOrder`
  공개 메서드: 없음
- 클래스 `SortField`
  공개 메서드: 없음
- 클래스 `Pagination`
  공개 메서드: 없음
- 클래스 `Query`
  공개 메서드: 없음
- 클래스 `VectorSearchRequest`
  공개 메서드: 없음
- 클래스 `VectorSearchResult`
  공개 메서드: 없음
- 클래스 `VectorSearchResponse`
  공개 메서드: 없음
- 클래스 `CollectionInfo`
  공개 메서드: 없음

## 3. 코드 설명

- 스키마와 필터 모델은 저장소, 엔진, query builder가 함께 사용하는 공용 계약이다.

## 4. 유지보수/추가개발 포인트

- 이 모듈을 확장할 때는 같은 계층의 이웃 모듈과 계약이 어디에서 맞물리는지 먼저 확인하는 편이 안전하다.

## 5. 관련 문서

- `docs/integrations/overview.md`
- `docs/integrations/db/README.md`
