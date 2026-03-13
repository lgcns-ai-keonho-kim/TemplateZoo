# Integrations FS 모듈 레퍼런스

`src/chatbot/integrations/fs`는 파일 시스템을 로그 저장 같은 보조 연동 경로로 사용할 때 필요한 계약과 구현을 제공한다.

## 1. 현재 기본 경로

1. 기본 채팅 런타임은 파일 저장소를 자동으로 조립하지 않는다.
2. `FileLogRepository`는 필요할 때 선택 주입하는 확장 경로다.
3. 현재 기본 구현체는 `LocalFSEngine` 하나다.

## 2. 구성 요소

1. `BaseFSEngine`: 파일 시스템 최소 계약
2. `LocalFSEngine`: 로컬 디스크 구현체
3. `FileLogRepository`: 날짜 디렉터리 + UUID 파일명 기반 로그 저장소

## 3. 유지보수 포인트

1. 저장 포맷은 JSON 문자열 단건 파일이다.
2. 손상 파일은 fallback 로그 레코드로 대체해 전체 조회 실패를 막는다.
3. 기본 런타임 비활성 기능이라는 점을 문서에서 명확히 구분해야 한다.

## 4. 관련 문서

- `docs/integrations/fs/base/engine.md`
- `docs/integrations/fs/file_repository.md`
- `docs/setup/filesystem.md`
