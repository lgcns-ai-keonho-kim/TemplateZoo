# `db/base/pool.py` 레퍼런스

## 1. 모듈 목적

- 목적: DB 커넥션 풀 추상화를 제공한다.
- 설명: 커넥션 획득/반환 및 with 문 사용을 위한 인터페이스를 정의한다.
- 디자인 패턴: 오브젝트 풀

## 2. 핵심 심볼

- `class BaseConnectionPool`

## 3. 입력/출력 관점

- 연결 풀 추상 인터페이스를 제공해 엔진별 연결 재사용 정책을 분리한다.
- 소스 경로: `src/chatbot/integrations/db/base/pool.py`
- 문서 경로: `docs/integrations/db/base/pool.md`

## 4. 실패 경로

- 이 파일에서 명시적으로 선언한 `ExceptionDetail.code` 문자열은 없다.

## 5. 연계 모듈

- `src/chatbot/integrations/db/base/session.py`

## 6. 변경 영향 범위

- 풀 계약 변경 시 connection manager 구현체와 자원 해제 흐름을 함께 조정해야 한다.
- 변경 후에는 `docs/integrations/overview.md` 및 해당 하위 `overview.md`와 동기화한다.
