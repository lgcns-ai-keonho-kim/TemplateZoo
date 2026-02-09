"""
목적: 저장소 모듈 공개 API를 제공한다.
설명: 도메인별 저장소 패키지를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/base_template/core/repositories/chat
"""

from base_template.core.repositories.chat import ChatHistoryRepository

__all__ = ["ChatHistoryRepository"]
