# Integrations LLM 레퍼런스

이 문서는 `src/chatbot/integrations/llm/client.py`의 `LLMClient` 인터페이스와 동작 기준을 정리한다.

## 1. 핵심 용어

| 용어 | 의미 |
| --- | --- |
| BaseChatModel | LangChain 채팅 모델 베이스 타입 |
| LLMClient | 모델 호출/로깅/예외를 표준화한 래퍼 |
| logging_engine | 로깅 주입 대상(엔진/로거/저장소) |
| background_runner | 스트림 완료 로그의 비동기 실행 훅 |

## 2. 관련 스크립트

| 파일 | 역할 |
| --- | --- |
| `src/chatbot/integrations/llm/client.py` | LLMClient 구현 |
| `src/chatbot/core/chat/nodes/response_node.py` | response 노드 조립 |
| `src/chatbot/core/chat/nodes/safeguard_node.py` | safeguard 노드 조립 |
| `tests/integrations/llm/test_llm_client.py` | invoke/stream 로깅 테스트 |

## 3. 인터페이스

1. 동기 호출: `invoke`
2. 비동기 호출: `ainvoke`
3. 동기 스트림: `stream`
4. 비동기 스트림: `astream`

## 4. 로깅 기준

1. `logging_engine`은 `BaseDBEngine`, `Logger`, `LogRepository`를 허용한다.
2. 로깅 실패는 본 호출을 깨지 않는 best-effort 정책을 따른다.
3. 스트림 완료 시 성공 로그를 백그라운드로 기록한다.

## 5. 예외 코드

| 상황 | 코드 |
| --- | --- |
| 동기 호출 실패 | `LLM_INVOKE_ERROR` |
| 비동기 호출 실패 | `LLM_AINVOKE_ERROR` |
| 동기 스트림 실패 | `LLM_STREAM_ERROR` |
| 비동기 스트림 실패 | `LLM_ASTREAM_ERROR` |

## 6. Gemini 사용 예시

```python
from langchain_google_genai import ChatGoogleGenerativeAI

from chatbot.integrations.llm import LLMClient

model = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    project="your-project",
    thinking_level="minimal",  # 정책 기준
)

client = LLMClient(model=model, name="chat-response-llm")

result = client.invoke("안녕하세요")
for chunk in client.stream("스트리밍 테스트"):
    print(chunk)
```

구현 전환 중 주석:

1. 현재 일부 코드에는 `thinking_level="low"`가 남아 있을 수 있다.
2. 문서 정책값은 `minimal`이며 코드와의 차이는 점진적으로 수렴한다.

## 7. 트러블슈팅

| 증상 | 원인 후보 | 조치 |
| --- | --- | --- |
| stream 호출 즉시 실패 | 모델 네이티브 스트림 미지원 | 지원 모델 사용 또는 invoke 경로 사용 |
| logging_engine 주입 오류 | 허용되지 않은 타입 전달 | `BaseDBEngine/Logger/LogRepository` 사용 |
| Gemini 필수 env 누락 | `GEMINI_MODEL`, `GEMINI_PROJECT` 미설정 | env 설정 후 프로세스 재시작 |

## 8. 관련 문서

- `docs/setup/env.md`
- `docs/setup/troubleshooting.md`
- `docs/core/chat.md`
