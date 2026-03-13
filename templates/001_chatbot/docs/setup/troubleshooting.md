# Setup 트러블슈팅 허브

이 문서는 현재 코드 기준으로 자주 발생할 수 있는 설정/연동 문제를 빠르게 분류하기 위한 레퍼런스다.

## 1. `ENV=dev/stg/prod`인데 서버가 시작되지 않을 때

증상 예시:

1. `FileNotFoundError: 환경 파일을 찾을 수 없습니다: .../src/chatbot/resources/<env>/.env`

확인 포인트:

1. `RuntimeEnvironmentLoader`는 샘플 파일이 아니라 실제 `.env` 파일을 찾는다.
2. `src/chatbot/resources/<env>/.env.sample`만 있으면 실패한다.

조치:

```bash
cp src/chatbot/resources/dev/.env.sample src/chatbot/resources/dev/.env
```

## 2. LLM 호출이 실패할 때

확인 포인트:

1. 현재 기본 노드는 `GEMINI_MODEL`, `GEMINI_PROJECT`를 직접 읽는다.
2. `.env.sample`의 `OPENAI_*`는 현재 기본 런타임을 자동으로 바꾸지 않는다.

점검 명령:

```bash
printf 'GEMINI_MODEL=%s\nGEMINI_PROJECT=%s\n' "$GEMINI_MODEL" "$GEMINI_PROJECT"
```

## 3. SQLite 파일 생성 또는 잠금 오류가 날 때

확인 포인트:

1. `CHAT_DB_PATH` 상위 디렉터리에 쓰기 권한이 있는지 확인한다.
2. `SQLITE_BUSY_TIMEOUT_MS`가 너무 작지 않은지 확인한다.
3. 다중 프로세스 쓰기 부하가 높다면 SQLite 자체 한계일 수 있다.

## 4. SSE가 `done` 없이 끝나거나 timeout처럼 보일 때

확인 포인트:

1. `CHAT_STREAM_TIMEOUT_SECONDS`가 너무 작지 않은지 확인한다.
2. `error` 이벤트도 정상적인 종료 이벤트라는 점을 먼저 확인한다.
3. 이벤트 버퍼는 현재 기본 경로에서 `InMemoryEventBuffer`를 사용한다.
4. 브라우저는 `POST /chat` 이후 약 1초 뒤에 SSE 연결을 시작한다.

## 5. MongoDB 또는 Elasticsearch 연동이 실패할 때

MongoDB:

1. `MONGODB_AUTH_DB`와 실제 사용자 생성 DB가 일치하는지 확인한다.
2. `MONGODB_URI`를 직접 넣었으면 `authSource`가 포함됐는지 확인한다.

Elasticsearch:

1. `ELASTICSEARCH_CA_CERTS` 경로가 올바른지 확인한다.
2. self-signed 환경이면 `ELASTICSEARCH_VERIFY_CERTS`와 CA 파일이 같이 맞아야 한다.

## 6. 유지보수 포인트

1. 트러블슈팅 문서는 실제 코드가 읽는 환경 변수와 실제 기본 조립을 기준으로 써야 한다.
2. 기본 런타임 문제와 선택 확장 문제를 섞지 않는 편이 대응 속도를 높인다.
