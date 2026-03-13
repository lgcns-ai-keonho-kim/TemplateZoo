# MongoDocumentMapper 가이드

이 문서는 `src/rag_chatbot/integrations/db/engines/mongodb/document_mapper.py`의 현재 구현을 기준으로 역할과 유지보수 포인트를 정리한다.

## 1. 역할

공통 Document 모델과 백엔드 저장 포맷 사이의 양방향 변환을 담당한다.

## 2. 공개 구성

- 클래스 `MongoDocumentMapper`
  공개 메서드: `to_update_payload`, `from_record`

## 3. 코드 설명

- 필드명, payload 직렬화, 벡터 필드 표현 차이는 이 레이어에서 해소한다.

## 4. 유지보수/추가개발 포인트

- 이 모듈은 같은 엔진 폴더의 `engine.py`와 짝을 이루므로, 내부 표현을 바꾸면 호출자와 반환 형식을 함께 점검해야 한다.
- 스키마 변경이나 필드명 변경이 생기면 mapper, schema manager, filter 계층을 동시에 확인해야 한다.

## 5. 관련 문서

- `docs/integrations/overview.md`
- `docs/integrations/db/README.md`
