"""
목적: Agent 응답 API 연동 Tool 예시를 제공한다.
설명: /chat 제출 후 SSE 이벤트를 수신하는 흐름을 가정하되, 현재는 mock 응답으로 동작한다.
디자인 패턴: 어댑터
참조: src/tool_proxy_agent/shared/chat/tools/types.py
"""

from __future__ import annotations

from typing import Any

from tool_proxy_agent.shared.chat.tools.types import ToolCall, ToolResult

AGENT_API_BASE_URL = "http://127.0.0.1:8000"
CHAT_SUBMIT_PATH = "/chat"
CHAT_EVENTS_PATH_TEMPLATE = "/chat/{session_id}/events"
DEFAULT_CONTEXT_WINDOW = 20
DEFAULT_CONNECT_TIMEOUT_SECONDS = 10.0
DEFAULT_READ_TIMEOUT_SECONDS = 60.0


def api_agent_response(tool_call: ToolCall) -> ToolResult:
    """현재 시스템과 동일한 큐 제출+SSE 수신 패턴을 설명하기 위한 Tool 함수."""

    # 참고: 현재 단계에서는 네트워크 호출 없이 고정 응답을 반환한다.
    #
    # 아래는 "큐 제출 + SSE 스트림 수신" 실구현 예시(주석)이다.
    #
    # import json
    # import httpx
    #
    # timeout = httpx.Timeout(
    #     connect=connect_timeout,
    #     read=read_timeout,
    #     write=30.0,
    #     pool=10.0,
    # )
    #
    # submit_payload = {
    #     "message": message,
    #     "context_window": context_window,
    # }
    # if session_id:
    #     submit_payload["session_id"] = session_id
    #
    # with httpx.Client(base_url=base_url, timeout=timeout) as client:
    #     submit = client.post(CHAT_SUBMIT_PATH, json=submit_payload)
    #     if submit.status_code != 202:
    #         return {
    #             "ok": False,
    #             "output": {},
    #             "error": f"작업 제출 실패: status={submit.status_code}, body={submit.text}",
    #         }
    #
    #     submit_json = submit.json()
    #     request_id = str(submit_json.get("request_id") or "").strip()
    #     resolved_session_id = str(submit_json.get("session_id") or "").strip()
    #     if not request_id or not resolved_session_id:
    #         return {
    #             "ok": False,
    #             "output": {},
    #             "error": "제출 응답에 request_id 또는 session_id가 없습니다.",
    #         }
    #
    #     events_path = CHAT_EVENTS_PATH_TEMPLATE.format(session_id=resolved_session_id)
    #     events: list[dict[str, Any]] = []
    #     response_text_parts: list[str] = []
    #
    #     with client.stream(
    #         "GET",
    #         events_path,
    #         params={"request_id": request_id},
    #         headers={"Accept": "text/event-stream"},
    #     ) as stream_response:
    #         if stream_response.status_code != 200:
    #             return {
    #                 "ok": False,
    #                 "output": {},
    #                 "error": (
    #                     "이벤트 스트림 연결 실패: "
    #                     f"status={stream_response.status_code}, body={stream_response.text}"
    #                 ),
    #             }
    #
    #         for line in stream_response.iter_lines():
    #             if not line or not line.startswith("data: "):
    #                 continue
    #             payload = json.loads(line[len("data: ") :].strip())
    #             events.append(payload)
    #             event_type = str(payload.get("type") or "")
    #             if event_type == "token":
    #                 response_text_parts.append(str(payload.get("content") or ""))
    #             if event_type in {"done", "error"}:
    #                 break
    #
    #     final_text = "".join(response_text_parts).strip()
    #     return {
    #         "ok": True,
    #         "output": {
    #             "data": {
    #                 "base_url": base_url,
    #                 "session_id": resolved_session_id,
    #                 "request_id": request_id,
    #                 "final_text": final_text,
    #                 "events": events,
    #             }
    #         },
    #         "error": None,
    #     }

    args: dict[str, Any] = dict(tool_call.get("args") or {})
    message = str(args.get("message") or "").strip()
    if not message:
        return {
            "ok": False,
            "output": {},
            "error": "message 인자가 비어 있습니다.",
        }

    base_url = (
        str(args.get("base_url") or AGENT_API_BASE_URL).strip() or AGENT_API_BASE_URL
    )
    session_id = str(args.get("session_id") or "").strip()

    context_window_raw = args.get("context_window")
    context_window = (
        int(context_window_raw)
        if context_window_raw is not None
        else DEFAULT_CONTEXT_WINDOW
    )
    if context_window <= 0:
        return {
            "ok": False,
            "output": {},
            "error": "context_window는 1 이상이어야 합니다.",
        }

    connect_timeout_raw = args.get("connect_timeout_seconds")
    read_timeout_raw = args.get("read_timeout_seconds")
    connect_timeout = (
        float(connect_timeout_raw)
        if connect_timeout_raw is not None
        else DEFAULT_CONNECT_TIMEOUT_SECONDS
    )
    read_timeout = (
        float(read_timeout_raw)
        if read_timeout_raw is not None
        else DEFAULT_READ_TIMEOUT_SECONDS
    )

    mock_data = {
        "base_url": base_url,
        "submitted": {
            "path": CHAT_SUBMIT_PATH,
            "session_id": session_id or "new_session",
            "message": message,
            "context_window": context_window,
        },
        "stream": {
            "path_template": CHAT_EVENTS_PATH_TEMPLATE,
            "request_id": "mock-request-id",
            "events": [
                {"type": "start", "node": "executor"},
                {"type": "token", "node": "response", "content": "mock token"},
                {"type": "done", "node": "response", "status": "COMPLETED"},
            ],
            "final_text": "mock token",
        },
        "timeouts": {
            "connect_timeout_seconds": connect_timeout,
            "read_timeout_seconds": read_timeout,
        },
    }
    return {
        "ok": True,
        "output": {"data": mock_data},
        "error": None,
    }
