# db/engines/mongodb/filter_builder.md

소스 경로: `src/text_to_sql/integrations/db/engines/mongodb/filter_builder.py`

## 1. 역할

- MongoDB 필터 쿼리 빌더를 제공한다.
- 필터 조건을 MongoDB 쿼리로 변환한다.
- 내부 구조는 빌더 패턴 기반이다.

## 2. 주요 구성

### 2-1. 클래스

| 클래스 | 핵심 메서드 |
| --- | --- |
| `MongoFilterBuilder` | `build` |

### 2-2. 함수

- 정의된 최상위 함수가 없다.

## 3. 오류/예외 코드

- 모듈 내부에서 명시적으로 정의한 오류 코드가 없다.

## 4. 관련 코드

- `src/text_to_sql/integrations/db/engines/mongodb/engine.py`
- `src/text_to_sql/integrations/db/base/models.py`
