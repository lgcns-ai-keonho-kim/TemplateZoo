# llm/client.md

소스 경로: `src/text_to_sql/integrations/llm/client.py`

## 1. 역할

- LangChain BaseChatModel 기반 LLM 클라이언트를 제공한다.
- 기존 메서드(invoke/ainvoke/stream/astream)를 유지하면서 로깅과 예외 처리를 통합한다.
- 내부 구조는 프록시, 데코레이터 기반이다.

## 2. 주요 구성

### 2-1. 클래스

| 클래스 | 핵심 메서드 |
| --- | --- |
| `LLMClient` | `__init__, chat, bind_tools, with_structured_output` |

### 2-2. 함수

- 정의된 최상위 함수가 없다.

## 3. 오류/예외 코드

- `LLM_AINVOKE_ERROR`
- `LLM_ASTREAM_ERROR`
- `LLM_ASTREAM_NOT_SUPPORTED`
- `LLM_INVOKE_ERROR`
- `LLM_STREAM_EMPTY`
- `LLM_STREAM_ERROR`
- `LLM_STREAM_NOT_SUPPORTED`

## 4. 관련 코드

- `src/text_to_sql/shared/logging`
- `src/text_to_sql/shared/exceptions`
- `src/text_to_sql/shared/exceptions/__init__.py`
- `src/text_to_sql/shared/logging/__init__.py`
