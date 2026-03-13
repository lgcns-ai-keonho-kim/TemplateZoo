# Shared 모듈 개요

`src/plan_and_then_execute_agent/shared` 계층의 책임 경계와 구성 요소를 코드 기준으로 정리한다.

## 1. 용어 정리

| 용어 | 의미 | 관련 스크립트 |
| --- | --- | --- |
| 공통 계층 | API/Core/Integrations 사이에서 재사용되는 실행/저장/보조 로직 계층 | `src/plan_and_then_execute_agent/shared/*` |
| 포트 | 구현체와 상위 계층 사이의 동작 인터페이스 | `src/plan_and_then_execute_agent/shared/chat/interface/ports.py` |
| 실행 오케스트레이터 | 큐 소비, 이벤트 중계, 상태 전이를 관리하는 컴포넌트 | `src/plan_and_then_execute_agent/shared/chat/services/service_executor.py`, `src/plan_and_then_execute_agent/shared/chat/services/_service_executor_support.py` |
| 런타임 컴포넌트 | Queue, EventBuffer, Worker, ThreadPool 같은 실행 인프라 | `src/plan_and_then_execute_agent/shared/runtime/*` |
| 공통 예외 | 계층 전체에서 통일해 사용하는 오류 모델 | `src/plan_and_then_execute_agent/shared/exceptions/*` |
| 공통 로깅 | 로거 인터페이스와 저장소 구현 | `src/plan_and_then_execute_agent/shared/logging/*` |

## 2. 모듈 구성과 스크립트 맵

| 경로 | 핵심 책임 | 주요 스크립트 |
| --- | --- | --- |
| `src/plan_and_then_execute_agent/shared/chat` | Chat 실행, 저장, 멱등 처리, 그래프 포트 | `services/chat_service.py`, `services/service_executor.py`, `services/_service_executor_support.py`, `repositories/history_repository.py` |
| `src/plan_and_then_execute_agent/shared/runtime` | 큐/이벤트 버퍼/워커/스레드풀 제공 | `queue/*.py`, `buffer/*.py`, `worker/*.py`, `thread_pool/*.py` |
| `src/plan_and_then_execute_agent/shared/config` | 환경 변수/JSON/dict 설정 병합과 런타임 `.env` 로딩 | `loader.py`, `runtime_env_loader.py` |
| `src/plan_and_then_execute_agent/shared/exceptions` | 공통 예외 모델과 베이스 예외 | `models.py`, `base.py` |
| `src/plan_and_then_execute_agent/shared/logging` | 로거 인터페이스, 인메모리/DB 로그 저장소 | `logger.py`, `_logger_base.py`, `_log_repository_interface.py`, `_in_memory_logger.py`, `db_repository.py`, `llm_repository.py` |
| `src/plan_and_then_execute_agent/shared/const` | 전역 상수 | `__init__.py` |

## 3. 책임 경계

핵심 규칙:

1. `api` 계층은 HTTP 경계 처리에 집중하고 실행 로직은 `shared/chat`으로 위임한다.
2. `core` 계층은 도메인 모델/그래프 정의에 집중하고 저장/오케스트레이션은 `shared`에서 처리한다.
3. `integrations` 구현체를 바꿔도 상위 계층이 영향받지 않도록 `shared` 포트 인터페이스를 유지한다.

의존 흐름:

```text
api -> shared -> core
shared -> integrations
```

## 4. 운영 관점 점검 지점

1. SSE 지연/타임아웃 이슈: `shared/chat/services/service_executor.py`, `shared/runtime/buffer/*`
2. 문맥 누락 이슈: `shared/chat/memory/session_store.py`, `shared/chat/services/chat_service.py`
3. 중복 저장 이슈: `shared/chat/repositories/history_repository.py`의 request_id 커밋 로직
4. 설정 누락 이슈: `shared/config/runtime_env_loader.py`
5. 로그 누락 이슈: `shared/logging/logger.py`, `shared/logging/_create_default_logger.py`, `shared/logging/*_repository.py`

## 6. 확장 포인트

1. 변경 대상은 실행 경로와 보조 경로로 구분해 영향 범위를 파악한다.
2. 포트 인터페이스 변경 여부가 상위 계층 파급 범위를 결정한다.
3. 구현체 변경 시 상위 호출 경로(`api/chat/services/runtime.py`)가 함께 점검된다.
4. 문서의 용어, 스크립트 경로, 기본값은 코드 상태와 동일하게 유지된다.

## 8. 관련 문서

- `docs/shared/chat/overview.md`
- `docs/shared/runtime.md`
- `docs/shared/config.md`
- `docs/shared/exceptions.md`
- `docs/shared/logging.md`
- `docs/shared/const.md`
