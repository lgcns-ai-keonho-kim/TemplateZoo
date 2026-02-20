"""
목적: sqlite-vec 벡터 직렬화 도우미를 제공한다.
설명: sqlite-vec 버전 차이를 흡수해 float32 직렬화/역직렬화를 수행한다.
디자인 패턴: 유틸리티 클래스
참조: src/rag_chatbot/integrations/db/engines/sqlite/engine.py
"""

from __future__ import annotations

import struct
from typing import List, Optional


class SqliteVectorCodec:
    """sqlite-vec 벡터 직렬화/역직렬화 유틸리티."""

    def __init__(self, sqlite_vec_module) -> None:
        self._sqlite_vec = sqlite_vec_module

    def serialize(self, values: List[float]) -> bytes:
        """리스트형 벡터를 sqlite-vec BLOB으로 직렬화한다."""

        if not self._sqlite_vec:
            raise RuntimeError("sqlite-vec 패키지가 설치되어 있지 않습니다.")
        if not values:
            raise ValueError("벡터 값이 비어 있습니다.")
        try:
            normalized = [float(value) for value in values]
        except (TypeError, ValueError) as exc:
            raise ValueError("벡터 값이 숫자로 변환되지 않습니다.") from exc
        if hasattr(self._sqlite_vec, "serialize_float32"):
            return self._sqlite_vec.serialize_float32(normalized)
        return struct.pack(f"{len(normalized)}f", *normalized)

    def deserialize(self, raw: object, dimension: int) -> Optional[List[float]]:
        """sqlite-vec BLOB을 리스트형 벡터로 복원한다."""

        if raw is None:
            return None
        if not self._sqlite_vec:
            return None
        if isinstance(raw, memoryview):
            raw = raw.tobytes()
        if isinstance(raw, (bytes, bytearray)):
            if hasattr(self._sqlite_vec, "deserialize_float32"):
                return self._sqlite_vec.deserialize_float32(raw)
            if hasattr(self._sqlite_vec, "deserialize"):
                return self._sqlite_vec.deserialize(raw)
            try:
                return list(struct.unpack(f"{dimension}f", raw))
            except struct.error:
                return None
        if isinstance(raw, list):
            return raw
        return None
