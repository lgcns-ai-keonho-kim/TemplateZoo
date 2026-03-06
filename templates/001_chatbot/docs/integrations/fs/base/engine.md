# `fs/base/engine.py` 레퍼런스

## 1. 모듈 목적

- 목적: 파일 시스템 엔진 인터페이스를 제공한다.
- 설명: 파일 쓰기/읽기/목록/이동/복사를 위한 표준 메서드를 정의한다.
- 디자인 패턴: 전략 패턴

## 2. 핵심 심볼

- `class BaseFSEngine`

## 3. 입력/출력 관점

- 파일 시스템 엔진 인터페이스를 정의한다.
- 소스 경로: `src/chatbot/integrations/fs/base/engine.py`
- 문서 경로: `docs/integrations/fs/base/engine.md`

## 4. 실패 경로

- 이 파일에서 명시적으로 선언한 `ExceptionDetail.code` 문자열은 없다.

## 5. 연계 모듈

- `src/chatbot/integrations/fs/engines/local.py`

## 6. 변경 영향 범위

- 인터페이스 변경 시 LocalFSEngine과 FileLogRepository 주입 경로를 함께 수정해야 한다.
- 변경 후에는 `docs/integrations/overview.md` 및 해당 하위 `overview.md`와 동기화한다.
