# Models Vector Search

## 개요

`src/single_request_tool_agent/integrations/db/base/_models_vector_search.py` 구현을 기준으로 현재 동작을 정리한다.

- DB 벡터 검색 모델 공개 API 파사드를 제공한다.
- 벡터 검색 요청/결과/응답/호환 별칭 분리 구현을 재노출한다.
- 구현 형태: 퍼사드

## 주요 구성

- 클래스: 없음
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/single_request_tool_agent/integrations/db/base/_vector_search_request.py`
- `src/single_request_tool_agent/integrations/db/base/_collection_info.py`
