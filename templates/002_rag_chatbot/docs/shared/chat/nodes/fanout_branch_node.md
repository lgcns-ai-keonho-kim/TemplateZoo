# FanoutBranchNode 가이드

이 문서는 `src/rag_chatbot/shared/chat/nodes/fanout_branch_node.py`의 현재 구현을 기준으로 역할과 유지보수 포인트를 정리한다.

## 1. 역할

여러 그래프에서 재사용할 수 있는 범용 노드 또는 노드 보조 함수다.

## 2. 공개 구성

- 클래스 `FanoutBranchNode`
  공개 메서드: `route`, `run`

## 3. 코드 설명

- LangGraph state 입력은 보통 `Mapping[str, Any]` 형태로 정규화한 뒤 처리한다.
- 노드 출력은 state delta로 병합할 수 있는 dict 형식을 유지해야 한다.

## 4. 유지보수/추가개발 포인트

- 범용 노드는 특정 도메인 상태 키에 종속되지 않도록 유지하는 편이 다른 그래프에서 재사용하기 쉽다.
- 예외는 `BaseAppException` 코드로 정규화해 상위 계층에서 같은 방식으로 처리되게 한다.

## 5. 관련 문서

- `docs/shared/overview.md`
- `docs/shared/chat/README.md`
