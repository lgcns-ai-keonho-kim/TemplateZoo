"""
목적: Agent API 서버 E2E 테스트를 제공한다.
설명: 실제 uvicorn 서버에 HTTP 요청을 보내 `/agent` 단건 응답 계약을 검증한다.
디자인 패턴: 블랙박스 E2E 테스트
참조: tests/conftest.py, src/one_shot_agent/api/agent/routers/router.py
"""

from __future__ import annotations

import logging

import httpx

_LOGGER = logging.getLogger("tests.e2e.agent_api")

SUMMARY_QUERY = "아래 문장을 두 문장으로 요약해줘. 프로젝트 일정이 일주일 밀렸고, 배포 범위는 그대로 유지되며, QA는 다음 주 화요일에 시작한다."
TRANSLATION_QUERY = "다음 문장을 한국어로 번역해줘: Please send me the final draft by tomorrow morning."
_REQUEST_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=10.0)


def _require_json_payload(response: httpx.Response) -> dict:
    """HTTP 응답을 JSON dict로 파싱해 반환한다."""

    payload = response.json()
    assert isinstance(payload, dict)
    return payload


def _assert_single_response_shape(payload: dict) -> None:
    """최소 단일 응답 구조를 확인한다."""

    assert str(payload.get("run_id") or "").strip()
    assert str(payload.get("status") or "").strip() == "COMPLETED"
    assert str(payload.get("output_text") or "").strip()
    assert "tool_results" not in payload


def test_agent_api_returns_single_json_response(agent_server_context) -> None:
    """요약 요청은 단일 JSON 응답으로 완료되어야 한다."""

    with httpx.Client(base_url=agent_server_context.base_url, timeout=_REQUEST_TIMEOUT) as client:
        response = client.post("/agent", json={"request": SUMMARY_QUERY})

    assert response.status_code == 200, response.text
    payload = _require_json_payload(response)

    _assert_single_response_shape(payload)

    _LOGGER.info("agent 단건 응답 요약: %s", payload.get("status"))


def test_agent_api_returns_translation_response(agent_server_context) -> None:
    """번역 요청도 동일한 단일 JSON 응답 계약을 따라야 한다."""

    with httpx.Client(base_url=agent_server_context.base_url, timeout=_REQUEST_TIMEOUT) as client:
        response = client.post("/agent", json={"request": TRANSLATION_QUERY})

    assert response.status_code == 200, response.text
    payload = _require_json_payload(response)

    _assert_single_response_shape(payload)
