# fs/engines/local.md

소스 경로: `src/text_to_sql/integrations/fs/engines/local.py`

## 1. 역할

- 목적: 로컬 파일 시스템 엔진을 제공한다.
- 설명: 표준 라이브러리를 사용해 파일 조작을 수행한다.
- 디자인 패턴: 어댑터 패턴

## 2. 주요 구성

### 2-1. 클래스

| 클래스 | 핵심 메서드 |
| --- | --- |
| `LocalFSEngine` | `name, write_text, read_text, list_files, exists, mkdir, move, copy` |

### 2-2. 함수

- 정의된 최상위 함수가 없다.

## 3. 오류/예외 코드

- 모듈 내부에서 명시적으로 정의한 오류 코드가 없다.

## 4. 연관 모듈

- `src/text_to_sql/integrations/fs/base/engine.py`
