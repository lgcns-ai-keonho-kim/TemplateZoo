"""
목적: Chat 메모리 저장소 공개 API를 제공한다.
설명: 세션 메모리 캐시 구현체를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/base_template/shared/chat/memory/session_store.py
"""

from base_template.shared.chat.memory.session_store import ChatSessionMemoryStore

__all__ = ["ChatSessionMemoryStore"]

