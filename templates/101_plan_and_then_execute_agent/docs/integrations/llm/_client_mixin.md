# Client Mixin

## 개요

`src/plan_and_then_execute_agent/integrations/llm/_client_mixin.py` 구현을 기준으로 현재 동작을 정리한다.

- LLMClient 보조 메서드 믹스인을 제공한다.
- 로깅 보호, 백그라운드 실행, 메시지/결과 직렬화 및 청크 정규화를 분리한다.
- 구현 형태: 믹스인

## 주요 구성

- 클래스: `_LLMClientMixin`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/plan_and_then_execute_agent/integrations/llm/client.py`
