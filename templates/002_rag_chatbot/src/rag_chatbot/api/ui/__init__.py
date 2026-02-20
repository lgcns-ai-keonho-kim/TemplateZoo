"""
목적: UI API 모듈 공개 API를 제공한다.
설명: UI 조회 라우터와 서비스 접근 함수를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/rag_chatbot/api/ui/routers/router.py, src/rag_chatbot/api/ui/services/chat_service.py
"""

from rag_chatbot.api.ui.routers import router
from rag_chatbot.api.ui.services import get_chat_ui_service

__all__ = ["router", "get_chat_ui_service"]
