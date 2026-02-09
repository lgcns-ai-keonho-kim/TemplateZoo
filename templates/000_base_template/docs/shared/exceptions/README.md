# 공통 예외 명세

이 문서는 `src/base_template/shared/exceptions`의 예외 모델과 전달 형식을 정의한다.

## 구성 요소

| 타입 | 파일 | 역할 |
| --- | --- | --- |
| `ExceptionDetail` | `shared/exceptions/models.py` | 에러 코드/원인/힌트/메타데이터 구조 |
| `BaseAppException` | `shared/exceptions/base.py` | 메시지 + 상세 모델 + 원본 예외를 묶는 공통 예외 |

## 데이터 계약

### `ExceptionDetail`

- `code`: 시스템 전역 에러 코드
- `cause`: 직접 원인
- `hint`: 해결 힌트
- `metadata`: 구조화 부가 정보

### `BaseAppException`

- `message`: 사용자/시스템 메시지
- `detail`: `ExceptionDetail`
- `original`: 원본 예외(`Exception | None`)
- `to_dict()`: 직렬화 가능한 예외 페이로드 반환

## 사용 규칙

1. 도메인/인프라 오류는 `BaseAppException`으로 표준화한다.
2. `detail.code`는 API 상태코드 매핑의 기준 필드다.
3. `metadata`에는 구조화된 진단 데이터만 저장한다.
4. 민감정보는 `message`와 `metadata`에 포함하지 않는다.

## 의존성

```text
api/router -> BaseAppException.to_dict()
api/service, runtime, repository -> BaseAppException raise
```

## 예시

```python
from base_template.shared.exceptions import BaseAppException, ExceptionDetail

try:
    raise ValueError("invalid")
except ValueError as error:
    detail = ExceptionDetail(code="INPUT_INVALID", cause=str(error))
    raise BaseAppException("요청 처리에 실패했습니다.", detail, error) from error
```
