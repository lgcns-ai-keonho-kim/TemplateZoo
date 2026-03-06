# filter_engine 모듈

이 문서는 `src/rag_chatbot/integrations/db/engines/lancedb/filter_engine.py`의 역할과 주요 구성을 설명한다.

## 1. 목적

LanceDB 필터/정렬 보조 엔진을 제공한다.

## 2. 설명

FilterExpression의 where 절 변환, 메모리 필터 평가, 정렬/점수 변환을 담당한다.

## 3. 디자인 패턴

정책 객체 패턴

## 4. 주요 구성

- 클래스 `LanceFilterEngine`
  주요 메서드: `build_where_clause`, `build_eq_clause`, `distance_to_similarity`, `apply_sort`, `match_filter`

## 5. 연동 포인트

- `src/rag_chatbot/integrations/db/base/models.py`

## 6. 관련 문서

- `docs/integrations/db/README.md`
- `docs/integrations/overview.md`
