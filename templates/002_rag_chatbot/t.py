"""
목적: Chat 그래프 수동 실행 드라이버를 제공한다.
설명: .env를 로드한 뒤 `chat_graph`를 스트림 모드로 실행해 응답을 콘솔에 출력한다.
디자인 패턴: 절차형 드라이버 스크립트
참조: src/rag_chatbot/core/chat/graphs/chat_graph.py, src/rag_chatbot/shared/config/runtime_env_loader.py
"""

from __future__ import annotations

import asyncio
import argparse
import threading
import json
import os
import time
from collections import defaultdict
from typing import Any
from uuid import uuid4
from rag_chatbot.shared.config import RuntimeEnvironmentLoader



def _parse_args() -> argparse.Namespace:
    """CLI 인자를 파싱한다."""

    parser = argparse.ArgumentParser(
        description="chat_graph를 스트림 모드로 실행한다.",
    )
    parser.add_argument(
        "--message",
        default="안녕하세요. 현재 문서 기반으로 핵심 내용을 요약해 주세요.",
        help="사용자 입력 메시지",
    )
    return parser.parse_args()


def _record_node_timing(
    node_timings: dict[str, list[float]],
    lock: threading.Lock,
    node_name: str,
    elapsed_ms: float,
) -> None:
    """노드 실행 시간을 스레드 안전하게 기록한다."""

    with lock:
        node_timings.setdefault(node_name, []).append(elapsed_ms)


def _install_node_timing_hooks() -> dict[str, list[float]]:
    """노드 클래스 메서드에 실행 시간 측정 훅을 설치한다."""

    from rag_chatbot.shared.chat.nodes.branch_node import BranchNode
    from rag_chatbot.shared.chat.nodes.fanout_branch_node import FanoutBranchNode
    from rag_chatbot.shared.chat.nodes.function_node import FunctionNode
    from rag_chatbot.shared.chat.nodes.llm_node import LLMNode
    from rag_chatbot.shared.chat.nodes.message_node import MessageNode

    node_timings: dict[str, list[float]] = defaultdict(list)
    lock = threading.Lock()

    original_llm_run = LLMNode.run
    original_llm_arun = LLMNode.arun
    original_function_run = FunctionNode.run
    original_function_arun = FunctionNode.arun
    original_branch_run = BranchNode.run
    original_message_run = MessageNode.run
    original_fanout_route = FanoutBranchNode.route

    def timed_llm_run(self: Any, state: object, config: object | None = None) -> dict[str, str]:
        started_at = time.perf_counter()
        try:
            return original_llm_run(self, state, config)
        finally:
            _record_node_timing(
                node_timings=node_timings,
                lock=lock,
                node_name=str(getattr(self, "_node_name", "llm_node")),
                elapsed_ms=(time.perf_counter() - started_at) * 1000.0,
            )

    async def timed_llm_arun(
        self: Any,
        state: object,
        config: object | None = None,
    ) -> dict[str, str]:
        started_at = time.perf_counter()
        try:
            return await original_llm_arun(self, state, config)
        finally:
            _record_node_timing(
                node_timings=node_timings,
                lock=lock,
                node_name=str(getattr(self, "_node_name", "llm_node")),
                elapsed_ms=(time.perf_counter() - started_at) * 1000.0,
            )

    def timed_function_run(self: Any, state: object, config: object | None = None) -> dict[str, Any]:
        started_at = time.perf_counter()
        try:
            return original_function_run(self, state, config)
        finally:
            _record_node_timing(
                node_timings=node_timings,
                lock=lock,
                node_name=str(getattr(self, "_node_name", "function_node")),
                elapsed_ms=(time.perf_counter() - started_at) * 1000.0,
            )

    async def timed_function_arun(
        self: Any,
        state: object,
        config: object | None = None,
    ) -> dict[str, Any]:
        started_at = time.perf_counter()
        try:
            return await original_function_arun(self, state, config)
        finally:
            _record_node_timing(
                node_timings=node_timings,
                lock=lock,
                node_name=str(getattr(self, "_node_name", "function_node")),
                elapsed_ms=(time.perf_counter() - started_at) * 1000.0,
            )

    def timed_branch_run(self: Any, state: object, config: object | None = None) -> dict[str, str]:
        started_at = time.perf_counter()
        try:
            return original_branch_run(self, state, config)
        finally:
            _record_node_timing(
                node_timings=node_timings,
                lock=lock,
                node_name=f"branch:{str(getattr(self, '_output_key', 'branch_node'))}",
                elapsed_ms=(time.perf_counter() - started_at) * 1000.0,
            )

    def timed_message_run(self: Any, state: object, config: object | None = None) -> dict[str, str]:
        started_at = time.perf_counter()
        try:
            return original_message_run(self, state, config)
        finally:
            _record_node_timing(
                node_timings=node_timings,
                lock=lock,
                node_name=f"message:{str(getattr(self, '_output_key', 'message_node'))}",
                elapsed_ms=(time.perf_counter() - started_at) * 1000.0,
            )

    def timed_fanout_route(self: Any, state: object, config: object | None = None) -> str | list[object]:
        started_at = time.perf_counter()
        try:
            return original_fanout_route(self, state, config)
        finally:
            _record_node_timing(
                node_timings=node_timings,
                lock=lock,
                node_name=f"fanout:{str(getattr(self, '_target_node', 'fanout'))}",
                elapsed_ms=(time.perf_counter() - started_at) * 1000.0,
            )

    LLMNode.run = timed_llm_run
    LLMNode.arun = timed_llm_arun
    FunctionNode.run = timed_function_run
    FunctionNode.arun = timed_function_arun
    BranchNode.run = timed_branch_run
    MessageNode.run = timed_message_run
    FanoutBranchNode.route = timed_fanout_route
    return node_timings


def _print_node_timing_report(node_timings: dict[str, list[float]]) -> dict[str, int]:
    """노드 실행 시간 리포트를 출력한다."""

    print("[리포트] 노드별 소요시간")
    if not node_timings:
        print("[리포트] 수집된 노드 실행 시간이 없습니다.")
        return {}

    rows: list[tuple[str, int, float, float, float, float]] = []
    call_counts: dict[str, int] = {}
    for node_name, values in node_timings.items():
        if not values:
            continue
        calls = len(values)
        call_counts[node_name] = calls
        total_ms = float(sum(values))
        avg_ms = total_ms / float(calls)
        min_ms = float(min(values))
        max_ms = float(max(values))
        rows.append((node_name, calls, total_ms, avg_ms, min_ms, max_ms))

    rows.sort(key=lambda item: item[2], reverse=True)
    for node_name, calls, total_ms, avg_ms, min_ms, max_ms in rows:
        print(
            f"[리포트] node={node_name}, calls={calls}, total_ms={total_ms:.2f}, "
            f"avg_ms={avg_ms:.2f}, min_ms={min_ms:.2f}, max_ms={max_ms:.2f}"
        )
    return call_counts


def _print_parallel_node_call_report(call_counts: dict[str, int]) -> None:
    """병렬/다중 호출 노드의 총 호출 횟수를 출력한다."""

    print("[리포트] 병렬/다중 호출 노드 횟수")
    parallel_like = {
        node_name: calls
        for node_name, calls in call_counts.items()
        if calls > 1 or node_name.startswith("fanout:")
    }
    if not parallel_like:
        print("[리포트] 병렬/다중 호출 노드가 없습니다.")
        return

    for node_name, calls in sorted(
        parallel_like.items(),
        key=lambda item: (-item[1], item[0]),
    ):
        print(f"[리포트] node={node_name}, total_calls={calls}")


async def _run_astream(
    chat_graph: Any,
    session_id: str,
    user_message: str,
) -> tuple[int, float, float | None]:
    """비동기 stream_events 모드로 그래프를 실행한다."""

    stream_started_at = time.perf_counter()
    first_response_at: float | None = None
    has_streamed_response = False

    print("=== stream 이벤트 ===")
    
    async for event in chat_graph.astream_events(
        session_id=session_id,
        user_message=user_message,
        history=[],
    ):
        node = str(event.get("node") or "").strip()
        event_name = str(event.get("event") or "").strip()
        data = event.get("data")

        if node == "response" and event_name == "token":
            token = "" if data is None else str(data)
            if token:
                if first_response_at is None:
                    first_response_at = time.perf_counter()
                has_streamed_response = True
                print(token, end="", flush=True)
            continue

        if node == "response" and event_name == "assistant_message":
            continue

        print(json.dumps(event, ensure_ascii=False))

    total_elapsed_ms = (time.perf_counter() - stream_started_at) * 1000.0
    ttft_ms: float | None = None
    if first_response_at is not None:
        ttft_ms = (first_response_at - stream_started_at) * 1000.0
    if has_streamed_response:
        print()
    return 0, total_elapsed_ms, ttft_ms


def main() -> int:
    """스크립트 엔트리 포인트."""

    args = _parse_args()
    session_id = f"manual-{uuid4().hex[:8]}"
    runtime_env = RuntimeEnvironmentLoader().load()
    print(
        "[환경] "
        f"ENV={runtime_env}, "
        f"LANCEDB_URI={str(os.getenv('LANCEDB_URI', '')).strip() or '<empty>'}"
    )
    print(f"[입력] session_id={session_id}")

    node_timings = _install_node_timing_hooks()

    from rag_chatbot.core.chat import chat_graph

    exit_code, total_elapsed_ms, ttft_ms = asyncio.run(
        _run_astream(
            chat_graph=chat_graph,
            session_id=session_id,
            user_message=str(args.message),
        )
    )
    if ttft_ms is not None:
        print(f"[메트릭] TTFT={ttft_ms:.2f}ms")
    else:
        print("[메트릭] TTFT=측정 불가(response 시작 이벤트 없음)")
    print(f"[메트릭] 총 실행 시간={total_elapsed_ms:.2f}ms")
    call_counts = _print_node_timing_report(node_timings=node_timings)
    _print_parallel_node_call_report(call_counts=call_counts)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
