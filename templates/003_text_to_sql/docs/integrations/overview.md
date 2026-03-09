# Integrations 모듈 가이드

이 문서는 `src/text_to_sql/integrations` 계층을 폴더형 문서 구조로 탐색하기 위한 허브다.

## 1. 용어 정리

| 용어 | 의미 | 관련 코드 |
| --- | --- | --- |
| 통합 계층 | 외부 시스템(DB, LLM, 파일시스템, 임베딩)과 직접 통신하는 계층 | `src/text_to_sql/integrations/*` |
| DB 클라이언트 | 엔진 호출을 공통 API로 감싼 퍼사드 | `src/text_to_sql/integrations/db/client.py` |
| LLM 클라이언트 | 모델 호출/로깅/예외 표준화를 담당하는 래퍼 | `src/text_to_sql/integrations/llm/client.py` |
| 파일 저장소 | 파일 시스템 엔진 위에서 로그 저장/조회 책임을 수행하는 저장소 | `src/text_to_sql/integrations/fs/file_repository.py` |
| 임베딩 클라이언트 | 임베딩 모델 호출을 담당하는 연동 모듈 | `src/text_to_sql/integrations/embedding/client.py` |

## 2. 문서 진입점

| 영역 | 문서 진입점 | 설명 |
| --- | --- | --- |
| DB | `docs/integrations/db/README.md` | base/query_builder/engine 구현 문서 인덱스 |
| LLM | `docs/integrations/llm/README.md` | `LLMClient` 중심 인터페이스 문서 인덱스 |
| FS | `docs/integrations/fs/README.md` | 파일 엔진/저장소 문서 인덱스 |
| Embedding | `docs/integrations/embedding/README.md` | 임베딩 연동 모듈 문서 인덱스 |

## 3. 구조 요약

```text
docs/integrations/
  overview.md
  db/
    README.md
    base/*.md
    query_builder/*.md
    engines/**/*.md
    client.md
    query_target_registry.md
  llm/
    README.md
    client.md
  fs/
    README.md
    base/engine.md
    engines/local.md
    file_repository.md
  embedding/
    README.md
    client.md
```

## 4. 관련 문서

- `docs/README.md`
- `docs/setup/mongodb.md`
- `docs/setup/filesystem.md`
- `docs/core/chat.md`
