# `db/engines/postgres/vector_adapter.py` 레퍼런스

## 1. 모듈 목적

- 목적: PGVector 타입 어댑터를 제공한다.
- 설명: pgvector 타입 등록, 파라미터 생성, 결과 파싱을 통합한다.
- 디자인 패턴: 어댑터 패턴

## 2. 핵심 심볼

- `class PostgresVectorAdapter`

## 3. 입력/출력 관점

- 벡터 필드 저장/인덱싱/유사도 계산 보조 로직을 담당한다.
- 소스 경로: `src/chatbot/integrations/db/engines/postgres/vector_adapter.py`
- 문서 경로: `docs/integrations/db/engines/postgres/vector_adapter.md`

## 4. 실패 경로

- 이 파일에서 명시적으로 선언한 `ExceptionDetail.code` 문자열은 없다.

## 5. 연계 모듈

- `src/chatbot/integrations/db/engines/postgres/engine.py`

## 6. 변경 영향 범위

- 벡터 처리 로직 변경 시 검색 품질, 성능, 인덱스 호환성에 영향을 준다.
- 변경 후에는 `docs/integrations/overview.md` 및 해당 하위 `overview.md`와 동기화한다.
