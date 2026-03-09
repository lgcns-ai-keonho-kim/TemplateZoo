# Static UI 구현 가이드

이 문서는 `src/text_to_sql/static`의 현재 동작과 백엔드 인터페이스를 기준으로 UI 구현 포인트를 설명합니다.

## 1. 범위

이 문서는 다음을 다룹니다.

1. 세션 목록/메시지 목록 로딩
2. `/chat` 제출과 SSE 스트림 소비
3. 현재 SSE 이벤트 타입과 node 값
4. 세션 삭제와 화면 반영

## 2. 주요 모듈

| 모듈 | 파일 | 역할 |
| --- | --- | --- |
| App 퍼사드 | `js/core/app.js` | 앱 초기화 |
| Grid 컨트롤러 | `js/ui/grid_manager.js` | 세션 로딩/전환/삭제 |
| API 어댑터 | `js/chat/api_transport.js` | HTTP/SSE 호출 |
| Cell 컴포넌트 | `js/chat/chat_cell.js` | 입력/전송/스트림 렌더 |
| Presenter | `js/chat/chat_presenter.js` | 메시지/상태 렌더링 |

## 3. 백엔드 인터페이스

### 3-1. UI API

- `POST /ui-api/chat/sessions`
- `GET /ui-api/chat/sessions`
- `GET /ui-api/chat/sessions/{session_id}/messages`
- `DELETE /ui-api/chat/sessions/{session_id}`

### 3-2. Chat API

- `POST /chat`
- `GET /chat/{session_id}/events?request_id=...`

## 4. SSE 이벤트 구조

```json
{
  "session_id": "...",
  "request_id": "...",
  "type": "start|token|sql_plan|sql_result|done|error",
  "node": "executor|safeguard|schema_selection_parse|raw_sql_generate|raw_sql_generate_retry|raw_sql_execute|raw_sql_execute_retry|sql_result_collect|response|blocked",
  "content": "...",
  "status": "COMPLETED|FAILED|null",
  "error_message": "...",
  "metadata": {}
}
```

## 5. 현재 스트림 의미

| type | node | 의미 |
| --- | --- | --- |
| `sql_plan` | `schema_selection_parse` | 선택된 alias |
| `sql_plan` | `raw_sql_generate`, `raw_sql_generate_retry` | 생성된 SQL |
| `sql_result` | `raw_sql_execute`, `raw_sql_execute_retry` | alias별 실행 결과 |
| `sql_result` | `sql_result_collect` | 최종 성공/실패 집계 |
| `done` | `response` | 최종 답변 |
| `done` | `blocked` | 차단 메시지 |

## 6. 화면 처리 규칙

1. `start`를 받으면 전송 중 상태를 켭니다.
2. `token`은 `response` 노드에서만 본문 스트림으로 붙입니다.
3. `sql_plan`, `sql_result`는 디버그/런타임 정보용으로만 표시합니다.
4. `done`을 받으면 전송 상태를 종료하고, 이후 메시지 목록 재조회가 가능해야 합니다.
5. `error`를 받으면 사용자에게 실패 메시지를 표시합니다.
