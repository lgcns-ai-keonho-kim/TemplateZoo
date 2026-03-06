# session 모듈

이 문서는 `src/rag_chatbot/integrations/db/base/session.py`의 역할과 주요 구성을 설명한다.

## 1. 목적

DB 세션/트랜잭션 추상화를 제공한다.

## 2. 설명

트랜잭션 제어와 with 문 사용을 위한 인터페이스를 정의한다.

## 3. 디자인 패턴

템플릿 메서드, 컨텍스트 매니저

## 4. 주요 구성

- 클래스 `BaseSession`
  주요 메서드: `begin`, `commit`, `rollback`

## 5. 연동 포인트

- `src/rag_chatbot/integrations/db/base/engine.py`

## 6. 관련 문서

- `docs/integrations/db/README.md`
- `docs/integrations/overview.md`
