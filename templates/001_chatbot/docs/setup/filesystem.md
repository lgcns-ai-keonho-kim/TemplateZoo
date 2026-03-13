# 파일 시스템 연동 레퍼런스

이 문서는 파일 시스템 기반 로그 저장소를 현재 코드에 연결하는 방법을 정리한다.

현재 기본 채팅 런타임은 파일 로그 저장소를 자동으로 주입하지 않는다.

## 1. 현재 구조

1. `BaseFSEngine`이 파일 엔진 최소 계약을 정의한다.
2. `LocalFSEngine`이 로컬 디스크 구현체를 제공한다.
3. `FileLogRepository`가 `LogRepository` 계약을 구현해 로그를 파일로 저장한다.

## 2. 예시 연결

```python
from chatbot.integrations.fs import FileLogRepository
from chatbot.shared.logging import InMemoryLogger

repository = FileLogRepository(base_dir="data/logs")
logger = InMemoryLogger(name="chatbot", repository=repository)
logger.info("서비스 시작")
```

## 3. 유지보수 포인트

1. 저장 포맷은 JSON 문자열 단건 파일이다.
2. 파일명 규칙은 `<base_dir>/<YYYYMMDD>/<uuid>.log` 형식이다.
3. 손상 파일은 fallback 로그 레코드로 바꿔 전체 조회 실패를 막는다.
4. 기본 런타임 비활성 기능이라는 점을 문서에 명확히 남겨야 한다.

## 4. 관련 문서

- `docs/integrations/fs/overview.md`
- `docs/integrations/fs/file_repository.md`
