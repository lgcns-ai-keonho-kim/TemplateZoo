"""
목적: LangGraph 노드 입력 state를 Mapping 형태로 정규화한다.
설명: TypedDict/dataclass/Pydantic BaseModel/Mapping 입력을 Mapping으로 변환해 공용 노드의 타입 경계를 단순화한다.
디자인 패턴: 어댑터
참조: src/base_template/shared/chat/nodes/llm_node.py, src/base_template/shared/chat/nodes/branch_node.py, src/base_template/shared/chat/nodes/message_node.py
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from typing import Any

from base_template.shared.exceptions import BaseAppException, ExceptionDetail


def coerce_state_mapping(state: object) -> Mapping[str, Any]:
    """
    노드 입력 state를 Mapping으로 정규화한다.

    Args:
        state: LangGraph가 노드에 전달한 입력 객체.

    Returns:
        키-값 접근이 가능한 Mapping 객체.

    Raises:
        BaseAppException: 지원하지 않는 state 타입인 경우.
    """
    if isinstance(state, Mapping):
        return state

    if not isinstance(state, type) and is_dataclass(state):
        data = asdict(state)
        if isinstance(data, Mapping):
            return data

    model_dump = getattr(state, "model_dump", None)
    if callable(model_dump):
        data = model_dump()
        if isinstance(data, Mapping):
            return data

    legacy_dump = getattr(state, "dict", None)
    if callable(legacy_dump):
        data = legacy_dump()
        if isinstance(data, Mapping):
            return data

    detail = ExceptionDetail(
        code="CHAT_NODE_INPUT_INVALID",
        cause=f"state_type={type(state).__name__}",
    )
    raise BaseAppException("노드 입력 state 타입이 올바르지 않습니다.", detail)

