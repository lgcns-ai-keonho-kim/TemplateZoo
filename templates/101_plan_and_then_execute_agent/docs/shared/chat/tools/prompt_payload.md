# Prompt Payload 문서

대상 코드: `src/plan_and_then_execute_agent/shared/chat/tools/prompt_payload.py`

## 역할

Planner 프롬프트에 주입할 Tool 목록 JSON payload를 생성합니다.

## 핵심 함수

- `build_planner_tools_payload(registry_or_specs)`

## 입력 규칙

1. `ToolRegistry` 입력 시 `list_for_planner()`를 사용합니다.
2. `Sequence[PlannerToolSpec]` 입력도 지원합니다.
3. payload는 `{"tools": [...]}` 형태로 직렬화됩니다.

## 출력 특성

- `ensure_ascii=False`, `indent=2`로 읽기 가능한 JSON 문자열을 반환합니다.

## 연관 문서

- `docs/shared/chat/tools/registry.md`
- `docs/shared/chat/tools/types.md`
