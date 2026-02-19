"""
목적: Chat 유틸 모듈 공개 API를 제공한다.
설명: Chat 도메인 전용 매퍼 클래스를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/base_template/core/chat/utils/mapper.py
"""

from base_template.core.chat.utils.mapper import ChatHistoryMapper

__all__ = ["ChatHistoryMapper"]
