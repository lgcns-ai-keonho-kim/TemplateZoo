# db/engines/postgres/vector_adapter.md

소스 경로: `src/text_to_sql/integrations/db/engines/postgres/vector_adapter.py`

## 1. 역할

- PGVector 타입 어댑터를 제공한다.
- pgvector 타입 등록, 파라미터 생성, 결과 파싱을 통합한다.
- 내부 구조는 어댑터 패턴 기반이다.

## 2. 주요 구성

### 2-1. 클래스

| 클래스 | 핵심 메서드 |
| --- | --- |
| `PostgresVectorAdapter` | `__init__, enabled, register, param, distance_expr, parse` |

### 2-2. 함수

- 정의된 최상위 함수가 없다.

## 3. 오류/예외 코드

- 모듈 내부에서 명시적으로 정의한 오류 코드가 없다.

## 4. 관련 코드

- `src/text_to_sql/integrations/db/engines/postgres/engine.py`
