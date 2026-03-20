"""
목적: Agent API 라우터를 단일 공개 경계로 제공한다.
설명: 1회성 Agent 실행 엔드포인트와 예외 매핑을 한 파일에서 관리한다.
디자인 패턴: 라우터 패턴
참조: src/one_shot_agent/api/agent/models/run.py, src/one_shot_agent/shared/agent/services/agent_service.py
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from one_shot_agent.api.agent.models import (
    RunAgentRequest,
    RunAgentResponse,
)
from one_shot_agent.api.agent.services import get_agent_service
from one_shot_agent.api.const import (
    AGENT_API_PREFIX,
    AGENT_API_RUN_PATH,
    AGENT_API_TAG,
)
from one_shot_agent.shared.agent import AgentService
from one_shot_agent.shared.exceptions import BaseAppException, ExceptionDetail

router = APIRouter(prefix=AGENT_API_PREFIX, tags=[AGENT_API_TAG])


def _to_public_error(error: BaseAppException) -> dict[str, Any]:
    """내부 오류를 외부 공개용 오류 형식으로 정리한다."""

    code = error.detail.code
    if code == "AGENT_STREAM_NODE_INVALID":
        public_error = BaseAppException(
            message="Agent 실행 설정이 올바르지 않습니다.",
            detail=ExceptionDetail(code="AGENT_EXECUTION_CONFIG_INVALID"),
        )
        return public_error.to_dict()

    if code == "AGENT_STREAM_EMPTY":
        public_error = BaseAppException(
            message="Agent 응답이 비어 있습니다.",
            detail=ExceptionDetail(
                code="AGENT_RESPONSE_EMPTY",
                cause=error.detail.cause,
                hint=error.detail.hint,
                metadata=error.detail.metadata,
            ),
        )
        return public_error.to_dict()

    return error.to_dict()


def _to_http_exception(error: BaseAppException) -> HTTPException:
    """도메인 예외를 HTTP 예외로 변환한다."""

    public_error = _to_public_error(error)
    detail = public_error.get("detail", {})
    code = str(detail.get("code") or "")
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    if code == "AGENT_REQUEST_EMPTY":
        status_code = status.HTTP_400_BAD_REQUEST
    if code in {"AGENT_REQUEST_TIMEOUT"}:
        status_code = status.HTTP_504_GATEWAY_TIMEOUT
    return HTTPException(status_code=status_code, detail=public_error)


@router.post(
    AGENT_API_RUN_PATH,
    response_model=RunAgentResponse,
    summary="1회성 Agent 요청을 실행합니다.",
)
async def run_agent(
    request: RunAgentRequest,
    service: AgentService = Depends(get_agent_service),
) -> RunAgentResponse:
    """사용자 요청 1건을 바로 실행한다."""

    try:
        result = await service.arun_once(request.request)
    except BaseAppException as error:
        raise _to_http_exception(error) from error

    return RunAgentResponse(
        run_id=result.run_id,
        status=result.status.value,
        output_text=result.output_text,
    )
