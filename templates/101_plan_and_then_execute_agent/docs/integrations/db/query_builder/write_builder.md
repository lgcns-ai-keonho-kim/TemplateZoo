# Write Builder 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/db/query_builder/write_builder.py`

## 역할

- 목적: 쓰기 전용 DSL 빌더를 제공한다.
- 설명: 업서트 중심의 간단한 쓰기 호출을 제공한다.
- 디자인 패턴: 파사드

## 주요 구성

- 클래스: `WriteBuilder`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 연관 코드

- `src/plan_and_then_execute_agent/integrations/db/base/engine.py`
