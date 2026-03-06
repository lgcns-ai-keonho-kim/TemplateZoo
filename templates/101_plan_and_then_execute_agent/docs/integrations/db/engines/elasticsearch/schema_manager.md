# Schema Manager 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/db/engines/elasticsearch/schema_manager.py`

## 역할

- 목적: Elasticsearch 스키마 관리 모듈을 제공한다.
- 설명: 인덱스 생성/삭제와 필드 매핑 추가를 담당한다.
- 디자인 패턴: 매니저 패턴

## 주요 구성

- 클래스: `ElasticSchemaManager`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 연관 코드

- `src/plan_and_then_execute_agent/integrations/db/engines/elasticsearch/engine.py`
