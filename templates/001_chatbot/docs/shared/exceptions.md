# Shared Exceptions 레퍼런스

`src/chatbot/shared/exceptions`은 애플리케이션 전역에서 쓰는 공통 예외 모델을 제공한다.

## 1. 핵심 타입

### 1-1. `ExceptionDetail`

주요 필드:

1. `code`
2. `cause`
3. `hint`
4. `metadata`

### 1-2. `BaseAppException`

보관 정보:

1. 사용자/시스템 메시지
2. `ExceptionDetail`
3. 원본 예외 객체

`to_dict()`는 아래 구조를 반환한다.

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

1. `detail.code`는 라우터 계층의 HTTP 상태코드 매핑 기준이다.
2. `cause`에는 디버깅에 필요한 최소 정보만 넣는 편이 안전하다.
3. API로 노출될 수 있으므로 민감한 원본 예외를 직접 넣는 경로를 주의해야 한다.

## 3. 관련 문서

- `docs/api/overview.md`
- `docs/api/chat.md`
- `docs/api/ui.md`
