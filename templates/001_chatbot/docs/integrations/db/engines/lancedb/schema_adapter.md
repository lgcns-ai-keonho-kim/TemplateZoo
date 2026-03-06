# `db/engines/lancedb/schema_adapter.py` 레퍼런스

## 1. 모듈 목적

- 목적: LanceDB 스키마/행 변환 어댑터를 제공한다.
- 설명: CollectionSchema를 PyArrow 스키마로 변환하고, 입력 row를 스키마 타입으로 정규화한다.
- 디자인 패턴: 어댑터 패턴

## 2. 핵심 심볼

- `class LanceSchemaAdapter`

## 3. 입력/출력 관점

- 컬렉션/테이블 스키마 생성·변경 로직을 담당한다.
- 소스 경로: `src/chatbot/integrations/db/engines/lancedb/schema_adapter.py`
- 문서 경로: `docs/integrations/db/engines/lancedb/schema_adapter.md`

## 4. 실패 경로

- 이 파일에서 명시적으로 선언한 `ExceptionDetail.code` 문자열은 없다.

## 5. 연계 모듈

- `src/chatbot/integrations/db/base/models.py`

## 6. 변경 영향 범위

- 스키마 처리 정책 변경 시 마이그레이션/초기화 절차와 데이터 호환성에 영향을 준다.
- 변경 후에는 `docs/integrations/overview.md` 및 해당 하위 `overview.md`와 동기화한다.
