# 파일 시스템 연동 레퍼런스

이 문서는 파일 시스템 기반 로그 저장소를 현재 코드에 연결하는 방법과 유지보수 포인트를 정리한다.
현재 기본 채팅 런타임은 파일 로그 저장소를 자동으로 주입하지 않는다.

## 1. 현재 코드 기준 구조

1. `BaseFSEngine`이 파일 엔진 최소 계약을 정의한다.
2. `LocalFSEngine`이 로컬 디스크 구현체를 제공한다.
3. `FileLogRepository`가 `LogRepository` 계약을 구현해 로그를 파일로 저장한다.

## 2. 예시 연결 방식

```python
from chatbot.integrations.fs import FileLogRepository
from chatbot.shared.logging import InMemoryLogger

repository = FileLogRepository(base_dir="data/logs")
logger = InMemoryLogger(name="chatbot", repository=repository)
logger.info("서비스 시작")
```

## 3. 유지보수 포인트

1. 저장 포맷은 JSON 문자열 단건 파일이며, 손상 파일 fallback 정책이 조회 실패를 막는다.
2. 파일명 규칙(`<base_dir>/<YYYYMMDD>/<uuid>.log`)을 바꾸면 운영 수집 도구와 조사 절차가 함께 영향을 받는다.
3. 기본 런타임 비활성 기능이므로 실제 사용 여부를 문서에서 분리해 적어야 한다.

## 4. 추가 개발과 확장 시 주의점

1. 원격 스토리지로 확장할 때는 `BaseFSEngine` 구현체 추가와 export 갱신으로 끝내고, `FileLogRepository` 책임은 그대로 두는 편이 안전하다.
2. 압축/보관 정책이 필요하면 저장 시점이 아니라 후처리 파이프라인으로 분리하는 편이 유지보수에 유리하다.

## 5. 관련 문서

- `docs/integrations/fs/overview.md`
- `docs/integrations/fs/file_repository.md`
- `docs/setup/troubleshooting.md`
