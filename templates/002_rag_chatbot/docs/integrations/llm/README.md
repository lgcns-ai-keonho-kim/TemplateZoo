# Integrations LLM 가이드

이 문서는 `LLMClient`가 현재 코드에서 어떤 문제를 해결하는지 설명한다.

## 1. 현재 역할

- LangChain `BaseChatModel`을 감싼다.
- invoke/stream 계열 호출에 로깅과 예외 표준화를 추가한다.
- tool binding, structured output 같은 확장 기능은 내부 모델에 위임한다.

## 2. 현재 사용 경로

- safeguard, context strategy, keyword generation, relevance judge, response 노드에서 사용된다.
- ingestion의 표/이미지 주석 생성에서도 같은 계열 모델을 사용한다.

## 3. 유지보수/추가개발 포인트

- 모델 제공자를 바꿔도 stream 계열 메서드와 structured output 지원 여부를 먼저 확인해야 한다.
- 로그 수집 범위를 키우면 민감 데이터와 비용 관리 정책을 함께 설계하는 편이 좋다.

## 4. 관련 문서

- `docs/integrations/llm/client.md`
- `docs/shared/logging.md`
- `docs/core/chat.md`
