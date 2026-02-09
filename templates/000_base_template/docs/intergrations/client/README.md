# LLM 클라이언트 명세

이 문서는 `src/base_template/integrations/llm/client.py`의 `LLMClient` 구조와 호출 계약을 정의한다.

## 역할

`LLMClient`는 LangChain `BaseChatModel`을 감싸는 프록시 계층이다.

- `invoke`, `ainvoke`, `stream`, `astream` 인터페이스를 그대로 유지한다.
- 호출 시작/성공/실패 로그를 통합한다.
- 외부 모델 예외를 `BaseAppException`으로 변환한다.
- `bind_tools`, `with_structured_output`를 내부 모델에 위임한다.

## 입력/출력 계약

| 항목 | 내용 |
| --- | --- |
| 입력 모델 | `BaseChatModel` 구현체 |
| 입력 메시지 | `Sequence[BaseMessage]` |
| 출력(동기/비동기) | `ChatResult` |
| 출력(스트리밍) | `ChatGenerationChunk` 이터레이터 |

## 로깅 구성

`LLMClient`는 세 가지 주입 경로를 지원한다.

1. `Logger` 직접 주입
2. `LogRepository` 직접 주입
3. `logging_engine` 주입 (`BaseDBEngine` 또는 `Logger` 또는 `LogRepository`)

`logging_engine`에 `BaseDBEngine`을 주입하면 내부에서 `DBClient`와 `LLMLogRepository`를 생성한다.

## 로그 메타데이터

기본 기록 필드:

- `action` (`invoke`, `ainvoke`, `stream`, `astream`)
- `model_name`, `llm_type`, `provider`
- `duration_ms`, `success`, `error_type`
- `usage_metadata` (토큰/비용 정보가 제공되는 모델에서만)

옵션 필드:

- `messages` (`log_payload=True`)
- `result` (`log_response=True`)

## 예외 변환 규칙

| 동작 | 에러 코드 |
| --- | --- |
| 동기 호출 실패 | `LLM_INVOKE_ERROR` |
| 비동기 호출 실패 | `LLM_AINVOKE_ERROR` |
| 동기 스트림 실패 | `LLM_STREAM_ERROR` |
| 비동기 스트림 실패 | `LLM_ASTREAM_ERROR` |

## 의존성 방향

```text
core/chat/nodes/reply_node
  -> integrations/llm/client.LLMClient
     -> shared/logging
     -> shared/exceptions
     -> (optional) integrations/db + shared/logging/llm_repository
```

## 최소 사용 예시

```python
from base_template.integrations.llm import LLMClient
from base_template.shared.logging import create_default_logger

client = LLMClient(
    model=langchain_chat_model,
    name="chat-core-llm",
    logger=create_default_logger("chat-llm"),
)

result = client.invoke("안녕하세요")
for chunk in client.stream("스트리밍 테스트"):
    print(chunk)
```

## 제약

1. `logging_engine`에는 `DBClient`를 직접 주입하지 않는다.
2. 로깅 저장 실패는 본 호출 흐름을 중단하지 않는다.
3. 내부 모델이 `_stream`/`_astream`을 구현하지 않은 경우 `stream`/`astream` 경로로 자동 전환한다.
