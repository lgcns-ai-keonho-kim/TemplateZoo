# Filter Engine 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/db/engines/lancedb/filter_engine.py`

## 역할

- 목적: LanceDB 필터/정렬 보조 엔진을 제공한다.
- 설명: FilterExpression의 where 절 변환, 메모리 필터 평가, 정렬/점수 변환을 담당한다.
- 디자인 패턴: 정책 객체 패턴

## 주요 구성

- 클래스: `LanceFilterEngine`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 연관 코드

- `src/plan_and_then_execute_agent/integrations/db/base/models.py`
