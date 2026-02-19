"""
목적: UI Chat 라우터 집계를 제공한다.
설명: 엔드포인트별 분리 라우터를 하나의 UI Chat 라우터로 묶는다.
디자인 패턴: 컴포지트 패턴
참조: src/chatbot/api/ui/routers/*.py
"""

from __future__ import annotations

from fastapi import APIRouter

from chatbot.api.const import UI_CHAT_API_PREFIX, UI_CHAT_API_TAG
from chatbot.api.ui.routers.create_session import router as create_session_router
from chatbot.api.ui.routers.delete_session import router as delete_session_router
from chatbot.api.ui.routers.list_messages import router as list_messages_router
from chatbot.api.ui.routers.list_sessions import router as list_sessions_router

router = APIRouter(prefix=UI_CHAT_API_PREFIX, tags=[UI_CHAT_API_TAG])
router.include_router(create_session_router)
router.include_router(list_sessions_router)
router.include_router(list_messages_router)
router.include_router(delete_session_router)
