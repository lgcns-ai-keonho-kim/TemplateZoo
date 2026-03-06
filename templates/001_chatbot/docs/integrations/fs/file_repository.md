# `fs/file_repository.py` 레퍼런스

## 1. 모듈 목적

- 목적: 파일 기반 로그 저장소를 제공한다.
- 설명: 파일 시스템 엔진을 통해 날짜-UUID.log 파일로 로그를 저장한다.
- 디자인 패턴: 저장소 패턴

## 2. 핵심 심볼

- `class FileLogRepository`

## 3. 입력/출력 관점

- 로그 레코드를 파일로 저장·조회하고 손상 레코드 fallback 처리까지 수행한다.
- 소스 경로: `src/chatbot/integrations/fs/file_repository.py`
- 문서 경로: `docs/integrations/fs/file_repository.md`

## 4. 실패 경로

- 이 파일에서 명시적으로 선언한 `ExceptionDetail.code` 문자열은 없다.

## 5. 연계 모듈

- `src/chatbot/integrations/fs/base/engine.py`
- `src/chatbot/integrations/fs/engines/local.py`

## 6. 변경 영향 범위

- 저장 경로/파싱/fallback 정책 변경 시 운영 로그 수집 및 진단 흐름에 영향이 크다.
- 변경 후에는 `docs/integrations/overview.md` 및 해당 하위 `overview.md`와 동기화한다.
