# Shared Config 레퍼런스

`src/chatbot/shared/config`은 일반 설정 병합과 런타임 환경별 `.env` 로딩을 담당한다.

## 1. 공개 API

1. `ConfigLoader`
2. `RuntimeEnvironmentLoader`

## 2. `ConfigLoader`

지원 입력:

1. `add_dict()`
2. `add_json_file()`
3. `add_env()`

병합 규칙:

1. 먼저 등록한 소스부터 순서대로 병합한다.
2. 같은 키가 겹치면 나중 값이 우선한다.
3. 중첩 `dict`는 재귀 병합한다.

환경 변수 파싱 규칙:

1. `true/false` -> `bool`
2. `null/none` -> `None`
3. 숫자 문자열 -> `int` 또는 `float`
4. JSON 모양 문자열 -> `json.loads()` 시도

중첩 키 구분자는 `SharedConst.ENV_NESTED_DELIMITER`, 현재 기본값은 `"__"`다.

## 3. `RuntimeEnvironmentLoader`

동작 순서:

1. 루트 `.env`를 먼저 로드한다.
2. `ENV`, `APP_ENV`, `APP_STAGE` 중 첫 번째 값으로 런타임 환경을 정한다.
3. 비어 있으면 `local`로 본다.
4. `development -> dev`, `staging -> stg`, `production -> prod`로 정규화한다.
5. `dev`, `stg`, `prod`인 경우 `src/chatbot/resources/<env>/.env`를 추가 로드한다.

지원 환경:

1. `local`
2. `dev`
3. `stg`
4. `prod`

## 4. 유지보수 포인트

1. 이 로더는 앱 import 전에 실행돼야 한다.
2. 환경별 실제 파일 이름은 `.env`다. `.env.sample`은 자동으로 읽지 않는다.
3. 새 환경을 추가하면 지원 환경 집합, 별칭, 리소스 디렉터리 구조를 같이 수정해야 한다.

## 5. 관련 문서

- `docs/setup/env.md`
- `docs/setup/troubleshooting.md`
