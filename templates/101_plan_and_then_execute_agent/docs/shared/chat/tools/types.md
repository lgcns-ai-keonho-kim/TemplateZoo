# Tools Types 문서

대상 코드: `src/plan_and_then_execute_agent/shared/chat/tools/types.py`

## 역할

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

## 연관 문서

- `docs/shared/chat/tools/registry.md`
- `docs/shared/chat/nodes/tool_exec_node.md`
