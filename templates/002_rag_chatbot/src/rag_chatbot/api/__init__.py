"""
목적: API 모듈 공개 API를 제공한다.
설명: FastAPI 앱 객체를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/rag_chatbot/api/main.py
"""

from rag_chatbot.api.main import app

__all__ = ["app"]
