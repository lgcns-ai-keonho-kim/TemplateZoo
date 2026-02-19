"""
목적: 코어 모듈 공개 API를 제공한다.
설명: Chat 코어 그래프 컴포넌트를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/base_template/core/chat/graphs/chat_graph.py
"""

from base_template.core.chat import ChatGraphInput, chat_graph

__all__ = ["ChatGraphInput", "chat_graph"]
