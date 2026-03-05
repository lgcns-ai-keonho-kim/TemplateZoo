# LanceDB 구성 가이드

이 문서는 파일 기반 벡터 저장소로 LanceDB를 사용할 때 필요한 최소 설정과 검증 절차를 정리합니다.

## 1. 적용 범위

1. 로컬 파일 기반 벡터 엔진 실험
2. LanceDB 엔진 CRUD/벡터 검색 테스트
3. 커스텀 런타임에서 LanceDB 엔진 주입

주의:

- 현재 기본 Chat 그래프는 벡터 검색 노드를 포함하지 않습니다.
- 따라서 LanceDB는 기본 런타임 필수 요소가 아니라 확장/실험용입니다.

## 2. 관련 코드

| 경로 | 역할 |
| --- | --- |
| `src/plan_and_then_execute_agent/integrations/db/engines/lancedb/engine.py` | LanceDB CRUD/벡터 검색 엔진 |
| `src/plan_and_then_execute_agent/integrations/db/engines/lancedb/schema_adapter.py` | 스키마/차원 어댑터 |
| `src/plan_and_then_execute_agent/integrations/db/client.py` | 엔진 공통 퍼사드 |
| `tests/integrations/db/Vector/test_lancedb_engine_vector.py` | LanceDB 벡터 테스트 |

## 3. 환경 변수

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `LANCEDB_URI` | `data/db/vector` | LanceDB 디렉터리 경로 |

예시:

```env
LANCEDB_URI=data/db/vector
```

## 4. 빠른 검증 절차

1. `LANCEDB_URI` 경로를 설정합니다.
2. LanceDB 벡터 테스트를 실행해 엔진 동작을 확인합니다.

```bash
uv run pytest tests/integrations/db/Vector/test_lancedb_engine_vector.py -q
```

3. 필요 시 커스텀 코드에서 `DBClient(LanceDBEngine(...))`를 주입합니다.

## 5. 장애 대응

| 증상 | 원인 후보 | 조치 |
| --- | --- | --- |
| `lancedb 패키지가 설치되어 있지 않습니다.` | 의존성 미설치 | `uv sync` 후 재실행 |
| 컬렉션 생성 실패 | 경로 권한/파일 잠금 | `LANCEDB_URI` 권한 점검 |
| 벡터 검색 결과가 비정상 | 차원 불일치 | 스키마 `vector_dimension`과 입력 벡터 길이 점검 |

## 6. 비고

1. SQLite 엔진은 벡터 검색을 지원하지 않습니다.
2. LanceDB는 로컬 파일 기반이므로 백업/복원 정책을 별도로 운영해야 합니다.
