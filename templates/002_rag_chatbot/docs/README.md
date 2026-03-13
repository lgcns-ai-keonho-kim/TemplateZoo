# 개발 문서

## 우선 확인

1. `docs/api/overview.md`
2. `docs/core/chat.md`
3. `docs/shared/chat/README.md`
4. `docs/shared/runtime.md`
5. `docs/integrations/overview.md`
6. `docs/setup/overview.md`
7. `docs/static/ui.md`

## 문서 묶음

- `docs/api`: FastAPI 경계, DTO, 런타임 조립, HTTP 계약
- `docs/core`: 채팅 그래프, 상태 키, 노드 분기, 프롬프트 사용 경로
- `docs/shared`: 서비스 실행, 저장소, 런타임 인프라, 설정, 로깅, 예외
- `docs/integrations`: DB, LLM, 임베딩, 파일 시스템 어댑터
- `docs/setup`: 환경 변수, ingestion, 백엔드 준비 절차
- `docs/static`: 정적 UI 구조와 API 소비 방식

## 코드 기준 체크포인트

- 활성 경로와 확장 가능 경로를 구분해서 읽는다.
- 환경 변수는 `.env.sample`이 아니라 실제 `os.getenv()` 사용 지점을 기준으로 본다.
- DB 엔진 구현이 있어도 `runtime.py`나 ingestion에서 조립되지 않으면 기본 경로가 아니다.
- SSE, UI, Chat 서비스 문서는 함께 맞춰야 실제 동작과 어긋나지 않는다.
