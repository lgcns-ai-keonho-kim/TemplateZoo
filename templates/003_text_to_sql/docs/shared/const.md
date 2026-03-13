# Shared Const

`src/text_to_sql/shared/const` 전역 상수의 의미와 사용 원칙을 정리한다.

## 1. 용어 정리

| 용어 | 의미 | 관련 스크립트 |
| --- | --- | --- |
| SharedConst | 전역 공통 상수 클래스 | `src/text_to_sql/shared/const/__init__.py` |
| 기본 인코딩 | 파일 입출력 기본 문자셋 | `DEFAULT_ENCODING` |
| 기본 타임존 | 시간 처리 기본 타임존 이름 | `DEFAULT_TIMEZONE` |
| ENV 중첩 구분자 | 환경 변수 키를 계층 구조로 해석하는 구분자 | `ENV_NESTED_DELIMITER` |

## 2. 관련 스크립트

| 파일 | 역할 |
| --- | --- |
| `src/text_to_sql/shared/const/__init__.py` | 공통 상수 정의 |
| `src/text_to_sql/shared/config/loader.py` | 중첩 구분자와 기본 인코딩 사용 |

## 3. 상수 인터페이스

| 상수 | 값 | 설명 |
| --- | --- | --- |
| `DEFAULT_ENCODING` | `"utf-8"` | 파일 입출력 기본 인코딩 |
| `DEFAULT_TIMEZONE` | `"UTC"` | 시간 처리 기본 타임존 |
| `ENV_NESTED_DELIMITER` | `"__"` | 환경 변수 중첩 키 파싱 구분자 |

## 4. 사용 원칙

1. 여러 모듈에서 반복되는 리터럴만 SharedConst로 관리한다.
2. 도메인 전용 상수는 `core/*/const`에 둔다.
3. 문자열 리터럴 하드코딩보다 SharedConst 참조를 우선한다.

## 5. 관련 문서

- `docs/shared/config.md`
- `docs/shared/overview.md`
