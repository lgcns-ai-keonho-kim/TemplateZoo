"""
목적: SQLite 조건 빌더 모듈을 제공한다.
설명: 필터 모델을 SQLite WHERE 절로 변환하고 메모리 필터 평가를 수행한다.
디자인 패턴: 빌더 패턴
참조: src/rag_chatbot/integrations/db/base/models.py
"""

from __future__ import annotations

from typing import List, Tuple

from rag_chatbot.integrations.db.base.models import (
    CollectionSchema,
    Document,
    FieldSource,
    FilterCondition,
    FilterExpression,
)
from rag_chatbot.integrations.db.engines.sql_common import (
    SQLIdentifierHelper,
    payload_field,
    resolve_source,
)


class SqliteConditionBuilder:
    """SQLite 조건 빌더."""

    def __init__(self, identifier_helper: SQLIdentifierHelper) -> None:
        self._identifier = identifier_helper

    def build(self, condition: FilterCondition, schema: CollectionSchema) -> Tuple[str, List[object]]:
        """필터 조건을 SQLite WHERE 절로 변환한다."""

        field = condition.field
        operator = condition.operator.value
        value = condition.value
        source = resolve_source(condition.source, field, schema)
        if source == FieldSource.PAYLOAD:
            payload = payload_field(schema)
            expr = f"json_extract({self._identifier.quote_identifier(payload)}, ?)"
            field_path = f"$.{field}"
            params: List[object] = [field_path]
            if operator == "EQ":
                return f"{expr} = ?", params + [value]
            if operator == "NE":
                return f"{expr} != ?", params + [value]
            if operator in {"GT", "GTE", "LT", "LTE"}:
                op_map = {"GT": ">", "GTE": ">=", "LT": "<", "LTE": "<="}
                cast_expr = (
                    "CAST(json_extract("
                    f"{self._identifier.quote_identifier(payload)}, ?) AS REAL)"
                    if isinstance(value, (int, float))
                    else expr
                )
                return f"{cast_expr} {op_map[operator]} ?", params + [value]
            if operator in {"IN", "NOT_IN"}:
                if not isinstance(value, list):
                    raise ValueError("IN/NOT_IN은 리스트 값이 필요합니다.")
                placeholders = ", ".join(["?"] * len(value))
                op = "IN" if operator == "IN" else "NOT IN"
                return f"{expr} {op} ({placeholders})", params + value
            if operator == "CONTAINS":
                return f"{expr} LIKE ?", params + [f"%{value}%"]
        column = self._identifier.quote_identifier(field)
        params = []
        if operator == "EQ":
            return f"{column} = ?", params + [value]
        if operator == "NE":
            return f"{column} != ?", params + [value]
        if operator in {"GT", "GTE", "LT", "LTE"}:
            op_map = {"GT": ">", "GTE": ">=", "LT": "<", "LTE": "<="}
            return f"{column} {op_map[operator]} ?", params + [value]
        if operator in {"IN", "NOT_IN"}:
            if not isinstance(value, list):
                raise ValueError("IN/NOT_IN은 리스트 값이 필요합니다.")
            placeholders = ", ".join(["?"] * len(value))
            op = "IN" if operator == "IN" else "NOT IN"
            return f"{column} {op} ({placeholders})", params + value
        if operator == "CONTAINS":
            return f"{column} LIKE ?", params + [f"%{value}%"]
        raise NotImplementedError("지원하지 않는 연산자입니다.")

    def match_filter(
        self,
        document: Document,
        filter_expression: FilterExpression,
        schema: CollectionSchema,
    ) -> bool:
        """문서가 필터를 만족하는지 검사한다."""

        logic = filter_expression.logic
        results = [
            self._evaluate_condition(document, condition, schema)
            for condition in filter_expression.conditions
        ]
        if logic == "OR":
            return any(results)
        return all(results)

    def _evaluate_condition(
        self,
        document: Document,
        condition: FilterCondition,
        schema: CollectionSchema,
    ) -> bool:
        source = resolve_source(condition.source, condition.field, schema)
        if source == FieldSource.PAYLOAD:
            value = document.payload.get(condition.field)
        else:
            value = document.fields.get(condition.field)
        operator = condition.operator.value
        target = condition.value
        if operator == "EQ":
            return value == target
        if operator == "NE":
            return value != target
        if operator == "GT":
            return self._compare(value, target, lambda a, b: a > b)
        if operator == "GTE":
            return self._compare(value, target, lambda a, b: a >= b)
        if operator == "LT":
            return self._compare(value, target, lambda a, b: a < b)
        if operator == "LTE":
            return self._compare(value, target, lambda a, b: a <= b)
        if operator == "IN":
            return value in target if isinstance(target, list) else False
        if operator == "NOT_IN":
            return value not in target if isinstance(target, list) else False
        if operator == "CONTAINS":
            if isinstance(value, list):
                return target in value
            if isinstance(value, str):
                return str(target) in value
            return False
        return False

    def _compare(self, left, right, func) -> bool:
        if left is None:
            return False
        try:
            return func(left, right)
        except TypeError:
            return False
