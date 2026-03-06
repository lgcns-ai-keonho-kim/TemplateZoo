# Client 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/db/client.py`

## 역할

- 목적: 공통 DB 클라이언트를 제공한다.
- 설명: 엔진을 주입받아 CRUD 중심의 단순한 호출을 제공한다.
- 디자인 패턴: 파사드

## 주요 구성

- 클래스: `DBClient`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 연관 코드

- `src/plan_and_then_execute_agent/integrations/db/base/engine.py`
- `src/plan_and_then_execute_agent/integrations/db/base/query_builder.py`
