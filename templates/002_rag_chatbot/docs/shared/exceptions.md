# Shared Exceptions 가이드

이 문서는 `src/rag_chatbot/shared/exceptions`의 공통 예외 모델과 사용 규칙을 코드 기준으로 정리한다.

## 1. 용어 정리

| 용어 | 의미 | 관련 스크립트 |
| --- | --- | --- |
| BaseAppException | 계층 공통 베이스 예외 | `base.py` |
| ExceptionDetail | 오류 코드/원인/힌트를 담는 상세 모델 | `models.py` |
| detail.code | 오류 분류 코드 | 라우터 HTTP 매핑 기준 |
| original | 원본 예외 객체 | 디버깅용 선택 필드 |

## 2. 관련 스크립트

| 파일 | 역할 |
| --- | --- |
| `src/rag_chatbot/shared/exceptions/base.py` | 공통 예외 클래스 정의 |
| `src/rag_chatbot/shared/exceptions/models.py` | 상세 모델 정의 |
| `src/rag_chatbot/shared/exceptions/__init__.py` | 공개 API 제공 |
| `src/rag_chatbot/api/chat/routers/common.py` | Chat API 예외를 HTTP 상태로 매핑 |
| `src/rag_chatbot/api/ui/routers/common.py` | UI API 예외를 HTTP 상태로 매핑 |

## 3. 인터페이스 정의

## 3-1. ExceptionDetail

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `code` | `str` | 시스템 공통 오류 코드 |
| `cause` | `str \| None` | 직접 원인 설명 |
| `hint` | `str \| None` | 해결 힌트 |
| `metadata` | `dict[str, Any]` | 구조화 메타데이터 |

## 3-2. BaseAppException

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `message` | `str` | 사용자/시스템 공통 메시지 |
| `detail` | `ExceptionDetail` | 상세 오류 정보 |
| `original` | `Exception \| None` | 원본 예외 |

`to_dict()` 반환 구조:

```json
{
  "message": "...",
  "detail": {
    "code": "...",
    "cause": "...",
    "hint": null,
    "metadata": {}
  },
  "original": null
}
```

## 4. 사용 규칙

1. 모듈별 커스텀 예외 대신 `BaseAppException`으로 통일한다.
2. `detail.code`는 API 상태코드 매핑 기준으로 사용한다.
3. 민감 정보는 `message`, `metadata`에 직접 넣지 않는다.
4. `original`은 내부 디버깅 목적으로만 사용한다.

## 5. 구현 패턴

권장 패턴:

1. 비즈니스 조건 검증 실패 시 `ExceptionDetail(code=...)` 생성
2. `BaseAppException(message, detail)` 발생
3. 라우터 계층에서 `to_http_exception`으로 변환

예시:

```python
from rag_chatbot.shared.exceptions import BaseAppException, ExceptionDetail

if not session_id:
    detail = ExceptionDetail(code="CHAT_SESSION_NOT_FOUND", cause="session_id is empty")
    raise BaseAppException("요청한 세션을 찾을 수 없습니다.", detail)
```

## 6. 변경 작업 절차

1. 신규 오류 코드가 필요하면 먼저 코드 네이밍 규칙을 정의한다.
2. 발생 지점에서 `detail.code`, `cause`를 채운다.
3. API 라우터 예외 매핑 표를 함께 갱신한다.
4. 문서의 오류 응답 예시를 동기화한다.

## 7. 트러블슈팅

| 증상 | 원인 후보 | 확인 스크립트 | 조치 |
| --- | --- | --- | --- |
| 같은 오류가 500으로만 반환 | 라우터 매핑 누락 | `api/*/routers/common.py` | `detail.code` 매핑 추가 |
| 응답 detail 필드가 비어 있음 | `to_dict()` 미사용 | 라우터 예외 변환 구간 | `error.to_dict()` 사용 |
| 원인 추적이 어려움 | `cause` 미기록 | 예외 생성 지점 | `ExceptionDetail.cause` 채우기 |

## 8. 소스 매칭 점검 항목

1. 필드 정의가 `base.py`, `models.py`와 일치하는가
2. 예외 변환 경로가 Chat/UI 라우터 공통 유틸과 일치하는가
3. 문서 경로가 실제 파일 구조와 일치하는가

## 9. 관련 문서

- `docs/shared/overview.md`
- `docs/api/chat.md`
- `docs/api/ui.md`
