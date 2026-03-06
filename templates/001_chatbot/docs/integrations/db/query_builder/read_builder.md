# `db/query_builder/read_builder.py` 레퍼런스

## 1. 모듈 목적

- 목적: 읽기 전용 DSL 빌더를 제공한다.
- 설명: QueryBuilder를 감싸 체이닝 후 fetch()로 조회한다.
- 디자인 패턴: 빌더 패턴

## 2. 핵심 심볼

- `class ReadBuilder`

## 3. 입력/출력 관점

- read/write/delete 전용 빌더가 Query/조건 구성 API를 제공한다.
- 소스 경로: `src/chatbot/integrations/db/query_builder/read_builder.py`
- 문서 경로: `docs/integrations/db/query_builder/read_builder.md`

## 4. 실패 경로

- 이 파일에서 명시적으로 선언한 `ExceptionDetail.code` 문자열은 없다.

## 5. 연계 모듈

- `src/chatbot/integrations/db/base/query_builder.py`

## 6. 변경 영향 범위

- 빌더 반환 형태 변경 시 DBClient 체이닝과 상위 저장소 호출 패턴이 깨질 수 있다.
- 변경 후에는 `docs/integrations/overview.md` 및 해당 하위 `overview.md`와 동기화한다.
