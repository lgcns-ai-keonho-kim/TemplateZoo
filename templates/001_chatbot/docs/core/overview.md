# Core 모듈 가이드

이 문서는 `src/base_template/core` 계층의 책임 경계와 학습 순서를 코드 기준으로 정리한다.

## 1. 용어 정리

| 용어 | 의미 | 관련 코드 |
| --- | --- | --- |
| 도메인 모델 | 세션/메시지 같은 핵심 데이터 구조 | `src/base_template/core/chat/models/entities.py` |
| 그래프 | 노드 실행 순서를 정의한 워크플로우 | `src/base_template/core/chat/graphs/chat_graph.py` |
| 노드 | 그래프에서 단위 작업을 수행하는 실행 컴포넌트 | `src/base_template/core/chat/nodes/*.py` |
| 상태 | 노드 사이를 흐르는 공통 키 집합 | `src/base_template/core/chat/state/graph_state.py` |
| 프롬프트 | LLM 노드에 주입되는 텍스트 템플릿 | `src/base_template/core/chat/prompts/*.py` |
| 상수 | 저장소/페이지/문맥 길이 같은 운영 기본값 | `src/base_template/core/chat/const/settings.py` |
| 스트림 노드 정책 | 어떤 노드의 어떤 이벤트를 외부에 노출할지 정한 규칙 | `chat_graph.py`의 `stream_node` |

## 2. 디렉터리와 관련 스크립트

| 경로 | 책임 | 주요 스크립트 |
| --- | --- | --- |
| `src/base_template/core/chat/models` | 도메인 엔티티 정의 | `entities.py`, `turn_result.py` |
| `src/base_template/core/chat/const` | 저장/조회/컨텍스트 상수 | `settings.py`, `messages/safeguard.py` |
| `src/base_template/core/chat/prompts` | 노드 프롬프트 템플릿 | `chat_prompt.py`, `safeguard_prompt.py` |
| `src/base_template/core/chat/nodes` | safeguard/response/blocked 노드 조립 | `response_node.py`, `safeguard_node.py`, `safeguard_route_node.py`, `safeguard_message_node.py` |
| `src/base_template/core/chat/graphs` | LangGraph 조립과 stream 노드 정책 | `chat_graph.py` |
| `src/base_template/core/chat/state` | 그래프 상태 타입 | `graph_state.py` |
| `src/base_template/core/chat/utils` | 도메인 문서 매퍼 | `mapper.py` |

연동 스크립트:

1. `src/base_template/shared/chat/graph/base_chat_graph.py`
2. `src/base_template/shared/chat/services/chat_service.py`
3. `src/base_template/shared/chat/services/service_executor.py`
4. `src/base_template/api/chat/services/runtime.py`

## 3. 의존성 경계

핵심 규칙:

1. `core`는 FastAPI 타입에 의존하지 않는다.
2. HTTP DTO는 `api/*/models`에만 둔다.
3. DB 엔진/외부 API 호출은 `integrations`와 `shared` 경유로 처리한다.

의존 흐름:

```text
core -> shared -> api
core -> integrations
```

피해야 할 구현:

1. `core`에서 `fastapi`를 import하는 코드
2. `core`에서 HTTP 상태코드를 직접 다루는 코드
3. `core`에서 라우터 계층 경로 상수를 참조하는 코드

## 4. 실행 관점 핵심 포인트

1. 그래프 진입점은 `chat_graph` 단일 객체다.
2. safeguard 결과는 `safeguard_route_node`에서 `response` 또는 `blocked`로 분기된다.
3. 최종 응답 키는 모든 경로에서 `assistant_message`를 사용한다.
4. 스트림에 노출할 이벤트는 `stream_node` 설정으로 제한한다.

## 5. 학습 순서

1. `src/base_template/core/chat/models/entities.py`
2. `src/base_template/core/chat/state/graph_state.py`
3. `src/base_template/core/chat/nodes/*.py`
4. `src/base_template/core/chat/graphs/chat_graph.py`
5. `src/base_template/shared/chat/services/chat_service.py`
6. `src/base_template/shared/chat/services/service_executor.py`

## 6. 소스 매칭 점검 항목

1. 문서의 노드 이름이 그래프 등록 이름과 일치하는가
2. `assistant_message` 출력 키가 모든 최종 경로에서 유지되는가
3. 상수 설명이 `settings.py` 값과 일치하는가
4. 문서에 적은 스크립트 경로가 실제 저장소에 존재하는가

## 7. 관련 문서

- `docs/core/chat.md`
- `docs/api/chat.md`
- `docs/shared/chat.md`
