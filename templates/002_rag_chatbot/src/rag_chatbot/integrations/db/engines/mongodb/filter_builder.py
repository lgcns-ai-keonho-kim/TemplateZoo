"""
목적: MongoDB 필터 쿼리 빌더를 제공한다.
설명: 필터 조건을 MongoDB 쿼리로 변환한다.
디자인 패턴: 빌더 패턴
참조: src/rag_chatbot/integrations/db/engines/mongodb/engine.py
"""

from __future__ import annotations

from rag_chatbot.integrations.db.base.models import CollectionSchema, FieldSource


class MongoFilterBuilder:
    """MongoDB 필터 빌더."""

    def build(self, filter_expression, schema: CollectionSchema) -> dict:
        """필터 표현식을 MongoDB 쿼리로 변환한다."""

        if not filter_expression or not filter_expression.conditions:
            return {}
        conditions = [
            self._condition_to_query(condition, schema)
            for condition in filter_expression.conditions
        ]
        if filter_expression.logic == "OR":
            return {"$or": conditions}
        return {"$and": conditions}

    def _condition_to_query(self, condition, schema: CollectionSchema) -> dict:
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
            return {field: value}
        if operator == "NE":
            return {field: {"$ne": value}}
        if operator == "GT":
            return {field: {"$gt": value}}
        if operator == "GTE":
            return {field: {"$gte": value}}
        if operator == "LT":
            return {field: {"$lt": value}}
        if operator == "LTE":
            return {field: {"$lte": value}}
        if operator == "IN":
            if not isinstance(value, list):
                raise ValueError("IN은 리스트 값이 필요합니다.")
            return {field: {"$in": value}}
        if operator == "NOT_IN":
            if not isinstance(value, list):
                raise ValueError("NOT_IN은 리스트 값이 필요합니다.")
            return {field: {"$nin": value}}
        if operator == "CONTAINS":
            if isinstance(value, str):
                return {field: {"$regex": value, "$options": "i"}}
            return {field: {"$in": [value]}}
        raise NotImplementedError("지원하지 않는 연산자입니다.")
