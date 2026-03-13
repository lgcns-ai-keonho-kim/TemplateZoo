# `fs/base/engine.py` 레퍼런스

`BaseFSEngine`은 파일 시스템 엔진 인터페이스다.

## 1. 계약

현재 구현체가 제공해야 하는 메서드:

1. `write_text(path, content, encoding)`
2. `read_text(path, encoding)`
3. `list_files(base_dir, recursive=False, suffix=None)`
4. `exists(path)`
5. `mkdir(path, exist_ok=True)`
6. `move(src, dst)`
7. `copy(src, dst)`

또한 `name` 프로퍼티를 제공해야 한다.

## 2. 유지보수 포인트

1. 상위 `FileLogRepository`는 이 최소 계약만 신뢰한다.
2. 구현체마다 경로 의미를 임의로 넓히면 상위 저장소가 깨질 수 있다.
3. 새 엔진을 추가하면 `src/chatbot/integrations/fs/__init__.py` export와 overview 문서도 함께 갱신해야 한다.

## 3. 관련 문서

- `docs/integrations/fs/file_repository.md`
