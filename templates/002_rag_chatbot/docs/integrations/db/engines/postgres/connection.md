# PostgresConnectionManager 가이드

이 문서는 `src/rag_chatbot/integrations/db/engines/postgres/connection.py`의 현재 구현을 기준으로 역할과 유지보수 포인트를 정리한다.

## 1. 역할

해당 백엔드의 연결 생성, 재사용, 종료 정책을 담당한다.

## 2. 공개 구성

- 클래스 `PostgresConnectionManager`
  공개 메서드: `connect`, `close`, `ensure_connection`

## 3. 코드 설명

- 현재 구현은 소스 파일의 공개 메서드와 인접 모듈 협업을 기준으로 읽는 것이 가장 안전하다.

## 4. 유지보수/추가개발 포인트

- 이 모듈은 같은 엔진 폴더의 `engine.py`와 짝을 이루므로, 내부 표현을 바꾸면 호출자와 반환 형식을 함께 점검해야 한다.
- 스키마 변경이나 필드명 변경이 생기면 mapper, schema manager, filter 계층을 동시에 확인해야 한다.

## 5. 관련 문서

- `docs/integrations/overview.md`
- `docs/integrations/db/README.md`
