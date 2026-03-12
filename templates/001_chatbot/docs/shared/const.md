# Shared Const 레퍼런스

`src/chatbot/shared/const/__init__.py`는 공통 상수 집합 `SharedConst`를 제공한다.

## 1. 코드 설명

현재 정의된 값:

| 상수 | 값 | 의미 |
| --- | --- | --- |
| `DEFAULT_ENCODING` | `"utf-8"` | 파일 입출력 기본 인코딩 |
| `DEFAULT_TIMEZONE` | `"UTC"` | 시간 처리 기본 타임존 |
| `ENV_NESTED_DELIMITER` | `"__"` | 환경 변수 중첩 키 구분자 |

현재 직접 사용하는 대표 경로:

1. `ConfigLoader`가 `DEFAULT_ENCODING`, `ENV_NESTED_DELIMITER` 사용

## 2. 유지보수 포인트

1. 도메인 전용 상수와 공통 상수를 섞지 않는 것이 중요하다. 채팅 전용 기본값은 `core/chat/const`에 두는 현재 경계를 유지하는 편이 좋다.
2. `ENV_NESTED_DELIMITER`를 바꾸면 환경 변수 설계 규칙이 달라지므로 영향 범위가 넓다.

## 3. 추가 개발/확장 가이드

1. 정말 여러 계층에서 반복되는 값만 여기에 추가하는 것이 적절하다.
2. 새 상수를 추가할 때는 실제 참조 경로가 두 곳 이상 있는지 먼저 확인하는 편이 좋다.

## 4. 관련 코드

- `src/chatbot/shared/config/loader.py`
- `src/chatbot/shared/config/runtime_env_loader.py`
