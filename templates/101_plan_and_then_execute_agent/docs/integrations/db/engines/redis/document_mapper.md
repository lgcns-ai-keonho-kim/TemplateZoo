# Document Mapper 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/db/engines/redis/document_mapper.py`

## 역할

- 목적: Redis 문서 매퍼 모듈을 제공한다.
- 설명: Document 모델과 Redis Hash 데이터 간 변환을 담당한다.
- 디자인 패턴: 매퍼 패턴

## 주요 구성

- 클래스: `RedisDocumentMapper`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 연관 코드

- `src/plan_and_then_execute_agent/integrations/db/base/models.py`
