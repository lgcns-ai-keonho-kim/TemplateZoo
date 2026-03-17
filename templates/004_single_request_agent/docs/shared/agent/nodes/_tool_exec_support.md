# Tool Exec Support

## 개요

`src/single_request_agent/shared/agent/nodes/_tool_exec_support.py` 구현을 기준으로 현재 동작을 정리한다.

`ToolExecNode`의 공통 보조 동작을 분리한 믹스인입니다.
이벤트 발행(`tool_start/tool_result/tool_error`), 재시도 백오프, 비정상 흐름 실패 변환을 제공합니다.

## 주요 메서드

1. `_emit_tool_start/_emit_tool_result/_emit_tool_error`
2. `_sleep_backoff/_sleep_backoff_async`
3. `_resolve_backoff_delay`
4. `_build_unexpected_flow_result`
5. `_safe_get_stream_writer`

## 실패 경로

- `TOOL_EXEC_FLOW_BROKEN`: 정상 분기에서 종료되지 않는 비정상 흐름 감지 시 강제 실패

## 관련 문서

- `docs/shared/agent/nodes/tool_exec_node.md`
