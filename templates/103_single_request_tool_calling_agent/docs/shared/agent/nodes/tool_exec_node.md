# Tool Exec Node

## 개요

`src/single_request_tool_agent/shared/agent/nodes/tool_exec_node.py` 구현을 기준으로 현재 동작을 정리한다.

`ToolRegistry`에 등록된 Tool을 실행하는 공용 노드입니다.
timeout/retry/backoff, tool 이벤트 발행, 성공/실패 envelope 생성을 담당합니다.

## 주요 흐름

1. `_extract_tool_call()`로 입력 검증
2. `registry.resolve()`로 Tool 스펙 조회
3. 동기 `_run_sync()` 또는 비동기 `_run_async()` 실행
4. 시도별 `tool_start` 이벤트 발행
5. 성공 시 `tool_result`, 실패 시 `tool_error` 이벤트 발행

## 주요 예외/오류 코드

- `TOOL_EXEC_NODE_CONFIG_INVALID`
- `TOOL_EXEC_INPUT_INVALID`
- `TOOL_EXEC_ASYNC_IN_SYNC_RUN`
- 실행 오류 envelope: `TOOL_RETRY_EXHAUSTED`, `TOOL_TIMEOUT`

## 출력 계약

- 성공: `{success_key: [envelope], failure_key: []}`
- 실패: `{success_key: [], failure_key: [envelope]}`

## 관련 문서

- `docs/shared/agent/nodes/_tool_exec_support.md`
- `docs/shared/agent/tools/registry.md`
- `docs/shared/agent/tools/types.md`
