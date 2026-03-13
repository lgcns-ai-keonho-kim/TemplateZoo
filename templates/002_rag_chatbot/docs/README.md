# 개발 문서 허브

이 문서는 `src/rag_chatbot`과 `ingestion`의 현재 구조를 기준으로, 어떤 문서를 먼저 읽어야 하는지와 유지보수 시 확인해야 할 경계를 정리한다.

## 1. 문서 묶음

- `docs/api`: FastAPI 라우터, DTO, 런타임 조립, HTTP 경계
- `docs/core`: 채팅 그래프, 프롬프트, 상태 키, 노드 분기
- `docs/shared`: 서비스 실행기, 저장소, 런타임 인프라, 설정, 로깅, 예외
- `docs/integrations`: DB, LLM, 임베딩, 파일 시스템 어댑터
- `docs/setup`: `.env`, ingestion, 백엔드 준비 절차
- `docs/static`: 정적 UI 구조와 API 소비 방식

## 2. 권장 읽기 순서

1. `docs/api/overview.md`
2. `docs/core/chat.md`
3. `docs/shared/chat/README.md`
4. `docs/shared/runtime.md`
5. `docs/integrations/overview.md`
6. `docs/setup/overview.md`
7. `docs/static/ui.md`

## 3. 변경 유형별 진입 문서

- API 응답/요청 형식 변경: `docs/api/chat.md`, `docs/api/ui.md`
- 그래프 분기나 노드 정책 변경: `docs/core/chat.md`
- 세션 저장, 멱등, 실행 흐름 변경: `docs/shared/chat/README.md`, `docs/shared/chat/services/*.md`
- 큐/버퍼/타임아웃 변경: `docs/shared/runtime.md`, `docs/shared/config.md`
- DB 엔진 교체 또는 스키마 변경: `docs/integrations/db/README.md`, `docs/integrations/db/**/*.md`
- ingestion 파이프라인 변경: `docs/setup/ingestion.md`
- 프런트 상태/스트림 처리 변경: `docs/static/ui.md`

## 4. 유지보수 원칙

- 문서의 경로와 타입 이름은 실제 코드 경로, 공개 메서드, 환경 변수 이름과 1:1로 맞춘다.
- 실행 흐름 문서는 "지금 실제로 쓰는 경로"와 "확장 가능하지만 아직 조립되지 않은 경로"를 구분해서 적는다.
- 설정 문서는 `.env.sample`의 예시값과 코드 기본값을 분리해서 설명한다.
- 새 기능을 추가할 때는 상위 개요 문서와 세부 모듈 문서를 함께 갱신해 탐색 비용을 줄인다.

## 5. 관련 문서

- `docs/api/overview.md`
- `docs/core/overview.md`
- `docs/shared/overview.md`
- `docs/integrations/overview.md`
- `docs/setup/overview.md`
- `docs/static/ui.md`
