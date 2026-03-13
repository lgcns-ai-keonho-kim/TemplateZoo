# Session

## 개요

`src/plan_and_then_execute_agent/integrations/db/base/session.py` 구현을 기준으로 현재 동작을 정리한다.

- DB 세션/트랜잭션 추상화를 제공한다.
- 트랜잭션 제어와 with 문 사용을 위한 인터페이스를 정의한다.
- 구현 형태: 템플릿 메서드, 컨텍스트 매니저

## 주요 구성

- 클래스: `BaseSession`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/plan_and_then_execute_agent/integrations/db/base/engine.py`
