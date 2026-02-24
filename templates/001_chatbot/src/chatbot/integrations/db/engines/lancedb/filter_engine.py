"""
목적: LanceDB 필터/정렬 보조 엔진을 제공한다.
설명: FilterExpression의 where 절 변환, 메모리 필터 평가, 정렬/점수 변환을 담당한다.
디자인 패턴: 정책 객체 패턴
참조: src/chatbot/integrations/db/base/models.py
"""

from __future__ import annotations

import json
import re
from typing import Any, Optional

from chatbot.integrations.db.base.models import (
    CollectionSchema,
    Document,
    FieldSource,
    FilterCondition,
    FilterExpression,
    Query,
    SortOrder,
)
from chatbot.integrations.db.engines.sql_common import resolve_source

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class LanceFilterEngine:
    """LanceDB 필터/정렬 보조 엔진."""

    def build_where_clause(
        self,
        filter_expression: Optional[FilterExpression],
        schema: CollectionSchema,
    ) -> Optional[str]:
        if not filter_expression or not filter_expression.conditions:
            return None

        clauses: list[str] = []
        for condition in filter_expression.conditions:
            source = resolve_source(condition.source, condition.field, schema)
            if source != FieldSource.COLUMN:
                return None
            clauses.append(self._condition_to_sql(condition))

        joiner = " OR " if filter_expression.logic == "OR" else " AND "
        return f"({joiner.join(clauses)})"

    def build_eq_clause(self, field: str, value: object) -> str:
        return f"{self._validate_identifier(field)} = {self._sql_literal(value)}"

    def distance_to_similarity(self, distance: Any, score: Any) -> float:
        if distance is not None:
            try:
                numeric = max(float(distance), 0.0)
            except (TypeError, ValueError):
                return 0.0
            return 1.0 / (1.0 + numeric)
        if score is None:
            return 0.0
        try:
            return float(score)
        except (TypeError, ValueError):
            return 0.0

    def apply_sort(
        self,
        documents: list[Document],
        query: Query,
        schema: CollectionSchema,
    ) -> list[Document]:
        if not query.sort:
            return documents

        sorted_docs = list(documents)
        for sort_field in reversed(query.sort):
            source = resolve_source(sort_field.source, sort_field.field, schema)
            reverse = sort_field.order == SortOrder.DESC
            sorted_docs.sort(
                key=lambda document: self._sort_key(
                    self._extract_sort_value(document, sort_field.field, source, schema)
                ),
                reverse=reverse,
            )
        return sorted_docs

    def match_filter(
        self,
        document: Document,
        filter_expression: FilterExpression,
        schema: CollectionSchema,
    ) -> bool:
        results = [
            self._evaluate_condition(document, condition, schema)
            for condition in filter_expression.conditions
        ]
        if filter_expression.logic == "OR":
            return any(results)
        return all(results)

    def _condition_to_sql(self, condition: FilterCondition) -> str:
        field = self._validate_identifier(condition.field)
        operator = condition.operator.value
        value = condition.value

        if operator == "EQ":
            return f"{field} = {self._sql_literal(value)}"
        if operator == "NE":
            return f"{field} != {self._sql_literal(value)}"
        if operator == "GT":
            return f"{field} > {self._sql_literal(value)}"
        if operator == "GTE":
            return f"{field} >= {self._sql_literal(value)}"
        if operator == "LT":
            return f"{field} < {self._sql_literal(value)}"
        if operator == "LTE":
            return f"{field} <= {self._sql_literal(value)}"
        if operator in {"IN", "NOT_IN"}:
            if not isinstance(value, list):
                raise ValueError("IN/NOT_IN은 리스트 값이 필요합니다.")
            if not value:
                return "1 = 1" if operator == "NOT_IN" else "1 = 0"
            serialized = ", ".join(self._sql_literal(item) for item in value)
            membership = "NOT IN" if operator == "NOT_IN" else "IN"
            return f"{field} {membership} ({serialized})"
        if operator == "CONTAINS":
            if not isinstance(value, (str, int, float, bool)):
                raise ValueError("CONTAINS는 문자열로 변환 가능한 값만 허용합니다.")
            text = str(value).replace("'", "''")
            return f"{field} LIKE '%{text}%'"
        raise NotImplementedError("지원하지 않는 연산자입니다.")

    def _extract_sort_value(
        self,
        document: Document,
        field: str,
        source: FieldSource,
        schema: CollectionSchema,
    ) -> Any:
        if source == FieldSource.PAYLOAD:
            return document.payload.get(field)
        if field == schema.primary_key:
            return document.doc_id
        if field == schema.vector_field and document.vector is not None:
            return document.vector.values
        return document.fields.get(field)

    def _sort_key(self, value: Any) -> tuple[int, Any]:
        if value is None:
            return (1, "")
        if isinstance(value, (dict, list)):
            return (0, json.dumps(value, ensure_ascii=False))
        return (0, value)

    def _evaluate_condition(
        self,
        document: Document,
        condition: FilterCondition,
        schema: CollectionSchema,
    ) -> bool:
        source = resolve_source(condition.source, condition.field, schema)
        if source == FieldSource.PAYLOAD:
            value = document.payload.get(condition.field)
        elif condition.field == schema.primary_key:
            value = document.doc_id
        elif condition.field == schema.vector_field and document.vector is not None:
            value = document.vector.values
        else:
            value = document.fields.get(condition.field)

        operator = condition.operator.value
        target = condition.value
        if operator == "EQ":
            return value == target
        if operator == "NE":
            return value != target
        if operator == "GT":
            return self._compare(value, target, lambda left, right: left > right)
        if operator == "GTE":
            return self._compare(value, target, lambda left, right: left >= right)
        if operator == "LT":
            return self._compare(value, target, lambda left, right: left < right)
        if operator == "LTE":
            return self._compare(value, target, lambda left, right: left <= right)
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

    def _compare(self, left: Any, right: Any, comparator) -> bool:
        if left is None:
            return False
        try:
            return bool(comparator(left, right))
        except TypeError:
            return False

    def _validate_identifier(self, name: str) -> str:
        if not _IDENTIFIER_RE.match(name):
            raise ValueError(f"허용되지 않는 식별자: {name}")
        return name

    def _sql_literal(self, value: object) -> str:
        if value is None:
            return "NULL"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        text = str(value).replace("'", "''")
        return f"'{text}'"
