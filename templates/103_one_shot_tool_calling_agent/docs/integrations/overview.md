# Integrations 개요

`src/one_shot_tool_calling_agent/integrations`의 파일 단위 문서 허브다.
`__init__.py`는 제외하고 실행 파일 기준으로 문서를 구성합니다.

## 통계

- 전체 non-init 코드 파일 수: `70`
- `db`: `63`
- `llm`: `2`
- `embedding`: `2`
- `fs`: `3`

## 모듈별 진입 문서

- `docs/integrations/db/overview.md`
- `docs/integrations/llm/overview.md`
- `docs/integrations/embedding/overview.md`
- `docs/integrations/fs/overview.md`

## 디렉터리 트리

```text
docs/integrations/
  overview.md
  db/
    overview.md
    client.md
    base/
      overview.md
      *.md
    engines/
      overview.md
      sql_common.md
      elasticsearch/
        overview.md
        *.md
      lancedb/
        overview.md
        *.md
      mongodb/
        overview.md
        *.md
      postgres/
        overview.md
        *.md
      redis/
        overview.md
        *.md
      sqlite/
        overview.md
        *.md
    query_builder/
      overview.md
      *.md
  llm/
    overview.md
    _client_mixin.md
    client.md
  embedding/
    overview.md
    _client_mixin.md
    client.md
  fs/
    overview.md
    file_repository.md
    base/
      overview.md
      engine.md
    engines/
      overview.md
      local.md
```
