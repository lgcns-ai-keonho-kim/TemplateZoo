# 파일 시스템 설정 가이드

이 문서는 파일 기반 로그 저장을 사용할 때 현재 어떤 조합이 필요한지 설명한다.

## 1. 현재 구성

- 포트: `src/rag_chatbot/integrations/fs/base/engine.py`
- 기본 구현: `src/rag_chatbot/integrations/fs/engines/local.py`
- 저장소: `src/rag_chatbot/integrations/fs/file_repository.py`

## 2. 현재 사용 방식

- 기본 애플리케이션 runtime에 자동 조립되지는 않는다.
- `FileLogRepository(base_dir=...)`를 별도로 만들고 logger나 로깅 저장소 경로에 주입해야 한다.

## 3. 유지보수/추가개발 포인트

- 파일 포맷을 바꾸면 기존 로그를 다시 읽는 경로와 손상 로그 fallback 정책을 같이 점검해야 한다.
- 디렉터리 보관 기간, 접근 권한, 아카이빙 정책은 코드 바깥 운영 규칙으로 따로 두는 편이 좋다.

## 4. 관련 문서

- `docs/integrations/fs/README.md`
- `docs/integrations/fs/file_repository.md`
- `docs/shared/logging.md`
