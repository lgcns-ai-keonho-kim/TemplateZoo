# Shared Config 가이드

이 문서는 `src/rag_chatbot/shared/config`의 설정 병합과 런타임 환경 로딩 규칙을 코드 기준으로 정리한다.

## 1. 용어 정리

| 용어 | 의미 | 관련 스크립트 |
| --- | --- | --- |
| ConfigLoader | dict/json/env 소스를 누적해 설정을 병합하는 빌더 | `loader.py` |
| RuntimeEnvironmentLoader | `.env`와 런타임 환경 리소스 파일을 로딩하는 컴포넌트 | `runtime_env_loader.py` |
| ENV 후보 키 | 런타임 환경값을 읽을 때 확인하는 키 목록 | `ENV`, `APP_ENV`, `APP_STAGE` |
| 중첩 구분자 | 환경 변수 키를 계층 구조로 해석할 때 쓰는 구분자 | `SharedConst.ENV_NESTED_DELIMITER` |

## 2. 관련 스크립트

| 파일 | 역할 |
| --- | --- |
| `src/rag_chatbot/shared/config/loader.py` | 설정 소스 추가와 병합 수행 |
| `src/rag_chatbot/shared/config/runtime_env_loader.py` | 실행 환경 판별과 `.env` 로딩 |
| `src/rag_chatbot/shared/config/__init__.py` | 공개 API 제공 |
| `src/rag_chatbot/shared/const/__init__.py` | 인코딩/구분자 상수 제공 |
| `src/rag_chatbot/api/main.py` | 런타임 환경 로더 호출 지점 |

## 3. ConfigLoader 인터페이스

## 3-1. 소스 추가 메서드

1. `add_dict(data)`
2. `add_json_file(path, required=False, encoding=None)`
3. `add_env(prefix="", delimiter="__", lowercase_keys=True)`

## 3-2. 병합 메서드

- `build(overrides=None)`

동작 규칙:

1. 추가된 소스는 등록 순서대로 병합한다.
2. 나중에 등록한 소스가 같은 키를 덮어쓴다.
3. dict-dict 충돌은 재귀 병합한다.
4. `overrides`는 최종 우선순위다.

## 3-3. 환경 변수 파싱 규칙

기본 구분자:

- `SharedConst.ENV_NESTED_DELIMITER` 값 `__`

예시:

```text
APP__DB__HOST=127.0.0.1
-> {"app": {"db": {"host": "127.0.0.1"}}}
```

값 변환 규칙:

1. `true/false` -> bool
2. `null/none` -> None
3. 숫자 문자열 -> int/float
4. JSON 문자열 -> dict/list
5. 나머지 -> str

## 4. RuntimeEnvironmentLoader 인터페이스

## 4-1. load 동작 순서

`RuntimeEnvironmentLoader.load()` 기준:

1. 프로젝트 루트 `.env`를 먼저 로드한다.
2. `ENV`, `APP_ENV`, `APP_STAGE`에서 환경값을 판별한다.
3. 값이 없으면 `local`로 처리한다.
4. `dev/stg/prod`면 `src/rag_chatbot/resources/<env>/.env`를 추가 로드한다.
5. 최종 환경값을 `os.environ["ENV"]`에 기록한다.

## 4-2. 지원 환경값

1. `local`
2. `dev`
3. `stg`
4. `prod`

alias:

1. `development -> dev`
2. `staging -> stg`
3. `production -> prod`

## 4-3. 예외 조건

1. 지원하지 않는 환경값이면 `ValueError`
2. 필수 리소스 디렉터리/파일이 없으면 `FileNotFoundError`
3. 필수 JSON 파일이 없으면 `FileNotFoundError`
4. JSON 파싱 실패 시 `ValueError`

## 5. 실제 사용 경로

1. `src/rag_chatbot/api/main.py`에서 `RuntimeEnvironmentLoader().load()` 실행
2. `.env` 로딩 완료 후 라우터/서비스 import
3. import 시점 생성 객체가 환경 변수값을 읽어 조립됨

## 6. 변경 작업 절차

## 6-1. 새 설정 파일 추가

1. `ConfigLoader.add_json_file` 호출 지점을 추가한다.
2. `required` 여부를 환경별 정책으로 결정한다.
3. 기본값과 override 우선순위를 문서화한다.

## 6-2. 환경 키 전략 변경

1. `RuntimeEnvironmentLoader`의 key candidates를 조정한다.
2. alias 맵을 함께 갱신한다.
3. 운영 배포 스크립트의 ENV 주입 규칙을 동기화한다.

## 6-3. 중첩 구분자 변경

1. `SharedConst.ENV_NESTED_DELIMITER` 변경 영향도를 분석한다.
2. 기존 환경 변수 이름과의 호환 전략을 수립한다.
3. `ConfigLoader.add_env` 호출부의 delimiter 인자를 점검한다.

## 7. 트러블슈팅

| 증상 | 원인 후보 | 확인 스크립트 | 조치 |
| --- | --- | --- | --- |
| 환경값이 local로 고정됨 | ENV 후보 키 미주입 | `runtime_env_loader.py` | `ENV`/`APP_ENV` 주입 확인 |
| JSON 설정이 반영되지 않음 | 경로 오타 또는 required=False | `loader.py` | 파일 존재 여부와 로그 확인 |
| 숫자/불린이 문자열로 남음 | 파싱 규칙 외 문자열 | `loader.py` | 입력값 형식 조정 또는 후처리 추가 |
| 예상과 다른 설정이 최종값으로 적용 | 병합 우선순위 착오 | `ConfigLoader.build` 호출부 | 소스 등록 순서 재정렬 |

## 8. 소스 매칭 점검 항목

1. 문서의 load 순서가 `runtime_env_loader.py` 코드와 일치하는가
2. 지원 환경값 목록이 `_SUPPORTED_ENVS`, `_ENV_ALIASES`와 일치하는가
3. 중첩 구분자 설명이 `SharedConst` 값과 일치하는가
4. 파일 경로가 실제 `src/rag_chatbot/shared/config` 구조와 일치하는가

## 9. 관련 문서

- `docs/shared/overview.md`
- `docs/shared/const.md`
- `docs/api/overview.md`
