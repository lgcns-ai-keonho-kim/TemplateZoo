# `fs/engines/local.py` 레퍼런스

## 1. 모듈 목적

- 목적: 로컬 파일 시스템 엔진을 제공한다.
- 설명: 표준 라이브러리를 사용해 파일 조작을 수행한다.
- 디자인 패턴: 어댑터 패턴

## 2. 핵심 심볼

- `class LocalFSEngine`

## 3. 입력/출력 관점

- 로컬 파일 시스템 기반 파일 읽기/쓰기/목록/이동/복사를 구현한다.
- 소스 경로: `src/chatbot/integrations/fs/engines/local.py`
- 문서 경로: `docs/integrations/fs/engines/local.md`

## 4. 실패 경로

- 이 파일에서 명시적으로 선언한 `ExceptionDetail.code` 문자열은 없다.

## 5. 연계 모듈

- `src/chatbot/integrations/fs/base/engine.py`

## 6. 변경 영향 범위

- 파일 생성/경로 처리 정책 변경 시 로그 저장 경로와 운영 스크립트가 영향을 받는다.
- 변경 후에는 `docs/integrations/overview.md` 및 해당 하위 `overview.md`와 동기화한다.
