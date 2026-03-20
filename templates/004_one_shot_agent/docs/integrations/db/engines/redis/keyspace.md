# Keyspace

## 개요

`src/one_shot_agent/integrations/db/engines/redis/keyspace.py` 구현을 기준으로 현재 동작을 정리한다.

- Redis 키스페이스 유틸 모듈을 제공한다.
- 키 생성 규칙과 SCAN 기반 키 수집을 담당한다.
- 구현 형태: 유틸리티 클래스

## 주요 구성

- 클래스: `RedisKeyspaceHelper`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/one_shot_agent/integrations/db/engines/redis/engine.py`
