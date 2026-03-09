# fs/file_repository.md

소스 경로: `src/text_to_sql/integrations/fs/file_repository.py`

## 1. 역할

- 목적: 파일 기반 로그 저장소를 제공한다.
- 설명: 파일 시스템 엔진을 통해 날짜-UUID.log 파일로 로그를 저장한다.
- 디자인 패턴: 저장소 패턴

## 2. 주요 구성

### 2-1. 클래스

| 클래스 | 핵심 메서드 |
| --- | --- |
| `FileLogRepository` | `__init__, base_dir, add, list` |

### 2-2. 함수

- 정의된 최상위 함수가 없다.

## 3. 오류/예외 코드

- 모듈 내부에서 명시적으로 정의한 오류 코드가 없다.

## 4. 연관 모듈

- `src/text_to_sql/integrations/fs/base/engine.py`
- `src/text_to_sql/integrations/fs/engines/local.py`
- `src/text_to_sql/shared/const/__init__.py`
- `src/text_to_sql/shared/logging/logger.py`
- `src/text_to_sql/shared/logging/models.py`
