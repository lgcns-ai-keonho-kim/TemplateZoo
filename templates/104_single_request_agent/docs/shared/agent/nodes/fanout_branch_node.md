# Fanout Branch Node

## 개요

`src/single_request_agent/shared/agent/nodes/fanout_branch_node.py` 구현을 기준으로 현재 동작을 정리한다.

리스트 입력을 `Send` 목록으로 변환해 fan-out 실행을 라우팅합니다.
입력이 비정상이면 기본 분기로 폴백합니다.

## 주요 메서드

1. `route()/run()`: 라우팅 진입점
2. `_route()`: 목록 검증 후 `list[Send]` 또는 `default_branch` 반환

## 실패 경로

- `FANOUT_BRANCH_NODE_CONFIG_INVALID`: `items_key`, `target_node`, `default_branch` 설정 오류

## 반환 규칙

- 유효 mapping 항목 존재: `list[Send]`
- 비어 있거나 형식 불일치: `default_branch`

## 관련 문서

- `docs/shared/agent/nodes/tool_exec_node.md`
- `docs/shared/agent/services/service_executor.md`
