# 예외 공통 가이드

이 문서는 `src/base_template/shared/exceptions` 모듈을 설명합니다.

**목적**

- 시스템 전반에서 통일된 예외 형식을 제공합니다.
- 메시지(사용자 노출)와 상세 정보(운영/디버깅)를 분리합니다.

**구성 요소**

- `ExceptionDetail`: 에러 코드, 원인, 힌트, 메타데이터
- `BaseAppException`: 공통 예외 베이스 클래스

## 기본 사용법

```python
from base_template.shared.exceptions import BaseAppException, ExceptionDetail

try:
    raise ValueError("잘못된 입력")
except ValueError as exc:
    detail = ExceptionDetail(
        code="INPUT_INVALID",
        cause=str(exc),
        hint="입력 값을 확인하세요",
        metadata={"field": "title"},
    )
    raise BaseAppException("요청이 실패했습니다.", detail, exc)
```

## 권장 에러 코드 규칙

- 도메인 접두사 + 원인 코드 형태를 사용합니다.
- 예시: `DB_CONNECT_ERROR`, `LLM_INVOKE_ERROR`, `QUEUE_PUSH_FAIL`

## to_dict 활용

- `BaseAppException.to_dict()`로 JSON 응답 형태를 쉽게 만들 수 있습니다.

```python
try:
    ...
except BaseAppException as exc:
    payload = exc.to_dict()
```

## 주의 사항

- 메시지는 외부에서 주입하는 구조입니다.
- `ExceptionDetail.metadata`에는 민감한 정보를 넣지 않습니다.
