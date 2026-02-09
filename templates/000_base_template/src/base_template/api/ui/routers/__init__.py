"""
목적: UI 라우터 공개 API를 제공한다.
설명: UI 조회 라우터 인스턴스를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/base_template/api/ui/routers/chat.py
"""

from base_template.api.ui.routers.chat import router

__all__ = ["router"]
