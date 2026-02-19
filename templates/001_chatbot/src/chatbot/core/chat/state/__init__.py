"""
목적: Chat 상태 모델 공개 API를 제공한다.
설명: 그래프 상태 타입을 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/chatbot/core/chat/state/graph_state.py
"""

from chatbot.core.chat.state.graph_state import ChatGraphState

__all__ = ["ChatGraphState"]
