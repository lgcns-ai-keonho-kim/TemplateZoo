"""
목적: 공통 메모리 모듈 공개 API를 제공한다.
설명: 세션 리스트 메모리 저장소를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/base_template/core/common/memory/session_list_store.py
"""

from base_template.core.common.memory.session_list_store import ChatSessionMemoryStore

__all__ = ["ChatSessionMemoryStore"]
