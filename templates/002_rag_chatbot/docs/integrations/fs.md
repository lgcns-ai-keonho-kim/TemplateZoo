# Integrations FS 가이드

이 문서는 `src/rag_chatbot/integrations/fs`의 파일 시스템 추상화와 파일 로그 저장소 동작을 코드 기준으로 정리한다.

## 1. 용어 정리

| 용어 | 의미 | 관련 스크립트 |
| --- | --- | --- |
| BaseFSEngine | 파일 시스템 엔진 인터페이스 | `base/engine.py` |
| LocalFSEngine | 로컬 디스크 기반 구현체 | `engines/local.py` |
| FileLogRepository | 로그를 파일로 저장/조회하는 저장소 | `file_repository.py` |
| fallback 레코드 | 손상된 로그 파일을 대체해 반환하는 경고 로그 | `FileLogRepository._fallback_record` |

## 2. 관련 스크립트

| 파일 | 역할 |
| --- | --- |
| `src/rag_chatbot/integrations/fs/base/engine.py` | 파일 엔진 표준 메서드 정의 |
| `src/rag_chatbot/integrations/fs/engines/local.py` | 로컬 파일 시스템 구현 |
| `src/rag_chatbot/integrations/fs/file_repository.py` | 파일 로그 저장소 구현 |
| `src/rag_chatbot/integrations/fs/__init__.py` | 공개 API 제공 |

## 3. BaseFSEngine 인터페이스

필수 메서드:

1. `write_text(path, content, encoding)`
2. `read_text(path, encoding)`
3. `list_files(base_dir, recursive=False, suffix=None)`
4. `exists(path)`
5. `mkdir(path, exist_ok=True)`
6. `move(src, dst)`
7. `copy(src, dst)`

의미:

1. 저장소 계층은 엔진 구현 상세를 몰라도 파일 작업을 수행할 수 있다.
2. 원격 스토리지 연동 시 같은 인터페이스로 교체 가능하다.

## 4. LocalFSEngine 동작

1. `write_text`는 `open(..., "x")`를 사용해 기존 파일 덮어쓰기를 막는다.
2. 쓰기/이동/복사 전에 부모 디렉터리를 자동 생성한다.
3. `list_files`는 재귀 탐색과 suffix 필터를 지원한다.
4. 대상 경로가 디렉터리가 아니면 빈 목록을 반환한다.

## 5. FileLogRepository 동작

## 5-1. 저장 규칙

1. 저장 경로: `<base_dir>/<YYYYMMDD>/<uuid>.log`
2. 포맷: `LogRecord` JSON 문자열
3. 인코딩: 기본 `SharedConst.DEFAULT_ENCODING`(`utf-8`)
4. base_dir가 비어 있으면 초기화 시 `ValueError`

## 5-2. 조회 규칙

1. `.log` 파일을 재귀 탐색한다.
2. JSON 파싱/모델 검증 성공 레코드를 수집한다.
3. timestamp 오름차순으로 정렬해 반환한다.
4. 손상 파일은 WARNING 레벨 fallback 레코드로 대체한다.

fallback 레코드 메타데이터:

1. `path`
2. `reason` (`디코딩 실패`, `유효성 검사 실패`)

## 6. 사용 예시

```python
from rag_chatbot.integrations.fs import FileLogRepository
from rag_chatbot.shared.logging import InMemoryLogger

repository = FileLogRepository(base_dir="data/logs")
logger = InMemoryLogger(name="file-logger", repository=repository)
logger.info("서비스 시작")
```

## 7. 변경 작업 절차

## 7-1. 원격 스토리지 엔진 추가

1. `BaseFSEngine` 구현체를 새 파일로 추가한다.
2. `FileLogRepository(engine=...)`로 주입한다.
3. 기존 로깅 호출 코드는 유지한다.

## 7-2. 파일명 규칙 변경

1. `_create_log_path` 규칙을 변경한다.
2. 조회 정렬 기준(timestamp)은 유지한다.
3. 운영 보관 정책(일자/크기 롤링)을 함께 정의한다.

## 7-3. 손상 파일 처리 정책 변경

1. `_fallback_record` 메타 필드를 확장한다.
2. 손상 파일을 스킵할지 경고 레코드로 남길지 정책을 명확히 한다.

## 8. 트러블슈팅

| 증상 | 원인 후보 | 확인 스크립트 | 조치 |
| --- | --- | --- | --- |
| 로그 파일이 생성되지 않음 | base_dir 권한/경로 문제 | `file_repository.py`, `local.py` | 경로 권한 및 parent 생성 여부 확인 |
| 동일 파일명 충돌 오류 | 외부에서 파일명 고정 사용 | `LocalFSEngine.write_text` | 고유 파일명 규칙 유지 |
| 조회 결과에 WARNING 로그가 많음 | 로그 파일 손상 | `FileLogRepository._read_record` | 로그 생성 경로/직렬화 오류 점검 |
| 목록이 비어 있음 | suffix 필터 또는 base_dir 오설정 | `LocalFSEngine.list_files` | 확장자/디렉터리 값 점검 |

## 9. 소스 매칭 점검 항목

1. 인터페이스 메서드 목록이 `base/engine.py`와 일치하는가
2. 저장 경로 규칙 설명이 `file_repository.py`와 일치하는가
3. fallback 처리 설명이 `_fallback_record` 구현과 일치하는가
4. 문서 경로가 실제 `src/rag_chatbot/integrations/fs` 구조와 일치하는가

## 10. 관련 문서

- `docs/integrations/overview.md`
- `docs/setup/filesystem.md`
- `docs/shared/logging.md`
