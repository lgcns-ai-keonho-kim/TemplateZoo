# 파일 시스템 로그 저장

## 관련 코드

- 포트: `src/rag_chatbot/integrations/fs/base/engine.py`
- 기본 구현: `src/rag_chatbot/integrations/fs/engines/local.py`
- 저장소: `src/rag_chatbot/integrations/fs/file_repository.py`

## 현재 사용 방식

- 기본 애플리케이션 런타임에 자동 조립되지는 않는다.
- 필요하면 `FileLogRepository(base_dir=...)`를 별도로 생성해 logger 또는 로그 저장소 경로에 주입한다.

## 주의

- 파일 포맷을 바꾸면 기존 로그 재조회 경로와 손상 로그 복구 동작을 함께 확인해야 한다.
