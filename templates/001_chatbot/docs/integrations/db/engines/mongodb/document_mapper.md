# `db/engines/mongodb/document_mapper.py` 레퍼런스

## 1. 모듈 목적

- 목적: MongoDB 문서 매퍼 모듈을 제공한다.
- 설명: Document 모델과 MongoDB 레코드 간 변환을 담당한다.
- 디자인 패턴: 매퍼 패턴

## 2. 핵심 심볼

- `class MongoDocumentMapper`

## 3. 입력/출력 관점

- 엔진 저장 형식과 공통 Document 모델 사이 변환을 담당한다.
- 소스 경로: `src/chatbot/integrations/db/engines/mongodb/document_mapper.py`
- 문서 경로: `docs/integrations/db/engines/mongodb/document_mapper.md`

## 4. 실패 경로

- 이 파일에서 명시적으로 선언한 `ExceptionDetail.code` 문자열은 없다.

## 5. 연계 모듈

- `src/chatbot/integrations/db/base/models.py`

## 6. 변경 영향 범위

- 매핑 규칙 변경 시 조회 결과 필드 형식, 직렬화/역직렬화 호환성에 영향을 준다.
- 변경 후에는 `docs/integrations/overview.md` 및 해당 하위 `overview.md`와 동기화한다.
