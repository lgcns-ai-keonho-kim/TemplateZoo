"""
목적: SQLite 엔진 공개 API를 제공한다.
설명: SQLite 벡터 엔진 클래스를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/base_template/integrations/db/engines/sqlite/engine.py
"""

from base_template.integrations.db.engines.sqlite.engine import SQLiteEngine

__all__ = ["SQLiteEngine"]
