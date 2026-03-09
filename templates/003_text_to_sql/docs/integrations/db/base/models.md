# db/base/models.md

소스 경로: `src/text_to_sql/integrations/db/base/models.py`

## 1. 역할

- 목적: DB 통합 인터페이스에서 공통으로 사용하는 모델을 정의한다.
- 설명: 컬렉션/문서/필터/정렬/페이지네이션/벡터 검색 모델을 제공한다.
- 디자인 패턴: 데이터 전송 객체(DTO)

## 2. 주요 구성

### 2-1. 클래스

| 클래스 | 핵심 메서드 |
| --- | --- |
| `ColumnSpec` | `-` |
| `CollectionSchema` | `has_payload, has_vector, column_names, resolve_vector_dimension, resolve_source, column_set, validate_document, validate_filter_expression, ...` |
| `Vector` | `-` |
| `Document` | `-` |
| `FieldSource` | `-` |
| `FilterOperator` | `-` |
| `FilterCondition` | `-` |
| `FilterExpression` | `-` |
| `SortOrder` | `-` |
| `SortField` | `-` |
| `Pagination` | `-` |
| `Query` | `-` |
| `AggregateFunction` | `-` |
| `AggregateField` | `-` |
| `GroupByField` | `-` |
| `AggregateQuery` | `-` |
| `VectorSearchRequest` | `-` |
| `VectorSearchResult` | `-` |
| `VectorSearchResponse` | `-` |
| `CollectionInfo` | `-` |

### 2-2. 함수

- 정의된 최상위 함수가 없다.

## 3. 오류/예외 코드

- 모듈 내부에서 명시적으로 정의한 오류 코드가 없다.

## 4. 연관 모듈

- `src/text_to_sql/integrations/db/base/engine.py`
