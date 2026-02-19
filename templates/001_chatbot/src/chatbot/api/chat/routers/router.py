"""
목적: Chat API 라우터 집계를 제공한다.
설명: 엔드포인트별 분리 라우터를 하나의 Chat 라우터로 묶는다.
디자인 패턴: 컴포지트 패턴
참조: src/chatbot/api/chat/routers/*.py
"""

from __future__ import annotations

from fastapi import APIRouter

from chatbot.api.const import CHAT_API_PREFIX, CHAT_API_TAG
from chatbot.api.chat.routers.create_chat import router as create_chat_router
from chatbot.api.chat.routers.get_chat_session import router as get_chat_session_router
from chatbot.api.chat.routers.stream_chat_events import router as stream_chat_events_router

router = APIRouter(tags=[CHAT_API_TAG])
router.include_router(create_chat_router, prefix=CHAT_API_PREFIX)
router.include_router(stream_chat_events_router, prefix=CHAT_API_PREFIX)
router.include_router(get_chat_session_router, prefix=CHAT_API_PREFIX)
