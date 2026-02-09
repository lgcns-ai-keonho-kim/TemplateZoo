# 공통 상수 명세

이 문서는 `src/base_template/shared/const/__init__.py`의 `SharedConst`를 정의한다.

## 상수 목록

| 상수 | 값 | 사용 목적 |
| --- | --- | --- |
| `DEFAULT_ENCODING` | `"utf-8"` | 파일 읽기/쓰기 기본 인코딩 |
| `DEFAULT_TIMEZONE` | `"UTC"` | 시간대 기본값 |
| `ENV_NESTED_DELIMITER` | `"__"` | 환경 변수 중첩 키 구분자 |

## 사용 지점

- `shared/config/loader.py`에서 인코딩/환경변수 파싱 기준으로 사용한다.
- 공통 설정 로직은 이 상수 값을 단일 진실 소스로 사용한다.

## 의존성

`SharedConst`는 외부 의존이 없는 순수 상수 객체다.
