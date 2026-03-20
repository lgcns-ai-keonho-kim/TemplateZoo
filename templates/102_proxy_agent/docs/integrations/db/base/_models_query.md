# Models Query

## 개요

`src/tool_proxy_agent/integrations/db/base/_models_query.py` 구현을 기준으로 현재 동작을 정리한다.

- DB 조회 모델 공개 API 파사드를 제공한다.
- 정렬/페이지네이션/조회 모델 분리 구현을 재노출한다.
- 구현 형태: 퍼사드

## 주요 구성

- 클래스: 없음
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/tool_proxy_agent/integrations/db/base/_sort_order.py`
- `src/tool_proxy_agent/integrations/db/base/_query.py`
