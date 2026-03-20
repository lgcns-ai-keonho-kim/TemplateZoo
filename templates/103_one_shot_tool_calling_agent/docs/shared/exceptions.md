# Shared Exceptions

`src/one_shot_tool_calling_agent/shared/exceptions`의 공통 예외 모델과 사용 규칙을 정리한다.

## 1. 관련 스크립트

| 파일 | 역할 |
| --- | --- |
| `src/one_shot_tool_calling_agent/shared/exceptions/base.py` | 공통 예외 클래스 정의 |
| `src/one_shot_tool_calling_agent/shared/exceptions/models.py` | 상세 모델 정의 |
| `src/one_shot_tool_calling_agent/shared/exceptions/__init__.py` | 공개 API 제공 |
| `src/one_shot_tool_calling_agent/api/agent/routers/common.py` | Agent API 예외를 HTTP 상태로 매핑 |

## 2. 핵심 구조

### 2-1. ExceptionDetail

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `code` | `str` | 시스템 공통 오류 코드 |
| `cause` | `str \| None` | 직접 원인 설명 |
| `hint` | `str \| None` | 해결 힌트 |
| `metadata` | `dict[str, Any]` | 구조화 메타데이터 |

### 2-2. BaseAppException

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `message` | `str` | 사용자/시스템 공통 메시지 |
| `detail` | `ExceptionDetail` | 상세 오류 정보 |
| `original` | `Exception \| None` | 원본 예외 |

## 3. 현재 기본 사용 규칙

1. 도메인/서비스 예외는 `BaseAppException`으로 통일한다.
2. 라우터는 `detail.code`를 기준으로 HTTP 상태를 매핑한다.
3. 현재 기본 `/agent` 경로에서는 `AGENT_REQUEST_EMPTY`, `AGENT_REQUEST_TIMEOUT` 같은 코드가 대표적으로 사용된다.
4. 민감 정보는 `message`나 `metadata`에 직접 넣지 않는다.

예시:

```python
from one_shot_tool_calling_agent.shared.exceptions import BaseAppException, ExceptionDetail

detail = ExceptionDetail(code="AGENT_REQUEST_EMPTY", cause="request is empty")
raise BaseAppException("요청 본문은 비어 있을 수 없습니다.", detail)
```

## 4. 관련 문서

- `docs/shared/overview.md`
- `docs/api/agent.md`
