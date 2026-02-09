"""
목적: 공통 모듈 공개 API를 제공한다.
설명: 도메인 간 재사용 가능한 공통 컴포넌트를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/base_template/core/common/memory/session_list_store.py
"""

from base_template.core.common.memory import ChatSessionMemoryStore

__all__ = ["ChatSessionMemoryStore"]
