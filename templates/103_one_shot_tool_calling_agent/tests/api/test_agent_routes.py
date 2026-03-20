"""
목적: Agent 공개 라우트 구성을 검증한다.
설명: `/agent`, `/health`, `/ui` 공개 경계와 불필요한 레거시 라우트 부재를 실제 앱 기준으로 확인한다.
디자인 패턴: 통합 테스트
참조: src/one_shot_tool_calling_agent/api/main.py
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from one_shot_tool_calling_agent.api.main import app


def test_public_routes_are_reduced_to_agent_health_and_ui() -> None:
    """앱은 `/agent`, `/health`, `/ui` 중심 공개 경계만 가져야 한다."""

    route_paths = {route.path for route in app.routes}

    assert "/agent" in route_paths
    assert "/health" in route_paths
    assert "/ui" in route_paths
    assert "/chat" not in route_paths
    assert "/ui-api/chat/sessions" not in route_paths


def test_agent_request_requires_request_body_field() -> None:
    """`/agent`는 request 필드가 없으면 422를 반환해야 한다."""

    client = TestClient(app)

    response = client.post("/agent", json={})

    assert response.status_code == 422


def test_ui_mount_serves_one_shot_page() -> None:
    """`/ui`는 정적 단일 요청 화면을 반환해야 한다."""

    client = TestClient(app)

    response = client.get("/ui")

    assert response.status_code == 200
    assert "one shot tool calling agent" in response.text
