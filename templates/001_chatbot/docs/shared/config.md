# Shared Config 레퍼런스

`src/chatbot/shared/config`은 일반 설정 병합과 런타임 환경별 `.env` 로딩을 담당한다.

## 1. 코드 설명

공개 API:

1. `ConfigLoader`
2. `RuntimeEnvironmentLoader`

### 1-1. `ConfigLoader`

지원 소스:

1. `add_dict()`
2. `add_json_file()`
3. `add_env()`

병합 규칙:

1. 먼저 등록한 소스부터 순서대로 병합
2. 같은 키가 겹치면 나중 값이 우선
3. 중첩 dict는 재귀 병합

환경 변수 파싱 규칙:

1. `true/false` -> bool
2. `null/none` -> `None`
3. 숫자 문자열 -> `int`, `float`
4. `{...}`, `[...]` -> JSON 파싱 시도

### 1-2. `RuntimeEnvironmentLoader`

동작 순서:

1. 루트 `.env` 로드
2. `ENV`, `APP_ENV`, `APP_STAGE` 중 첫 값을 읽음
3. 비어 있으면 `local`
4. `dev/stg/prod`면 `src/chatbot/resources/<env>/.env` 추가 로드

지원 환경:

1. `local`
2. `dev`
3. `stg`
4. `prod`

별칭:

1. `development -> dev`
2. `staging -> stg`
3. `production -> prod`

## 2. 유지보수 포인트

1. `RuntimeEnvironmentLoader`는 앱 import 전에 실행되어야 한다. 그렇지 않으면 모듈 레벨에서 읽는 환경 변수값이 최신값을 보지 못한다.
2. `ConfigLoader.add_env()`의 기본 구분자는 `SharedConst.ENV_NESTED_DELIMITER`다. 이 값을 바꾸면 중첩 키 해석 규칙이 전체적으로 바뀐다.
3. `resources/<env>/.env` 파일명이 고정이므로, 샘플 파일과 실제 파일을 혼동하지 않도록 운영 가이드를 함께 유지해야 한다.

## 3. 추가 개발/확장 가이드

1. 런타임 환경 종류를 추가하려면 지원 환경 집합, 별칭, 리소스 디렉터리까지 함께 맞춰야 한다.
2. JSON 기반 설정을 도입해도 병합 우선순위는 문서에 함께 적어 두는 편이 운영 혼선을 줄인다.

## 4. 관련 코드

- `src/chatbot/shared/const/__init__.py`
- `src/chatbot/api/main.py`
