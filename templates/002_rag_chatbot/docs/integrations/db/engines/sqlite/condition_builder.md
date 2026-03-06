# condition_builder 모듈

이 문서는 `src/rag_chatbot/integrations/db/engines/sqlite/condition_builder.py`의 역할과 주요 구성을 설명한다.

## 1. 목적

SQLite 조건 빌더 모듈을 제공한다.

## 2. 설명

필터 모델을 SQLite WHERE 절로 변환하고 메모리 필터 평가를 수행한다.

## 3. 디자인 패턴

빌더 패턴

## 4. 주요 구성

- 클래스 `SqliteConditionBuilder`
  주요 메서드: `build`, `match_filter`

## 5. 연동 포인트

- `src/rag_chatbot/integrations/db/base/models.py`

## 6. 관련 문서

- `docs/integrations/db/README.md`
- `docs/integrations/overview.md`
