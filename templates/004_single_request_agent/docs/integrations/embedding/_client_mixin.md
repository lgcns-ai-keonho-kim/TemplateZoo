# Client Mixin

## 개요

`src/single_request_agent/integrations/embedding/_client_mixin.py` 구현을 기준으로 현재 동작을 정리한다.

- EmbeddingClient 보조 메서드 믹스인을 제공한다.
- 임베딩 호출 로깅/백그라운드 실행/컨텍스트 조회 책임을 분리한다.
- 구현 형태: 믹스인

## 주요 구성

- 클래스: `_EmbeddingClientMixin`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/single_request_agent/integrations/embedding/client.py`
