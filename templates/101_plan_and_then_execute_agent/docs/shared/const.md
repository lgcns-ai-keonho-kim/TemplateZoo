# Shared Const 문서

이 문서는 `src/plan_and_then_execute_agent/shared/const` 전역 상수의 의미와 사용 원칙을 정리한다.

## 1. 용어 정리

| 용어 | 의미 | 관련 스크립트 |
| --- | --- | --- |
| SharedConst | 전역 공통 상수 클래스 | `src/plan_and_then_execute_agent/shared/const/__init__.py` |
| 기본 인코딩 | 파일 입출력 기본 문자셋 | `DEFAULT_ENCODING` |
| 기본 타임존 | 시간 처리 기본 타임존 이름 | `DEFAULT_TIMEZONE` |
| ENV 중첩 구분자 | 환경 변수 키를 계층 구조로 해석하는 구분자 | `ENV_NESTED_DELIMITER` |

## 2. 관련 스크립트

| 파일 | 역할 |
| --- | --- |
| `src/plan_and_then_execute_agent/shared/const/__init__.py` | 공통 상수 정의 |
| `src/plan_and_then_execute_agent/shared/config/loader.py` | 중첩 구분자와 기본 인코딩 사용 |

## 3. 상수 인터페이스

| 상수 | 값 | 설명 |
| --- | --- | --- |
| `DEFAULT_ENCODING` | `"utf-8"` | 파일 입출력 기본 인코딩 |
| `DEFAULT_TIMEZONE` | `"UTC"` | 시간 처리 기본 타임존 |
| `ENV_NESTED_DELIMITER` | `"__"` | 환경 변수 중첩 키 파싱 구분자 |

## 4. 적용 기준

1. SharedConst는 여러 모듈에서 반복되는 공통 리터럴을 담는다.
2. 도메인 전용 상수는 `core/*/const` 경로에서 분리 관리된다.
3. 공통 리터럴 사용 구간은 SharedConst 참조를 기준으로 맞춰진다.

## 5. 확장 포인트

1. 상수값 변경 영향 범위는 참조 스크립트 검색으로 식별된다.
2. 파싱 규칙 관련 상수는 호환성 검토가 선행된다.
3. 상수값 변경 이력은 관련 문서에 함께 반영된다.

## 7. 관련 문서

- `docs/shared/config.md`
- `docs/shared/overview.md`
