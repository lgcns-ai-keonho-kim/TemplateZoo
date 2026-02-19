"""
목적: 파일 시스템 베이스 모듈 공개 API를 제공한다.
설명: 파일 시스템 엔진 인터페이스를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/chatbot/integrations/fs/base/engine.py
"""

from chatbot.integrations.fs.base.engine import BaseFSEngine

__all__ = ["BaseFSEngine"]
