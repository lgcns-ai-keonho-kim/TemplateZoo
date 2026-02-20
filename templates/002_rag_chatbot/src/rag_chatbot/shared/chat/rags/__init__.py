"""
목적: RAG 모듈 공개 API를 제공한다.
설명: 함수형 파이프라인 진입점을 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/rag_chatbot/shared/chat/rags/functions/pipeline.py
"""

from rag_chatbot.shared.chat.rags.functions import run_rag_pipeline

__all__ = ["run_rag_pipeline"]
