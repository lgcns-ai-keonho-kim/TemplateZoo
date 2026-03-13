# DeleteBuilder 가이드

이 문서는 `src/rag_chatbot/integrations/db/query_builder/delete_builder.py`의 현재 구현을 기준으로 역할과 유지보수 포인트를 정리한다.

## 1. 역할

QueryBuilder 기반 DSL의 한 조각이다. 체이닝 방식으로 Query 또는 VectorSearchRequest를 조립한다.

## 2. 공개 구성

- 클래스 `DeleteBuilder`
  공개 메서드: `by_id`, `by_ids`, `where`, `where_column`, `where_payload`, `and_`, `or_`, `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `in_`, `not_in`, `contains`, `execute`, `delete_by_query`

## 3. 코드 설명

- DSL 체이닝 결과는 마지막에 `Query` 또는 `VectorSearchRequest`로 변환된다.
- 벡터 검색과 일반 조회 경로를 혼용하지 않도록 런타임 검증이 포함돼 있다.

## 4. 유지보수/추가개발 포인트

- 새 필터 연산자를 추가하면 QueryBuilder와 각 엔진의 filter/condition builder를 함께 갱신해야 한다.
- 체이닝 객체는 내부 상태를 누적하므로 한 인스턴스를 여러 요청에서 재사용하지 않는 편이 안전하다.

## 5. 관련 문서

- `docs/integrations/overview.md`
- `docs/integrations/db/README.md`
