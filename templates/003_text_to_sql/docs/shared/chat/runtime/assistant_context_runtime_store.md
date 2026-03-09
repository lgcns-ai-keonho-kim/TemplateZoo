# runtime/assistant_context_runtime_store.py

assistant 컨텍스트 저장소를 모듈 전역으로 관리하는 런타임 상태 모듈이다.

## 1. 역할

- 실행 시점에 선택된 `AssistantContextStore` 구현체를 전역으로 보관한다.
- 세션 삭제/종료 시 캐시 정리 API를 제공한다.

## 2. 공개 함수

| 함수 | 설명 |
| --- | --- |
| `set_assistant_context_store` | 전역 저장소 설정 |
| `get_assistant_context_store` | 전역 저장소 조회 |
| `clear_assistant_context` | 세션 단위 캐시 삭제 |
| `close_assistant_context_store` | 저장소 종료 및 전역 해제 |

## 3. 사용 위치

- 초기 조립: `src/text_to_sql/api/chat/services/runtime.py`
- 세션 삭제 후 정리: `services/chat_service.py`
- shutdown 정리: 런타임 종료 훅
