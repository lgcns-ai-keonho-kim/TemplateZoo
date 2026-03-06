# client 모듈

이 문서는 `src/rag_chatbot/integrations/llm/client.py`의 역할과 주요 구성을 설명한다.

## 1. 목적

LangChain BaseChatModel 기반 LLM 클라이언트를 제공한다.

## 2. 설명

기존 메서드(invoke/ainvoke/stream/astream)를 유지하면서 로깅과 예외 처리를 통합한다.

## 3. 디자인 패턴

프록시, 데코레이터

## 4. 주요 구성

- 클래스 `LLMClient`
  주요 메서드: `chat`, `bind_tools`, `with_structured_output`

## 5. 연동 포인트

- `src/rag_chatbot/shared/logging`
- `src/rag_chatbot/shared/exceptions`

## 6. 관련 문서

- `docs/integrations/llm/README.md`
- `docs/integrations/overview.md`
