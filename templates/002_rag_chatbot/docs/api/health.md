# API Health 가이드

이 문서는 `GET /health` 엔드포인트의 현재 범위와 유지보수 지점을 설명한다.

## 1. 현재 동작

- 경로: `/health`
- 메서드: `GET`
- 응답: `200`, `{"status": "ok"}`
- 목적: 프로세스 liveness 확인

## 2. 포함하지 않는 범위

- DB 연결 상태
- LLM 공급자 연결 상태
- 벡터 저장소 readiness
- 워커 큐 적재 가능 여부

## 3. 유지보수/추가개발 포인트

- readiness가 필요하면 `/health`를 확장하기보다 별도 경로를 두는 편이 운영 의미를 분리하기 쉽다.
- 외부 의존성 확인을 추가하면 timeout과 실패 기준을 문서에 명시해야 한다.

## 4. 관련 문서

- `docs/api/overview.md`
- `docs/shared/runtime.md`
