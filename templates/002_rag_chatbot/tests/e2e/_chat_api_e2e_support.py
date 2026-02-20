"""
목적: Chat API E2E 테스트 공통 유틸을 제공한다.
설명: 세션 생성/스트림 수집/이력 대기/레퍼런스 파싱 등 중복 로직을 분리한다.
디자인 패턴: 테스트 헬퍼 모듈
참조: tests/e2e/test_chat_api_server_e2e.py
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable

import httpx

_E2E_CONNECT_TIMEOUT_SECONDS = float(os.getenv("E2E_CONNECT_TIMEOUT_SECONDS", "10.0"))
_E2E_READ_TIMEOUT_SECONDS = float(os.getenv("E2E_READ_TIMEOUT_SECONDS", "60.0"))
_E2E_WRITE_TIMEOUT_SECONDS = float(os.getenv("E2E_WRITE_TIMEOUT_SECONDS", "30.0"))
_E2E_POOL_TIMEOUT_SECONDS = float(os.getenv("E2E_POOL_TIMEOUT_SECONDS", "10.0"))
STREAM_TIMEOUT = httpx.Timeout(
    connect=_E2E_CONNECT_TIMEOUT_SECONDS,
    read=_E2E_READ_TIMEOUT_SECONDS,
    write=_E2E_WRITE_TIMEOUT_SECONDS,
    pool=_E2E_POOL_TIMEOUT_SECONDS,
)
HISTORY_WAIT_TIMEOUT_SECONDS = float(os.getenv("E2E_HISTORY_WAIT_TIMEOUT_SECONDS", "20.0"))
HISTORY_WAIT_POLL_SECONDS = float(os.getenv("E2E_HISTORY_WAIT_POLL_SECONDS", "0.2"))


def log_response(label: str, response: httpx.Response) -> dict:
    """HTTP 응답 본문을 로그로 출력하고 JSON 본문을 반환한다."""

    print(f"[e2e] {label} status={response.status_code}")
    try:
        payload = response.json()
    except Exception:  # noqa: BLE001 - 테스트 로그 출력 용도
        print(f"[e2e] {label} body={response.text}")
        return {}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return payload


def stream_message(
    client: httpx.Client,
    session_id: str,
    message: str,
    context_window: int = 20,
) -> list[dict]:
    """작업 제출 + 이벤트 스트림 구독을 호출하고 SSE 이벤트 목록을 반환한다."""

    events: list[dict] = []
    submit_response = client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": message,
            "context_window": context_window,
        },
        timeout=STREAM_TIMEOUT,
    )
    assert submit_response.status_code == 202, submit_response.text
    submit_payload = submit_response.json()
    request_id = str(submit_payload.get("request_id") or "")
    resolved_session_id = str(submit_payload.get("session_id") or "")
    assert request_id
    assert resolved_session_id == session_id

    with client.stream(
        "GET",
        f"/chat/{session_id}/events",
        params={"request_id": request_id},
        headers={"Accept": "text/event-stream"},
        timeout=STREAM_TIMEOUT,
    ) as response:
        assert response.status_code == 200, response.text
        stream_debug = os.getenv("E2E_STREAM_DEBUG", "0") == "1"
        for line in response.iter_lines():
            if not line:
                continue
            if not line.startswith("data: "):
                continue
            payload = json.loads(line[len("data: ") :].strip())
            events.append(payload)
            event_type = str(payload.get("type") or "")
            if stream_debug:
                print("[e2e] stream payload:")
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            if event_type == "token":
                _typewriter_print(str(payload.get("content") or ""))
            if event_type == "references":
                parsed_references = parse_references(payload)
                print("\n[e2e] references payload:")
                print(json.dumps(parsed_references, ensure_ascii=False, indent=2))
            if event_type == "error":
                print("\n[e2e] stream error payload:")
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            if event_type in {"done", "error"}:
                break
    print()
    return events


def wait_until_messages(
    client: httpx.Client,
    session_id: str,
    predicate: Callable[[list[dict]], bool],
    timeout_seconds: float = HISTORY_WAIT_TIMEOUT_SECONDS,
    poll_seconds: float = HISTORY_WAIT_POLL_SECONDS,
) -> list[dict]:
    """메시지 이력이 조건을 만족할 때까지 polling 한다."""

    deadline = time.monotonic() + timeout_seconds
    last_payload: dict | None = None
    while time.monotonic() < deadline:
        response = client.get(
            f"/ui-api/chat/sessions/{session_id}/messages",
            params={"limit": 50, "offset": 0},
        )
        if response.status_code == 200:
            payload = response.json()
            last_payload = payload
            messages = payload.get("messages")
            if isinstance(messages, list) and predicate(messages):
                return messages
        time.sleep(poll_seconds)

    raise AssertionError(
        "이력 반영 대기 시간 초과. "
        f"session_id={session_id}, last_payload={json.dumps(last_payload or {}, ensure_ascii=False)}"
    )


def parse_references(payload: dict) -> list[dict]:
    """SSE payload에서 references 목록을 파싱한다."""

    content = payload.get("content")
    if isinstance(content, list):
        return [item for item in content if isinstance(item, dict)]
    if isinstance(content, str):
        raw = content.strip()
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return []
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]
    return []


def create_session(client: httpx.Client, title: str) -> str:
    """UI API를 통해 세션을 생성하고 session_id를 반환한다."""

    create_response = client.post("/ui-api/chat/sessions", json={"title": title})
    created = log_response("create-session", create_response)
    assert create_response.status_code == 201, create_response.text
    session_id = str(created.get("session_id") or "")
    assert session_id
    return session_id


def _typewriter_print(text: str, delay_seconds: float = 0.003) -> None:
    """텍스트를 typewriter 형태로 출력한다."""

    delay = float(os.getenv("E2E_TYPEWRITER_DELAY_SECONDS", str(delay_seconds)))
    for char in text:
        print(char, end="", flush=True)
        if delay > 0:
            time.sleep(delay)
