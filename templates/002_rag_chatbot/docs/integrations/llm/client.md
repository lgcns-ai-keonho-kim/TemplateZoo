# LLMClient 가이드

이 문서는 `src/rag_chatbot/integrations/llm/client.py`의 현재 구현을 기준으로 역할과 유지보수 포인트를 정리한다.

## 1. 역할

LLMClient는 LangChain BaseChatModel 위에 로깅, 예외 표준화, 구조화 출력 위임을 덧씌운 래퍼다.

## 2. 공개 구성

- 클래스 `LLMClient`
  공개 메서드: `chat`, `bind_tools`, `with_structured_output`

## 3. 코드 설명

- 동기/비동기 invoke와 stream 경로 모두 예외를 `BaseAppException`으로 표준화한다.
- `bind_tools`, `with_structured_output`은 내부 모델에 그대로 위임한다.
- 로깅 저장소나 DB 엔진을 주입하면 호출 로그를 별도 저장소에 남길 수 있다.

## 4. 유지보수/추가개발 포인트

- 모델 제공자를 바꿀 때도 `bind_tools`, `with_structured_output`, stream 계열 메서드의 지원 여부를 함께 검증해야 한다.
- payload/response 전문 저장은 비용이 크므로 운영 환경에서는 저장 정책을 분리해 관리하는 편이 좋다.

## 5. 관련 문서

- `docs/integrations/overview.md`
