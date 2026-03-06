# `db/base/session.py` 레퍼런스

## 1. 모듈 목적

- 목적: DB 세션/트랜잭션 추상화를 제공한다.
- 설명: 트랜잭션 제어와 with 문 사용을 위한 인터페이스를 정의한다.
- 디자인 패턴: 템플릿 메서드, 컨텍스트 매니저

## 2. 핵심 심볼

- `class BaseSession`

## 3. 입력/출력 관점

- 세션 단위 연결 실행 계약을 정의한다.
- 소스 경로: `src/chatbot/integrations/db/base/session.py`
- 문서 경로: `docs/integrations/db/base/session.md`

## 4. 실패 경로

- 이 파일에서 명시적으로 선언한 `ExceptionDetail.code` 문자열은 없다.

## 5. 연계 모듈

- `src/chatbot/integrations/db/base/engine.py`

## 6. 변경 영향 범위

- 세션 인터페이스 변경 시 트랜잭션/쿼리 실행 경로 전체가 영향을 받는다.
- 변경 후에는 `docs/integrations/overview.md` 및 해당 하위 `overview.md`와 동기화한다.
