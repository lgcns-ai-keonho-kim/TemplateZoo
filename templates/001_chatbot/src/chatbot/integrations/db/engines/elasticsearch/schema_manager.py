"""
목적: Elasticsearch 스키마 관리 모듈을 제공한다.
설명: 인덱스 생성/삭제와 필드 매핑 추가를 담당한다.
디자인 패턴: 매니저 패턴
참조: src/chatbot/integrations/db/engines/elasticsearch/engine.py
"""

from __future__ import annotations

from chatbot.integrations.db.base.models import CollectionSchema, ColumnSpec


class ElasticSchemaManager:
    """Elasticsearch 스키마 관리자."""

    def create_collection(self, client, schema: CollectionSchema) -> None:
        """인덱스를 생성한다."""

        mappings = {"properties": {}}
        if schema.payload_field:
            mappings["properties"][schema.payload_field] = {"type": "object"}

        for column in schema.columns:
            mappings["properties"][column.name] = self._column_mapping(schema, column)

        if schema.vector_field and schema.vector_field not in mappings["properties"]:
            vector_dim = schema.resolve_vector_dimension()
            if vector_dim is None:
                raise ValueError("벡터 차원 정보가 필요합니다.")
            mappings["properties"][schema.vector_field] = {
                "type": "dense_vector",
                "dims": vector_dim,
                "index": True,
                "similarity": "cosine",
            }

        client.indices.create(index=schema.name, mappings=mappings)

    def delete_collection(self, client, name: str) -> None:
        """인덱스를 삭제한다."""

        client.indices.delete(index=name)

    def add_column(
        self,
        client,
        schema: CollectionSchema,
        column: ColumnSpec,
    ) -> None:
        """필드 매핑을 추가한다."""

        properties: dict = {
            column.name: self._column_mapping(schema, column)
        }
        client.indices.put_mapping(index=schema.name, properties=properties)

    def _column_mapping(self, schema: CollectionSchema, column: ColumnSpec) -> dict:
        """컬럼 스펙을 Elasticsearch mapping으로 변환한다."""

        if column.is_vector or column.name == schema.vector_field:
            vector_dim = column.dimension or schema.resolve_vector_dimension()
            if vector_dim is None:
                raise ValueError("벡터 차원 정보가 필요합니다.")
            return {
                "type": "dense_vector",
                "dims": vector_dim,
                "index": True,
                "similarity": "cosine",
            }
        if schema.payload_field and column.name == schema.payload_field:
            return {"type": "object"}
        if column.data_type:
            return {"type": column.data_type}
        return {"type": "keyword"}
