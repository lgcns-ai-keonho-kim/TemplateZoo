# Core 모듈 레퍼런스

이 문서는 `src/chatbot/core` 계층의 책임과 변경 기준을 코드 중심으로 설명한다.

## 1. 역할

`core`는 채팅 도메인의 규칙을 가진다. 현재 범위는 다음과 같다.

1. 세션/메시지 도메인 모델 정의
2. 그래프 상태 키 정의
3. 시스템 프롬프트 정의
4. 노드 조립
5. 그래프 연결과 분기 규칙 정의

이 계층은 HTTP 라우팅을 직접 다루지 않으며, 저장소/큐/이벤트 버퍼 운영도 직접 맡지 않는다.

## 2. 구조

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

| 경로 | 코드 설명 | 유지보수 포인트 |
| --- | --- | --- |
| `models` | `ChatSession`, `ChatMessage`, `ChatRole`, `ChatTurnResult` 정의 | 엔티티 필드 변경은 API/저장소 문서와 함께 봐야 한다 |
| `const` | 기본 DB 경로, 페이지네이션, 문맥 길이, 차단 메시지 | 상수는 설정 설명과 함께 유지한다 |
| `prompts` | 응답용/세이프가드용 프롬프트 | 프롬프트 변경은 분류/응답 품질에 직접 영향을 준다 |
| `nodes` | 실제 사용할 노드 인스턴스 조립 | 출력 키와 노드 이름을 바꾸면 상위 계층 스트림 계약이 깨질 수 있다 |
| `graphs` | LangGraph builder와 stream 정책 | 분기와 노드 노출 정책의 단일 기준점이다 |
| `state` | 그래프 상태 타입 정의 | 상태 키 이름은 모든 노드가 공유하므로 안정적으로 유지한다 |
| `utils` | 도메인과 저장 문서 간 매핑 보조 | 저장 포맷 변경 시 함께 검토한다 |

## 3. 코드 의존 관계

호출 흐름 기준:

```text
api/runtime -> shared/chat service -> core/chat graph -> integrations/shared nodes
```

설명:

1. API는 `core`를 직접 호출하지 않고 주로 `shared` 서비스 계층을 경유한다.
2. `core`는 HTTP 타입에 의존하지 않는다.
3. `core`는 재사용 노드/그래프 인터페이스를 위해 `shared`와 `integrations`를 사용한다.

## 4. 현재 핵심 구현

1. 그래프 진입점은 `chat_graph` 단일 인스턴스다.
2. 실행 흐름은 `safeguard -> safeguard_route -> response/blocked`다.
3. 최종 응답 키는 `assistant_message`다.
4. `response_node`와 `safeguard_node`는 Gemini 기반 `ChatGoogleGenerativeAI`와 `LLMClient`를 사용한다.
5. 분기 결과는 `safeguard_route`에 기록된다.

## 5. 유지보수 포인트

1. 그래프 상태 키를 바꾸면 노드, 그래프, 서비스 문서를 모두 갱신해야 한다.
2. 노드 이름은 스트림 payload의 `node` 필드에도 반영되므로 외부 계약의 일부로 봐야 한다.
3. `DEFAULT_CONTEXT_WINDOW`는 API 요청 기본값과 프런트엔드 전송값에 영향을 준다.
4. 세이프가드 분기 규칙은 프롬프트, 라우트 노드, 차단 메시지가 함께 맞아야 한다.

## 6. 추가 개발과 확장 가이드

### 6-1. 새 노드 추가

1. `nodes`에 조립체를 추가한다.
2. `graphs/chat_graph.py`에 노드와 엣지를 등록한다.
3. `stream_node` 정책에 외부 노출 여부를 반영한다.

### 6-2. 새 상태 키 추가

1. `state/graph_state.py`를 먼저 수정한다.
2. 노드 입력/출력 키를 맞춘다.
3. 상위 서비스가 새 키를 외부에 노출해야 하는지 검토한다.

### 6-3. 프롬프트/모델 교체

1. 노드의 출력 키와 스트림 계약은 유지한다.
2. 분류 라벨이 바뀌면 라우트 노드 보정 규칙도 함께 수정한다.
3. 응답 스타일 변경보다 구조 변경이 더 큰 영향이 있으므로 단계적으로 적용하는 편이 안전하다.

## 7. 관련 문서

- `docs/core/chat.md`
- `docs/api/chat.md`
- `docs/static/ui.md`
