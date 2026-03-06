# keyspace 모듈

이 문서는 `src/rag_chatbot/integrations/db/engines/redis/keyspace.py`의 역할과 주요 구성을 설명한다.

## 1. 목적

Redis 키스페이스 유틸 모듈을 제공한다.

## 2. 설명

키 생성 규칙과 SCAN 기반 키 수집을 담당한다.

## 3. 디자인 패턴

유틸리티 클래스

## 4. 주요 구성

- 클래스 `RedisKeyspaceHelper`
  주요 메서드: `payload_storage_key`, `make_key`, `scan_keys`

## 5. 연동 포인트

- `src/rag_chatbot/integrations/db/engines/redis/engine.py`

## 6. 관련 문서

- `docs/integrations/db/README.md`
- `docs/integrations/overview.md`
