# Local 문서

대상 코드: `src/plan_and_then_execute_agent/integrations/fs/engines/local.py`

## 역할

- 목적: 로컬 파일 시스템 엔진을 제공한다.
- 설명: 표준 라이브러리를 사용해 파일 조작을 수행한다.
- 디자인 패턴: 어댑터 패턴

## 주요 구성

- 클래스: `LocalFSEngine`
- 함수: 없음

## 실패 경로

- 코드에서 명시적으로 정의한 `ExceptionDetail.code`가 없습니다.

## 연관 코드

- `src/plan_and_then_execute_agent/integrations/fs/base/engine.py`
