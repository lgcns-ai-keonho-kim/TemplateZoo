# document_mapper 모듈

이 문서는 `src/rag_chatbot/integrations/db/engines/redis/document_mapper.py`의 역할과 주요 구성을 설명한다.

## 1. 목적

Redis 문서 매퍼 모듈을 제공한다.

## 2. 설명

Document 모델과 Redis Hash 데이터 간 변환을 담당한다.

## 3. 디자인 패턴

매퍼 패턴

## 4. 주요 구성

- 클래스 `RedisDocumentMapper`
  주요 메서드: `to_hash_mapping`, `from_hash`

## 5. 연동 포인트

- `src/rag_chatbot/integrations/db/base/models.py`

## 6. 관련 문서

- `docs/integrations/db/README.md`
- `docs/integrations/overview.md`
