# engine 모듈

이 문서는 `src/rag_chatbot/integrations/fs/base/engine.py`의 역할과 주요 구성을 설명한다.

## 1. 목적

파일 시스템 엔진 인터페이스를 제공한다.

## 2. 설명

파일 쓰기/읽기/목록/이동/복사를 위한 표준 메서드를 정의한다.

## 3. 디자인 패턴

전략 패턴

## 4. 주요 구성

- 클래스 `BaseFSEngine`
  주요 메서드: `name`, `write_text`, `read_text`, `list_files`, `exists`, `mkdir`, `move`, `copy`

## 5. 연동 포인트

- `src/rag_chatbot/integrations/fs/engines/local.py`

## 6. 관련 문서

- `docs/integrations/fs/README.md`
- `docs/integrations/overview.md`
