"""
목적: Agent API 공개 오류 매핑을 검증한다.
설명: 내부 스트림 관련 오류 코드가 외부 응답에서 비스트림 명칭으로 정리되는지 확인한다.
디자인 패턴: 경계 단위 테스트
참조: src/one_shot_agent/api/agent/routers/router.py, src/one_shot_agent/shared/agent/services/agent_service.py
"""

from __future__ import annotations

from fastapi import status

from one_shot_agent.api.agent.routers.router import _to_http_exception
from one_shot_agent.shared.exceptions import BaseAppException, ExceptionDetail


def test_agent_http_exception_rewrites_stream_config_error_to_public_code() -> None:
    """내부 stream 설정 오류는 외부 공개 코드로 치환되어야 한다."""

    error = BaseAppException(
        message="stream_node 설정 형식이 올바르지 않습니다.",
        detail=ExceptionDetail(
            code="AGENT_STREAM_NODE_INVALID",
            cause="stream_node must be mapping[str, set[str]]",
        ),
    )

    http_error = _to_http_exception(error)

    assert http_error.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert isinstance(http_error.detail, dict)
    assert http_error.detail["message"] == "Agent 실행 설정이 올바르지 않습니다."
    assert http_error.detail["detail"]["code"] == "AGENT_EXECUTION_CONFIG_INVALID"
    assert "STREAM" not in http_error.detail["detail"]["code"]
    assert "stream" not in http_error.detail["message"].lower()


def test_agent_http_exception_preserves_public_response_empty_code() -> None:
    """응답 비어 있음 오류는 공개 코드 이름으로만 노출되어야 한다."""

    error = BaseAppException(
        message="Agent 응답이 비어 있습니다.",
        detail=ExceptionDetail(
            code="AGENT_RESPONSE_EMPTY",
            cause="run_id=test-run, graph returned empty content",
        ),
    )

    http_error = _to_http_exception(error)

    assert http_error.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert isinstance(http_error.detail, dict)
    assert http_error.detail["detail"]["code"] == "AGENT_RESPONSE_EMPTY"
    assert "STREAM" not in http_error.detail["detail"]["code"]
