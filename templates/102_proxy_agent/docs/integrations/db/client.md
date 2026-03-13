# Client

## 개요

`src/tool_proxy_agent/integrations/db/client.py` 구현을 기준으로 현재 동작을 정리한다.

- 공통 DB 클라이언트를 제공한다.
- 엔진을 주입받아 CRUD 중심의 단순한 호출을 제공한다.
- 구현 형태: 파사드

## 주요 구성

- 클래스: `DBClient`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/tool_proxy_agent/integrations/db/base/engine.py`
- `src/tool_proxy_agent/integrations/db/base/query_builder.py`
