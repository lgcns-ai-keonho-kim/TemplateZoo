"""
목적: Chat API 서버 E2E 테스트를 제공한다.
설명: 실제 uvicorn 서버에 HTTP 요청을 보내 세션/큐/스트림/상태/결과 흐름을 검증한다.
디자인 패턴: 블랙박스 E2E 테스트
참조: tests/e2e/conftest.py, src/base_template/api/chat/routers/router.py
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import httpx


def _log_response(label: str, response: httpx.Response) -> dict:
    """HTTP 응답 본문을 로그로 출력하고 JSON 본문을 반환한다."""

    print(f"[e2e] {label} status={response.status_code}")
    try:
        payload = response.json()
    except Exception:  # noqa: BLE001 - 테스트 로그 출력 용도
        print(f"[e2e] {label} body={response.text}")
        return {}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return payload


def _typewriter_print(text: str, delay_seconds: float = 0.003) -> None:
    """텍스트를 typewriter 형태로 출력한다."""

    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay_seconds)


def _wait_until_completed(
    client: httpx.Client,
    session_id: str,
    task_id: str,
    timeout_seconds: float = 90.0,
) -> dict:
    """태스크가 완료 또는 실패 상태가 될 때까지 폴링한다."""

    deadline = time.monotonic() + timeout_seconds
    last_payload: dict = {}
    while time.monotonic() < deadline:
        response = client.get(f"/chat/sessions/{session_id}/tasks/{task_id}/status")
        assert response.status_code == 200, response.text
        last_payload = _log_response("task-status", response)
        status = last_payload["status"]
        if status in {"COMPLETED", "FAILED"}:
            return last_payload
        time.sleep(0.2)
    raise AssertionError(f"태스크 완료 대기 타임아웃: {last_payload}")


def test_create_and_list_sessions(chat_api_client: httpx.Client) -> None:
    """세션 생성 후 목록 조회에서 동일 세션이 보이는지 확인한다."""

    create_response = chat_api_client.post("/chat/sessions", json={"title": "E2E 세션"})
    created = _log_response("create-session", create_response)
    assert create_response.status_code == 201, create_response.text
    session_id = created["session_id"]
    assert session_id

    list_response = chat_api_client.get("/chat/sessions", params={"limit": 20, "offset": 0})
    listed = _log_response("list-sessions", list_response)
    assert list_response.status_code == 200, list_response.text
    sessions = listed["sessions"]
    assert any(item["session_id"] == session_id for item in sessions)


def test_delete_session_via_ui_api(chat_api_client: httpx.Client) -> None:
    """UI API로 세션을 삭제하면 목록/메시지 조회에서 제거되는지 확인한다."""

    create_response = chat_api_client.post("/chat/sessions", json={"title": "삭제 테스트"})
    created = _log_response("create-session", create_response)
    assert create_response.status_code == 201, create_response.text
    session_id = created["session_id"]

    queue_response = chat_api_client.post(
        f"/chat/sessions/{session_id}/queue",
        json={"message": "삭제 전 메시지 1건 저장"},
    )
    queued = _log_response("queue-message-before-delete", queue_response)
    assert queue_response.status_code == 201, queue_response.text
    _wait_until_completed(chat_api_client, session_id, queued["task_id"])

    delete_response = chat_api_client.delete(f"/ui-api/chat/sessions/{session_id}")
    deleted = _log_response("delete-session", delete_response)
    assert delete_response.status_code == 200, delete_response.text
    assert deleted["session_id"] == session_id
    assert deleted["deleted"] is True

    list_response = chat_api_client.get("/chat/sessions", params={"limit": 50, "offset": 0})
    listed = _log_response("list-sessions-after-delete", list_response)
    assert list_response.status_code == 200, list_response.text
    assert all(item["session_id"] != session_id for item in listed["sessions"])

    messages_response = chat_api_client.get(
        f"/chat/sessions/{session_id}/messages",
        params={"limit": 20, "offset": 0},
    )
    _ = _log_response("list-messages-after-delete", messages_response)
    assert messages_response.status_code == 404, messages_response.text


def test_queue_status_result_and_history(chat_api_client: httpx.Client) -> None:
    """큐 등록 후 상태/결과/이력 조회 흐름을 검증한다."""

    create_response = chat_api_client.post("/chat/sessions", json={"title": "큐 테스트"})
    created = _log_response("create-session", create_response)
    assert create_response.status_code == 201, create_response.text
    session_id = created["session_id"]

    queue_response = chat_api_client.post(
        f"/chat/sessions/{session_id}/queue",
        json={"message": "안녕하세요. 큐 기반 테스트입니다."},
    )
    queued = _log_response("queue-message", queue_response)
    assert queue_response.status_code == 201, queue_response.text
    assert queued["session_id"] == session_id
    task_id = queued["task_id"]
    assert task_id

    status_payload = _wait_until_completed(chat_api_client, session_id, task_id)
    assert status_payload["status"] in {"COMPLETED", "FAILED"}

    second_message = "이전 답변을 바탕으로 핵심만 1줄로 다시 정리해줘."
    queue_response_2 = chat_api_client.post(
        f"/chat/sessions/{session_id}/queue",
        json={"message": second_message},
    )
    queued_2 = _log_response("queue-message-2", queue_response_2)
    assert queue_response_2.status_code == 201, queue_response_2.text
    second_task_id = queued_2["task_id"]
    assert second_task_id
    second_status_payload = _wait_until_completed(chat_api_client, session_id, second_task_id)
    assert second_status_payload["status"] in {"COMPLETED", "FAILED"}

    result_response = chat_api_client.get(f"/chat/sessions/{session_id}/tasks/{task_id}/result")
    assert result_response.status_code == 200, result_response.text
    result_payload = _log_response("task-result", result_response)
    assert result_payload["status"] in {"COMPLETED", "FAILED"}
    if result_payload["status"] == "COMPLETED":
        assert result_payload["assistant_message"] is not None
        assert result_payload["assistant_message"]["content"]
    else:
        assert result_payload["error_message"]

    messages_response = chat_api_client.get(
        f"/chat/sessions/{session_id}/messages",
        params={"limit": 20, "offset": 0},
    )
    messages_payload = _log_response("list-messages", messages_response)
    assert messages_response.status_code == 200, messages_response.text
    messages = messages_payload["messages"]
    if status_payload["status"] == "COMPLETED" and second_status_payload["status"] == "COMPLETED":
        assert len(messages) >= 4
        roles = [item["role"] for item in messages[-4:]]
        assert roles == ["user", "assistant", "user", "assistant"]
        assert messages[-2]["content"] == second_message
    else:
        user_contents = [item["content"] for item in messages if item["role"] == "user"]
        assert "안녕하세요. 큐 기반 테스트입니다." in user_contents
        assert second_message in user_contents


def test_stream_endpoint(chat_api_client: httpx.Client) -> None:
    """스트림 엔드포인트에서 token 타입 SSE 포맷을 검증한다."""

    create_response = chat_api_client.post("/chat/sessions", json={"title": "스트림 테스트"})
    created = _log_response("create-session", create_response)
    assert create_response.status_code == 201, create_response.text
    session_id = created["session_id"]

    queue_response = chat_api_client.post(
        f"/chat/sessions/{session_id}/queue",
        json={"message": "스트림으로 응답을 받고 싶습니다."},
    )
    queued = _log_response("queue-message", queue_response)
    assert queue_response.status_code == 201, queue_response.text
    task_id = queued["task_id"]

    types: list[str] = []
    print("[e2e] stream-token-output:")
    with chat_api_client.stream(
        "GET",
        f"/chat/sessions/{session_id}/tasks/{task_id}/stream",
    ) as response:
        assert response.status_code == 200, response.text
        for line in response.iter_lines():
            if not line:
                continue
            if line.startswith("data: "):
                raw = line[len("data: ") :].strip()
                payload = json.loads(raw)
                assert isinstance(payload, dict)
                assert "type" in payload
                payload_type = str(payload["type"])
                types.append(payload_type)
                assert payload_type in {"start", "token", "done", "error"}
                if payload_type == "token":
                    assert "content" in payload
                    assert isinstance(payload["content"], str)
                    _typewriter_print(payload["content"])
                if payload_type in {"done", "error"}:
                    break
    print()

    assert "start" in types
    assert "token" in types
    assert "done" in types


def test_chat_sqlite_file_created(chat_server_context, chat_api_client: httpx.Client) -> None:
    """서버 기동 후 대화 DB 파일이 실제로 생성되는지 확인한다."""

    health_response = chat_api_client.get("/health")
    _ = _log_response("health", health_response)
    assert health_response.status_code == 200, health_response.text

    db_path = Path(chat_server_context.chat_db_path)
    assert db_path.exists()
