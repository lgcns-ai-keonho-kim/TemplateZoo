# fs/base/engine.md

소스 경로: `src/text_to_sql/integrations/fs/base/engine.py`

## 1. 역할

- 파일 시스템 엔진 인터페이스를 제공한다.
- 파일 쓰기/읽기/목록/이동/복사를 위한 표준 메서드를 정의한다.
- 내부 구조는 전략 패턴 기반이다.

## 2. 주요 구성

### 2-1. 클래스

| 클래스 | 핵심 메서드 |
| --- | --- |
| `BaseFSEngine` | `name, write_text, read_text, list_files, exists, mkdir, move, copy` |

### 2-2. 함수

- 정의된 최상위 함수가 없다.

## 3. 오류/예외 코드

- 모듈 내부에서 명시적으로 정의한 오류 코드가 없다.

## 4. 관련 코드

- `src/text_to_sql/integrations/fs/engines/local.py`
