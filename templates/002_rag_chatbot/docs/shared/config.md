# Shared Config 가이드

이 문서는 설정 병합기(`ConfigLoader`)와 런타임 환경 로더(`RuntimeEnvironmentLoader`)의 현재 동작을 정리한다.

## 1. ConfigLoader

- `add_dict`, `add_json_file`, `add_env`로 설정 소스를 순서대로 누적한다.
- `build()`는 나중에 등록한 값이 앞선 값을 덮어쓰도록 병합한다.
- 환경 변수는 `__` 구분자를 중첩 키로 해석하고, bool/number/json 문자열을 가능한 범위에서 자동 변환한다.

## 2. RuntimeEnvironmentLoader

- 루트 `.env`를 먼저 로드한다.
- `ENV`, `APP_ENV`, `APP_STAGE` 중 먼저 들어온 값을 환경으로 사용한다.
- 비어 있으면 `local`이다.
- `dev/stg/prod`면 `src/rag_chatbot/resources/<env>/.env`를 추가 로드한다.
- 최종 환경값을 `os.environ["ENV"]`에 다시 기록한다.

## 3. 유지보수/추가개발 포인트

- import 시점에 환경 변수를 읽는 모듈이 있으므로 환경 로딩 순서를 바꾸면 초기화 타이밍까지 함께 점검해야 한다.
- 설정 키 추가 시 `.env.sample`, `docs/setup/env.md`, 실제 소비 지점을 같이 갱신하는 편이 안전하다.
- 중첩 구분자나 ENV alias를 바꾸면 배포 스크립트와 운영 변수명도 같이 바뀐다.

## 4. 관련 문서

- `docs/setup/env.md`
- `docs/shared/overview.md`
- `docs/api/overview.md`
