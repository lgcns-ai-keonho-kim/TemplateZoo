# Core Chat 레퍼런스

이 문서는 `src/chatbot/core/chat`의 모델, 프롬프트, 노드, 그래프를 코드 기준으로 설명한다.

## 1. 디렉터리 구조

```text
src/chatbot/core/chat/
  const/
  graphs/
  models/
  nodes/
  prompts/
  state/
  utils/
```

## 2. 도메인 모델

### 2-1. `ChatSession`

파일: `src/chatbot/core/chat/models/entities.py`

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `session_id` | `str` | 세션 식별자 |
| `title` | `str` | 세션 제목 |
| `created_at` | `datetime` | 생성 시각 |
| `updated_at` | `datetime` | 마지막 갱신 시각 |
| `message_count` | `int` | 저장된 메시지 수 |
| `last_message_preview` | `str \| None` | 최근 메시지 미리보기 |

### 2-2. `ChatMessage`

파일: `src/chatbot/core/chat/models/entities.py`

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `message_id` | `str` | 메시지 식별자 |
| `session_id` | `str` | 소속 세션 |
| `role` | `ChatRole` | `user`, `assistant`, `system` |
| `content` | `str` | 메시지 본문 |
| `sequence` | `int` | 세션 내 순번 |
| `created_at` | `datetime` | 생성 시각 |
| `metadata` | `dict[str, Any]` | 부가 메타데이터 |

### 2-3. `ChatTurnResult`

파일: `src/chatbot/core/chat/models/turn_result.py`

사용자 1턴 처리 결과를 세션, 사용자 메시지, assistant 메시지로 묶는다.

## 3. 상수와 상태

### 3-1. `settings.py`

파일: `src/chatbot/core/chat/const/settings.py`

| 상수 | 값 | 설명 |
| --- | --- | --- |
| `CHAT_DB_PATH` | 환경 변수 또는 `data/db/chat/chat_history.sqlite` | 기본 SQLite 경로 |
| `CHAT_SESSION_COLLECTION` | `chat_sessions` | 세션 컬렉션명 |
| `CHAT_MESSAGE_COLLECTION` | `chat_messages` | 메시지 컬렉션명 |
| `CHAT_REQUEST_COMMIT_COLLECTION` | `chat_request_commits` | 저장 멱등성 기록 컬렉션명 |
| `DEFAULT_PAGE_SIZE` | `50` | 목록 조회 기본값 |
| `MAX_PAGE_SIZE` | `200` | 목록 조회 최대값 |
| `DEFAULT_CONTEXT_WINDOW` | `20` | 최근 문맥 길이 기본값 |

### 3-2. 차단 메시지

파일: `src/chatbot/core/chat/const/messages/safeguard.py`

현재 차단 메시지 유형:

1. `PII`
2. `HARMFUL`
3. `PROMPT_INJECTION`

### 3-3. `ChatGraphState`

파일: `src/chatbot/core/chat/state/graph_state.py`

```python
class ChatGraphState(TypedDict):
    session_id: str
    user_message: str
    history: list[ChatMessage]
    safeguard_result: NotRequired[str]
    safeguard_route: NotRequired[str]
    safeguard_reason: NotRequired[str]
    assistant_message: str
```

핵심 상태 키:

1. `user_message`: 현재 요청
2. `history`: 최근 대화 문맥
3. `safeguard_result`: 분류 결과
4. `safeguard_route`: 다음 노드 이름
5. `assistant_message`: 최종 응답

## 4. 프롬프트

### 4-1. `CHAT_PROMPT`

파일: `src/chatbot/core/chat/prompts/chat_prompt.py`

설명:

1. 사용자 질문에 정확하고 간결하게 답하도록 제한한다.
2. 항상 한국어 답변을 요구한다.
3. 불필요한 범위 확장이나 일반적인 후속 질문 유도를 금지한다.

### 4-2. `SAFEGUARD_PROMPT`

파일: `src/chatbot/core/chat/prompts/safeguard_prompt.py`

설명:

1. 최신 사용자 입력만 기준으로 분류한다.
2. 반환값은 `PASS`, `PII`, `HARMFUL`, `PROMPT_INJECTION` 중 하나여야 한다.
3. 확신이 없을 때는 `HARMFUL`로 분류한다.

## 5. 노드 조립

### 5-1. `safeguard_node`

파일: `src/chatbot/core/chat/nodes/safeguard_node.py`

설명:

1. Gemini 기반 `ChatGoogleGenerativeAI`를 `LLMClient`로 감싼다.
2. `history_key="__skip_history__"`로 대화 이력을 사용하지 않는다.
3. `stream_tokens=False`로 분류 결과만 반환한다.
4. 출력 키는 `safeguard_result`다.

### 5-2. `safeguard_route_node`

파일: `src/chatbot/core/chat/nodes/safeguard_route_node.py`

설명:

1. `BranchNode`를 사용한다.
2. `PASS`면 `response`, 그 외는 `blocked`로 보낸다.
3. `PROMPT_INJETION` 오타는 `PROMPT_INJECTION`으로 정규화한다.
4. 허용 집합 밖 값은 `HARMFUL`로 보정한다.
5. 보정된 값은 다시 `safeguard_result`에 기록한다.

### 5-3. `response_node`

파일: `src/chatbot/core/chat/nodes/response_node.py`

설명:

1. Gemini 기반 `ChatGoogleGenerativeAI`를 사용한다.
2. 출력 키는 `assistant_message`다.
3. 토큰 스트리밍 이벤트를 발생시킨다.

### 5-4. `safeguard_message_node`

파일: `src/chatbot/core/chat/nodes/safeguard_message_node.py`

설명:

1. `MessageNode`를 사용한다.
2. `SafeguardRejectionMessage`에서 사용자 안내 문구를 선택한다.
3. 출력 키는 `assistant_message`다.

## 6. 그래프 구조

파일: `src/chatbot/core/chat/graphs/chat_graph.py`

```mermaid
flowchart LR
    S[safeguard] --> R[safeguard_route]
    R -->|response| A[response]
    R -->|blocked| B[blocked]
    A --> END
    B --> END
```

구현 포인트:

1. 진입점은 `safeguard`다.
2. `safeguard_route`는 `safeguard_route` 값을 읽어 다음 노드를 결정한다.
3. `response`, `blocked`는 둘 다 종료 노드다.
4. `checkpointer`는 `InMemorySaver()`를 사용한다.

`stream_node` 정책:

| 노드 | 외부 노출 이벤트 |
| --- | --- |
| `safeguard` | `safeguard_result` |
| `safeguard_route` | `safeguard_route`, `safeguard_result` |
| `response` | `token`, `assistant_message` |
| `blocked` | `assistant_message` |

## 7. 상위 계층과의 연결

1. `ChatService`는 사용자 메시지를 저장한 뒤 최근 히스토리를 만들고 그래프를 호출한다.
2. `ServiceExecutor`는 그래프 이벤트를 SSE 이벤트로 정규화한다.
3. `response`의 `token`은 실시간 스트림으로, `blocked`의 `assistant_message`는 완료 응답으로 소비된다.

## 8. 유지보수 포인트

1. `assistant_message` 출력 키는 상위 계층이 최종 응답으로 기대하므로 쉽게 바꾸지 않는 편이 안전하다.
2. 그래프 노드 이름은 SSE payload의 `node` 값과 연결되므로 외부 계약에 가깝다.
3. 세이프가드 라벨을 추가하면 프롬프트, 라우트 노드, 차단 메시지, 문서를 함께 갱신해야 한다.
4. `DEFAULT_CONTEXT_WINDOW`는 API 요청 기본값과 정적 UI 전송 기본값에 영향을 준다.

## 9. 추가 개발과 확장 가이드

### 9-1. 새 분류 라벨 추가

1. `SAFEGUARD_PROMPT` 반환 토큰을 확장한다.
2. `safeguard_route_node`의 `allowed_selectors`와 분기 정책을 수정한다.
3. 필요하면 `SafeguardRejectionMessage`를 확장한다.
4. 상위 API와 UI 문서도 함께 맞춘다.

### 9-2. 응답 모델 교체

1. `response_node.py`의 모델 조립부를 수정한다.
2. 출력 키와 스트림 이벤트 계약은 유지한다.
3. 상위 SSE 소비 로직을 깨지 않도록 `token`과 `assistant_message` 의미를 유지한다.

### 9-3. 그래프 단계 추가

1. 새 노드를 조립한다.
2. `chat_graph.py`에 노드와 엣지를 추가한다.
3. 외부에 보여줄 이벤트만 `stream_node`에 등록한다.

## 10. 관련 문서

- `docs/core/overview.md`
- `docs/api/chat.md`
- `docs/static/ui.md`
