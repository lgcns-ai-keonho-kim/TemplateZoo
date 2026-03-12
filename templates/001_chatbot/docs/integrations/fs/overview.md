# Integrations FS 모듈 레퍼런스

`src/chatbot/integrations/fs`는 파일 시스템을 로그 저장소 같은 보조 연동 경로로 사용할 때 필요한 최소 계약과 구현을 제공한다.

## 1. 현재 기본 런타임

1. 기본 채팅 런타임은 파일 저장소를 자동으로 조립하지 않는다.
2. `FileLogRepository`는 필요할 때 `Logger` 또는 `LLMClient`에 선택 주입하는 확장 경로다.
3. 현재 기본 구현체는 `LocalFSEngine` 하나다.

## 2. 코드 설명

1. `BaseFSEngine`은 쓰기/읽기/목록/존재 확인/디렉터리 생성/이동/복사 계약을 정의한다.
2. `LocalFSEngine`은 표준 라이브러리 기반 구현체로 로컬 디스크를 직접 다룬다.
3. `FileLogRepository`는 날짜 디렉터리와 UUID 파일명을 사용해 로그를 JSON 문자열로 저장한다.

## 3. 유지보수 포인트

1. 파일 포맷을 바꾸면 기존 로그 파서와 장애 조사 절차가 영향을 받으므로 쉽게 바꾸지 않는 편이 안전하다.
2. 손상 로그 fallback 정책은 조회 실패를 줄이는 장치이므로 유지해야 한다.
3. 기본 런타임 비활성 기능이라는 점을 문서에 명확히 남겨야 혼동이 줄어든다.

## 4. 추가 개발과 확장 시 주의점

1. S3 같은 원격 스토리지를 붙일 때는 `BaseFSEngine` 구현체로 추가하고 `FileLogRepository` 책임은 그대로 유지하는 편이 좋다.
2. 보관 정책이나 압축 기능이 필요하면 저장 포맷을 바꾸기보다 별도 후처리 계층을 두는 편이 안전하다.

## 5. 상세 문서

- `docs/integrations/fs/base/engine.md`
- `docs/integrations/fs/engines/local.md`
- `docs/integrations/fs/file_repository.md`
- `docs/setup/filesystem.md`
