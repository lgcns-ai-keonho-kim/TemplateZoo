# read_builder 모듈

이 문서는 `src/rag_chatbot/integrations/db/query_builder/read_builder.py`의 역할과 주요 구성을 설명한다.

## 1. 목적

읽기 전용 DSL 빌더를 제공한다.

## 2. 설명

QueryBuilder를 감싸 체이닝 후 fetch()로 조회한다.

## 3. 디자인 패턴

빌더 패턴

## 4. 주요 구성

- 클래스 `ReadBuilder`
  주요 메서드: `where`, `where_column`, `where_payload`, `and_`, `or_`, `eq`, `ne`, `gt`

## 5. 연동 포인트

- `src/rag_chatbot/integrations/db/base/query_builder.py`

## 6. 관련 문서

- `docs/integrations/db/README.md`
- `docs/integrations/overview.md`
