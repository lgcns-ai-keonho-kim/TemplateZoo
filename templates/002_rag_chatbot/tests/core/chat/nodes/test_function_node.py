"""
목적: FunctionNode 동작을 검증한다.
설명: 주입 함수 실행 결과와 실패 케이스를 테스트한다.
디자인 패턴: 단위 테스트
참조: src/rag_chatbot/shared/chat/nodes/function_node.py
"""

from __future__ import annotations

import pytest

from rag_chatbot.shared.chat.nodes.function_node import function_node
from rag_chatbot.shared.exceptions import BaseAppException


def test_function_node_returns_mapping_output() -> None:
    """주입 함수 결과가 state payload로 그대로 반환되어야 한다."""

    def run_step(state: dict[str, object]) -> dict[str, object]:
        return {"result": int(state.get("x", 0)) + 1}

    node = function_node(fn=run_step, node_name="sample")
    output = node.run({"x": 41})
    assert output == {"result": 42}


def test_function_node_raises_when_output_is_not_mapping() -> None:
    """주입 함수 출력이 Mapping이 아니면 예외가 발생해야 한다."""

    def run_invalid_step(state: dict[str, object]) -> int:
        del state
        return 1

    node = function_node(fn=run_invalid_step, node_name="invalid")  # type: ignore[arg-type]

    with pytest.raises(BaseAppException):
        node.run({"x": 1})


@pytest.mark.asyncio
async def test_function_node_arun_supports_async_function() -> None:
    """비동기 주입 함수는 arun에서 정상 실행되어야 한다."""

    async def run_async_step(state: dict[str, object]) -> dict[str, object]:
        return {"result": int(state.get("x", 0)) + 1}

    node = function_node(fn=run_async_step, node_name="async-sample")
    output = await node.arun({"x": 41})
    assert output == {"result": 42}


def test_function_node_run_raises_when_async_function_is_injected() -> None:
    """비동기 주입 함수를 run으로 호출하면 명시적 예외가 발생해야 한다."""

    async def run_async_step(state: dict[str, object]) -> dict[str, object]:
        return {"result": int(state.get("x", 0)) + 1}

    node = function_node(fn=run_async_step, node_name="async-invalid-run")

    with pytest.raises(BaseAppException) as captured:
        node.run({"x": 1})

    assert captured.value.detail.code == "FUNCTION_NODE_ASYNC_IN_SYNC_RUN"
