# Shared 모듈 레퍼런스

`src/chatbot/shared`는 API 계층이 직접 다루기 어려운 실행 공통 로직을 모아 둔 계층이다.

## 1. 역할

현재 이 계층이 담당하는 일:

1. 채팅 실행 서비스와 오케스트레이션
2. 세션 메모리와 저장소 추상화
3. 큐, 이벤트 버퍼, 워커, 스레드풀 같은 공용 런타임 유틸
4. 설정 로딩
5. 공통 예외와 로깅

의존 방향:

```text
api -> shared
shared -> core
shared -> integrations
```

## 2. 구조

| 경로 | 역할 | 대표 파일 |
| --- | --- | --- |
| `src/chatbot/shared/chat` | 그래프 포트, 실행 서비스, 메모리, 저장소, 공용 노드 | `services/chat_service.py`, `services/service_executor.py` |
| `src/chatbot/shared/runtime` | 큐, 이벤트 버퍼, 워커, 스레드풀 | `queue/*.py`, `buffer/*.py` |
| `src/chatbot/shared/config` | 설정 병합과 런타임 환경 로딩 | `loader.py`, `runtime_env_loader.py` |
| `src/chatbot/shared/exceptions` | 공통 예외 모델 | `models.py`, `base.py` |
| `src/chatbot/shared/logging` | 로거, 저장소, DB/LLM 로그 저장 | `logger.py`, `db_repository.py`, `llm_repository.py` |
| `src/chatbot/shared/const` | 공통 상수 | `__init__.py` |

## 3. 공개 API

`src/chatbot/shared/__init__.py`가 외부에 노출하는 대표 항목:

1. 예외: `BaseAppException`, `ExceptionDetail`
2. 로깅: `Logger`, `InMemoryLogger`, `DBLogRepository`, `LLMLogRepository`
3. Chat: `BaseChatGraph`, `ChatService`, `ServiceExecutor`, `ChatSessionMemoryStore`, `ChatHistoryRepository`
4. Runtime: `QueueConfig`, `InMemoryQueue`, `RedisQueue`, `EventBufferConfig`, `InMemoryEventBuffer`, `RedisEventBuffer`, `Worker`, `ThreadPool`

## 4. 현재 기본 경로

기본 채팅 런타임에서 실제로 쓰는 조합:

```text
ChatService
 -> ChatHistoryRepository(SQLite)
 -> ChatSessionMemoryStore
 -> chat_graph

ServiceExecutor
 -> InMemoryQueue
 -> InMemoryEventBuffer
```

`RedisQueue`, `RedisEventBuffer`, `ThreadPool`, `Worker`는 현재 기본 조립에서는 직접 쓰지 않는 선택 확장 경로다.

## 5. 유지보수 포인트

1. `shared/chat/services`의 이벤트 스키마가 바뀌면 API와 정적 UI가 바로 영향을 받는다.
2. 환경 변수는 `RuntimeEnvironmentLoader`가 앱 import 이전에 로드해야 한다.
3. `detail.code`는 라우터 계층의 HTTP 상태코드 매핑 기준이다.
4. 기본 경로와 선택 확장 경로를 문서에서 섞어 쓰면 운영 판단이 흐려진다.

## 6. 관련 문서

- `docs/shared/chat/overview.md`
- `docs/shared/runtime.md`
- `docs/shared/config.md`
- `docs/shared/logging.md`
- `docs/shared/exceptions.md`
- `docs/shared/const.md`
