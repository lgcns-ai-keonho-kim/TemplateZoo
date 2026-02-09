"""
목적: Chat API 라우터 집계를 제공한다.
설명: 엔드포인트별 분리 라우터를 하나의 Chat 라우터로 묶는다.
디자인 패턴: 컴포지트 패턴
참조: src/base_template/api/chat/routers/*.py
"""

from __future__ import annotations

from fastapi import APIRouter

from base_template.api.chat.routers.create_session import router as create_session_router
from base_template.api.chat.routers.get_task_result import router as get_task_result_router
from base_template.api.chat.routers.get_task_status import router as get_task_status_router
from base_template.api.chat.routers.list_messages import router as list_messages_router
from base_template.api.chat.routers.list_sessions import router as list_sessions_router
from base_template.api.chat.routers.queue_message import router as queue_message_router
from base_template.api.chat.routers.stream_task_result import (
    router as stream_task_result_router,
)

router = APIRouter(prefix="/chat", tags=["chat"])
router.include_router(create_session_router)
router.include_router(list_sessions_router)
router.include_router(list_messages_router)
router.include_router(queue_message_router)
router.include_router(get_task_status_router)
router.include_router(get_task_result_router)
router.include_router(stream_task_result_router)

