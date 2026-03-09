# db/base/engine.md

소스 경로: `src/text_to_sql/integrations/db/base/engine.py`

## 1. 역할

- 목적: DB 엔진 추상 인터페이스를 정의한다.
- 설명: 컬렉션 관리, 문서 CRUD, 벡터 검색을 위한 표준 메서드를 제공한다.
- 디자인 패턴: 전략 패턴

## 2. 주요 구성

### 2-1. 클래스

| 클래스 | 핵심 메서드 |
| --- | --- |
| `BaseDBEngine` | `name, supports_vector_search, connect, close, create_collection, delete_collection, add_column, drop_column, ...` |

### 2-2. 함수

- 정의된 최상위 함수가 없다.

## 3. 오류/예외 코드

- 모듈 내부에서 명시적으로 정의한 오류 코드가 없다.

## 4. 연관 모듈

- `src/text_to_sql/integrations/db/base/models.py`
