# Shared Const 가이드

이 문서는 `src/base_template/shared/const` 전역 상수의 의미와 사용 원칙을 정리한다.

## 1. 용어 정리

| 용어 | 의미 | 관련 스크립트 |
| --- | --- | --- |
| SharedConst | 전역 공통 상수 클래스 | `src/base_template/shared/const/__init__.py` |
| 기본 인코딩 | 파일 입출력 기본 문자셋 | `DEFAULT_ENCODING` |
| 기본 타임존 | 시간 처리 기본 타임존 이름 | `DEFAULT_TIMEZONE` |
| ENV 중첩 구분자 | 환경 변수 키를 계층 구조로 해석하는 구분자 | `ENV_NESTED_DELIMITER` |

## 2. 관련 스크립트

| 파일 | 역할 |
| --- | --- |
| `src/base_template/shared/const/__init__.py` | 공통 상수 정의 |
| `src/base_template/shared/config/loader.py` | 중첩 구분자와 기본 인코딩 사용 |

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

## 5. 변경 작업 절차

1. 상수값 변경 전 참조 스크립트를 검색한다.
2. 파싱 규칙에 영향을 주는 값은 호환성 검토를 먼저 수행한다.
3. 변경 후 관련 문서를 함께 갱신한다.

## 6. 소스 매칭 점검 항목

1. 상수값 설명이 `shared/const/__init__.py`와 일치하는가
2. 참조 스크립트 경로가 실제로 존재하는가

## 7. 관련 문서

- `docs/shared/config.md`
- `docs/shared/overview.md`
