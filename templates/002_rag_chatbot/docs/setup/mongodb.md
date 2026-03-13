# MongoDB

## 현재 범위

- 엔진 구현과 CRUD 테스트는 존재한다.
- 기본 Chat 저장소와 기본 online retrieval 경로에는 포함되지 않는다.
- 실제 사용 경로를 만들려면 런타임 조립에서 `DBClient(MongoDBEngine(...))`를 주입해야 한다.

## 관련 코드

- 엔진: `src/rag_chatbot/integrations/db/engines/mongodb/*`
- capability: `supports_vector_search=False`

## 환경 변수

- `MONGODB_HOST`
- `MONGODB_PORT`
- `MONGODB_DB`
- `MONGODB_URI`

## 주의

- Chat 저장소로 바꾸려면 세션/메시지/commit 스키마와 정렬 의미가 유지되는지 먼저 확인해야 한다.
