# Collection Schema 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/db/base/_collection_schema.py`

## 역할

- 목적: DB 컬렉션 스키마 모델을 제공한다.
- 설명: 컬럼/페이로드/벡터 정책과 입력 검증 로직을 포함한 스키마 DTO를 정의한다.
- 디자인 패턴: 데이터 전송 객체(DTO)

## 주요 구성

- 클래스: `CollectionSchema`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 연관 코드

- `src/plan_and_then_execute_agent/integrations/db/base/models.py`
