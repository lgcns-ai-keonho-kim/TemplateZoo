# db/base/session.md

소스 경로: `src/text_to_sql/integrations/db/base/session.py`

## 1. 역할

- DB 세션/트랜잭션 추상화를 제공한다.
- 트랜잭션 제어와 with 문 사용을 위한 인터페이스를 정의한다.
- 내부 구조는 템플릿 메서드, 컨텍스트 매니저 기반이다.

## 2. 주요 구성

### 2-1. 클래스

| 클래스 | 핵심 메서드 |
| --- | --- |
| `BaseSession` | `begin, commit, rollback` |

### 2-2. 함수

- 정의된 최상위 함수가 없다.

## 3. 오류/예외 코드

- 모듈 내부에서 명시적으로 정의한 오류 코드가 없다.

## 4. 관련 코드

- `src/text_to_sql/integrations/db/base/engine.py`
