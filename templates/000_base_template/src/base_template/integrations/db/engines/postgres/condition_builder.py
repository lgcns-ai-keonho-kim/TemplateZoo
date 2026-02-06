"""
목적: PostgreSQL 조건 빌더 모듈을 제공한다.
설명: 필터 모델을 PostgreSQL WHERE 절로 변환한다.
디자인 패턴: 빌더 패턴
참조: src/base_template/integrations/db/base/models.py
"""

from __future__ import annotations

from typing import List, Tuple

from base_template.integrations.db.base.models import (
    CollectionSchema,
    FieldSource,
    FilterCondition,
)
from base_template.integrations.db.engines.sql_common import (
    SQLIdentifierHelper,
    payload_field,
    resolve_source,
)


class PostgresConditionBuilder:
    """PostgreSQL 조건 빌더."""

    def __init__(self, identifier_helper: SQLIdentifierHelper) -> None:
        self._identifier = identifier_helper

    def build(self, condition: FilterCondition, schema: CollectionSchema) -> Tuple[str, List[object]]:
        """필터 조건을 WHERE 절로 변환한다."""

        field = condition.field
        operator = condition.operator.value
        value = condition.value
        source = resolve_source(condition.source, field, schema)
        if source == FieldSource.PAYLOAD:
            payload = payload_field(schema)
            expr = f"{self._identifier.quote_identifier(payload)} ->> %s"
            params: List[object] = [field]
            if operator == "EQ":
                return f"{expr} = %s", params + [str(value)]
            if operator == "NE":
                return f"{expr} != %s", params + [str(value)]
            if operator in {"GT", "GTE", "LT", "LTE"}:
                op_map = {"GT": ">", "GTE": ">=", "LT": "<", "LTE": "<="}
                cast_expr = (
                    f"({expr})::numeric" if isinstance(value, (int, float)) else expr
                )
                return f"{cast_expr} {op_map[operator]} %s", params + [value]
            if operator in {"IN", "NOT_IN"}:
                if not isinstance(value, list):
                    raise ValueError("IN/NOT_IN은 리스트 값이 필요합니다.")
                placeholders = ", ".join(["%s"] * len(value))
                op = "IN" if operator == "IN" else "NOT IN"
                return f"{expr} {op} ({placeholders})", params + [str(v) for v in value]
            if operator == "CONTAINS":
                return f"{expr} ILIKE %s", params + [f"%{value}%"]
        column = self._identifier.quote_identifier(field)
        params = []
        if operator == "EQ":
            return f"{column} = %s", params + [value]
        if operator == "NE":
            return f"{column} != %s", params + [value]
        if operator in {"GT", "GTE", "LT", "LTE"}:
            op_map = {"GT": ">", "GTE": ">=", "LT": "<", "LTE": "<="}
            return f"{column} {op_map[operator]} %s", params + [value]
        if operator in {"IN", "NOT_IN"}:
            if not isinstance(value, list):
                raise ValueError("IN/NOT_IN은 리스트 값이 필요합니다.")
            placeholders = ", ".join(["%s"] * len(value))
            op = "IN" if operator == "IN" else "NOT IN"
            return f"{column} {op} ({placeholders})", params + value
        if operator == "CONTAINS":
            return f"{column} ILIKE %s", params + [f"%{value}%"]
        raise NotImplementedError("지원하지 않는 연산자입니다.")
