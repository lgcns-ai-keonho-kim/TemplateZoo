# 개발 문서 허브

현재 템플릿은 `single request agent` 구조를 기준으로 정리되어 있다.

## 문서 트리

```text
docs/
  README.md
  api/
    overview.md
    agent.md
    health.md
  core/
    overview.md
    agent.md
  shared/
    overview.md
    agent/
      overview.md
  static/
    ui.md
```

## 코드-문서 매핑

| 코드 경로 | 문서 |
| --- | --- |
| `src/single_request_agent/api` | `docs/api/overview.md` |
| `src/single_request_agent/api/agent` | `docs/api/agent.md` |
| `src/single_request_agent/core/agent` | `docs/core/agent.md` |
| `src/single_request_agent/shared/agent` | `docs/shared/agent/overview.md` |
| `src/single_request_agent/static` | `docs/static/ui.md` |

## 확인 순서

1. 공개 계약은 `docs/api/overview.md`, `docs/api/agent.md`
2. 그래프 구조는 `docs/core/agent.md`
3. 공용 조립과 범용 Node는 `docs/shared/agent/overview.md`
4. 화면 동작은 `docs/static/ui.md`
