# Shared 모듈 레퍼런스

`src/chatbot/shared`는 API 계층이 직접 다루기 어려운 실행 공통 로직을 모아 둔 계층이다. 현재 코드에서는 채팅 실행 오케스트레이션, 런타임 유틸리티, 설정 로딩, 공통 예외, 로깅을 담당한다.

## 1. 코드 설명

| 경로 | 역할 | 대표 파일 |
| --- | --- | --- |
| `src/chatbot/shared/chat` | 채팅 실행 서비스, 포트, 저장소, 메모리, 공용 노드 | `services/chat_service.py`, `services/service_executor.py` |
| `src/chatbot/shared/runtime` | 큐, 이벤트 버퍼, 워커, 스레드풀 | `queue/*.py`, `buffer/*.py` |
| `src/chatbot/shared/config` | 설정 병합과 런타임 환경 해석 | `loader.py`, `runtime_env_loader.py` |
| `src/chatbot/shared/exceptions` | 공통 예외 모델과 베이스 예외 | `models.py`, `base.py` |
| `src/chatbot/shared/logging` | 인메모리/DB 로깅 인터페이스와 저장소 | `logger.py`, `db_repository.py`, `llm_repository.py` |
| `src/chatbot/shared/const` | 공통 상수 | `__init__.py` |

현재 의존 방향은 다음과 같다.

```text
api -> shared
shared -> core
shared -> integrations
```

`shared`는 `core`의 그래프와 도메인 모델을 실행 서비스로 묶고, 외부 시스템 접근은 `integrations`에 위임한다.

## 2. 공개 API

`src/chatbot/shared/__init__.py`가 외부에 노출하는 주요 항목은 다음과 같다.

1. 예외: `BaseAppException`, `ExceptionDetail`
2. 로깅: `Logger`, `LogRepository`, `InMemoryLogger`, `DBLogRepository`, `LLMLogRepository`
3. Chat: `BaseChatGraph`, `ChatService`, `ServiceExecutor`, `ChatSessionMemoryStore`, `ChatHistoryRepository`
4. Runtime: `QueueConfig`, `InMemoryQueue`, `RedisQueue`, `EventBufferConfig`, `InMemoryEventBuffer`, `RedisEventBuffer`, `Worker`, `ThreadPool`

## 3. 유지보수 포인트

1. `shared/chat/services`는 현재 채팅 실행의 핵심 경로다. 여기서 이벤트 스키마를 바꾸면 API와 정적 UI가 함께 영향을 받는다.
2. `shared/runtime`는 재사용 가능한 유틸 계층이지만, 현재 기본 조립은 `InMemoryQueue`와 `InMemoryEventBuffer`를 사용한다.
3. 환경 변수는 `shared/config/runtime_env_loader.py`에서 앱 import 이전에 로드되므로, 로더 순서를 바꾸면 전체 초기화 방식이 달라진다.
4. 예외 코드는 라우터 계층에서 HTTP 상태 매핑 기준으로 사용되므로, `detail.code`를 임의로 바꾸면 API 응답 의미가 깨질 수 있다.

## 4. 추가 개발/확장 가이드

1. 새로운 공통 서비스가 필요하면 먼저 `shared`에 둘 책임인지 확인해야 한다. HTTP 경계면 `api`, 도메인 규칙이면 `core`, 외부 제품 세부 구현이면 `integrations`가 맞다.
2. 다른 채팅 그래프를 추가해도 `ChatServicePort`, `ServiceExecutorPort`, `GraphPort`를 유지하면 상위 계층 영향도를 줄일 수 있다.
3. 런타임 백엔드를 Redis로 바꾸더라도 조립 지점은 `src/chatbot/api/chat/services/runtime.py` 하나로 유지하는 것이 안전하다.

## 5. 문서 진입점

- `docs/shared/chat/overview.md`
- `docs/shared/runtime.md`
- `docs/shared/config.md`
- `docs/shared/exceptions.md`
- `docs/shared/logging.md`
- `docs/shared/const.md`
