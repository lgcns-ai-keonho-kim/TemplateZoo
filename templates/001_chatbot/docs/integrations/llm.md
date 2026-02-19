# Integrations LLM 가이드

이 문서는 `src/chatbot/integrations/llm/client.py`의 `LLMClient` 인터페이스와 동작 규칙을 코드 기준으로 정리한다.

## 1. 용어 정리

| 용어 | 의미 | 관련 스크립트 |
| --- | --- | --- |
| BaseChatModel | LangChain 채팅 모델 베이스 타입 | `langchain_core.language_models` |
| LLMClient | 모델 호출을 감싸 로깅/예외 처리까지 표준화한 래퍼 | `integrations/llm/client.py` |
| logging_engine | 로깅 주입 대상(엔진/로거/저장소) | `LLMClient.__init__` |
| context_provider | 로그 컨텍스트를 동적으로 공급하는 함수 | `LLMClient._get_context` |
| background_runner | 성공 로그를 백그라운드 실행하는 훅 | `LLMClient._run_background` |

## 2. 관련 스크립트

| 파일 | 역할 |
| --- | --- |
| `src/chatbot/integrations/llm/client.py` | LLMClient 구현 |
| `src/chatbot/integrations/llm/__init__.py` | 공개 API 제공 |
| `src/chatbot/shared/logging/*` | 로깅 모델/저장소/로거 |
| `src/chatbot/shared/exceptions/*` | 공통 예외 모델 |
| `src/chatbot/core/chat/nodes/response_node.py` | response 노드의 LLMClient 사용 예 |
| `src/chatbot/core/chat/nodes/safeguard_node.py` | safeguard 노드의 LLMClient 사용 예 |

## 3. 인터페이스

## 3-1. 호출 메서드

1. 동기 호출: `invoke`, 내부 `_generate`
2. 비동기 호출: `ainvoke`, 내부 `_agenerate`
3. 동기 스트림: `stream`, 내부 `_stream`
4. 비동기 스트림: `astream`, 내부 `_astream`
5. 메시지 스트림 결합 호출: `chat(messages)`

## 3-2. 도구/구조화 출력 위임

1. `bind_tools(...)`
2. `with_structured_output(...)`

설명:

1. 내부 모델이 해당 기능을 지원하지 않으면 `NotImplementedError`를 전달한다.

## 4. 로깅 주입 규칙

## 4-1. 허용 타입

`logging_engine` 허용 대상:

1. `BaseDBEngine`
2. `Logger`
3. `LogRepository`

주의:

1. `DBClient`를 직접 `logging_engine`으로 주입하면 `ValueError`를 발생시킨다.
2. `BaseDBEngine` 주입 시 내부에서 `DBClient(engine)`를 생성해 LLM 로그 저장소를 구성한다.

## 4-2. 기본 로거 선택

1. `logger`가 있으면 그대로 사용한다.
2. `log_repository`만 있으면 `InMemoryLogger(repository=...)`를 생성한다.
3. 둘 다 없으면 `create_default_logger(name)`를 사용한다.

## 4-3. stdout 출력

1. 내부 로거가 `InMemoryLogger`인 경우 `LOG_STDOUT` 환경 변수 규칙을 따른다.
2. 로깅 실패는 핵심 호출을 깨지 않도록 best-effort로 처리한다.

## 5. 예외 코드

| 상황 | 코드 |
| --- | --- |
| 동기 호출 실패 | `LLM_INVOKE_ERROR` |
| 비동기 호출 실패 | `LLM_AINVOKE_ERROR` |
| 동기 스트림 실패 | `LLM_STREAM_ERROR` |
| 비동기 스트림 실패 | `LLM_ASTREAM_ERROR` |
| 스트림 결과가 비어 있음 | `LLM_STREAM_EMPTY` |
| 모델이 네이티브 스트림 미지원 | `LLM_STREAM_NOT_SUPPORTED` |
| 모델이 네이티브 비동기 스트림 미지원 | `LLM_ASTREAM_NOT_SUPPORTED` |

## 6. 동작 규칙

## 6-1. 스트리밍 규칙

1. `_stream`, `_astream`은 내부 모델의 네이티브 구현만 사용한다.
2. 네이티브 구현이 없으면 즉시 예외를 발생시킨다.
3. 스트림 완료 시 성공 로그를 백그라운드로 기록한다.

## 6-2. 로그 메타데이터

기본 메타 키:

1. `action`
2. `model_name`
3. `ls_model_name`
4. `llm_type`
5. `provider`
6. `ls_provider`

성공 시 추가:

1. `duration_ms`
2. `success`
3. `usage_metadata` (가능한 경우)
4. `result` (`log_response=True`일 때)

시작 시 추가:

1. `message_count`
2. `stop`
3. `stream`
4. `kwargs`
5. `messages` (`log_payload=True`일 때)

## 6-3. 안전 동작

1. 로깅 실패는 본 호출 결과를 깨지 않는다.
2. `context_provider` 실패는 무시하고 컨텍스트 없이 로그를 남긴다.
3. `background_runner` 실패는 무시하고 호출을 계속 진행한다.

## 7. 사용 예시

```python
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from chatbot.integrations.llm import LLMClient

model = ChatOpenAI(model="gpt-4o-mini", api_key=SecretStr("..."))
client = LLMClient(model=model, name="chat-response-llm")

result = client.invoke("안녕하세요")
for chunk in client.stream("스트리밍 테스트"):
    print(chunk)
```

## 8. 변경 작업 절차

## 8-1. 모델 공급자 교체

1. 노드 조립 파일에서 `BaseChatModel` 생성부를 변경한다.
2. `LLMClient` 래퍼 호출 구조는 유지한다.
3. 스트림 지원 여부를 사전 점검한다.

## 8-2. LLM 로그를 DB로 저장

1. `BaseDBEngine` 인스턴스를 준비한다.
2. `LLMClient(logging_engine=engine)`로 주입한다.
3. 로그 컬렉션/스키마 정책을 운영 기준으로 맞춘다.

## 8-3. 로그 상세도 조정

1. 요청 본문 기록이 필요하면 `log_payload=True`를 설정한다.
2. 응답 전문 기록이 필요하면 `log_response=True`를 설정한다.
3. 민감 정보가 포함될 수 있으므로 마스킹 정책을 먼저 적용한다.

## 9. 트러블슈팅

| 증상 | 원인 후보 | 확인 스크립트 | 조치 |
| --- | --- | --- | --- |
| stream 호출 시 즉시 실패 | 모델 네이티브 스트림 미지원 | `client.py` `_iter_stream_chunks` | 지원 모델 사용 또는 invoke 경로 사용 |
| logging_engine 주입 오류 | DBClient 직접 전달 | `client.py` `_resolve_logging` | BaseDBEngine 전달로 수정 |
| usage 메타가 비어 있음 | 모델 응답에 usage 정보 없음 | `_extract_usage_metadata` | 모델/프로바이더 응답 구조 확인 |
| 로그는 남는데 본문 미포함 | `log_payload=False` 기본값 | `LLMClient.__init__` | 옵션 활성화 |

## 10. 소스 매칭 점검 항목

1. 예외 코드 표가 `client.py` 구현과 일치하는가
2. logging_engine 허용 타입 설명이 `_resolve_logging`과 일치하는가
3. 스트림 동작 설명이 `_stream`, `_astream` 구현과 일치하는가
4. 문서 경로가 실제 `src/chatbot/integrations/llm` 구조와 일치하는가

## 11. 관련 문서

- `docs/integrations/overview.md`
- `docs/shared/logging.md`
- `docs/core/chat.md`
