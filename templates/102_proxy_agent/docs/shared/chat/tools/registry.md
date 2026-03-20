# Tool Registry

## 개요

`src/tool_proxy_agent/shared/chat/tools/registry.py` 구현을 기준으로 현재 동작을 정리한다.

Tool 스펙의 등록/조회/planner 노출을 담당하는 이름 기반 레지스트리입니다.

## 주요 메서드

1. 등록: `add_tool`, `register_spec`
2. 조회: `resolve`, `has`
3. 목록: `get_tools`, `list_specs`, `list_for_planner`

## 정책

- 중복 이름 등록을 허용하지 않습니다.
- 기본 설정에서 Tool 함수 모듈 경로는 `core/chat/tools` prefix 검증을 통과해야 합니다.

## 실패 경로

- `TOOL_REGISTRY_INVALID_NAME`
- `TOOL_REGISTRY_DUPLICATE`
- `TOOL_REGISTRY_INVALID_SPEC`
- `TOOL_NOT_FOUND`
- `TOOL_REGISTRY_MODULE_INVALID`

## 관련 문서

- `docs/shared/chat/tools/types.md`
- `docs/shared/chat/tools/prompt_payload.md`
- `docs/shared/chat/nodes/tool_exec_node.md`
