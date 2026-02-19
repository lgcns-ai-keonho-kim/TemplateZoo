"""
목적: PGVector 타입 어댑터를 제공한다.
설명: pgvector 타입 등록, 파라미터 생성, 결과 파싱을 통합한다.
디자인 패턴: 어댑터 패턴
참조: src/chatbot/integrations/db/engines/postgres/engine.py
"""

from __future__ import annotations

from typing import Any, List, Optional


class PostgresVectorAdapter:
    """PGVector 어댑터 구현체."""

    def __init__(self, register_fn, vector_cls) -> None:
        self._register_fn = register_fn
        self._vector_cls = vector_cls
        self._enabled = False

    @property
    def enabled(self) -> bool:
        """PGVector 어댑터 활성 여부를 반환한다."""

        return self._enabled

    def register(self, connection) -> bool:
        """PGVector 타입 어댑터를 등록한다."""

        if self._register_fn is None:
            self._enabled = False
            return False
        try:
            self._register_fn(connection)
        except Exception:
            self._enabled = False
            return False
        self._enabled = True
        return True

    def param(self, values: List[float]) -> object:
        """쿼리 파라미터로 사용할 벡터를 생성한다."""

        if not values:
            raise ValueError("벡터 값이 비어 있습니다.")
        if self._enabled and self._vector_cls is not None:
            return self._vector_cls(values)
        return self._literal(values)

    def distance_expr(self, column: str) -> str:
        """거리 계산 SQL 표현식을 반환한다."""

        if self._enabled:
            return f"{column} <-> %s"
        return f"{column} <-> %s::vector"

    def parse(self, raw_vector: Any) -> Optional[List[float]]:
        """PGVector 결과를 파싱해 float 리스트로 반환한다."""

        if raw_vector is None:
            return None
        if hasattr(raw_vector, "to_list"):
            try:
                return list(raw_vector.to_list())
            except Exception:
                pass
        if hasattr(raw_vector, "tolist"):
            try:
                return list(raw_vector.tolist())
            except Exception:
                pass
        if isinstance(raw_vector, memoryview):
            raw_vector = raw_vector.tobytes()
        if isinstance(raw_vector, (bytes, bytearray)):
            raw_vector = raw_vector.decode()
        if isinstance(raw_vector, list):
            return raw_vector
        if isinstance(raw_vector, tuple):
            return list(raw_vector)
        if isinstance(raw_vector, str):
            cleaned = raw_vector.strip()
            if cleaned.startswith("[") and cleaned.endswith("]"):
                cleaned = cleaned[1:-1]
            if not cleaned:
                return []
            try:
                return [float(item) for item in cleaned.split(",")]
            except ValueError:
                return None
        try:
            return list(raw_vector)
        except TypeError:
            return None

    def _literal(self, values: List[float]) -> str:
        return "[" + ",".join(str(value) for value in values) + "]"
