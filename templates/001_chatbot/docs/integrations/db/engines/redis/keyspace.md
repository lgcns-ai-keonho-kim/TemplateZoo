# `db/engines/redis/keyspace.py` 레퍼런스

## 1. 모듈 목적

- 목적: Redis 키스페이스 유틸 모듈을 제공한다.
- 설명: 키 생성 규칙과 SCAN 기반 키 수집을 담당한다.
- 디자인 패턴: 유틸리티 클래스

## 2. 핵심 심볼

- `class RedisKeyspaceHelper`

## 3. 입력/출력 관점

- Redis 키 네이밍/스코프 규칙을 관리한다.
- 소스 경로: `src/chatbot/integrations/db/engines/redis/keyspace.py`
- 문서 경로: `docs/integrations/db/engines/redis/keyspace.md`

## 4. 실패 경로

- 이 파일에서 명시적으로 선언한 `ExceptionDetail.code` 문자열은 없다.

## 5. 연계 모듈

- `src/chatbot/integrations/db/engines/redis/engine.py`

## 6. 변경 영향 범위

- 키스페이스 규칙 변경 시 기존 데이터 조회 경로와 정리 작업이 영향을 받는다.
- 변경 후에는 `docs/integrations/overview.md` 및 해당 하위 `overview.md`와 동기화한다.
