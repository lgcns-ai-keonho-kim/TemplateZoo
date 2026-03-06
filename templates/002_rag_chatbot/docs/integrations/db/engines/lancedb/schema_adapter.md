# schema_adapter 모듈

이 문서는 `src/rag_chatbot/integrations/db/engines/lancedb/schema_adapter.py`의 역할과 주요 구성을 설명한다.

## 1. 목적

LanceDB 스키마/행 변환 어댑터를 제공한다.

## 2. 설명

CollectionSchema를 PyArrow 스키마로 변환하고, 입력 row를 스키마 타입으로 정규화한다.

## 3. 디자인 패턴

어댑터 패턴

## 4. 주요 구성

- 클래스 `LanceSchemaAdapter`
  주요 메서드: `build_arrow_schema`, `build_arrow_field`, `normalize_row`

## 5. 연동 포인트

- `src/rag_chatbot/integrations/db/base/models.py`

## 6. 관련 문서

- `docs/integrations/db/README.md`
- `docs/integrations/overview.md`
