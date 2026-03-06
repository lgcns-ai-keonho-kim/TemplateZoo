# Schema Adapter 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/db/engines/lancedb/schema_adapter.py`

## 역할

- 목적: LanceDB 스키마/행 변환 어댑터를 제공한다.
- 설명: CollectionSchema를 PyArrow 스키마로 변환하고, 입력 row를 스키마 타입으로 정규화한다.
- 디자인 패턴: 어댑터 패턴

## 주요 구성

- 클래스: `LanceSchemaAdapter`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 연관 코드

- `src/plan_and_then_execute_agent/integrations/db/base/models.py`
