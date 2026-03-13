# Core 모듈 레퍼런스

`src/chatbot/core`는 채팅 도메인 규칙을 가진 계층이다. HTTP, 저장소 구현, 큐/버퍼 운영은 여기서 직접 다루지 않는다.

## 1. 역할

현재 `core/chat`이 담당하는 일:

1. 채팅 도메인 모델 정의
2. 그래프 상태 키 정의
3. 시스템 프롬프트 정의
4. 노드 조립
5. 그래프 연결과 분기 규칙 정의

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

## 3. 현재 핵심 구현

1. 그래프 진입점은 `chat_graph` 단일 인스턴스다.
2. 실행 흐름은 `safeguard -> safeguard_route -> response/blocked`다.
3. 최종 응답 키는 `assistant_message`다.
4. `response_node`, `safeguard_node`는 `ChatGoogleGenerativeAI`를 `LLMClient`로 감싸 사용한다.
5. 분기 결과는 `safeguard_route`에 기록된다.

## 4. 상위 계층과의 관계

```text
api/runtime -> shared/chat service -> core/chat graph -> shared/integrations
```

정리:

1. API는 `core`를 직접 호출하지 않고 `shared` 서비스 계층을 경유한다.
2. `core`는 HTTP 타입에 의존하지 않는다.
3. `core`는 `shared.chat.nodes`, `shared.chat.graph`, `integrations.llm`에 의존해 그래프를 조립한다.

## 5. 유지보수 포인트

1. 상태 키를 바꾸면 노드, 그래프, 서비스 문서를 같이 수정해야 한다.
2. 노드 이름은 SSE 페이로드의 `node` 값에도 노출된다.
3. `DEFAULT_CONTEXT_WINDOW`를 바꾸면 API DTO와 정적 UI 기본 동작에 영향이 있다.
4. 세이프가드 라벨을 바꾸면 프롬프트, 라우트 노드, 차단 메시지, 문서를 함께 수정해야 한다.

## 6. 관련 문서

- `docs/core/chat.md`
- `docs/api/chat.md`
- `docs/shared/chat/overview.md`
