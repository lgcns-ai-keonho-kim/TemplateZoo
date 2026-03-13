"""
목적: 1회성 Agent 실행 라우터를 제공한다.
설명: 사용자 요청 1건을 직접 실행하고 최종 응답 JSON을 반환한다.
디자인 패턴: 라우터 패턴
참조: src/single_request_tool_agent/shared/agent/services/agent_service.py
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from single_request_tool_agent.api.agent.models import (
    RunAgentRequest,
    RunAgentResponse,
    ToolResultItem,
)
from single_request_tool_agent.api.agent.routers.common import to_http_exception
from single_request_tool_agent.api.agent.services import get_agent_service
from single_request_tool_agent.api.const import AGENT_API_RUN_PATH
from single_request_tool_agent.shared.agent import AgentService
from single_request_tool_agent.shared.exceptions import BaseAppException

router = APIRouter()


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
        raise to_http_exception(error) from error

    return RunAgentResponse(
        run_id=result.run_id,
        status=result.status.value,
        output_text=result.output_text,
        tool_results=[
            ToolResultItem(
                tool_name=item.tool_name,
                status=item.status,
                output=item.output,
                error_message=item.error_message,
                attempt=item.attempt,
            )
            for item in result.tool_results
        ],
    )
