"""
목적: MongoDB 스키마 관리 모듈을 제공한다.
설명: 컬렉션 생성/삭제 및 필드 제거 동작을 담당한다.
디자인 패턴: 매니저 패턴
참조: src/rag_chatbot/integrations/db/engines/mongodb/engine.py
"""

from __future__ import annotations

from rag_chatbot.integrations.db.base.models import CollectionSchema, ColumnSpec


class MongoSchemaManager:
    """MongoDB 스키마 관리자."""

    def create_collection(self, database, schema: CollectionSchema) -> None:
        """컬렉션을 생성한다."""

        if schema.name in database.list_collection_names():
            return
        database.create_collection(schema.name)

    def delete_collection(self, database, name: str) -> None:
        """컬렉션을 삭제한다."""

        database.drop_collection(name)

    def add_column(self, schema: CollectionSchema, column: ColumnSpec) -> None:
        """컬럼 추가 시 사전 검증을 수행한다."""

        if column.is_vector or column.name == schema.vector_field:
            raise RuntimeError("MongoDB 벡터 필드는 별도 설계가 필요합니다.")

    def drop_column(
        self,
        database,
        collection: str,
        schema: CollectionSchema,
        column_name: str,
    ) -> None:
        """컬럼 값을 컬렉션 전체에서 제거한다."""

        coll = database[collection]
        if schema.payload_field:
            field = f"{schema.payload_field}.{column_name}"
        else:
            field = column_name
        coll.update_many({}, {"$unset": {field: ""}})
