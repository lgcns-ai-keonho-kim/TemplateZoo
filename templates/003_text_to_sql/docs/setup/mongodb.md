# MongoDB 구성 가이드

이 문서는 MongoDB를 Text-to-SQL 조회 타깃으로 연결하는 방법을 정리한다.

## 1. 적용 범위

1. MongoDB target 연결 파라미터 구성
2. `table_allowlist` 기반 allowlist/컬럼 정책 설정
3. startup introspection 통과 기준과 장애 대응

## 2. 관련 스크립트

| 경로 | 역할 |
| --- | --- |
| `src/text_to_sql/integrations/db/engines/mongodb/engine.py` | MongoDB 엔진 본체 |
| `src/text_to_sql/integrations/db/engines/mongodb/connection.py` | 연결/DB 객체 초기화 |
| `src/text_to_sql/integrations/db/engines/mongodb/schema_manager.py` | 컬렉션 생성/필드 변경 |
| `src/text_to_sql/core/chat/utils/table_allowlist_loader.py` | allowlist 로드 + env 참조 해석 |
| `src/text_to_sql/core/chat/utils/schema_introspection.py` | allowlist 대상 introspection |
| `src/text_to_sql/api/chat/services/runtime.py` | target 초기화/registry 등록 |

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
MONGODB_AUTH_DB=admin
# 선택: URI 직접 지정
# MONGODB_URI=mongodb://playground:playground@127.0.0.1:27017/?authSource=admin
```

키 사용 규칙:

1. `MONGODB_URI`를 지정하면 URI를 우선 사용한다.
2. DB 이름은 `.env`가 아니라 `table_allowlist`의 `connection.database`에서 관리한다.
3. `table_allowlist`에서 `*_env` 키를 사용하면 해당 환경 변수 값을 읽어 해석한다.

## 6. 프로젝트 연동 절차

MongoDB 연결은 `table_allowlist` target으로 선언한다.

예시(`table_allowlist.yaml`, `.yml`도 지원):

```yaml
version: 1
targets:
  - alias: mongo_main
    engine: mongodb
    connection:
      host_env: MONGODB_HOST
      port_env: MONGODB_PORT
      user_env: MONGODB_USER
      password_env: MONGODB_PW
      auth_source_env: MONGODB_AUTH_DB
      database: playground
    allowlist:
      tables:
        - name: orders
          description: 주문 정보
          columns:
            - name: order_id
            - name: customer_id
            - name: total_amount
        - name: customers
          columns:
            - name: customer_id
            - name: name
            - name: region
```

startup 순서:

1. `api/main.py` lifespan startup에서 allowlist를 로드한다.
2. `schema_introspection.py`가 allowlist 대상 컬렉션 메타데이터를 조회한다.
3. 성공 시 `runtime.py`가 target registry를 초기화하고 그래프 static input(`schema_snapshot`)을 설정한다.
4. 실패 시 서버는 fail-fast로 시작에 실패한다.

## 7. 구현 특성

1. MongoDB target은 allowlist에 선언된 컬렉션만 조회 대상이 된다.
2. 컬렉션별 컬럼 allowlist를 지정하면 실행 단계에서 허용 컬럼만 선택/필터링할 수 있다.
3. startup introspection 스냅샷은 runtime 컨텍스트에 보관되고 실행 중 자동 갱신되지 않는다.

## 8. 장애 대응

| 증상 | 원인 후보 | 확인 경로 | 조치 |
| --- | --- | --- | --- |
| `pymongo 패키지가 설치되어 있지 않습니다.` | 의존성 누락 | `mongodb/connection.py` | `uv sync` 후 재시작 |
| 인증 실패(`Authentication failed`) | `authSource`/계정 DB 불일치 | `.env`, Mongo 사용자 정의 | `MONGODB_AUTH_DB` 및 사용자 권한 재확인 |
| 연결은 되지만 데이터가 보이지 않음 | 다른 DB로 연결됨 | `table_allowlist`의 `connection.database` | 타깃 DB 이름 통일 |
| 서버 시작 시 즉시 종료 | allowlist 대상 introspection 실패(권한/접속) | `api/main.py`, `runtime.py`, `schema_introspection.py` | 대상 DB 권한 및 allowlist 연결 정보 점검 |

## 9. 관련 문서

- `docs/setup/env.md`
- `docs/setup/overview.md`
- `docs/integrations/db/README.md`
- `docs/core/chat.md`
