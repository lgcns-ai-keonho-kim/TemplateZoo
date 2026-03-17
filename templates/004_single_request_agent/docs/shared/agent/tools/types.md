# Tools Types

## 개요

`src/single_request_agent/shared/agent/tools/types.py` 구현을 기준으로 현재 동작을 정리한다.

Tool 실행 계약 타입을 정의합니다.
Registry, Planner payload, Tool 실행 노드가 동일 타입을 공유하도록 기준을 제공합니다.

## 주요 타입

1. `ToolCall`: 실행 컨텍스트(`tool_name`, `args`, `session_id`, `request_id`, `plan_id`, `step_id` 등)
2. `ToolResult`: 표준 결과(`ok`, `output`, `error`)
3. `PlannerToolSpec`: planner 주입용 최소 스펙
4. `ToolFn`: 실행 함수 타입 별칭
5. `ToolSpec`: Registry 저장용 불변 데이터 클래스

## `ToolSpec` 검증

- 이름 비어 있음 금지
- `fn` callable 필수
- `args_schema` dict 필수
- `timeout_seconds > 0`
- `retry_count >= 0`
- backoff 값 음수 금지

## 관련 문서

- `docs/shared/agent/tools/registry.md`
- `docs/shared/agent/nodes/tool_exec_node.md`
