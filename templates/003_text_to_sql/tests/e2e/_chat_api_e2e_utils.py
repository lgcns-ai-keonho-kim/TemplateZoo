"""
목적: Chat API E2E 테스트 공통 유틸을 제공한다.
설명: 세션 생성/스트리밍/이력 대기/응답 파싱과 공통 로깅을 재사용 가능한 함수로 분리한다.
디자인 패턴: 테스트 유틸리티 모듈
참조: tests/e2e/_chat_api_e2e_cases.py, tests/e2e/test_chat_api_server_e2e.py
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from typing import Any

import httpx

STREAM_TIMEOUT = httpx.Timeout(connect=10.0, read=180.0, write=30.0, pool=10.0)
HISTORY_WAIT_TIMEOUT_SECONDS = 30.0
HISTORY_WAIT_POLL_SECONDS = 0.5
HOUSING_COMPARISON_QUERY = "미국에서 가장 비싼 집이랑 보스톤에서 가장 비싼 집 가격 비교해줘"
HOUSING_SECOND_QUERY = "방금 결과에서 MEDV 값이 무슨 의미인지 설명해줘."
ECOMMERCE_TOP_AGENTS_QUERY = """
영업사원별 총 주문금액, 주문 건수, 담당 고객 수를 집계해서 총 주문금액 상위 5명의 이름과 어떤 지역에서 일하는지 알려줘. 종합적으로 정보를 제공해줘.
"""

_LOGGER = logging.getLogger("tests")


def _log_sse_event(session_id: str, request_id: str, payload: dict[str, Any]) -> None:
    """sql_plan/sql_result 및 최종 response(done) 이벤트만 테스트 로그로 출력한다."""

    event_type = str(payload.get("type") or "")
    node = str(payload.get("node") or "")
    content = str(payload.get("content") or "")
    error_message = str(payload.get("error_message") or "")

    if event_type == "error":
        _LOGGER.error(
            "[sse] session_id=%s request_id=%s type=%s node=%s error=%s content=%s",
            session_id,
            request_id,
            event_type,
            node,
            error_message,
            content,
        )
        return

    if event_type in {"sql_plan", "sql_result"}:
        _LOGGER.info(
            "[sse] session_id=%s request_id=%s type=%s node=%s content=%s",
            session_id,
            request_id,
            event_type,
            node,
            content,
        )
        return

    if event_type != "done":
        return

    _LOGGER.info(
        "[response] session_id=%s request_id=%s content=%s",
        session_id,
        request_id,
        content,
    )


def require_json_payload(response: httpx.Response) -> dict[str, Any]:
    """HTTP 응답을 JSON dict로 파싱해 반환한다."""

    try:
        payload = response.json()
    except Exception as error:  # noqa: BLE001 - 테스트 실패 메시지 구체화
        raise AssertionError(
            f"JSON 파싱 실패: status={response.status_code}, body={response.text}"
        ) from error
    if not isinstance(payload, dict):
        raise AssertionError(f"응답 본문 타입이 dict가 아닙니다: {type(payload).__name__}")
    return {str(key): value for key, value in payload.items()}


def parse_event_content(payload: dict[str, Any]) -> dict[str, Any]:
    """SSE 이벤트의 content 필드를 JSON dict로 파싱해 반환한다."""

    content = payload.get("content")
    if isinstance(content, dict):
        return {str(key): value for key, value in content.items()}
    if not isinstance(content, str):
        raise AssertionError(
            "SSE content 타입이 JSON 객체 또는 문자열이 아닙니다: "
            f"{type(content).__name__}"
        )
    try:
        parsed = json.loads(content)
    except Exception as error:  # noqa: BLE001 - 테스트 실패 메시지 구체화
        raise AssertionError(f"SSE content JSON 파싱 실패: content={content}") from error
    if not isinstance(parsed, dict):
        raise AssertionError(
            f"SSE content 파싱 결과 타입이 dict가 아닙니다: {type(parsed).__name__}"
        )
    return {str(key): value for key, value in parsed.items()}


def find_sse_event(
    events: list[dict[str, Any]],
    *,
    event_type: str,
    node: str | None = None,
) -> dict[str, Any]:
    """조건에 맞는 마지막 SSE 이벤트를 반환한다."""

    matched: dict[str, Any] | None = None
    for item in events:
        if str(item.get("type") or "") != event_type:
            continue
        if node is not None and str(item.get("node") or "") != node:
            continue
        matched = item
    if matched is None:
        raise AssertionError(
            f"SSE 이벤트를 찾지 못했습니다: event_type={event_type}, node={node}"
        )
    return matched


def create_session(client: httpx.Client, title: str) -> str:
    """UI API로 세션을 생성하고 session_id를 반환한다."""

    response = client.post("/ui-api/chat/sessions", json={"title": title})
    assert response.status_code == 201, response.text

    payload = require_json_payload(response)
    session_id = str(payload.get("session_id") or "")
    assert session_id
    return session_id


def stream_message(
    client: httpx.Client,
    session_id: str,
    message: str,
    context_window: int = 20,
) -> list[dict[str, Any]]:
    """작업 제출 + 이벤트 스트림 구독을 호출하고 SSE 이벤트 목록을 반환한다."""

    _LOGGER.info(
        "[chat_query] session_id=%s context_window=%s message=%s",
        session_id,
        context_window,
        message,
    )

    submit = client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": message,
            "context_window": context_window,
        },
        timeout=STREAM_TIMEOUT,
    )
    assert submit.status_code == 202, submit.text
    submit_payload = require_json_payload(submit)

    request_id = str(submit_payload.get("request_id") or "")
    resolved_session_id = str(submit_payload.get("session_id") or "")
    assert request_id
    assert resolved_session_id == session_id
    _LOGGER.info(
        "[chat_submit] session_id=%s request_id=%s",
        session_id,
        request_id,
    )

    events: list[dict[str, Any]] = []
    with client.stream(
        "GET",
        f"/chat/{session_id}/events",
        params={"request_id": request_id},
        headers={"Accept": "text/event-stream"},
        timeout=STREAM_TIMEOUT,
    ) as response:
        assert response.status_code == 200, response.text
        for line in response.iter_lines():
            if not line or not line.startswith("data: "):
                continue
            payload = json.loads(line[len("data: ") :].strip())
            if not isinstance(payload, dict):
                continue
            normalized_payload = {str(key): value for key, value in payload.items()}
            _log_sse_event(
                session_id=session_id,
                request_id=request_id,
                payload=normalized_payload,
            )
            events.append(normalized_payload)
            if str(normalized_payload.get("type") or "") in {"done", "error"}:
                break

    if not any(str(item.get("type") or "") in {"done", "error"} for item in events):
        _LOGGER.warning(
            "[sse] session_id=%s request_id=%s finished_without_terminal_event last_event=%s",
            session_id,
            request_id,
            events[-1] if events else {},
        )

    return events


def wait_until_messages(
    client: httpx.Client,
    session_id: str,
    predicate: Callable[[list[dict[str, Any]]], bool],
    timeout_seconds: float = HISTORY_WAIT_TIMEOUT_SECONDS,
    poll_seconds: float = HISTORY_WAIT_POLL_SECONDS,
) -> list[dict[str, Any]]:
    """메시지 이력이 조건을 만족할 때까지 polling 한다."""

    deadline = time.monotonic() + timeout_seconds
    last_payload: dict[str, Any] | None = None

    while time.monotonic() < deadline:
        response = client.get(
            f"/ui-api/chat/sessions/{session_id}/messages",
            params={"limit": 50, "offset": 0},
        )
        if response.status_code == 200:
            payload = require_json_payload(response)
            last_payload = payload
            messages = payload.get("messages")
            if isinstance(messages, list):
                normalized_messages = [
                    {str(key): value for key, value in item.items()}
                    for item in messages
                    if isinstance(item, dict)
                ]
                if predicate(normalized_messages):
                    return normalized_messages
        time.sleep(poll_seconds)

    raise AssertionError(
        "이력 반영 대기 시간 초과. "
        f"session_id={session_id}, last_payload={json.dumps(last_payload or {}, ensure_ascii=False)}"
    )
