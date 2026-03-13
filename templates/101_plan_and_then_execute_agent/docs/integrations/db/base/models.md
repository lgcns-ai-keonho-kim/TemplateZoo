# Models

## 개요

`src/plan_and_then_execute_agent/integrations/db/base/models.py` 구현을 기준으로 현재 동작을 정리한다.

- DB 공통 모델 공개 API 파사드를 제공한다.
- 분리된 모델 구현 파일을 단일 진입점으로 재노출한다.
- 구현 형태: 퍼사드

## 주요 구성

- 클래스: 없음
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/plan_and_then_execute_agent/integrations/db/base/_models_schema.py`
- `src/plan_and_then_execute_agent/integrations/db/base/_models_document.py`
