"""
목적: Chat 그래프 공개 API를 제공한다.
설명: LangGraph 기반 대화 그래프 엔트리를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/base_template/core/chat/graphs/chat_graph.py
"""

from base_template.core.chat.graphs.chat_graph import ChatGraph

__all__ = ["ChatGraph"]
