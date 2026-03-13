# Shared Const 레퍼런스

`src/chatbot/shared/const/__init__.py`는 공통 상수 클래스 `SharedConst`를 제공한다.

## 1. 현재 정의

| 상수 | 값 | 의미 |
| --- | --- | --- |
| `DEFAULT_ENCODING` | `"utf-8"` | 파일 입출력 기본 인코딩 |
| `DEFAULT_TIMEZONE` | `"UTC"` | 기본 타임존 이름 |
| `ENV_NESTED_DELIMITER` | `"__"` | 환경 변수 중첩 키 구분자 |

## 2. 사용 위치

1. `ConfigLoader`가 `DEFAULT_ENCODING`, `ENV_NESTED_DELIMITER`를 사용한다.
2. `FileLogRepository`가 `DEFAULT_ENCODING`을 기본 인코딩으로 사용한다.

## 3. 유지보수 포인트

1. 공통 상수는 여러 계층에서 반복 사용하는 값만 두는 편이 좋다.
2. 채팅 전용 기본값은 `core/chat/const`에 두는 현재 경계를 유지해야 한다.
3. `ENV_NESTED_DELIMITER` 변경은 환경 변수 설계 전반에 영향을 준다.

## 4. 관련 문서

- `docs/shared/config.md`
- `docs/integrations/fs/file_repository.md`
