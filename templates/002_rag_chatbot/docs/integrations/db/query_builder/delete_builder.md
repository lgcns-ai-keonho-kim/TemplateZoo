# delete_builder 모듈

이 문서는 `src/rag_chatbot/integrations/db/query_builder/delete_builder.py`의 역할과 주요 구성을 설명한다.

## 1. 목적

삭제 전용 DSL 빌더를 제공한다.

## 2. 설명

ID 삭제와 QueryBuilder 기반 다건 삭제를 지원한다.

## 3. 디자인 패턴

파사드

## 4. 주요 구성

- 클래스 `DeleteBuilder`
  주요 메서드: `by_id`, `by_ids`, `where`, `where_column`, `where_payload`, `and_`, `or_`, `eq`

## 5. 연동 포인트

- `src/rag_chatbot/integrations/db/base/query_builder.py`

## 6. 관련 문서

- `docs/integrations/db/README.md`
- `docs/integrations/overview.md`
