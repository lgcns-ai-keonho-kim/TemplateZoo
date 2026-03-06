# Client Mixin 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/embedding/_client_mixin.py`

## 역할

- 목적: EmbeddingClient 보조 메서드 믹스인을 제공한다.
- 설명: 임베딩 호출 로깅/백그라운드 실행/컨텍스트 조회 책임을 분리한다.
- 디자인 패턴: 믹스인

## 주요 구성

- 클래스: `_EmbeddingClientMixin`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 연관 코드

- `src/plan_and_then_execute_agent/integrations/embedding/client.py`
