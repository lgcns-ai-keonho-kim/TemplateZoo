"""
목적: Elasticsearch 필터 쿼리 빌더를 제공한다.
설명: 필터 조건을 Elasticsearch DSL로 변환한다.
디자인 패턴: 빌더 패턴
참조: src/rag_chatbot/integrations/db/engines/elasticsearch/engine.py
"""

from __future__ import annotations

from typing import List, Optional

from rag_chatbot.integrations.db.base.models import CollectionSchema, FieldSource


class ElasticFilterBuilder:
    """Elasticsearch 필터 쿼리 빌더."""

    def build(self, filter_expression, schema: CollectionSchema) -> Optional[dict]:
        """필터 표현식을 Elasticsearch DSL로 변환한다."""

        if filter_expression is None or not filter_expression.conditions:
            return None
        must = []
        should = []
        must_not = []
        for condition in filter_expression.conditions:
            positive, negative = self._condition_to_query(condition, schema)
            if positive:
                if filter_expression.logic == "OR":
                    should.append(positive)
                else:
                    must.append(positive)
            if negative:
                must_not.append(negative)
        bool_query: dict = {}
        if must:
            bool_query["must"] = must
        if should:
            bool_query["should"] = should
            bool_query["minimum_should_match"] = 1
        if must_not:
            bool_query["must_not"] = must_not
        return {"bool": bool_query} if bool_query else None

    def _condition_to_query(self, condition, schema: CollectionSchema) -> tuple[Optional[dict], Optional[dict]]:
        source = schema.resolve_source(condition.field, condition.source)
        if source == FieldSource.PAYLOAD:
            if not schema.payload_field:
                raise RuntimeError("payload 필드가 정의되어 있지 않습니다.")
            field = f"{schema.payload_field}.{condition.field}"
        else:
            field = condition.field
        operator = condition.operator.value
        value = condition.value
        if operator == "EQ":
            if isinstance(value, str):
                return self._string_term_query(field, value), None
            return {"term": {field: value}}, None
        if operator == "NE":
            if isinstance(value, str):
                return None, self._string_term_query(field, value)
            return None, {"term": {field: value}}
        if operator in {"GT", "GTE", "LT", "LTE"}:
            op_map = {"GT": "gt", "GTE": "gte", "LT": "lt", "LTE": "lte"}
            return {"range": {field: {op_map[operator]: value}}}, None
        if operator == "IN":
            if not isinstance(value, list):
                raise ValueError("IN은 리스트 값이 필요합니다.")
            if all(isinstance(item, str) for item in value):
                return self._string_terms_query(field, value), None
            return {"terms": {field: value}}, None
        if operator == "NOT_IN":
            if not isinstance(value, list):
                raise ValueError("NOT_IN은 리스트 값이 필요합니다.")
            if all(isinstance(item, str) for item in value):
                return None, self._string_terms_query(field, value)
            return None, {"terms": {field: value}}
        if operator == "CONTAINS":
            return {"wildcard": {field: f"*{value}*"}}, None
        raise NotImplementedError("지원하지 않는 연산자입니다.")

    def _string_term_query(self, field: str, value: str) -> dict:
        return {
            "bool": {
                "should": [
                    {"term": {field: value}},
                    {"term": {f"{field}.keyword": value}},
                ],
                "minimum_should_match": 1,
            }
        }

    def _string_terms_query(self, field: str, values: List[str]) -> dict:
        return {
            "bool": {
                "should": [
                    {"terms": {field: values}},
                    {"terms": {f"{field}.keyword": values}},
                ],
                "minimum_should_match": 1,
            }
        }
