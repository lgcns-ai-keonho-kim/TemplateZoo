# MongoDB

MongoDB 설치, 인증 설정, `.env` 구성, 그리고 선택적 DB 엔진 실험 경로를 정리한다.

## 1. 적용 범위

1. MongoDB 엔진 기반 CRUD 검증
2. 계정/인증 DB(`authSource`)를 포함한 접속 표준화
3. 수동 조립 코드에서 MongoDB 저장소를 사용하는 예시

주의:

- 현재 기본 `/agent` 런타임은 MongoDB 저장소를 자동으로 사용하지 않는다.
- 이 문서는 DB 엔진 테스트 또는 커스텀 조립 시 참고용이다.

## 2. 관련 스크립트

| 경로 | 역할 |
| --- | --- |
| `src/single_request_tool_agent/integrations/db/engines/mongodb/engine.py` | MongoDB 엔진 본체 |
| `src/single_request_tool_agent/integrations/db/engines/mongodb/connection.py` | 연결/DB 객체 초기화 |
| `src/single_request_tool_agent/integrations/db/engines/mongodb/schema_manager.py` | 컬렉션 생성/필드 변경 |
| `src/single_request_tool_agent/integrations/db/engines/mongodb/filter_builder.py` | Query -> Mongo 필터 변환 |
| `src/single_request_tool_agent/shared/agent/repositories/history_repository.py` | `db_client` 주입형 저장소 |
| `tests/integrations/db/CRUD/test_mongodb_engine_crud.py` | CRUD 검증 |

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

## 6. 수동 조립 예시

기본 런타임 대신 별도 저장소 조립이 필요할 때만 사용한다.

```python
import os

from single_request_tool_agent.integrations.db import DBClient
from single_request_tool_agent.integrations.db.engines.mongodb import MongoDBEngine
from single_request_tool_agent.shared.agent.repositories import ChatHistoryRepository

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
3. 따라서 MongoDB는 일반 CRUD 검증 또는 저장소 실험 용도로만 사용하는 편이 적절하다.

## 8. 장애 대응

| 증상 | 원인 후보 | 확인 경로 | 조치 |
| --- | --- | --- | --- |
| `pymongo 패키지가 설치되어 있지 않습니다.` | 의존성 누락 | `mongodb/connection.py` | `uv sync` 후 재시작 |
| 인증 실패(`Authentication failed`) | `authSource`/계정 DB 불일치 | `.env`, Mongo 사용자 정의 | `MONGODB_AUTH_DB` 재설정 |
| 연결은 되지만 데이터가 보이지 않음 | 다른 DB로 연결됨 | `MONGODB_DB` 값 | DB 이름 통일 |
| 벡터 검색 API 사용 시 실패 | 구현상 미지원 | `mongodb/engine.py` | 벡터 기능 지원 엔진으로 분리 |

## 9. 관련 문서

- `docs/setup/env.md`
- `docs/integrations/db/overview.md`
