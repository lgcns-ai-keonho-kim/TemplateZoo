"""
목적: Chat LangGraph 오케스트레이터를 제공한다.
설명: Reply 노드 1개로 구성된 최소 그래프를 컴파일하고 대화 응답을 생성한다.
디자인 패턴: 파이프라인 패턴
참조: src/base_template/core/chat/nodes/reply_node.py
"""

from __future__ import annotations

from typing import Iterator, Optional

from langgraph.graph import END, StateGraph

from base_template.core.chat.models import ChatMessage
from base_template.core.chat.nodes import ChatReplyNode
from base_template.core.chat.state import ChatGraphState
from base_template.shared.exceptions import BaseAppException, ExceptionDetail
from base_template.shared.logging import Logger, create_default_logger


class ChatGraph:
    """LangGraph 기반 대화 그래프 래퍼."""

    def __init__(
        self,
        reply_node: Optional[ChatReplyNode] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        self._logger = logger or create_default_logger("ChatGraph")
        self._reply_node = reply_node or ChatReplyNode(logger=self._logger)

        builder = StateGraph(ChatGraphState)
        builder.add_node("reply", self._reply_node.run)
        builder.set_entry_point("reply")
        builder.add_edge("reply", END)
        self._graph = builder.compile()

    def invoke(
        self,
        session_id: str,
        user_message: str,
        history: list[ChatMessage],
    ) -> str:
        """대화 상태를 그래프에 전달해 스트림 결과를 단일 문자열로 합친다."""

        self._logger.info("Chat 그래프 실행")
        chunks = [
            chunk
            for chunk in self.stream(
                session_id=session_id,
                user_message=user_message,
                history=history,
            )
            if chunk
        ]
        answer = "".join(chunks).strip()
        if answer:
            return answer
        detail = ExceptionDetail(
            code="CHAT_STREAM_EMPTY",
            cause="chat graph stream produced empty content",
        )
        raise BaseAppException("스트리밍 응답이 비어 있습니다.", detail)

    def stream(
        self,
        session_id: str,
        user_message: str,
        history: list[ChatMessage],
    ) -> Iterator[str]:
        """대화 상태를 그래프에 전달해 토큰 스트림을 생성한다."""

        self._logger.info("Chat 그래프 스트리밍 실행")
        yield from self._reply_node.stream(
            {
                "session_id": session_id,
                "user_message": user_message,
                "history": history,
                "assistant_message": "",
            }
        )
