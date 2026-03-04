# MongoDB 구성 가이드

이 문서는 MongoDB 설치, 인증 설정, `.env` 구성, 그리고 프로젝트 저장소 조립 연결 방법을 정리한다.
핵심은 `authSource`와 계정 생성 DB를 일치시키는 것이다.

## 1. 적용 범위

1. MongoDB 엔진 기반 CRUD 검증
2. Chat 저장소를 MongoDB로 교체하는 구성
3. 계정/인증 DB(`authSource`) 표준화

## 2. 관련 스크립트

| 경로 | 역할 |
| --- | --- |
| `src/chatbot/integrations/db/engines/mongodb/engine.py` | MongoDB 엔진 본체 |
| `src/chatbot/integrations/db/engines/mongodb/connection.py` | 연결/DB 초기화 |
| `src/chatbot/integrations/db/engines/mongodb/schema_manager.py` | 컬렉션 생성/필드 변경 |
| `src/chatbot/integrations/db/engines/mongodb/filter_builder.py` | Query -> Mongo 필터 변환 |
| `src/chatbot/api/chat/services/runtime.py` | 저장소 조립 지점 |
| `src/chatbot/shared/chat/repositories/history_repository.py` | `db_client` 주입형 저장소 |

## 3. 설치 방법

Ubuntu 기준 설치 절차:

```bash
sudo apt update
sudo apt install -y gnupg curl
curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc | sudo gpg --dearmor -o /usr/share/keyrings/mongodb-server-8.0.gpg
echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/8.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-8.0.list
sudo apt update
sudo apt install -y mongodb-org
sudo systemctl enable --now mongod
```

설치 확인:

```bash
systemctl status mongod --no-pager
ss -ltnp | rg ':27017'
```

## 4. 초기 사용자/DB 준비

```bash
mongosh
```

```javascript
use admin

db.createUser({
  user: "admin",
  pwd: "admin",
  roles: [
    { role: "readWriteAnyDatabase", db: "admin" }
  ]
})
```

## 5. 환경 변수 설정

```env
MONGODB_HOST=127.0.0.1
MONGODB_PORT=27017
MONGODB_USER=admin
MONGODB_PW=admin
MONGODB_DB=playground
MONGODB_AUTH_DB=admin
# 선택: URI 직접 지정
# MONGODB_URI=mongodb://admin:admin@127.0.0.1:27017/?authSource=admin
```

## 6. `authSource` 핵심 규칙

1. `MONGODB_AUTH_DB`가 설정되면 해당 값이 인증 DB로 사용된다.
2. `MONGODB_AUTH_DB`가 비어 있고 사용자/비밀번호가 있으면 `MONGODB_DB`가 인증 DB로 사용된다.
3. 계정이 `admin` DB에 생성되었는데 `MONGODB_AUTH_DB`를 비워두면 인증 실패가 발생할 수 있다.

## 7. 즉시 점검 명령

1. 환경 변수 확인:

```bash
printf 'MONGODB_USER=%s\nMONGODB_DB=%s\nMONGODB_AUTH_DB=%s\n' "$MONGODB_USER" "$MONGODB_DB" "$MONGODB_AUTH_DB"
```

2. admin 인증 기준 연결 확인:

```bash
mongosh "mongodb://$MONGODB_USER:$MONGODB_PW@$MONGODB_HOST:$MONGODB_PORT/admin?authSource=admin" --eval 'db.runCommand({connectionStatus:1})'
```

기대 출력:

1. `ok: 1`
2. `authenticatedUsers`에 현재 사용자 표시

## 8. 프로젝트 연동 절차

1. `runtime.py`에서 기본 SQLite 저장소 대신 MongoDB 엔진 주입 코드를 배치한다.
2. `MongoDBEngine -> DBClient -> ChatHistoryRepository(db_client=...)` 순서로 조립한다.
3. 서버 재시작 후 세션 생성/조회/삭제를 점검한다.

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

history_repository = ChatHistoryRepository(db_client=DBClient(mongo_engine))
```

## 9. 구현 특성

1. `MongoDBEngine.supports_vector_search`는 `False`다.
2. `vector_search()` 호출 시 런타임 오류를 발생시킨다.
3. 벡터 검색이 필요하면 LanceDB/PostgreSQL/Elasticsearch 전략을 사용한다.

## 10. 장애 대응

| 증상 | 원인 후보 | 확인 경로 | 조치 |
| --- | --- | --- | --- |
| `Authentication failed` | `authSource`/계정 DB 불일치 | `.env`, 사용자 생성 스크립트 | `MONGODB_AUTH_DB` 명시 또는 계정 재생성 |
| 연결은 되지만 데이터가 보이지 않음 | 다른 DB 연결 | `MONGODB_DB` | DB 이름 통일 |
| 벡터 검색 호출 실패 | 구현상 미지원 | `mongodb/engine.py` | 벡터 지원 엔진으로 분리 |

## 11. 관련 문서

- `docs/setup/env.md`
- `docs/setup/troubleshooting.md`
- `docs/integrations/db.md`
- `docs/shared/chat.md`
