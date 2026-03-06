# connection 모듈

이 문서는 `src/rag_chatbot/integrations/db/engines/elasticsearch/connection.py`의 역할과 주요 구성을 설명한다.

## 1. 목적

Elasticsearch 연결 관리 모듈을 제공한다.

## 2. 설명

클라이언트 생성/종료와 옵션 클라이언트 반환을 담당한다.

## 3. 디자인 패턴

매니저 패턴

## 4. 주요 구성

- 클래스 `ElasticConnectionManager`
  주요 메서드: `connect`, `close`, `ensure_client`, `with_options`

## 5. 연동 포인트

- `src/rag_chatbot/integrations/db/engines/elasticsearch/engine.py`

## 6. 관련 문서

- `docs/integrations/db/README.md`
- `docs/integrations/overview.md`
