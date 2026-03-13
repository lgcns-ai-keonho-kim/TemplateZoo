# LLMClient

## 역할

- LangChain `BaseChatModel` 서브클래스다.
- 내부 모델 호출에 로깅과 예외 표준화를 추가한다.
- `bind_tools`, `with_structured_output`은 내부 모델에 위임한다.

## 공개 동작

- `chat`
- `bind_tools`
- `with_structured_output`
- `invoke`, `ainvoke`, `stream`, `astream`
  - 외부에서는 `BaseChatModel` 인터페이스로 사용한다.
  - 내부 `_generate`, `_agenerate`, `_stream`, `_astream`에서 로깅과 예외 래핑을 수행한다.

## 로깅

- `Logger`, `LogRepository`, `BaseDBEngine` 중 하나를 받아 로그 경로를 구성할 수 있다.
- `log_payload`, `log_response` 옵션으로 요청/응답 전문 기록 여부를 제어한다.
- `context_provider`가 있으면 `request_id` 같은 컨텍스트를 로그에 실을 수 있다.

## 예외

- invoke 계열 실패: `LLM_INVOKE_ERROR`, `LLM_AINVOKE_ERROR`
- stream 계열 실패: `LLM_STREAM_ERROR`, `LLM_ASTREAM_ERROR`
- 네이티브 스트리밍 미지원: `LLM_STREAM_NOT_SUPPORTED`, `LLM_ASTREAM_NOT_SUPPORTED`
