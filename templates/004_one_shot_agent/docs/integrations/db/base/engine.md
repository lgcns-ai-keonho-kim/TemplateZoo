# Engine

## 개요

`src/one_shot_agent/integrations/db/base/engine.py` 구현을 기준으로 현재 동작을 정리한다.

- DB 엔진 추상 인터페이스를 정의한다.
- 컬렉션 관리, 문서 CRUD, 벡터 검색을 위한 표준 메서드를 제공한다.
- 구현 형태: 전략 패턴

## 주요 구성

- 클래스: `BaseDBEngine`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/one_shot_agent/integrations/db/base/models.py`
