# db/query_builder/write_builder.md

소스 경로: `src/text_to_sql/integrations/db/query_builder/write_builder.py`

## 1. 역할

- 목적: 쓰기 전용 DSL 빌더를 제공한다.
- 설명: 업서트 중심의 간단한 쓰기 호출을 제공한다.
- 디자인 패턴: 파사드

## 2. 주요 구성

### 2-1. 클래스

| 클래스 | 핵심 메서드 |
| --- | --- |
| `WriteBuilder` | `__init__, upsert, upsert_one` |

### 2-2. 함수

- 정의된 최상위 함수가 없다.

## 3. 오류/예외 코드

- 모듈 내부에서 명시적으로 정의한 오류 코드가 없다.

## 4. 연관 모듈

- `src/text_to_sql/integrations/db/base/engine.py`
- `src/text_to_sql/integrations/db/base/models.py`
