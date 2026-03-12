# `llm/client.py` 레퍼런스

이 문서는 `src/chatbot/integrations/llm/client.py`의 현재 코드 기준 책임과 유지보수 포인트를 정리한다.

## 1. 역할

| 항목 | 내용 |
| --- | --- |
| 목적 | LangChain BaseChatModel 기반 LLM 클라이언트를 제공한다. |
| 설명 | 기존 메서드(invoke/ainvoke/stream/astream)를 유지하면서 로깅과 예외 처리를 통합한다. |
| 디자인 패턴 | 프록시, 데코레이터 |

## 2. 코드 구성

| 심볼 | 종류 |
| --- | --- |
| `LLMClient` | 클래스 |

## 3. 현재 코드 설명

1. 이 모듈의 직접 책임은 `llm/client.py` 파일 내부에 한정된다.
2. 상위 계층은 이 파일의 공개 클래스/함수와 반환 형식을 그대로 신뢰하므로, 문서화된 역할과 실제 구현이 어긋나지 않아야 한다.
3. 현재 코드에서 이 모듈은 `기존 메서드(invoke/ainvoke/stream/astream)를 유지하면서 로깅과 예외 처리를 통합한다.`라는 역할로 사용된다.

## 4. 유지보수 포인트

1. 스키마 등록(`register_schema`)과 실제 엔진 생성 시점이 어긋나지 않도록 호출 순서를 유지해야 한다.
2. 새 엔진을 붙일 때는 `supports_vector_search`, `should_serialize_io` 같은 엔진 능력 플래그가 `DBClient` 기대와 맞는지 먼저 확인해야 한다.

## 5. 추가 개발과 확장 시 주의점

1. 다른 모델 공급자를 추가하더라도 기본 노드가 기대하는 `invoke/ainvoke/stream/astream` 계약은 그대로 맞춰야 한다.
2. 추가 로깅 저장소를 붙일 때는 `Logger`, `LogRepository`, `DBClient` 중 어느 경계를 사용할지 먼저 고정해야 한다.

## 6. 관련 코드

- 소스: `src/chatbot/integrations/llm/client.py`
- `src/chatbot/shared/logging`
- `src/chatbot/shared/exceptions`
