# Filter Engine

## 개요

`src/single_request_agent/integrations/db/engines/lancedb/filter_engine.py` 구현을 기준으로 현재 동작을 정리한다.

- LanceDB 필터/정렬 보조 엔진을 제공한다.
- FilterExpression의 where 절 변환, 메모리 필터 평가, 정렬/점수 변환을 담당한다.
- 구현 형태: 정책 객체 패턴

## 주요 구성

- 클래스: `LanceFilterEngine`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/single_request_agent/integrations/db/base/models.py`
