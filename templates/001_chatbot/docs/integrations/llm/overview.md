# Integrations LLM 모듈 레퍼런스

`src/chatbot/integrations/llm`은 LangChain 호환 모델을 상위 계층이 다루기 쉬운 형태로 감싸는 계층이다.

## 1. 현재 기본 경로

1. 기본 채팅 그래프는 `response_node`, `safeguard_node`에서 `ChatGoogleGenerativeAI`를 생성한다.
2. 생성된 모델은 모두 `LLMClient`로 감싸 예외 표준화와 로깅을 거친다.
3. `.env.sample`에 `OPENAI_*`가 남아 있어도 현재 기본 그래프는 직접 사용하지 않는다.

## 2. `LLMClient` 역할

1. `invoke`, `ainvoke`, `stream`, `astream` 흐름을 공통화한다.
2. 예외를 `BaseAppException`으로 정규화한다.
3. 로깅 메타데이터를 남길 수 있다.
4. 스트리밍 결과가 비면 명시적 예외를 발생시킨다.

## 3. 유지보수 포인트

1. 어떤 환경 변수를 읽는지는 `LLMClient`가 아니라 노드 조립 코드가 결정한다.
2. 예외 코드와 로그 메타데이터 구조를 바꾸면 상위 장애 대응 흐름이 영향을 받는다.
3. 다른 공급자 모델을 붙여도 스트리밍 계약은 유지하는 편이 안전하다.

## 4. 관련 문서

- `docs/core/chat.md`
- `docs/setup/env.md`
