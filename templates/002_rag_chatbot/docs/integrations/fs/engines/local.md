# local 모듈

이 문서는 `src/rag_chatbot/integrations/fs/engines/local.py`의 역할과 주요 구성을 설명한다.

## 1. 목적

로컬 파일 시스템 엔진을 제공한다.

## 2. 설명

표준 라이브러리를 사용해 파일 조작을 수행한다.

## 3. 디자인 패턴

어댑터 패턴

## 4. 주요 구성

- 클래스 `LocalFSEngine`
  주요 메서드: `name`, `write_text`, `read_text`, `list_files`, `exists`, `mkdir`, `move`, `copy`

## 5. 연동 포인트

- `src/rag_chatbot/integrations/fs/base/engine.py`

## 6. 관련 문서

- `docs/integrations/fs/README.md`
- `docs/integrations/overview.md`
