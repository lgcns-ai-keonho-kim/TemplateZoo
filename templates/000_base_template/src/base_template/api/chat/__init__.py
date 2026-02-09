"""
목적: Chat API 모듈 공개 API를 제공한다.
설명: Chat 라우터와 서비스 접근 함수를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/base_template/api/chat/routers/chat.py, src/base_template/api/chat/services/chat_service.py
"""

from base_template.api.chat.routers import router
from base_template.api.chat.services import get_chat_api_service, shutdown_chat_api_service

__all__ = ["router", "get_chat_api_service", "shutdown_chat_api_service"]
