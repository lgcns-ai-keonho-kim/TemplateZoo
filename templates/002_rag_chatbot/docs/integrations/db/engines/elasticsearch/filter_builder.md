# filter_builder 모듈

이 문서는 `src/rag_chatbot/integrations/db/engines/elasticsearch/filter_builder.py`의 역할과 주요 구성을 설명한다.

## 1. 목적

Elasticsearch 필터 쿼리 빌더를 제공한다.

## 2. 설명

필터 조건을 Elasticsearch DSL로 변환한다.

## 3. 디자인 패턴

빌더 패턴

## 4. 주요 구성

- 클래스 `ElasticFilterBuilder`
  주요 메서드: `build`

## 5. 연동 포인트

- `src/rag_chatbot/integrations/db/engines/elasticsearch/engine.py`

## 6. 관련 문서

- `docs/integrations/db/README.md`
- `docs/integrations/overview.md`
