# `db/base/models.py` 레퍼런스

이 문서는 `src/chatbot/integrations/db/base/models.py`의 현재 코드 기준 책임과 유지보수 포인트를 정리한다.

## 1. 역할

| 항목 | 내용 |
| --- | --- |
| 목적 | DB 통합 인터페이스에서 공통으로 사용하는 모델을 정의한다. |
| 설명 | 컬렉션/문서/필터/정렬/페이지네이션/벡터 검색 모델을 제공한다. |
| 디자인 패턴 | 데이터 전송 객체(DTO) |

## 2. 코드 구성

| 심볼 | 종류 |
| --- | --- |
| `ColumnSpec` | 클래스 |
| `CollectionSchema` | 클래스 |
| `Vector` | 클래스 |
| `Document` | 클래스 |
| `FieldSource` | 클래스 |
| `FilterOperator` | 클래스 |
| `FilterCondition` | 클래스 |
| `FilterExpression` | 클래스 |
| `SortOrder` | 클래스 |
| `SortField` | 클래스 |
| `Pagination` | 클래스 |
| `Query` | 클래스 |
| `VectorSearchRequest` | 클래스 |
| `VectorSearchResult` | 클래스 |
| `VectorSearchResponse` | 클래스 |
| `CollectionInfo` | 클래스 |

## 3. 현재 코드 설명

1. 이 모듈의 직접 책임은 `db/base/models.py` 파일 내부에 한정된다.
2. 상위 계층은 이 파일의 공개 클래스/함수와 반환 형식을 그대로 신뢰하므로, 문서화된 역할과 실제 구현이 어긋나지 않아야 한다.
3. 현재 코드에서 이 모듈은 `컬렉션/문서/필터/정렬/페이지네이션/벡터 검색 모델을 제공한다.`라는 역할로 사용된다.

## 4. 유지보수 포인트

1. 공통 모델은 모든 엔진이 공유하므로 필드 추가 시 직렬화와 검증 흐름 전체를 함께 확인해야 한다.
2. 선택 필드를 필수로 바꾸는 변경은 기존 엔진 구현 전체에 파급된다.

## 5. 추가 개발과 확장 시 주의점

1. 새 연동 구현을 추가할 때는 현재 기본 런타임에서 실제로 사용하는지, 예시 수준인지 문서에서 분리해 설명해야 한다.
2. 공개 API에 노출하는 경우 `__init__.py` export와 overview 문서를 함께 갱신해야 한다.

## 6. 관련 코드

- 소스: `src/chatbot/integrations/db/base/models.py`
- `src/chatbot/integrations/db/base/engine.py`
