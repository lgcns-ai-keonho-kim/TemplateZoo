"""
목적: Agent API 라우터를 제공한다.
설명: one shot tool calling agent 실행 엔드포인트를 직접 정의한다.
디자인 패턴: 라우터 패턴
참조: src/one_shot_tool_calling_agent/shared/agent/services/agent_service.py
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from one_shot_tool_calling_agent.api.agent.models import (
    RunAgentRequest,
    RunAgentResponse,
    ToolResultItem,
)
from one_shot_tool_calling_agent.api.agent.routers.common import to_http_exception
from one_shot_tool_calling_agent.api.agent.services import get_agent_service
from one_shot_tool_calling_agent.api.const import AGENT_API_PREFIX, AGENT_API_TAG
from one_shot_tool_calling_agent.api.const import AGENT_API_RUN_PATH
from one_shot_tool_calling_agent.shared.agent import AgentService
from one_shot_tool_calling_agent.shared.exceptions import BaseAppException

router = APIRouter(prefix=AGENT_API_PREFIX, tags=[AGENT_API_TAG])


@router.post(
    AGENT_API_RUN_PATH,
    response_model=RunAgentResponse,
    summary="one shot tool calling agent 요청을 실행합니다.",
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
