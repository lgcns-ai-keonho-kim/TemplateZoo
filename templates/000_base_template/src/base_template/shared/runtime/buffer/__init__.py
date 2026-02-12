"""
목적: 런타임 이벤트 버퍼 모듈 공개 API를 제공한다.
설명: 인메모리/Redis 이벤트 버퍼 구현과 모델을 노출한다.
디자인 패턴: 퍼사드
참조: src/base_template/shared/runtime/buffer/model.py, src/base_template/shared/runtime/buffer/in_memory_buffer.py, src/base_template/shared/runtime/buffer/redis_buffer.py
"""

from base_template.shared.runtime.buffer.in_memory_buffer import InMemoryEventBuffer
from base_template.shared.runtime.buffer.model import EventBufferConfig, StreamEventItem
from base_template.shared.runtime.buffer.redis_buffer import RedisEventBuffer

__all__ = [
    "EventBufferConfig",
    "StreamEventItem",
    "InMemoryEventBuffer",
    "RedisEventBuffer",
]

