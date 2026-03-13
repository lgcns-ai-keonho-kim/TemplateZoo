# Engine

## 개요

`src/plan_and_then_execute_agent/integrations/db/engines/mongodb/engine.py` 구현을 기준으로 현재 동작을 정리한다.

- MongoDB 기반 DB 엔진을 제공한다.
- 스키마 기반 필드 매핑과 기본 CRUD를 지원한다.
- 구현 형태: 어댑터 패턴

## 주요 구성

- 클래스: `MongoDBEngine`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/plan_and_then_execute_agent/integrations/db/base/engine.py`
