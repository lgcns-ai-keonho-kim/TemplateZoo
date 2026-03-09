# query_target_registry.py

`QueryTargetRegistry`는 target alias와 실제 DB 연결 대상을 연결하는 레지스트리입니다.

## 1. 역할

- alias별 엔진, 연결 객체, 테이블 allowlist를 보관합니다.
- startup에서 구성된 registry를 런타임 노드가 공통으로 사용합니다.
- 현재는 schema selection, raw SQL 준비, raw SQL 실행 단계에서 같은 registry를 참조합니다.
- registry 등록 자체는 startup에서 수행하지만, 실제 DB 연결은 각 엔진의 connection manager가 첫 사용 시점에 lazy connect 합니다.

## 2. 주요 기능

| 기능 | 설명 |
| --- | --- |
| target 등록 | alias와 target 정보를 등록 |
| target 조회 | alias로 target 조회 |
| 존재 확인 | alias 유효성 검사 |
| 일괄 종료 | shutdown 시 등록된 client를 순회하며 close |

## 3. 사용 위치

- 조립: `src/text_to_sql/api/chat/services/runtime.py`
- 스키마 선택 준비: `src/text_to_sql/core/chat/nodes/schema_selection_prepare_node.py`
- raw SQL 준비: `src/text_to_sql/core/chat/nodes/raw_sql_prepare_node.py`
- raw SQL 실행: `src/text_to_sql/core/chat/nodes/raw_sql_execute_node.py`
