"""
목적: 스레드풀 모듈 공개 API를 제공한다.
설명: 스레드풀 설정/태스크 모델과 실행기를 노출한다.
디자인 패턴: 퍼사드
참조: src/chatbot/shared/runtime/thread_pool/model.py, src/chatbot/shared/runtime/thread_pool/thread_pool.py
"""

from chatbot.shared.runtime.thread_pool.model import TaskRecord, ThreadPoolConfig
from chatbot.shared.runtime.thread_pool.thread_pool import ThreadPool

__all__ = ["TaskRecord", "ThreadPoolConfig", "ThreadPool"]
