# write_builder 모듈

이 문서는 `src/rag_chatbot/integrations/db/query_builder/write_builder.py`의 역할과 주요 구성을 설명한다.

## 1. 목적

쓰기 전용 DSL 빌더를 제공한다.

## 2. 설명

업서트 중심의 간단한 쓰기 호출을 제공한다.

## 3. 디자인 패턴

파사드

## 4. 주요 구성

- 클래스 `WriteBuilder`
  주요 메서드: `upsert`, `upsert_one`

## 5. 연동 포인트

- `src/rag_chatbot/integrations/db/base/engine.py`

## 6. 관련 문서

- `docs/integrations/db/README.md`
- `docs/integrations/overview.md`
