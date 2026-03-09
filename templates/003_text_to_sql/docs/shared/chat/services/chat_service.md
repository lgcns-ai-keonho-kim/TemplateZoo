# services/chat_service.py

채팅 세션 저장소와 그래프 실행을 결합하는 서비스 레이어다.

## 1. 역할

- 사용자 메시지 저장, 컨텍스트 히스토리 구성, 그래프 실행, assistant 저장을 통합한다.
- memory cache와 repository를 함께 사용해 조회 비용과 일관성을 동시에 관리한다.

## 2. 주요 메서드

| 메서드 | 설명 |
| --- | --- |
| `create_session/list_sessions/get_session/delete_session` | 세션 수명주기 관리 |
| `invoke/ainvoke` | 단건 실행 후 assistant 메시지 저장 |
| `stream/astream` | 그래프 이벤트 중계 + done 이벤트 생성 |
| `persist_assistant_message` | `request_id` 멱등 저장 |

## 3. 데이터 흐름

1. user 메시지를 repository + memory_store에 append
2. memory_store에서 context window 히스토리 구성
3. graph 실행 후 token 또는 assistant_message를 결합
4. 최종 assistant 메시지를 저장하고 request commit 기록

## 4. 실패 경로

| 코드 | 발생 조건 |
| --- | --- |
| `CHAT_SESSION_NOT_FOUND` | 세션 조회 실패 |
| `CHAT_STREAM_EMPTY` | 그래프 응답이 비어 있음 |
| `CHAT_MESSAGE_EMPTY` | 입력 메시지가 비어 있음 |

## 5. 연관 모듈

- `services/service_executor.py`
- `repositories/history_repository.py`
- `memory/session_store.py`
