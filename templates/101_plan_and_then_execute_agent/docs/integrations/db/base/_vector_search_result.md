# Vector Search Result 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/db/base/_vector_search_result.py`

## 역할

- 목적: DB 벡터 검색 결과 항목 모델을 제공한다.
- 설명: 검색된 문서와 유사도 점수를 담는 DTO를 정의한다.
- 디자인 패턴: 데이터 전송 객체(DTO)

## 주요 구성

- 클래스: `VectorSearchResult`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 연관 코드

- `src/plan_and_then_execute_agent/integrations/db/base/models.py`
