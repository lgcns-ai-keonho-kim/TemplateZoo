"""
목적: Chat 그래프 공통 추상체 공개 API를 제공한다.
설명: BaseChatGraph를 외부 모듈에서 재사용 가능하도록 노출한다.
디자인 패턴: 퍼사드
참조: src/chatbot/shared/chat/graph/base_chat_graph.py
"""

from chatbot.shared.chat.graph.base_chat_graph import BaseChatGraph

__all__ = ["BaseChatGraph"]
