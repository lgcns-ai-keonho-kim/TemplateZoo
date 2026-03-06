# file_repository 모듈

이 문서는 `src/rag_chatbot/integrations/fs/file_repository.py`의 역할과 주요 구성을 설명한다.

## 1. 목적

파일 기반 로그 저장소를 제공한다.

## 2. 설명

파일 시스템 엔진을 통해 날짜-UUID.log 파일로 로그를 저장한다.

## 3. 디자인 패턴

저장소 패턴

## 4. 주요 구성

- 클래스 `FileLogRepository`
  주요 메서드: `base_dir`, `add`, `list`

## 5. 연동 포인트

- `src/rag_chatbot/integrations/fs/base/engine.py`
- `src/rag_chatbot/integrations/fs/engines/local.py`

## 6. 관련 문서

- `docs/integrations/fs/README.md`
- `docs/integrations/overview.md`
