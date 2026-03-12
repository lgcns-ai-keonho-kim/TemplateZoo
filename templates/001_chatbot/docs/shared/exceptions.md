# Shared Exceptions 레퍼런스

`src/chatbot/shared/exceptions`은 애플리케이션 전역에서 공통으로 쓰는 예외 모델을 제공한다.

## 1. 코드 설명

핵심 타입:

1. `ExceptionDetail`
2. `BaseAppException`

### 1-1. `ExceptionDetail`

필드:

1. `code`
2. `cause`
3. `hint`
4. `metadata`

### 1-2. `BaseAppException`

보관 정보:

1. 사용자/시스템 메시지
2. `ExceptionDetail`
3. 원본 예외 객체(`original`)

`to_dict()`는 다음 구조를 반환한다.

```json
{
  "message": "요청한 세션을 찾을 수 없습니다.",
  "detail": {
    "code": "CHAT_SESSION_NOT_FOUND",
    "cause": "session_id=..."
  },
  "original": null
}
```

## 2. 유지보수 포인트

1. `detail.code`는 라우터 계층에서 HTTP 상태 매핑 기준으로 사용된다.
2. `cause`에는 디버깅에 필요한 최소 정보만 넣고, 민감한 값은 그대로 노출하지 않는 편이 좋다.
3. 원본 예외는 `repr()`로 직렬화되므로, API 응답에 그대로 노출하는 경로가 있는지 항상 확인해야 한다.

## 3. 추가 개발/확장 가이드

1. 새 오류 코드가 필요하면 먼저 기존 코드 체계(`CHAT_*`, `FUNCTION_NODE_*` 등)와 같은 수준으로 맞추는 것이 좋다.
2. 계층별 개별 예외 클래스를 많이 늘리기보다 현재처럼 공통 예외 + 상세 코드 구조를 유지하는 편이 API 매핑이 단순하다.

## 4. 관련 코드

- `src/chatbot/api/chat/routers/common.py`
- `src/chatbot/api/ui/routers/common.py`
