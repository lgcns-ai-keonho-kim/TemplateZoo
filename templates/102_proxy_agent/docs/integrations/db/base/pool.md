# Pool

## 개요

`src/tool_proxy_agent/integrations/db/base/pool.py` 구현을 기준으로 현재 동작을 정리한다.

- DB 커넥션 풀 추상화를 제공한다.
- 커넥션 획득/반환 및 with 문 사용을 위한 인터페이스를 정의한다.
- 구현 형태: 오브젝트 풀

## 주요 구성

- 클래스: `BaseConnectionPool`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/tool_proxy_agent/integrations/db/base/session.py`
