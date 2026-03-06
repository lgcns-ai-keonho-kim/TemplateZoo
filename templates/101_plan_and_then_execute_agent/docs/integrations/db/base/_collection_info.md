# Collection Info 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/db/base/_collection_info.py`

## 역할

- 목적: DB 컬렉션 정보 호환 모델을 제공한다.
- 설명: 기존 호환을 위해 CollectionSchema 별칭 클래스를 유지한다.
- 디자인 패턴: 별칭 래퍼

## 주요 구성

- 클래스: `CollectionInfo`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 연관 코드

- `src/plan_and_then_execute_agent/integrations/db/base/models.py`
