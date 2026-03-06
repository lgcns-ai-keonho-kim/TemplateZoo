# Keyspace 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/db/engines/redis/keyspace.py`

## 역할

- 목적: Redis 키스페이스 유틸 모듈을 제공한다.
- 설명: 키 생성 규칙과 SCAN 기반 키 수집을 담당한다.
- 디자인 패턴: 유틸리티 클래스

## 주요 구성

- 클래스: `RedisKeyspaceHelper`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 연관 코드

- `src/plan_and_then_execute_agent/integrations/db/engines/redis/engine.py`
