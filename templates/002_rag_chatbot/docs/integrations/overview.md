# Integrations 모듈 가이드

이 문서는 외부 시스템 연동 계층의 현재 범위와 확장 지점을 설명한다.

## 1. 현재 구성

- `integrations/db`: 엔진 포트, 스키마 모델, query builder, 백엔드 구현체
- `integrations/llm`: LLM 모델 래퍼
- `integrations/embedding`: 임베딩 모델 래퍼
- `integrations/fs`: 파일 시스템 기반 저장소

## 2. 책임 경계

- integrations는 외부 제품의 API, 연결, 데이터 표현 차이를 흡수한다.
- 채팅 정책, HTTP 라우팅, 세션 유스케이스 결정은 이 계층의 책임이 아니다.
- 엔진 선택은 주로 `runtime.py`와 ingestion 러너에서 수행한다.

## 3. 유지보수/추가개발 포인트

- 새 백엔드를 붙일 때는 포트 계약을 먼저 맞추고, 실제 조립 경로가 있는지 별도로 확인해야 한다.
- 현재 repo에 구현이 있어도 runtime이나 core에서 직접 사용하지 않으면 "확장 가능"이지 "활성 사용"은 아니다.
- 환경 변수 문서는 setup 문서와 함께 유지해야 실제 사용 경로를 추적하기 쉽다.

## 4. 관련 문서

- `docs/integrations/db/README.md`
- `docs/integrations/llm/README.md`
- `docs/integrations/embedding/README.md`
- `docs/integrations/fs/README.md`
- `docs/setup/overview.md`
