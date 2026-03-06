# Setup 트러블슈팅 허브

이 문서는 최근 운영/테스트에서 반복된 장애를 빠르게 복구하기 위한 중앙 레퍼런스다.
각 섹션은 `증상 -> 원인 -> 즉시 실행 명령 -> 기대 출력 -> 조치 -> 재발 방지` 순서로 구성한다.

## 1. Elasticsearch TLS 오류 분기

### 1-1. 증상 A: `CERTIFICATE_VERIFY_FAILED`

원인 후보:

1. `ELASTICSEARCH_CA_CERTS` 경로 누락 또는 오경로
2. 잘못된 CA 파일 사용
3. `ELASTICSEARCH_SCHEME=https`인데 인증서 검증 정보 미설정

즉시 실행 명령:

```bash
ls -l "$ELASTICSEARCH_CA_CERTS"
curl --cacert "$ELASTICSEARCH_CA_CERTS" -u "$ELASTICSEARCH_USER:$ELASTICSEARCH_PW" "https://$ELASTICSEARCH_HOST:$ELASTICSEARCH_PORT"
```

기대 출력:

1. `ls`에서 CA 파일이 존재
2. `curl` 결과에 Elasticsearch JSON(`cluster_name`, `version`)이 출력

조치:

1. `ELASTICSEARCH_CA_CERTS`를 절대경로로 고정
2. 서버 인증서 체인과 일치하는 CA 파일로 교체
3. 테스트/서버 프로세스 재시작

재발 방지 확인 항목:

1. `.env`에 상대경로 대신 절대경로 사용
2. 배포 전 `curl --cacert` 헬스체크를 자동화

### 1-2. 증상 B: `SSLError([Errno 13] Permission denied)`

원인 후보:

1. CA 파일 소유자/권한 문제로 실행 계정이 읽지 못함
2. 상위 디렉터리 execute 권한 누락

즉시 실행 명령:

```bash
whoami
namei -l "$ELASTICSEARCH_CA_CERTS"
ls -l "$ELASTICSEARCH_CA_CERTS"
head -n 1 "$ELASTICSEARCH_CA_CERTS"
```

기대 출력:

1. `head`가 인증서 시작 줄(`-----BEGIN CERTIFICATE-----`)을 출력
2. `Permission denied`가 발생하지 않음

조치:

```bash
# 예시: 현재 실행 사용자에게 읽기 권한 부여
chown "$(whoami):$(id -gn)" "$ELASTICSEARCH_CA_CERTS"
chmod 644 "$ELASTICSEARCH_CA_CERTS"
```

재발 방지 확인 항목:

1. 인증서 파일 생성 스크립트에서 소유자/권한을 즉시 고정
2. CI/사전 점검에 `head "$ELASTICSEARCH_CA_CERTS"`를 포함

## 2. MongoDB 인증 실패 (`AuthenticationFailed`)

### 2-1. 증상

`pymongo.errors.OperationFailure: Authentication failed. code=18`

원인 후보:

1. `MONGODB_AUTH_DB`와 실제 사용자 생성 DB 불일치
2. 사용자/비밀번호 오타
3. URI 직접 지정 시 `authSource` 누락

핵심 동작:

1. `MONGODB_AUTH_DB`가 비어 있고 사용자/비밀번호가 있으면 엔진이 `MONGODB_DB`를 인증 DB로 사용한다.
2. 실제 계정이 `admin` DB에 생성되어 있으면 `MONGODB_AUTH_DB=admin`이 필요하다.

즉시 실행 명령:

```bash
# 현재 env 확인
printf 'MONGODB_DB=%s\nMONGODB_AUTH_DB=%s\nMONGODB_USER=%s\n' "$MONGODB_DB" "$MONGODB_AUTH_DB" "$MONGODB_USER"

# admin 인증 기준 연결 확인
mongosh "mongodb://$MONGODB_USER:$MONGODB_PW@$MONGODB_HOST:$MONGODB_PORT/admin?authSource=admin" --eval 'db.runCommand({connectionStatus:1})'
```

기대 출력:

1. `ok: 1` 포함
2. `authenticatedUsers`에 현재 사용자가 표시

조치:

1. `.env`에 `MONGODB_AUTH_DB=admin` 명시(계정이 admin DB 기준일 때)
2. 또는 계정을 `MONGODB_DB` 기준으로 재생성해 일치시킴

재발 방지 확인 항목:

1. 사용자 생성 스크립트와 `.env`의 인증 DB를 같은 값으로 표준화
2. `MONGODB_URI` 직접 사용 시 `authSource` 명시

## 3. E2E 서버 기동 실패 (`Connection refused`)

### 3-1. 증상

`RuntimeError: E2E 서버 기동 대기 타임아웃: [Errno 111] Connection refused`

원인 후보:

1. 서버 부팅 시간이 헬스체크 제한 시간보다 길다
2. 서버가 초기화 중 예외로 즉시 종료된다
3. 포트 충돌 또는 환경 변수 누락으로 앱이 뜨지 못함

즉시 실행 명령:

```bash
# 서버 단독 기동 확인
uv run uvicorn chatbot.api.main:app --host 127.0.0.1 --port 8001

# 별도 터미널 헬스체크
curl -i http://127.0.0.1:8001/health
```

기대 출력:

1. `/health`가 `200 OK`
2. 서버 로그에 import/runtime 초기화 에러 없음

조치:

1. E2E 서버 기동 대기 시간을 실환경에 맞게 상향
2. `GEMINI_MODEL`, `GEMINI_PROJECT`, `CHAT_DB_PATH` 등 필수 env 재확인
3. 서버 stdout/stderr를 확인해 초기화 예외를 먼저 제거

재발 방지 확인 항목:

1. E2E 시작 전 `/health` 선확인 루틴 유지
2. 로컬/CI 환경별 서버 부팅 시간 프로파일 기록

## 4. SSE `ReadTimeout` 및 `done/error` 종료 동작

### 4-1. 증상 A: `httpx.ReadTimeout`

원인 후보:

1. 클라이언트 read timeout이 모델 응답 시간보다 짧음
2. 스트림 도중 LLM 호출 지연 또는 외부 API 대기

즉시 실행 명령:

```bash
# timeout 관련 env 확인
printf 'CHAT_STREAM_TIMEOUT_SECONDS=%s\n' "$CHAT_STREAM_TIMEOUT_SECONDS"

# SSE 요청은 충분한 read timeout으로 실행
curl -N "http://127.0.0.1:8001/chat/<session_id>/events?request_id=<request_id>"
```

기대 출력:

1. 스트림 이벤트(`data: ...`)가 순차 수신
2. 최종 이벤트가 `type=done` 또는 `type=error`

조치:

1. 서버 `CHAT_STREAM_TIMEOUT_SECONDS`와 테스트 클라이언트 read timeout을 함께 상향
2. 모델 응답 시간 분포에 맞춰 timeout 기준을 통일

재발 방지 확인 항목:

1. E2E timeout 값을 단일 상수로 관리
2. 느린 외부 LLM 환경을 고려한 안전 마진 확보

### 4-2. 증상 B: `done` 미수신

원인 후보:

1. 실제 종료 이벤트가 `error`인 경우
2. 테스트가 `done`만 성공으로 간주하는 경우

핵심 동작:

1. SSE 정상 종료 이벤트는 `done` 또는 `error` 둘 다 가능하다.
2. `error` 종료는 실패 원인 파악을 위한 정상적인 종료 시그널이다.

즉시 실행 명령:

```bash
# 이벤트 타입 분포 확인용 예시
rg -n '"type": "(start|token|done|error)"' /tmp/chat_events.log
```

기대 출력:

1. 요청별로 `start` 이후 `done` 또는 `error` 중 하나가 존재

조치:

1. 테스트 단언을 `done` 강제에서 `done/error` 종료 확인으로 개선
2. `error`일 때 `error_message`, `metadata.error_code`를 함께 검증

재발 방지 확인 항목:

1. 테스트 케이스 설계에서 성공/실패 종료 시나리오를 분리
2. `error` 이벤트 본문을 진단 정보로 보존

## 5. Gemini 환경 변수/모델 설정 오류

### 5-1. 증상

1. `RuntimeError: 테스트를 위해 GEMINI_MODEL 환경 변수가 필요합니다.`
2. `RuntimeError: 테스트를 위해 GEMINI_PROJECT 환경 변수가 필요합니다.`
3. LLM 호출 실패(모델명 오타/프로젝트 오설정)

원인 후보:

1. `.env` 누락 또는 키 오타
2. 잘못된 프로젝트/모델 조합

즉시 실행 명령:

```bash
printf 'GEMINI_MODEL=%s\nGEMINI_PROJECT=%s\n' "$GEMINI_MODEL" "$GEMINI_PROJECT"
```

기대 출력:

1. 두 값 모두 비어 있지 않음

조치:

1. `.env`에 `GEMINI_MODEL`, `GEMINI_PROJECT` 명시
2. 테스트/서버 재시작으로 env 재로딩

재발 방지 확인 항목:

1. 필수 env 누락 시 fixture 단계에서 즉시 실패하도록 유지
2. 팀 공용 `.env` 템플릿과 실제 배포 변수 이름을 동일하게 관리

## 6. 관련 문서

- `docs/setup/env.md`
- `docs/setup/mongodb.md`
- `docs/setup/sqlite.md`
- `docs/setup/lancedb.md`
- `docs/api/chat.md`
- `docs/shared/chat.md`
- `docs/integrations/db.md`
