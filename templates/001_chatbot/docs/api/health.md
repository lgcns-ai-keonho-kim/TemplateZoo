# API Health 레퍼런스

이 문서는 `/health` 엔드포인트의 현재 구현과 확장 기준을 정리한다.

## 1. 현재 구현

관련 코드:

1. `src/chatbot/api/health/routers/server.py`
2. `src/chatbot/api/main.py`

현재 인터페이스:

- Method: `GET`
- Path: `/health`
- 상태코드: `200 OK`

응답:

```json
{
  "status": "ok"
}
```

## 2. 코드 설명

현재 헬스체크는 고정 JSON을 반환하는 liveness 엔드포인트다.

구현 특징:

1. DB, LLM, 큐, 이벤트 버퍼 연결 상태를 검사하지 않는다.
2. 라우터 내부에 외부 의존성 접근이 없다.
3. 앱 등록은 `src/chatbot/api/main.py`에서 수행된다.

## 3. 유지보수 포인트

1. `/health`는 빠른 생존 확인이 목적이므로 고비용 검사를 넣지 않는 편이 안전하다.
2. 로드밸런서나 모니터링 시스템이 이 경로를 사용 중일 가능성이 높으므로 응답 구조는 보수적으로 바꿔야 한다.
3. `status` 필드를 제거하거나 이름을 바꾸면 외부 시스템이 깨질 수 있다.

## 4. 추가 개발과 확장 가이드

### 4-1. readiness 분리

외부 의존성 상태를 확인하고 싶다면 기존 `/health`를 바꾸기보다 별도 readiness 경로를 추가하는 편이 안전하다.

권장 절차:

1. `src/chatbot/api/health/routers`에 새 라우터를 추가한다.
2. `src/chatbot/api/main.py`에 등록한다.
3. `/health`는 현재 응답을 유지한다.

### 4-2. 응답 확장

필드 추가가 필요하면:

1. 기존 `status`는 유지한다.
2. 새 필드는 하위 호환으로 추가한다.
3. 운영 환경 모니터링 파서와 함께 맞춘다.

## 5. 관련 문서

- `docs/api/overview.md`
