# Integrations LLM 모듈 레퍼런스

`src/chatbot/integrations/llm`은 LangChain 호환 모델을 상위 계층이 다루기 쉬운 형태로 감싸는 계층이다.

## 1. 현재 기본 런타임

1. 현재 기본 채팅 그래프는 `core/chat/nodes/response_node.py`, `safeguard_node.py`에서 `ChatGoogleGenerativeAI`를 생성한다.
2. 생성된 모델은 모두 `LLMClient`로 감싸져 로깅과 예외 표준화를 거친다.
3. `.env.sample`에 `OPENAI_*` 키가 남아 있어도 현재 기본 노드는 이를 직접 사용하지 않는다.

## 2. 코드 설명

1. `LLMClient`는 `invoke`, `ainvoke`, `stream`, `astream` 흐름을 유지하면서 예외를 `BaseAppException`으로 정규화한다.
2. 로깅은 `Logger`, `LogRepository`, 또는 DB 엔진 경유 저장소로 연결할 수 있다.
3. 스트리밍 결과가 비어 있으면 즉시 명시적 예외를 발생시켜 상위 노드가 실패를 감지하게 한다.

## 3. 유지보수 포인트

1. 현재 기본 노드가 어떤 환경 변수를 읽는지는 `LLMClient`가 아니라 노드 조립 코드에서 결정된다는 점을 문서에서 분리해야 한다.
2. 예외 코드(`LLM_*`)는 상위 로그와 장애 대응 문서가 참조하므로 쉽게 바꾸지 않는 편이 좋다.
3. payload/response 로깅 옵션은 개인정보나 토큰 비용 이슈와 연결되므로 운영 적용 범위를 문서화해야 한다.

## 4. 추가 개발과 확장 시 주의점

1. 다른 공급자 모델을 주입하더라도 스트리밍 메서드 계약은 동일하게 유지해야 한다.
2. 도구 바인딩이나 구조화 출력 확장을 사용할 때는 내부 모델이 해당 기능을 지원하는지 먼저 점검해야 한다.
3. 기본 런타임 공급자를 바꾸면 setup/env, core/chat, static 문서까지 함께 갱신해야 한다.

## 5. 상세 문서

- `docs/integrations/llm/client.md`
- `docs/setup/env.md`
