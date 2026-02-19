"""
목적: Redis 필터 평가기를 제공한다.
설명: 쿼리 필터 조건을 문서에 적용해 일치 여부를 반환한다.
디자인 패턴: 전략 패턴
참조: src/chatbot/integrations/db/engines/redis/engine.py
"""

from __future__ import annotations

from chatbot.integrations.db.base.models import CollectionSchema, FieldSource, Query


class RedisFilterEvaluator:
    """Redis 필터 평가기."""

    def match(self, document, query: Query, schema: CollectionSchema) -> bool:
        """문서가 필터 조건을 만족하는지 판단한다."""

        if not query.filter_expression or not query.filter_expression.conditions:
            return True
        logic = query.filter_expression.logic
        results = [
            self._evaluate_condition(document, condition, schema)
            for condition in query.filter_expression.conditions
        ]
        if logic == "OR":
            return any(results)
        return all(results)

    def _evaluate_condition(self, document, condition, schema: CollectionSchema) -> bool:
        source = schema.resolve_source(condition.field, condition.source)
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
            return self._contains(value, target)
        raise NotImplementedError("지원하지 않는 연산자입니다.")

    def _compare(self, left, right, func) -> bool:
        if left is None:
            return False
        try:
            return func(left, right)
        except TypeError:
            return False

    def _contains(self, value, target) -> bool:
        if value is None:
            return False
        if isinstance(value, list):
            return target in value
        if isinstance(value, str):
            return str(target) in value
        return False
