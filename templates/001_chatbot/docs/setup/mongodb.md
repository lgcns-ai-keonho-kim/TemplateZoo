# MongoDB 구성 가이드

이 문서는 MongoDB 설치, 인증 설정, `.env` 구성, 그리고 이 프로젝트의 저장소 조립에 연결하는 방법을 정리한다.

## 1. 적용 범위

1. MongoDB 엔진 기반 CRUD 검증
2. Chat 저장소를 MongoDB로 교체하는 실전 구성
3. 계정/인증 DB(`authSource`)를 포함한 접속 표준화

## 2. 관련 스크립트

| 경로 | 역할 |
| --- | --- |
| `src/chatbot/integrations/db/engines/mongodb/engine.py` | MongoDB 엔진 본체 |
| `src/chatbot/integrations/db/engines/mongodb/connection.py` | 연결/DB 객체 초기화 |
| `src/chatbot/integrations/db/engines/mongodb/schema_manager.py` | 컬렉션 생성/필드 변경 |
| `src/chatbot/integrations/db/engines/mongodb/filter_builder.py` | Query -> Mongo 필터 변환 |
| `src/chatbot/api/chat/services/runtime.py` | 저장소 조립 지점 |
| `src/chatbot/shared/chat/repositories/history_repository.py` | `db_client` 주입형 저장소 |

## 3. 설치 방법

### 3-1. Docker 기반

```bash
docker run --name mongo-playground \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=admin \
  -d mongo:8
```

### 3-2. Ubuntu/Debian

```bash
sudo apt update
sudo apt install -y gnupg curl
curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc | sudo gpg --dearmor -o /usr/share/keyrings/mongodb-server-8.0.gpg
echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/8.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-8.0.list
sudo apt update
sudo apt install -y mongodb-org
sudo systemctl enable --now mongod
```

### 3-3. macOS(Homebrew)

```bash
brew tap mongodb/brew
brew install mongodb-community@8.0
brew services start mongodb-community@8.0
```

## 4. 초기 사용자/DB 준비

```bash
mongosh
```

```javascript
use admin

db.createUser({
  user: "playground",
  pwd: "playground",
  roles: [
    { role: "readWrite", db: "playground" }
  ]
})
```

## 5. 환경 변수 설정

```env
MONGODB_HOST=127.0.0.1
MONGODB_PORT=27017
MONGODB_USER=playground
MONGODB_PW=playground
MONGODB_DB=playground
MONGODB_AUTH_DB=admin
# 선택: URI 직접 지정
# MONGODB_URI=mongodb://playground:playground@127.0.0.1:27017/?authSource=admin
```

키 사용 규칙:

1. `MONGODB_URI`를 직접 주면 URI 우선 전략으로 조립 가능하다.
2. `MONGODB_AUTH_DB`가 비어 있고 계정 정보가 있으면 `MONGODB_DB`가 인증 DB로 사용된다.
3. 인증을 쓰지 않으면 `MONGODB_USER`, `MONGODB_PW`를 비워둘 수 있다.

## 6. 프로젝트 연동 절차

현재 기본 조립은 SQLite다. MongoDB로 전환하려면 조립 코드를 교체한다.

1. `runtime.py`에서 `ChatHistoryRepository()` 기본 생성 대신 MongoDB 엔진 주입 코드를 배치한다.
2. `MongoDBEngine` -> `DBClient` -> `ChatHistoryRepository(db_client=...)` 순서로 조립한다.
3. 서버 재시작 후 세션 생성/조회/삭제 흐름을 점검한다.

예시 코드:

```python
import os

from chatbot.integrations.db import DBClient
from chatbot.integrations.db.engines.mongodb import MongoDBEngine
from chatbot.shared.chat import ChatHistoryRepository

mongo_engine = MongoDBEngine(
    uri=(os.getenv("MONGODB_URI") or "").strip() or None,
    database=os.getenv("MONGODB_DB", "playground"),
    host=os.getenv("MONGODB_HOST", "127.0.0.1"),
    port=int(os.getenv("MONGODB_PORT", "27017")),
    user=(os.getenv("MONGODB_USER") or "").strip() or None,
    password=(os.getenv("MONGODB_PW") or "").strip() or None,
    auth_source=(os.getenv("MONGODB_AUTH_DB") or "").strip() or None,
)

history_repository = ChatHistoryRepository(
    db_client=DBClient(mongo_engine),
)
```

## 7. 현재 구현 특성

1. `MongoDBEngine.supports_vector_search`는 `False`다.
2. `vector_search()` 호출 시 런타임 오류를 발생시킨다.
3. 따라서 MongoDB 전환 시에는 일반 CRUD 중심으로 사용하고, 벡터 검색이 필요하면 PostgreSQL/Elasticsearch/Redis 전략을 병행 검토한다.

## 8. 장애 대응

| 증상 | 원인 후보 | 확인 경로 | 조치 |
| --- | --- | --- | --- |
| `pymongo 패키지가 설치되어 있지 않습니다.` | 의존성 누락 | `mongodb/connection.py` | `uv sync` 후 재시작 |
| 인증 실패(`Authentication failed`) | `authSource`/계정 DB 불일치 | `.env`, Mongo 사용자 정의 | `MONGODB_AUTH_DB` 재설정 |
| 연결은 되지만 데이터가 보이지 않음 | 다른 DB로 연결됨 | `MONGODB_DB` 값 | DB 이름 통일 |
| 벡터 검색 API 사용 시 실패 | 구현상 미지원 | `mongodb/engine.py` | 벡터 기능 지원 엔진으로 분리 |

## 9. 운영 체크리스트

1. 사용자 계정 최소 권한 원칙(`readWrite` 등)을 적용했는가
2. 운영 환경에서 TLS/네트워크 ACL이 설정되었는가
3. 백업/복구(`mongodump`, 스냅샷) 전략이 정의되었는가
4. 컬렉션 인덱스 정책이 서비스 질의 패턴과 일치하는가

## 10. 관련 문서

- `docs/setup/env.md`
- `docs/integrations/db.md`
- `docs/shared/chat.md`
