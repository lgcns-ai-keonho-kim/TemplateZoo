# `db/client.py` 레퍼런스

## 1. 모듈 목적

- 목적: 공통 DB 클라이언트를 제공한다.
- 설명: 엔진을 주입받아 CRUD 중심의 단순한 호출을 제공한다.
- 디자인 패턴: 파사드

## 2. 핵심 심볼

- `class DBClient`

## 3. 입력/출력 관점

- DBClient 퍼사드가 엔진 연결, 스키마, CRUD, 벡터 검색 호출을 통합한다.
- 소스 경로: `src/chatbot/integrations/db/client.py`
- 문서 경로: `docs/integrations/db/client.md`

## 4. 실패 경로

- 이 파일에서 명시적으로 선언한 `ExceptionDetail.code` 문자열은 없다.

## 5. 연계 모듈

- `src/chatbot/integrations/db/base/engine.py`
- `src/chatbot/integrations/db/base/query_builder.py`

## 6. 변경 영향 범위

- 퍼사드 메서드 변경 시 shared 저장소와 runtime 조립 지점의 호출 방식이 영향을 받는다.
- 변경 후에는 `docs/integrations/overview.md` 및 해당 하위 `overview.md`와 동기화한다.
