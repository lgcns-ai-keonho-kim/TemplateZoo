# `fs/file_repository.py` 레퍼런스

`FileLogRepository`는 파일 시스템 엔진을 통해 로그를 파일 단위로 저장하는 저장소다.

## 1. 현재 동작

1. `base_dir` 아래에 날짜 디렉터리(`YYYYMMDD`)를 만든다.
2. 각 로그는 `<uuid>.log` 파일로 저장한다.
3. 저장 내용은 `LogRecord`의 JSON 문자열이다.
4. 엔진을 주입하지 않으면 `LocalFSEngine`을 사용한다.

## 2. 조회 동작

1. `.log` 파일을 재귀적으로 조회한다.
2. 파일을 읽어 `LogRecord`로 역직렬화한다.
3. 손상 파일은 `WARNING` 레벨 fallback 레코드로 대체한다.
4. 반환 순서는 timestamp 오름차순이다.

## 3. 유지보수 포인트

1. 파일명 규칙을 바꾸면 운영 수집 절차가 함께 영향을 받는다.
2. fallback 정책을 제거하면 일부 손상 파일이 전체 조회 실패로 번질 수 있다.
3. 기본 인코딩은 `SharedConst.DEFAULT_ENCODING`이다.

## 4. 관련 문서

- `docs/integrations/fs/base/engine.md`
- `docs/setup/filesystem.md`
