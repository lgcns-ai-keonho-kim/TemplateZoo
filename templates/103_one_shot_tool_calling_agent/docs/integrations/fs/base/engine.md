# Engine

## 개요

`src/one_shot_tool_calling_agent/integrations/fs/base/engine.py` 구현을 기준으로 현재 동작을 정리한다.

- 파일 시스템 엔진 인터페이스를 제공한다.
- 파일 쓰기/읽기/목록/이동/복사를 위한 표준 메서드를 정의한다.
- 구현 형태: 전략 패턴

## 주요 구성

- 클래스: `BaseFSEngine`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/one_shot_tool_calling_agent/integrations/fs/engines/local.py`
