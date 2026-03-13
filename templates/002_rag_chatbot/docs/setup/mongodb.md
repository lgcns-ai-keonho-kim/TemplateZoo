# MongoDB 설정 가이드

이 문서는 MongoDB 엔진이 현재 코드에서 어떤 위치를 차지하는지 설명한다.

## 1. 현재 사용 범위

- 엔진 구현과 CRUD 테스트는 존재한다.
- 기본 Chat 저장소나 online retrieval 경로로는 조립돼 있지 않다.
- runtime에서 `DBClient(MongoDBEngine(...))`를 주입해야 실제 사용 경로가 생긴다.

## 2. 현재 특징

- 문서형 저장에 맞는 mapper와 filter builder를 제공한다.
- 현재 `supports_vector_search`는 `False`다.

## 3. 유지보수/추가개발 포인트

- Chat 저장소로 쓰려면 세션/메시지/commit 스키마와 정렬 규칙이 MongoDB 표현으로도 같은 의미를 가지는지 먼저 확인해야 한다.
- vector search를 붙일 계획이 있으면 현재 포트 계약과 엔진 capability 노출 방식을 함께 바꿔야 한다.

## 4. 관련 문서

- `docs/setup/env.md`
- `docs/integrations/db/engines/mongodb/engine.md`
- `docs/integrations/db/README.md`
