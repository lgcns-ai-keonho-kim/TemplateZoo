"""
목적: Chat 메시지 상수(Enum) 공개 API를 제공한다.
설명: safeguard 거부 메시지 Enum을 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/chatbot/core/chat/const/messages/safeguard.py
"""

from chatbot.core.chat.const.messages.safeguard import SafeguardRejectionMessage

__all__ = ["SafeguardRejectionMessage"]

