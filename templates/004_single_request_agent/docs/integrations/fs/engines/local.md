# Local

## 개요

`src/single_request_agent/integrations/fs/engines/local.py` 구현을 기준으로 현재 동작을 정리한다.

- 로컬 파일 시스템 엔진을 제공한다.
- 표준 라이브러리를 사용해 파일 조작을 수행한다.
- 구현 형태: 어댑터 패턴

## 주요 구성

- 클래스: `LocalFSEngine`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 관련 코드

- `src/single_request_agent/integrations/fs/base/engine.py`
