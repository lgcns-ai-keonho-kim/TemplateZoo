# Engine 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/db/engines/elasticsearch/engine.py`

## 역할

- 목적: Elasticsearch 기반 DB 엔진을 제공한다.
- 설명: 스키마 기반 필드 매핑과 벡터 검색을 지원한다.
- 디자인 패턴: 어댑터 패턴

## 주요 구성

- 클래스: `ElasticsearchEngine`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 연관 코드

- `src/plan_and_then_execute_agent/integrations/db/base/engine.py`
