# `llm/client.py` 레퍼런스

## 1. 모듈 목적

- 목적: LangChain BaseChatModel 기반 LLM 클라이언트를 제공한다.
- 설명: 기존 메서드(invoke/ainvoke/stream/astream)를 유지하면서 로깅과 예외 처리를 통합한다.
- 디자인 패턴: 프록시, 데코레이터

## 2. 핵심 심볼

- `class LLMClient`

## 3. 입력/출력 관점

- LLMClient가 모델 호출(invoke/stream)과 로깅/예외 표준화를 제공한다.
- 소스 경로: `src/chatbot/integrations/llm/client.py`
- 문서 경로: `docs/integrations/llm/client.md`

## 4. 실패 경로

- 이 파일에서 사용하는 예외 코드:
  - `LLM_AINVOKE_ERROR`
  - `LLM_ASTREAM_ERROR`
  - `LLM_ASTREAM_NOT_SUPPORTED`
  - `LLM_INVOKE_ERROR`
  - `LLM_STREAM_EMPTY`
  - `LLM_STREAM_ERROR`
  - `LLM_STREAM_NOT_SUPPORTED`

## 5. 연계 모듈

- `src/chatbot/shared/logging`
- `src/chatbot/shared/exceptions`

## 6. 변경 영향 범위

- 호출/예외/로깅 정책 변경 시 core 노드와 관측 지표 수집 경로가 영향을 받는다.
- 변경 후에는 `docs/integrations/overview.md` 및 해당 하위 `overview.md`와 동기화한다.
