# QueryBuilder 가이드

이 문서는 `src/rag_chatbot/integrations/db/base/query_builder.py`의 현재 구현을 기준으로 역할과 유지보수 포인트를 정리한다.

## 1. 역할

읽기/쓰기/삭제 DSL이 공통으로 사용하는 Query 조립 유틸리티를 제공한다.

## 2. 공개 구성

- 클래스 `QueryBuilder`
  공개 메서드: `where`, `where_column`, `where_payload`, `and_`, `or_`, `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `in_`, `not_in`, `contains`, `order_by`, `order_by_column`, `order_by_payload`, `asc`, `desc`, `limit`, `offset`, `vector`, `top_k`, `include_vectors`, `build`, `build_vector_request`, `has_vector`, `reset`

## 3. 코드 설명

- 현재 구현은 소스 파일의 공개 메서드와 인접 모듈 협업을 기준으로 읽는 것이 가장 안전하다.

## 4. 유지보수/추가개발 포인트

- 새 필터 연산자를 추가하면 QueryBuilder와 각 엔진의 filter/condition builder를 함께 갱신해야 한다.
- 체이닝 객체는 내부 상태를 누적하므로 한 인스턴스를 여러 요청에서 재사용하지 않는 편이 안전하다.

## 5. 관련 문서

- `docs/integrations/overview.md`
- `docs/integrations/db/README.md`
