# Client 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/llm/client.py`

## 역할

- 목적: LangChain BaseChatModel 기반 LLM 클라이언트를 제공한다.
- 설명: 기존 메서드(invoke/ainvoke/stream/astream)를 유지하면서 로깅과 예외 처리를 통합한다.
- 디자인 패턴: 프록시, 데코레이터

## 주요 구성

- 클래스: `LLMClient`
- 함수: 없음

## 실패 경로

- `LLM_AINVOKE_ERROR`
- `LLM_ASTREAM_ERROR`
- `LLM_ASTREAM_NOT_SUPPORTED`
- `LLM_INVOKE_ERROR`
- `LLM_STREAM_EMPTY`
- `LLM_STREAM_ERROR`
- `LLM_STREAM_NOT_SUPPORTED`

## 연관 코드

- `src/plan_and_then_execute_agent/shared/logging`
- `src/plan_and_then_execute_agent/shared/exceptions`
