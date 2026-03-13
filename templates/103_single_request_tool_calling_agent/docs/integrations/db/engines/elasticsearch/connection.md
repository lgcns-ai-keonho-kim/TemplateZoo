# Connection

## 개요

`src/single_request_tool_agent/integrations/db/engines/elasticsearch/connection.py` 구현을 기준으로 현재 동작을 정리한다.

- Elasticsearch 연결 관리 모듈을 제공한다.
- 클라이언트 생성/종료와 옵션 클라이언트 반환을 담당한다.
- 구현 형태: 매니저 패턴

## 주요 구성

- 클래스: `ElasticConnectionManager`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/single_request_tool_agent/integrations/db/engines/elasticsearch/engine.py`
